module "aurora_postgresql" {
  source  = "terraform-aws-modules/rds-aurora/aws"
  version = "6.0.0"

  name              = "otter"
  engine            = "aurora-postgresql"
  engine_mode       = "serverless"
  storage_encrypted = true

  vpc_id                 = var.vpc_id
  subnets                = [var.subnet_az1, var.subnet_az2]
  create_security_group  = false
  allowed_cidr_blocks    = var.subnet_cidr_block
  vpc_security_group_ids = [aws_security_group.otter_postgres_db.id]

  create_random_password = false
  master_username        = local.postgres_credentials.POSTGRES_USER
  master_password        = local.postgres_credentials.POSTGRES_PASSWORD

  monitoring_interval = 60
  apply_immediately   = true
  skip_final_snapshot = true

  scaling_configuration = {
    auto_pause               = true
    min_capacity             = 2
    max_capacity             = 16
    seconds_until_auto_pause = 300
    timeout_action           = "ForceApplyCapacityChange"
  }
  depends_on = [
    local.postgres_credentials
  ]
}

# Security Group
resource "aws_security_group" "otter_postgres_db" {
  name        = "otter_api_db"
  description = "Allow Connection to Postgres Database"
  vpc_id      = var.vpc_id

  ingress {
    description = "Postgres Database Ingress"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.subnet_cidr_block
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "otter-api-db"
  }
}

locals {
  postgres_credentials = jsondecode(
    "${resource.aws_secretsmanager_secret_version.postgres_credentials.secret_string}"
  )
}

# RDS Master Secret
resource "random_password" "database" {
  length           = 25
  special          = true
  override_special = "!#$&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "database" {
  name = "${var.prefix}/otter/database"
}

resource "aws_secretsmanager_secret_version" "postgres_credentials" {
  secret_id     = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({ "POSTGRES_USER" = "postgres", "POSTGRES_PASSWORD" = "${random_password.database.result}" })
}

resource "aws_secretsmanager_secret" "private_key" {
  name = "${var.prefix}/otter/private_key"
}

resource "aws_secretsmanager_secret" "public_key" {
  name = "${var.prefix}/otter/public_key"
}
