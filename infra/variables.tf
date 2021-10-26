terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "3.1.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "3.63.0"
    }
  }
}

provider "aws" {
  region  = var.region
  profile = "default"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

data "aws_caller_identity" "otter" {}
