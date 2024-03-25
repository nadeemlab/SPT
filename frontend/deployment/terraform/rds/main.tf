provider "aws" {
  region = var.region
}

data "aws_availability_zones" "available" {}

resource "aws_db_subnet_group" "database" {
  name_prefix = var.db_identifier
  subnet_ids = var.subnet_ids
}

resource "aws_security_group_rule" "allow_from_k8s" {
  type              = "ingress"
  to_port           = 0
  protocol          = "-1"
  from_port         = 0
  security_group_id = aws_security_group.rds.id
  source_security_group_id = var.peer_security_group_id
}

resource "aws_security_group_rule" "allow_from_internal_vpn_networks" {
  count             = length(var.allowed_cidrs)
  type              = "ingress"
  to_port           = 5432
  protocol          = "tcp"
  from_port         = 5432
  security_group_id = aws_security_group.rds.id
  cidr_blocks = [var.allowed_cidrs[count.index]]
}

resource "aws_security_group" "rds" {
  name_prefix = var.db_identifier
  vpc_id = var.vpc_id

  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_parameter_group" "database" {
  name_prefix   = var.db_identifier
  family = "postgres14"

  parameter {
    name  = "log_connections"
    value = "1"
  }
}


resource "aws_db_instance" "database" {
  identifier             = var.db_identifier
  instance_class         = "db.t3.large"
  storage_type           = "gp2"
  allocated_storage      = 150
  engine                 = "postgres"
  engine_version         = "14.7"
  username               = var.db_user
  password               = "Password"
  db_name                = var.db_name
  db_subnet_group_name   = aws_db_subnet_group.database.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.database.name
  publicly_accessible    = false
  skip_final_snapshot    = true
  apply_immediately      = true
}

