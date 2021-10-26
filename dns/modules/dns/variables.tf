variable "certificate_common_name" {
  type        = string
  description = "Common name to use for certificate validation"
}

variable "subject_alternative_names" {
  type        = list(string)
  description = "List of subject alternative names for certificate validation"
  default     = []
}

variable "private_zone" {
  type        = bool
  description = "Route53 DNS Zone type"
  default     = false
}

variable "alias_domain_name" {
  type        = string
  description = "Route53 DNS Subdelegate Domain Name"
}

variable "ttl" {
  type        = string
  description = "Route53 DNS record TTL"
  default     = "300"
}
