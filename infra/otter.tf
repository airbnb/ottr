module "otter" {
  source                = "./modules/otter"
  acme_subdelegate_zone = "example-acme.com"
  hosted_zone_ids       = ["arn:aws:route53:::hostedzone/QWERTYUIOPASDF"]
  subnet_cidr_block     = ["10.0.0.0/28", "10.0.0.16/28"]
  subnet_az1            = "subnet-xxxxxxxx"
  subnet_az2            = "subnet-yyyyyyyy"
  private_subnet        = false
  vpc_id                = "vpc-xxxxxxxx"
  region                = "us-east-21"
  cloudwatch_schedule   = "rate(12 hours)"
  prefix                = "development"

  # Certificate Signing Request Parameters
  country           = "US"
  state             = "CA"
  locality          = "San Francisco"
  email             = "security@example.com"
  organization      = "Example, Inc"
  organization_unit = "Security"
}
