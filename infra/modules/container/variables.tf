# ECR Variables
variable "repo_name" {
  type        = string
  description = "ECR Repository Name"
}


variable "image_tag_mutability" {
  type        = string
  description = "Image tag mutability of: [MUTABLE, IMMUTABLE]. Defaults to MUTABLE."
  default     = "MUTABLE"
}

# ECS Variables
variable "family" {
  type        = string
  description = "ECR Task Name"
}

variable "task_role_arn" {
  type        = string
  description = "IAM Role ARN for ECS"
}

variable "execution_role_arn" {
  type        = string
  description = "IAM Role ARN to Execute ECS Task"
}

variable "region" {
  type    = string
  default = "us-east-1"
}
