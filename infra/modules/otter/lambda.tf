resource "aws_iam_role" "otter" {
  name = "otter-acme"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

data "aws_iam_policy_document" "ecr_repo_iam_policy" {
  statement {
    effect = "Allow"
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage"
    ]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
  }

}

data "aws_iam_policy_document" "otter" {
  statement {
    actions = [
      "dynamodb:UpdateItem",
      "dynamodb:Query",
      "dynamodb:PutItem",
      "dynamodb:Scan",
      "dynamodb:DeleteItem"
    ]
    resources = [
      "arn:aws:dynamodb:${var.region}:${data.aws_caller_identity.otter.account_id}:table/${aws_dynamodb_table.otter.name}",
      "arn:aws:dynamodb:${var.region}:${data.aws_caller_identity.otter.account_id}:table/${aws_dynamodb_table.otter.name}/*"
    ]
  }


  statement {
    actions = [
      "states:StartExecution"
    ]
    resources = [
      "${aws_sfn_state_machine.otter.arn}"
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
      "arn:aws:secretsmanager:${var.region}:${data.aws_caller_identity.otter.account_id}:secret:${var.prefix}/otter/*"
    ]
    actions = [
      "secretsmanager:GetSecretValue"
    ]
  }
}

resource "aws_iam_role_policy" "otter_policy" {
  name   = "otter-acme"
  role   = aws_iam_role.otter.name
  policy = data.aws_iam_policy_document.otter.json
}

resource "aws_iam_role_policy_attachment" "lambda-basic-execution-attachment" {
  role       = aws_iam_role.otter.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda-eni-attachment" {
  role       = aws_iam_role.otter.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaENIManagementAccess"
}
resource "aws_iam_role_policy_attachment" "otter-ecr" {
  role       = aws_iam_role.otter.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}
resource "aws_lambda_function" "otter" {
  description   = "Lambda function that is triggered periodically by CloudWatch Events for Otter ACME Certificate Rotation"
  function_name = "otter"
  role          = aws_iam_role.otter.arn
  image_uri     = "${aws_ecr_repository.otter_infrastructure.repository_url}:router"
  package_type  = "Image"
  timeout       = 900
  image_config {
    command = ["orchestrator.main"]
  }
  depends_on = [
    aws_ecr_repository.otter_infrastructure,
    module.otter_router_build
  ]
  environment {
    variables = {
      aws_region        = "${var.region}"
      dynamodb_table    = "${aws_dynamodb_table.otter.name}",
      step_function_arn = "${aws_sfn_state_machine.otter.arn}",
      prefix            = "${var.prefix}"
    }
  }
}

module "otter_router_build" {
  source = "terraform-aws-modules/lambda/aws//modules/docker-build"

  create_ecr_repo = false
  ecr_repo        = aws_ecr_repository.otter_infrastructure.name
  image_tag       = "router"
  source_path     = "../otter/router"
}

# Lambda Handler (Error Handling Function)
resource "aws_iam_role" "otter_handler" {
  name = "otter-acme-handler"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda-basic-execution-attachment-handler" {
  role       = aws_iam_role.otter_handler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "otter_handler" {
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
    sid = "Database"
    actions = [
      "dynamodb:Query"
    ]

    resources = [
      "${aws_dynamodb_table.otter.arn}/*"
    ]
  }
}

resource "aws_iam_role_policy" "otter_handler_policy" {
  name   = "otter-handler"
  role   = aws_iam_role.otter_handler.name
  policy = data.aws_iam_policy_document.otter_handler.json
}

resource "aws_lambda_function" "otter_handler" {
  description   = "Otter Error Handler External Integration"
  function_name = "otter-handler"
  role          = aws_iam_role.otter_handler.arn
  image_uri     = "${aws_ecr_repository.otter_infrastructure.repository_url}:handler"
  package_type  = "Image"
  timeout       = 900
  image_config {
    command = ["handler.main"]
  }
  depends_on = [
    aws_ecr_repository.otter_infrastructure,
    module.otter_handler
  ]
  environment {
    variables = {
      aws_region     = "${var.region}"
      dynamodb_table = "${aws_dynamodb_table.otter.name}"
      prefix         = "${var.prefix}"
    }
  }
}

module "otter_handler" {
  source = "terraform-aws-modules/lambda/aws//modules/docker-build"

  create_ecr_repo = false
  ecr_repo        = aws_ecr_repository.otter_infrastructure.name
  image_tag       = "handler"
  source_path     = "../otter/handler"
}

# ECR Registry

resource "aws_ecr_repository" "otter_infrastructure" {
  name                 = "otter-infrastructure"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
}
resource "aws_ecr_lifecycle_policy" "ecr_lifecycle_policy" {
  repository = aws_ecr_repository.otter_infrastructure.name

  policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Expire Images Older than 2 Days",
            "selection": {
                "tagStatus": "untagged",
                "countType": "sinceImagePushed",
                "countUnit": "days",
                "countNumber": 2
            },
            "action": {
                "type": "expire"
            }
          },
          {
              "rulePriority": 2,
              "description": "Keep Previous 5 Images",
              "selection": {
                  "tagStatus": "tagged",
                  "tagPrefixList": ["v"],
                  "countType": "imageCountMoreThan",
                  "countNumber": 5
              },
              "action": {
                  "type": "expire"
              }
          }
    ]
}
EOF
}

resource "aws_ecr_repository_policy" "ecr_repo_policy" {
  repository = aws_ecr_repository.otter_infrastructure.name
  policy     = data.aws_iam_policy_document.ecr_repo_iam_policy.json
}
