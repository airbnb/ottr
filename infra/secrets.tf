module "lets_encrypt_account_json" {
  source         = "./modules/secrets"
  name           = "${module.otter.prefix}/otter/account.json"
  region         = var.region
  aws_account_id = data.aws_caller_identity.otter.account_id
}

module "lets_encrypt_account_key" {
  source         = "./modules/secrets"
  name           = "${module.otter.prefix}/otter/account.key"
  region         = var.region
  aws_account_id = data.aws_caller_identity.otter.account_id
}

module "lets_encrypt_account_conf" {
  source         = "./modules/secrets"
  name           = "${module.otter.prefix}/otter/ca.conf"
  region         = var.region
  aws_account_id = data.aws_caller_identity.otter.account_id
}

module "slack" {
  source         = "./modules/secrets"
  name           = "${module.otter.prefix}/otter/slack"
  region         = var.region
  aws_account_id = data.aws_caller_identity.otter.account_id
}

# Platform Credentials (Authentication)

module "f5" {
  source         = "./modules/secrets"
  name           = "${module.otter.prefix}/otter/f5"
  region         = var.region
  aws_account_id = data.aws_caller_identity.otter.account_id
}

module "panos" {
  source         = "./modules/secrets"
  name           = "${module.otter.prefix}/otter/panos"
  region         = var.region
  aws_account_id = data.aws_caller_identity.otter.account_id
}

module "lighthouse" {
  source         = "./modules/secrets"
  name           = "${module.otter.prefix}/otter/lighthouse"
  region         = var.region
  aws_account_id = data.aws_caller_identity.otter.account_id
}
