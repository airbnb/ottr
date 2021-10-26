output "otter_appliance_ecs_role" {
  value       = aws_iam_role.otter_appliance_ecs_fargate.arn
  description = "Otter ECS Fargate Execution Role for Appliance Platforms"
  sensitive   = false
}

output "otter_server_ecs_role" {
  value       = aws_iam_role.otter_server_ecs_fargate.arn
  description = "Otter ECS Fargate Execution Role for Server Platforms"
  sensitive   = false
}

output "dynamodb_table" {
  value       = aws_dynamodb_table.otter.name
  description = "DynamoDB Table Asset Inventory Name"
  sensitive   = false
}

output "prefix" {
  value       = var.prefix
  description = "Secrets Manager Prefix String"
}

output "ecs_cluster" {
  value       = aws_ecs_cluster.otter_fargate.id
  description = "Otter ECS Cluster ID"
}
