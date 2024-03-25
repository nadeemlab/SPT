output "rds_hostname" {
  description = "RDS instance hostname"
  value       = aws_db_instance.database.address
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.database.port
  sensitive   = true
}

output "rds_username" {
  description = "RDS instance root username"
  value       = aws_db_instance.database.username
  sensitive   = true
}

output "rds_password" {
  description = "RDS instance password"
  value       = aws_db_instance.database.password
  sensitive   = true
}