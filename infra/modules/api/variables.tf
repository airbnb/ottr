variable "region" {
  type    = string
  default = "us-east-1"
}

variable "certificate_arn" {
  type = string
}
variable "vpc_id" {
  type = string
}

variable "subnet_az1" {
  type = string
}

variable "subnet_az2" {
  type = string
}

variable "ingress_ip_ranges" {
  description = "Ingress IP ranges that will be allowed to reach the Otter API over 443 and SSH access to EC2 backed ECS Cluster."
  type        = list(string)
}

variable "subnet_cidr_block" {
  description = "For devices running within AWS that require certificate rotations, you will need to allow ingress rules from the Otter subnets (subnet_az1 and subnet_az2). This variable are the CIDR Blocks for subnet_az1 and subnet_az2 i.e. [10.0.0.1/24, 10.0.0.2/24]"
  type        = list(string)
}

variable "instance_type" {
  type    = string
  default = "t2.small"
}

variable "ec2_desired_capacity" {
  type    = number
  default = 2
}

variable "ec2_minimum_capacity" {
  type    = number
  default = 1
}

variable "ec2_maximum_capacity" {
  type    = number
  default = 2
}

variable "dynamodb_table" {
  type = string
}

variable "ecs_cluster" {
  type = string
}
variable "internal_alb" {
  type    = string
  default = true
}

variable "prefix" {
  type = string
}

variable "hosted_zone_ids" {
  type = list(string)
}

variable "api_domain_name" {
  type = string
}

variable "api_zone_id" {
  type = string
}
data "aws_caller_identity" "otter" {}
