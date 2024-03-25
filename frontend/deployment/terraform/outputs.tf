output "values_rds" {
  value = yamlencode({
    rds_db_config = {
      username = module.rds.rds_username
      host     = module.rds.rds_hostname
      # password_parameter = aws_ssm_parameter.secret.name
    }
  })
  sensitive = true
}

output "values_elb" {
  value = yamlencode({
    clusterName = module.eks.cluster_name
    region      = var.region
    vpcId       = var.vpc_id
    serviceAccount = {
      name   = "aws-load-balancer-controller"
      create = true
      annotations = {
        "eks.amazonaws.com/role-arn" = module.elb_controller_role.iam_role_arn
      }
    }
  })
  sensitive = true
}

output "values_ingress" {
  value = yamlencode({
    controller = {
      service = {
        annotations = {
          "service.beta.kubernetes.io/aws-load-balancer-ssl-cert" = var.certificate_arn
          "service.beta.kubernetes.io/aws-load-balancer-nlb-target-type" = "instance"
          "service.beta.kubernetes.io/aws-load-balancer-type"            = "external"
          "service.beta.kubernetes.io/aws-load-balancer-scheme"          = "internal"
          "service.beta.kubernetes.io/aws-load-balancer-internal"        = "true"
          "service.beta.kubernetes.io/aws-load-balancer-subnets"         = join(",", var.subnet_ids)
          "service.beta.kubernetes.io/load-balancer-source-ranges"       = join(",", var.allowed_cidrs)
          "service.beta.kubernetes.io/aws-load-balancer-ssl-ports"       = "https"
          "service.beta.kubernetes.io/aws-load-balancer-backend-protocol"= "ssl"
        }
      }
      "kind" = "DaemonSet"
    }
  })
  sensitive = true
}

output "values_s3_mounter" {
  value = yamlencode({
      serviceAccount = {
        create = true
        name = "s3-otomounter"
      }

      bucketName = var.fast_counts_bucket_name
      iamRoleARN = module.s3_mounter_role.iam_role_arn
      hostPath   = "/mnt/s3data"
  })
  sensitive = true
}