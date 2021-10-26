module "dns_example" {
  source                  = "./modules/dns"
  certificate_common_name = "subdomain.example.com"
  alias_domain_name       = "example-acme.com"
}
