variable "region" {
  default     = "us-east-1"
  description = "AWS region"
}

variable "db_password" {
  default     = "Password"
  description = "RDS root user password"
  sensitive   = true
}

variable "db_user" {
  default     = "apireader"
  description = "RDS user password"
  sensitive   = true
}

variable "db_name" {
  default     = "scstudies"
  description = "RDS user password"
  sensitive   = true
}


variable "subnet_ids" {
  default     = ["subnet-061ca565de53395e4", "subnet-0b67a6cb9712a2d35", "subnet-0e3e0379722037f2d"]
  description = "Public subnets"
  sensitive   = true
}

variable "vpc_id" {
  default     =  "vpc-059a7bcd0fb57db89"
  description = "Existing VPC id"
  sensitive   = true
}

variable "peer_security_group_id" {
  type = string
  description = "Security group id of the peer"
}

variable "db_identifier" {
  type = string
  description = "Database name identifier"
  default = "spt"
}

variable "allowed_cidrs" {
  type = list(string)
  description = "Allowed CIDRs list for RDS security group"
}
