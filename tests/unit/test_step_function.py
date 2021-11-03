from string import Template
import json

import boto3
from moto import mock_sts, mock_stepfunctions

from otter.router.src.shared.client import start_execution, lookup_attributes

region = "us-east-1"
account_id = None

definition: str = Template(
    """
{
	"Comment": "Otter ECS Fargate Execution Error Handler",
	"StartAt": "Map",
	"States": {
		"Map": {
			"Type": "Map",
			"Iterator": {
				"StartAt": "PlatformTaskExecution",
				"States": {
					"PlatformTaskExecution": {
						"Type": "Task",
						"TimeoutSeconds": 3600,
						"Resource": "arn:aws:states:::ecs:runTask.sync",
						"Parameters": {
							"LaunchType": "FARGATE",
							"Cluster": "otter",
							"TaskDefinition.$": "$.asset.task_definition",
							"Overrides": {
								"ContainerOverrides": [{
									"Name": "otter",
									"Environment": [{
											"Name": "HOSTNAME",
											"Value.$": "$.asset.hostname"
										},
                    {
											"Name": "HOSTED_ZONE_ID",
											"Value.$": "$.asset.dns"
										},
										{
											"Name": "AWS_REGION",
											"Value.$": "$.region"
										},
										{
											"Name": "DYNAMODB_TABLE",
											"Value.$": "$.table"
										},
                    {
                      "Name": "ACCOUNT_ID",
                      "Value": "xxx"
                    },
                    {
                      "Name": "ACME_DNS",
                      "Value": "xxx"
                    },
                    {
                      "Name": "PREFIX",
                      "Value": "xxx"
                    },
                    {
                      "Name": "country",
                      "Value": "xxx"
                    },
                    {
                      "Name": "state",
                      "Value": "xxx"
                    },
                    {
                      "Name": "locality",
                      "Value": "xxx"
                    },
                    {
                      "Name": "email",
                      "Value": "xxx"
                    },
                    {
                      "Name": "organization",
                      "Value": "xxx"
                    },
                    {
                      "Name": "organization_unit",
                      "Value": "xxx"
                    }
									]
								}]
							},
							"NetworkConfiguration": {
								"AwsvpcConfiguration": {
									"SecurityGroups": [
										"xxx"
									],
									"Subnets": [
										"xxx",
										"xxx"
									],
									"AssignPublicIp": "DISABLED"
								}
							}
						},
						"Catch": [{
							"ErrorEquals": ["States.ALL"],
							"Next": "Message"
						}],
						"Next": "Exit"
					},
					"Message": {
						"Type": "Task",
						"Resource": "arn:aws:states:::lambda:invoke",
						"Parameters": {
							"FunctionName": "xxx",
							"Payload": {
								"Input.$": "$"
							}
						},
						"Retry": [{
							"ErrorEquals": ["States.ALL"],
							"IntervalSeconds": 1,
							"MaxAttempts": 3,
							"BackoffRate": 2
						}],
						"End": true
					},
					"Exit": {
						"Type": "Pass",
						"Result": "End",
						"End": true
					}
				}
			},
			"End": true,
			"MaxConcurrency": 1,
			"InputPath": "$",
			"ItemsPath": "$.assets",
			"Parameters": {
				"asset.$": "$$.Map.Item.Value",
				"region.$": "$.region",
				"table.$": "$.table"
			}
		}
	}
}
    """
)


@mock_stepfunctions
@mock_sts
def test_state_machine_start_execution(monkeypatch):
    client = boto3.client("stepfunctions", region_name=region)

    sm = client.create_state_machine(
        name="name", definition=str(definition), roleArn=_get_default_role()
    )

    monkeypatch.setenv('step_function_arn', sm["stateMachineArn"])
    monkeypatch.setenv('aws_region', region)
    monkeypatch.setenv('dynamodb_table', 'otter')

    payload = {
        "assets": [
            {
                "hostname": "test.example.com",  # PanOS 9.x Device
                "common_name": "test.example.com",
                "certificate_validation": "True",
                "task_definition": "otter-panos-9x-lets-encrypt",
                "dns": "XXXXXXXXXXXXXX"  # Route53 Hosted Zone ID for example.com
            },
            {
                "hostname": "test.company.com",  # F5 14.x Device,
                "common_name": "test.example.com",
                "certificate_validation": "True",
                "task_definition": "otter-f5-14x-lets-encrypt",
                "dns": "YYYYYYYYYYYYYY"  # Route53 Hosted Zone ID for company.com
            }
        ],
        "region": "us-east-1",
        "table": "otter"  # DynamoDB Table Name
    }
    string_payload = json.dumps(payload)
    execution = start_execution(string_payload)
    assert execution["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_lookup_attribute():
    device = {
        "system_name": "test.example.com",
        "certificate_authority": "lets_encrypt",
        "certificate_expiration": "2021-10-31T01:49:35",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "origin": "API",
        "os_version": "9.1.0",
        "subject_alternative_name": [
            "test01.example.com"
        ]
    }
    task_definition, hosted_zone_id = lookup_attributes(device)
    assert task_definition == "otter-panos-9x-lets-encrypt"


def test_lookup_attribute_no_model():
    device = {
        "system_name": "ubuntu.example.com",
        "certificate_authority": "lets_encrypt",
        "certificate_expiration": "2021-10-31T01:49:35",
        "data_center": "AWS",
        "device_model": "N/A",
        "host_platform": "Ubuntu",
        "ip_address": "10.0.0.1",
        "origin": "API",
        "os_version": "20.04",
        "subject_alternative_name": [
            "ubuntu02.example.com"
        ]
    }
    task_definition, hosted_zone_id = lookup_attributes(device)
    assert task_definition == "otter-linux-aws-ssm-lets-encrypt"


def test_lookup_attribute_exception():
    device = {
        "system_name": "test.example.com",
        "certificate_authority": "lets_encrypt",
        "certificate_expiration": "None",
        "data_center": "DC1",
        "device_model": "PA-XXXX",
        "host_platform": "panos",
        "ip_address": "10.0.0.1",
        "origin": "API",
        "os_version": "0.0.1",
        "subject_alternative_name": [
            "test01.example.com"
        ]
    }
    task_definition, hosted_zone_id = lookup_attributes(device)
    assert task_definition == None


def _get_account_id():
    global account_id
    if account_id:
        return account_id
    sts = boto3.client("sts", region_name=region)
    identity = sts.get_caller_identity()
    account_id = identity["Account"]
    return account_id


def _get_default_role():
    return "arn:aws:iam::" + _get_account_id() + ":role/unknown_sf_role"
