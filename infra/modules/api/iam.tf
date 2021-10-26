# ECS API IAM Resource
resource "aws_iam_role" "otter_ecs_api" {
  name               = "otter-ecs-api"
  description        = "IAM Role for Otter PKI API on ECS"
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

data "aws_iam_policy_document" "otter_ecs_api_policy_document" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:Query",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Scan"
    ]
    resources = [
      "arn:aws:dynamodb:${var.region}:${data.aws_caller_identity.otter.account_id}:table/${var.dynamodb_table}",
      "arn:aws:dynamodb:${var.region}:${data.aws_caller_identity.otter.account_id}:table/${var.dynamodb_table}/*"
    ]
  }

  statement {
    effect    = "Allow"
    resources = ["*"]
    actions = [
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
    actions = [
      "states:StartExecution"
    ]
    resources = [
      "arn:aws:states:${var.region}:${data.aws_caller_identity.otter.account_id}:stateMachine:otter-state"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      "arn:aws:secretsmanager:${var.region}:${data.aws_caller_identity.otter.account_id}:secret:${var.prefix}/otter/*"
    ]
  }
}

resource "aws_iam_role_policy" "otter_ecs_api_policy" {
  name   = "otter-ecs-api"
  role   = aws_iam_role.otter_ecs_api.name
  policy = data.aws_iam_policy_document.otter_ecs_api_policy_document.json
}

resource "aws_iam_role_policy_attachment" "ecs_policy_attachment" {
  role       = aws_iam_role.otter_ecs_api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# --
data "aws_iam_policy_document" "ecs_agent" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "ecs_agent_ebs" {
  statement {
    effect = "Allow"
    actions = [
      "ec2:AttachVolume",
      "ec2:CreateVolume",
      "ec2:CreateSnapshot",
      "ec2:CreateTags",
      "ec2:DeleteVolume",
      "ec2:DeleteSnapshot",
      "ec2:DescribeAvailabilityZones",
      "ec2:DescribeInstances",
      "ec2:DescribeVolumes",
      "ec2:DescribeVolumeAttribute",
      "ec2:DescribeVolumeStatus",
      "ec2:DescribeSnapshots",
      "ec2:CopySnapshot",
      "ec2:DescribeSnapshotAttribute",
      "ec2:DetachVolume",
      "ec2:ModifySnapshotAttribute",
      "ec2:ModifyVolumeAttribute",
      "ec2:DescribeTags"
    ]
    resources = ["*"]
  }
}
resource "aws_iam_role" "ecs_agent" {
  name               = "ecs-agent"
  assume_role_policy = data.aws_iam_policy_document.ecs_agent.json
}


resource "aws_iam_role_policy_attachment" "ecs_agent" {
  role       = aws_iam_role.ecs_agent.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_role_policy" "ecs_agent_volume" {
  name   = "otter-ecs-agent-volume"
  role   = aws_iam_role.ecs_agent.name
  policy = data.aws_iam_policy_document.ecs_agent_ebs.json
}

resource "aws_iam_instance_profile" "ecs_agent" {
  name = "ecs-agent"
  role = aws_iam_role.ecs_agent.name
}
