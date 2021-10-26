resource "aws_secretsmanager_secret" "service" {
  name = var.name
}

resource "aws_secretsmanager_secret_policy" "service" {
  secret_arn = aws_secretsmanager_secret.service.arn

  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "OtterPermissions",
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "ecs-tasks.amazonaws.com",
          "lambda.amazonaws.com"
        ]
      },
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:${var.region}:${var.aws_account_id}:secret:${var.name}-*"
    }
  ]
}
POLICY
}