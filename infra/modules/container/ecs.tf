resource "aws_ecs_task_definition" "otter" {
  family                   = var.family
  network_mode             = "awsvpc"
  task_role_arn            = var.task_role_arn
  execution_role_arn       = var.execution_role_arn
  cpu                      = 256
  memory                   = 2048
  requires_compatibilities = ["FARGATE"]
  container_definitions    = <<DEFINITION
    [
      {
        "volumesFrom": [],
        "memory": 512,
        "portMappings": [],
        "essential": true,
        "mountPoints": [],
        "name": "otter",
        "environment": [],
        "image": "${aws_ecr_repository.otter.repository_url}:latest",
        "cpu": 1,
        "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
            "awslogs-group": "/ecs/otter",
            "awslogs-region": "${var.region}",
            "awslogs-stream-prefix": "/${var.family}"
          }
        }
      }
    ]
DEFINITION
}

data "aws_ecs_task_definition" "otter" {
  depends_on      = [aws_ecs_task_definition.otter]
  task_definition = aws_ecs_task_definition.otter.family
}
