module "rds" {
    source = "./rds"
    peer_security_group_id = module.eks.node_security_group_id
    vpc_id = var.vpc_id
    subnet_ids = var.subnet_ids
    allowed_cidrs = var.allowed_cidrs
    db_password = random_password.password.result
}

resource "random_password" "password" {
  length           = 16
  special          = true
  override_special = "_%@"
}

# resource "aws_ssm_parameter" "secret" {
#   name        = "/prod/database/password/master"
#   type        = "SecureString"
#   value       = random_password.password.result

#   tags = {
#     environment = "prod"
#   }
# }
