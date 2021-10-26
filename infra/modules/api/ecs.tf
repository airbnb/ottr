data "template_file" "otter-envoy" {
  template = file("task-definition.json")
  vars = {
    envoy_image_uri              = "${aws_ecr_repository.otter_acme_api.repository_url}:envoy"
    otter_image_uri              = "${aws_ecr_repository.otter_acme_api.repository_url}:server"
    service_name                 = "otter-api"
    dns_namespace                = var.api_domain_name
    secrets_manager_database_arn = aws_secretsmanager_secret.database.arn
    aurora_endpoint              = module.aurora_postgresql.cluster_endpoint
    region                       = var.region
  }
  depends_on = [
    module.aurora_postgresql
  ]
}

resource "aws_ecs_task_definition" "otter_api" {
  family                   = "otter-api"
  container_definitions    = data.template_file.otter-envoy.rendered
  requires_compatibilities = ["FARGATE"]
  memory                   = 4096
  cpu                      = 2048
  network_mode             = "awsvpc"
  execution_role_arn       = aws_iam_role.otter_ecs_api.arn
  task_role_arn            = aws_iam_role.otter_ecs_api.arn
}

# ECS Service
resource "aws_ecs_service" "otter_ecs_service" {
  name                               = "otter-api-service"
  cluster                            = var.ecs_cluster
  desired_count                      = 2
  task_definition                    = aws_ecs_task_definition.otter_api.id
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  launch_type                        = "FARGATE"

  load_balancer {
    target_group_arn = aws_alb_target_group.otter_tg.arn
    container_name   = "envoy"
    container_port   = 8443
  }

  network_configuration {
    subnets          = [var.subnet_az1, var.subnet_az2]
    security_groups  = [aws_security_group.alb_to_ecs.id]
    assign_public_ip = var.internal_alb ? false : true
  }
  provisioner "local-exec" {
    when    = destroy
    command = "./modules/api/templates/stop-tasks.sh"
    environment = {
      CLUSTER = "otter-api"
      SERVICE = "otter-api-service"
    }
  }

  depends_on = [
    aws_alb_listener.api_ssl_listener,
    aws_alb_target_group.otter_tg,
  ]
}

# Internal Traffic to Load Balancer Security Group
resource "aws_security_group" "internal_to_alb" {
  name        = "otter_api_alb"
  description = "Allow API Inbound Traffic to ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "TLS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.ingress_ip_ranges
  }

  ingress {
    description = "API Container Port"
    from_port   = 8443
    to_port     = 8443
    protocol    = "tcp"
    cidr_blocks = var.ingress_ip_ranges
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {
    Name = "otter-api-alb"
  }
}

# Load Balancer to ECS Security Group
resource "aws_security_group" "alb_to_ecs" {
  name        = "otter_api_cluster"
  description = "Allow API Inbound Traffic from ALB to Cluster"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Container Port Mapping"
    from_port       = 8443
    to_port         = 8443
    protocol        = "tcp"
    security_groups = [aws_security_group.internal_to_alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "otter-api-cluster"
  }
}
