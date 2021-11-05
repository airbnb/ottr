resource "aws_sfn_state_machine" "otter" {
  name     = "otter-state"
  role_arn = aws_iam_role.otter_acme_state.arn

  definition = <<EOF
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
						"TimeoutSeconds": 600,
						"Resource": "arn:aws:states:::ecs:runTask.sync",
						"Parameters": {
							"LaunchType": "FARGATE",
							"Cluster": "otter",
							"TaskDefinition.$": "$.asset.task_definition",
							"Overrides": {
								"ContainerOverrides": [{
									"Name": "otter",
									"Environment": [
										{
											"Name": "SYSTEM_NAME",
											"Value.$": "$.asset.hostname"
										},
										{
											"Name": "COMMON_NAME",
											"Value.$": "$.asset.common_name"
										},
										{
											"Name": "VALIDATE_CERTIFICATE",
											"Value.$": "$.asset.certificate_validation"
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
											"Value": "${data.aws_caller_identity.otter.account_id}"
										},
										{
											"Name": "ACME_DNS",
											"Value": "${aws_route53_zone.acme.name}"
										},
										{
											"Name": "PREFIX",
											"Value": "${var.prefix}"
										},
										{
											"Name": "country",
											"Value": "${var.country}"
										},
										{
											"Name": "state",
											"Value": "${var.state}"
										},
										{
											"Name": "locality",
											"Value": "${var.locality}"
										},
										{
											"Name": "email",
											"Value": "${var.email}"
										},
										{
											"Name": "organization",
											"Value": "${var.organization}"
										},
										{
											"Name": "organization_unit",
											"Value": "${var.organization_unit}"
										}
									]
								}]
							},
							"NetworkConfiguration": {
								"AwsvpcConfiguration": {
									"SecurityGroups": [
										"${aws_security_group.otter_security_group.id}"
									],
									"Subnets": [
										"${var.subnet_az1}",
										"${var.subnet_az2}"
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
							"FunctionName": "${aws_lambda_function.otter_handler.arn}",
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
			"MaxConcurrency": 50,
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
EOF
}

# State Machine IAM

data "aws_iam_policy_document" "otter_states_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "otter_acme_state" {
  name               = "otter-acme-state"
  description        = "IAM Role for Otter Step Functions}."
  assume_role_policy = data.aws_iam_policy_document.otter_states_policy.json
}

data "aws_iam_policy_document" "sfn_iam_policy_document" {
  statement {
    sid     = "LambdaInvokeEvidentAutoremediateFunctions"
    actions = ["lambda:InvokeFunction"]

    resources = [
      "${aws_lambda_function.otter_handler.arn}"
    ]
  }

  statement {
    sid = "ECS"
    actions = [
      "ecs:RunTask"
    ]

    resources = [
      "arn:aws:ecs:${var.region}:${data.aws_caller_identity.otter.account_id}:task-definition/otter*"
    ]
  }

  statement {
    sid = "PassRole"
    actions = [
      "iam:PassRole"
    ]

    resources = [
      "${aws_iam_role.otter_appliance_ecs_fargate.arn}",
      "${aws_iam_role.otter_server_ecs_fargate.arn}"
    ]
  }


  statement {
    sid = "ManagedRule"
    actions = [
      "events:PutTargets",
      "events:PutRule",
      "events:DescribeRule"
    ]

    resources = [
      "*"
    ]
  }
}

resource "aws_iam_role_policy" "otter_acme_state" {
  name   = "otter-acme-state"
  role   = aws_iam_role.otter_acme_state.name
  policy = data.aws_iam_policy_document.sfn_iam_policy_document.json
}
