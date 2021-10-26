terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "3.58.0"
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
