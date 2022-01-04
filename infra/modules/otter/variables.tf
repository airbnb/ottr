variable "database" {
  type    = string
  default = "otter"
}

variable "acme_subdelegate_zone" {
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

variable "private_subnet" {
  type = bool
}
variable "hosted_zone_ids" {
  description = "List of Route53 DNS Hosted Zone IDs that your organization owns that will be used to validate domain during the certificate rotation process."
  type        = list(string)
}

variable "subnet_cidr_block" {
  description = "For devices running within AWS that require certificate rotations, you will need to allow ingress rules from the Otter subnets (subnet_az1 and subnet_az2). This variable are the CIDR Blocks for subnet_az1 and subnet_az2 i.e. [10.0.0.1/24, 10.0.0.2/24]"
  type        = list(string)
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "cloudwatch_schedule" {
  description = "Frequency of Ottr beginning a job, this is the value for the schedule_expression field within aws_cloudwatch_event_rule in Terraform."
  type        = string
  default     = "rate(1 day)"
}


variable "prefix" {
  type    = string
  default = "prod"
}

data "aws_caller_identity" "otter" {}

variable "country" {
  description = "Certificate Signing Request Field: Country"
  type        = string
}

variable "state" {
  description = "Certificate Signing Request Field: State"
  type        = string
}

variable "locality" {
  description = "Certificate Signing Request Field: City"
  type        = string
}

variable "email" {
  description = "Certificate Signing Request Field: Organization Email"
  type        = string
}

variable "organization" {
  description = "Certificate Signing Request Field: Company"
  type        = string
}

variable "organization_unit" {
  description = "Certificate Signing Request Field: Team"
  type        = string
}

