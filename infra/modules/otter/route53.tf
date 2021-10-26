resource "aws_route53_zone" "acme" {
  name    = var.acme_subdelegate_zone
  comment = "PKI DNS Validation Subdelegate Zone"
}
