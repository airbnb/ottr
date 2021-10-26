module "api" {
  source            = "./modules/api"
  dynamodb_table    = module.otter.dynamodb_table
  prefix            = module.otter.prefix
  certificate_arn   = module.acm.acm_certificate_arn
  ecs_cluster       = module.otter.ecs_cluster
  ingress_ip_ranges = ["10.0.0.0/24"]
  subnet_cidr_block = ["10.0.0.0/28", "10.0.0.16/28"]
  subnet_az1        = "subnet-xxxxxxxx"
  subnet_az2        = "subnet-yyyyyyyy"
  vpc_id            = "vpc-xxxxxxxx"
  region            = "us-east-1"
  internal_alb      = true
  hosted_zone_ids   = ["arn:aws:route53:::hostedzone/QWERTYUIOPASDF"]
  api_domain_name   = "ottr.example.com"
  api_zone_id       = "QWERTYUIOPASDF"
  depends_on = [
    module.otter,
    module.acm
  ]
}

module "acm" {
  source  = "terraform-aws-modules/acm/aws"
  version = "~> 3.0"

  domain_name = "ottr.example.com"
  zone_id     = "QWERTYUIOPASDF"

  wait_for_validation = true
}
