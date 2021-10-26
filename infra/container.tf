module "otter_panos_8x" {
  source             = "./modules/container"
  region             = "us-east-1"
  repo_name          = "otter-panos-8.x"
  family             = "otter-panos-8x-lets-encrypt"
  task_role_arn      = module.otter.otter_appliance_ecs_role
  execution_role_arn = module.otter.otter_appliance_ecs_role
}

module "otter_panos_9x" {
  source             = "./modules/container"
  repo_name          = "otter-panos-9.x"
  family             = "otter-panos-9x-lets-encrypt"
  task_role_arn      = module.otter.otter_appliance_ecs_role
  execution_role_arn = module.otter.otter_appliance_ecs_role
}

module "otter_f5_14x" {
  source             = "./modules/container"
  repo_name          = "otter-f5-14.x"
  family             = "otter-f5-14x-lets-encrypt"
  task_role_arn      = module.otter.otter_appliance_ecs_role
  execution_role_arn = module.otter.otter_appliance_ecs_role
}

module "otter_lighthouse_21x" {
  source             = "./modules/container"
  repo_name          = "otter-lighthouse-21.x"
  family             = "otter-lighthouse-21x-lets-encrypt"
  task_role_arn      = module.otter.otter_appliance_ecs_role
  execution_role_arn = module.otter.otter_appliance_ecs_role
}

module "otter_linux_aws_ssm" {
  source             = "./modules/container"
  repo_name          = "otter-linux-aws-ssm"
  family             = "otter-linux-aws-ssm-lets-encrypt"
  task_role_arn      = module.otter.otter_server_ecs_role
  execution_role_arn = module.otter.otter_server_ecs_role
}
