
locals {
  domain_mappings = {
    for k in compact(concat(tolist([var.certificate_common_name]), var.subject_alternative_names)) : k => join(".", tolist([reverse(split(".", k))[1], reverse(split(".", k))[0]]))
  }
  common_name_hostname = split(".${join(".", tolist([reverse(split(".", var.certificate_common_name))[1], reverse(split(".", var.certificate_common_name))[0]]))}", var.certificate_common_name)[0]
  dns_record_prefix    = "_acme-challenge"
}

data "aws_route53_zone" "selected" {
  for_each = local.domain_mappings

  name         = "${each.value}."
  private_zone = var.private_zone
}

resource "aws_route53_record" "default" {
  for_each = local.domain_mappings

  zone_id = data.aws_route53_zone.selected[each.key].zone_id
  name    = join(".", concat(tolist([local.dns_record_prefix]), tolist([split(".${each.value}", "${each.key}")[0]]), tolist([data.aws_route53_zone.selected[each.key].name])))
  type    = "CNAME"
  ttl     = var.ttl
  records = [join(".", concat(tolist([local.dns_record_prefix]), tolist([local.common_name_hostname]), tolist([var.alias_domain_name])))]
}
