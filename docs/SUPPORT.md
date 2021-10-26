# Supported Platforms

_Supported:_

- [`PAN-OS 8.x`](../platforms/panos-8.x)
- [`PAN-OS 9.x`](../platforms/panos-9.x)
- [`F5 BIG-IP 14.x`](../platforms/f5-14.x)
- [`Opengear Lighthouse 21.x`](../platforms/lighthouse-21.x)
- [`Linux Ubuntu 16.04/18.04/20.04`](../platforms/linux-aws-ssm)

_Roadmap:_

- Windows Server 2019

## Disclosures

- PanOS 8.x does not use HTTP Headers to pass API Tokens into the request but
  rather passes the credentials through the URL. If the runtime does not execute
  successfully, credentials being leaked within CloudWatch Logs. If possible
  upgrade PanOS to 9.x or later.
- F5 14.x has an /etc/hosts.allow configuration which blocks
  SSH traffic if you have it enabled. You will need to add the IP Ranges from
  the subnets that Ottr comes from otherwise Apache will likely fail and a
  restart of the service will need to be done manually.

  - https://support.f5.com/csp/article/K5380

- Authentication is based off of username and password. For the majority of
  platforms we need to retrieve an API Key after authentication with a service
  account. There may be additional ways to do it with an SSH Client with a
  Public/Private Key Pair but that is not the current implementation.
- Because we are using Public CAs that leverage the ACME Protocol any
  certificates that are generated will appear on certificate transparency
  logs: `https://crt.sh/`
- RDS database master password is auto-generated through Terraform. If you are doing
  a local deployment the credentials will be in plaintext within your
  `terraform.tfstate` and `terraform.tfstate.backup` files. If you are using
  this for a production environment please deploy through Terraform Enterprise
  (TFE) or the state files stored in an S3 backend.
