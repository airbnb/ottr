## DNS Validation with Subdelegation:

The typical flow when you send a Certificate Signing Request (CSR) to a
Certificate Authority (CA) is to update a DNS TXT Record within your domain to
validate that you have ownership. With Ottr the service handles this all
without manual intervention by having IAM Permissions to Route53.

Currently AWS does not give the granularity to specify the ability to only write
TXT records to a specific domain, instead if you need to write a TXT record you
must provide `route53:ChangeResourceRecordSets` permissions which gives
permissions to change A Records, MX Records, CNAME Records, etc.

An alternative to providing write access to your production hosted zone is for Ottr
to use a CNAME record for subdelegation and allow the ACME Client to use a DNS
Alias to confirm domain ownership. What the looks like can be explained below:

1. Certificate Authority (CA) needs to generate certificate for
   `subdomain.example.com`.
2. ACME Client needs to write a TXT Record to your production domain
   `example.com` but we do not want to the ability for the client to change DNS records
   in our production domain.
3. We create another domain named `example-acme.com` which you can define and
   build within `infra/otter.tf`.
4. Create a CNAME Record between `_acme-challenge.subdomain.example.com` to
   `_acme-challenge.subdomain.example-acme.com`.
5. Since Ottr has IAM Permissions to read `example.com` records and write
   permissions to `example-acme.com`, when the ACME client attempts to write a
   DNS TXT record to `_acme-challenge.subdomain.example.com` it will be routed
   and written to `_acme-challenge.example-acme.com` instead.

This architecture reduces the permissions Ottr is able to have to modify your
organization's DNS records and ultimately only gives the ability to confirm
domain ownership without the ability to modify other records.

`dns/platform.tf`: Terraform Module for Ottr DNS Subdelegation

| Variable                  | Optional | Type         | Description                             | Default | Example                                     |
| ------------------------- | -------- | ------------ | --------------------------------------- | ------- | ------------------------------------------- |
| certificate_common_name   | False    | string       | Certificate Common Name                 |         | "`ottr.example.com`"                        |
| alias_domain_name         | False    | string       | Route53 Subdelegate DNS Zone            |         | ["`example-acme.com`"]                      |
| subject_alternative_names | True     | List[string] | Certificate Subject Alternative Name(s) | []      | ["`test.example.com`", "`test.example.io`"] |
| private_zone              | True     | bool         | Route53 Private Zone                    | `false` | `true`                                      |
| ttl                       | True     | string       | DNS Record TTL                          | "`300`" | "`100`"                                     |

_Allow Ottr to perform DNS verification for a certificate that is
valid for ottr.example.com, test.example.com, and test.example.io._

```py
module "dns_example" {
  source                    = "./modules/dns"
  certificate_common_name   = "ottr.example.com"
  subject_alternative_names = ["test.example.com", "test.example.io"]
}
```

_After the module is built within Route53 these CNAME Records will be built:_

```sh
_acme-challenge.test.example.com
  =>   _acme-challenge.test.example-acme.com

_acme-challenge.01.variable.example.com
  =>   _acme-challenge.test.example-acme.com

_acme-challenge.test.example.io
  =>   _acme-challenge.test.example-acme.com
```
