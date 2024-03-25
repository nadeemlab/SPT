variable "region" {
  default     = "us-east-1"
  description = "AWS region"
}

variable "environment" {
  default     = "dev"
  description = "Deployment environment"
}

variable "db_password" {
  default     = "Password"
  description = "RDS root user password"
  sensitive   = true
}

variable "db_name" {
  default     = "scstudies"
  description = "RDS user password"
  sensitive   = true
}

variable "db_user" {
  default     = "apireader"
  description = "RDS username"
  sensitive   = true
}

variable "subnet_ids" {
  default     = ["subnet-0674d408752ee61bf", "subnet-062a1c7eb9f96c87e", "subnet-01cbaae4aa6d2216e"]
  description = "Existing subnet ids"
  sensitive   = true
}

variable "vpc_id" {
  default     = "vpc-059a7bcd0fb57db89"
  description = "Existing VPC id"
  sensitive   = true
}

variable "cluster_name" {
  default     = "spt-prod"
  description = "Name of the cluster"
  sensitive   = true
}

variable "db_identifier" {
  type = string
  description = "Database name identifier"
  default = "spt"
}

variable "allowed_cidrs" {
  type = list(string)
  description = "Allowed CIDRs list for RDS security group"
  default = [ "0.0.0.0/0" ]
}

variable "certificate_arn" {
  type = string
  description = "Certificate arn for internal LB"
  default = "arn:aws:acm:us-east-1:666466118732:certificate/2ae8282e-87ec-4427-b88d-9b0b072ed7ab"
}

variable "fast_counts_bucket_name" {
  type = string
  description = "S3 bucket name for fast-counts cache"
  default = "spt-prod-fast-counts"
}