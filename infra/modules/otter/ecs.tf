# ECS Fargate IAM Resource
resource "aws_iam_role" "otter_appliance_ecs_fargate" {
  name               = "otter-appliance-ecs-fargate"
  description        = "IAM Role for Otter PKI Fargate Task for Appliance Platforms"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role" "otter_server_ecs_fargate" {
  name               = "otter-server-ecs-fargate"
  description        = "IAM Role for Otter PKI Fargate Task for Server Platforms"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

data "aws_iam_policy_document" "otter_appliance_ecs_fargate_policy_document" {
  statement {
    actions = [
      "dynamodb:Query",
      "dynamodb:UpdateItem"
    ]
    resources = [
      "arn:aws:dynamodb:${var.region}:${data.aws_caller_identity.otter.account_id}:table/${aws_dynamodb_table.otter.name}",
      "arn:aws:dynamodb:${var.region}:${data.aws_caller_identity.otter.account_id}:table/${aws_dynamodb_table.otter.name}/*"
    ]
  }

  statement {
    effect    = "Allow"
    resources = ["arn:aws:iam::${data.aws_caller_identity.otter.account_id}:role/${aws_iam_role.otter_appliance_ecs_fargate.name}"]
    actions = [
      "sts:AssumeRole"
    ]
  }

  statement {
    effect    = "Allow"
    resources = ["*"]
    actions = [
      "route53:ListHostedZones",
      "route53:ListHostedZonesByName"
    ]
  }

  statement {
    effect    = "Allow"
    resources = var.hosted_zone_ids
    actions = [
      "route53:GetHostedZone",
      "route53:ListResourceRecordSets",
    ]
  }

  statement {
    effect = "Allow"
    resources = [
      "arn:aws:route53:::hostedzone/${aws_route53_zone.acme.zone_id}"
    ]
    actions = [
      "route53:GetHostedZone",
      "route53:ListResourceRecordSets",
      "route53:ChangeResourceRecordSets"
    ]
  }

  statement {
    effect = "Allow"
    resources = [
      "arn:aws:secretsmanager:${var.region}:${data.aws_caller_identity.otter.account_id}:secret:${var.prefix}/otter/*"
    ]
    actions = [
      "secretsmanager:GetSecretValue"
    ]
  }
}

data "aws_iam_policy_document" "otter_server_ecs_fargate_policy_document" {
  statement {
    actions = [
      "dynamodb:Query",
      "dynamodb:UpdateItem"
    ]
    resources = [
      "arn:aws:dynamodb:${var.region}:${data.aws_caller_identity.otter.account_id}:table/${aws_dynamodb_table.otter.name}",
      "arn:aws:dynamodb:${var.region}:${data.aws_caller_identity.otter.account_id}:table/${aws_dynamodb_table.otter.name}/*"
    ]
  }

  statement {
    effect    = "Allow"
    resources = ["arn:aws:iam::${data.aws_caller_identity.otter.account_id}:role/${aws_iam_role.otter_server_ecs_fargate.name}"]
    actions = [
      "sts:AssumeRole"
    ]
  }

  statement {
    effect    = "Allow"
    resources = ["*"]
    actions = [
      "route53:ListHostedZones",
      "route53:ListHostedZonesByName"
    ]
  }

  statement {
    effect    = "Allow"
    resources = var.hosted_zone_ids
    actions = [
      "route53:GetHostedZone",
      "route53:ListResourceRecordSets"
    ]
  }

  statement {
    effect = "Allow"
    resources = [
      "arn:aws:route53:::hostedzone/${aws_route53_zone.acme.zone_id}"
    ]
    actions = [
      "route53:GetHostedZone",
      "route53:ListResourceRecordSets",
      "route53:ChangeResourceRecordSets"
    ]
  }

  statement {
    effect = "Allow"
    resources = [
      "arn:aws:secretsmanager:${var.region}:${data.aws_caller_identity.otter.account_id}:secret:${var.prefix}/otter/*"
    ]
    actions = [
      "secretsmanager:GetSecretValue"
    ]
  }

  statement {
    effect    = "Allow"
    resources = ["*"]
    actions = [
      "ssm:DescribeInstanceInformation",
      "ssm:GetCommandInvocation"
    ]
  }

  statement {
    effect = "Allow"
    resources = [
      "arn:aws:ec2:${var.region}:${data.aws_caller_identity.otter.account_id}:instance/*",
      "arn:aws:ssm:*:*:document/AWS-RunShellScript",
      "arn:aws:ssm:*:*:document/AWS-RunPowerShellScript"
    ]
    actions = [
      "ssm:SendCommand"
    ]
  }
}

resource "aws_iam_role_policy" "otter_appliance_ecs_fargate_policy" {
  name   = "otter-appliance-ecs-fargate"
  role   = aws_iam_role.otter_appliance_ecs_fargate.name
  policy = data.aws_iam_policy_document.otter_appliance_ecs_fargate_policy_document.json
}

resource "aws_iam_role_policy" "otter_server_ecs_fargate_policy" {
  name   = "otter-server-ecs-fargate"
  role   = aws_iam_role.otter_server_ecs_fargate.name
  policy = data.aws_iam_policy_document.otter_server_ecs_fargate_policy_document.json
}

resource "aws_iam_role_policy_attachment" "otter_appliance_ecs_fargate_policy_attachment" {
  role       = aws_iam_role.otter_appliance_ecs_fargate.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "otter_server_ecs_fargate_policy_attachment" {
  role       = aws_iam_role.otter_server_ecs_fargate.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Fargate Cluster
resource "aws_ecs_cluster" "otter_fargate" {
  name               = "otter"
  capacity_providers = ["FARGATE"]

  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}
resource "aws_cloudwatch_log_group" "otter_log_group" {
  name = "/ecs/otter"
}

# Security Group
resource "aws_security_group" "otter_security_group" {
  name        = "otter_security_group"
  description = "Egress Traffic"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "otter-security-group"
  }
}
