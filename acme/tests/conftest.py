from string import Template

import boto3
import os
import pytest
from moto import (
    mock_secretsmanager,
    mock_dynamodb2,
    mock_route53,
    mock_stepfunctions,
    mock_sts)


AWS_REGION=os.environ['AWS_DEFAULT_REGION']
@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture
def secretsmanager_client(aws_credentials):
    with mock_secretsmanager():
        conn = boto3.client("secretsmanager", region_name=AWS_REGION)
        conn.create_secret(Name="test/otter/account.json",
                    SecretString='test')
        conn.create_secret(Name="test/otter/account.key",
                    SecretString='test')
        conn.create_secret(Name="test/otter/ca.conf",
                    SecretString='test')
        yield conn

@pytest.fixture
def init_database():
    from otter.router.src.shared.client import DynamoDBClient
    from otter.router.src.shared.device import Device
    @mock_dynamodb2
    def dynamodb_client():
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

        # Create Mock DynamoDB Database
        dynamodb.create_table(
            TableName='ottr-example',
            KeySchema=[
                {"AttributeName": "system_name", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "system_name", "AttributeType": "S"},
                {"AttributeName": "ip_address", "AttributeType": "S"},
                {"AttributeName": "data_center", "AttributeType": "S"},
                {"AttributeName": "host_platform", "AttributeType": "S"},
                {"AttributeName": "origin", "AttributeType": "S"}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'system_name_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'system_name',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    }
                },
                {
                    'IndexName': 'host_platform_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'host_platform',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    }
                },
                {
                    'IndexName': 'ip_address_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'ip_address',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    }
                },
                {
                    'IndexName': 'data_center_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'data_center',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    }
                },
                {
                    'IndexName': 'origin_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'origin',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    }
                }
            ]
        )
        client = DynamoDBClient(region_name=AWS_REGION,
                        table_name='ottr-example')
        device = Device(
            system_name='example.com',
            common_name='example.com',
            ip_address='10.0.0.1',
            certificate_authority='lets_encrypt',
            data_center='DC0',
            host_platform='panos',
            os_version='9.1.0',
            device_model='PA-XXXX',
            origin='API',
            subject_alternative_name=['dev.example.com']
        )
        client.create_item(device)

        device = Device(
            system_name='test.example.com',
            common_name='test.example.com',
            ip_address='10.0.0.2',
            certificate_authority='lets_encrypt',
            data_center='DC0',
            host_platform='Ubuntu',
            os_version='18.04',
            device_model='None',
            origin='API',
            subject_alternative_name=['ubuntu.example.com']
        )
        client.create_item(device)

        table = dynamodb.Table('ottr-example')
        response = table.update_item(
            Key={
                'system_name': 'example.com'
            },
            UpdateExpression="SET certificate_expiration = :certificate_expiration",
            ExpressionAttributeValues={
                ":certificate_expiration": '2021-01-01T00:00:00'
            },
            ReturnValues="UPDATED_NEW"
        )
    return dynamodb_client

@pytest.fixture
def init_dns():
    @mock_route53
    def route53_client():
        conn = boto3.client("route53", region_name="us-east-1")
        # Subdelegate Zone
        conn.create_hosted_zone(
            Name="example-acme.com.",
            CallerReference=str(hash("foo")),
            HostedZoneConfig=dict(
                PrivateZone=True, Comment="Subdelegate Zone"),
        )

        # Main Hosted Zone
        conn.create_hosted_zone(
            Name="example.com.",
            CallerReference=str(hash("bar")),
            HostedZoneConfig=dict(
                PrivateZone=True, Comment="Subdelegate Zone"),
        )

        # example.com Route53 Hosted Zone ID
        hosted_zone_id = conn.list_hosted_zones_by_name(
            DNSName="example.com.").get('HostedZones')[0].get('Id').split('/')[-1]
        # Create CNAME Mapping _acme-challenge.test.example.com =>
        # _acme-challenge.example-acme.com
        cname_record_endpoint_payload = {
            "Comment": "Create CNAME record _acme-challenge.test.example.com",
            "Changes": [
                {
                    "Action": "CREATE",
                    "ResourceRecordSet": {
                        "Name": "_acme-challenge.test.example.com.",
                        "Type": "CNAME",
                        "TTL": 10,
                        "ResourceRecords": [{"Value": "_acme-challenge.test.example-acme.com."}],
                    },
                }
            ],
        }

        conn.change_resource_record_sets(
            HostedZoneId=hosted_zone_id, ChangeBatch=cname_record_endpoint_payload
        )

        return hosted_zone_id
    return route53_client

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