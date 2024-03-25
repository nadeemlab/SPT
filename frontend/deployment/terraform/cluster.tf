
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.10.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.24"

  cluster_endpoint_public_access  = true

  create_iam_role = false
  create_cloudwatch_log_group = false

  iam_role_arn = aws_iam_role.cluster_role.arn

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  vpc_id                   = var.vpc_id 
  subnet_ids               = var.subnet_ids

  # EKS Managed Node Group(s)
  eks_managed_node_group_defaults = {
    instance_types = ["m6i.xlarge", "m5.large", "m5n.large", "m5zn.large"]
    create_iam_role = false
    iam_role_arn = aws_iam_role.node_role.arn
  }

  eks_managed_node_groups = {
    spt-dev = {
      desired_size = 3
      min_size     = 1
      max_size     = 5

      instance_types = ["m6i.xlarge"]
    }
  }

  tags = {
    Environment = var.environment
    Terraform   = "true"
  }

  # Extend node-to-node security group rules
  node_security_group_additional_rules = {
    ingress_self_all = {
      description = "Node to node all ports/protocols"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "ingress"
      self        = true
    }
    egress_all = {
      description      = "Allow all egress"
      protocol         = "-1"
      from_port        = 0
      to_port          = 0
      type             = "egress"
      cidr_blocks      = ["0.0.0.0/0"]
      #ipv6_cidr_blocks = ["::/0"]
    }
  }
}

data "aws_caller_identity" "current" {}

output "account_id" {
  value = "${data.aws_caller_identity.current.account_id}"
}

output "caller_arn" {
  value = "${data.aws_caller_identity.current.arn}"
}

output "caller_user" {
  value = "${data.aws_caller_identity.current.user_id}"
}


resource "aws_iam_role" "cluster_role" {
  name_prefix         = "userServiceRole"
  assume_role_policy  = <<-EOD
    {
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Principal": {
                  "Service": "eks.amazonaws.com"
              },
              "Action": "sts:AssumeRole"
          }
      ]
    }
  EOD
  permissions_boundary = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/EngineerOrUserServiceRolePermissions"
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy", 
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess",
    "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
  ]
}

resource "aws_iam_role" "node_role" {
  name_prefix         = "userServiceRole"
  assume_role_policy  = <<-EOD
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
  EOD
  permissions_boundary = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/EngineerOrUserServiceRolePermissions"
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:aws:iam::aws:policy/AmazonEKSServicePolicy",
    "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy",
    "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  ]
}