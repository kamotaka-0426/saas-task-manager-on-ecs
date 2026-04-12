variable "vpc_id"             { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "db_sg_id"           { type = string }

resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "random_id" "db_secret_suffix" {
  byte_length = 4
}

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "saas-task-manager-db-password-${random_id.db_secret_suffix.hex}"
  description             = "RDS master password for SaaS Task Manager"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

resource "aws_db_subnet_group" "main" {
  name       = "saas-task-manager-db-subnet-group"
  subnet_ids = var.private_subnet_ids
  tags       = { Name = "saas-task-manager-db-subnet-group" }
}

resource "aws_db_instance" "main" {
  identifier             = "saas-task-manager-db"
  engine                 = "postgres"
  engine_version         = "15"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  db_name                = "taskdb"
  username               = "postgres"
  password               = random_password.db_password.result
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.db_sg_id]
  skip_final_snapshot    = true
  publicly_accessible    = false
}

output "db_password_raw" {
  value     = random_password.db_password.result
  sensitive = true
}

output "db_instance_endpoint" {
  value = aws_db_instance.main.address
}

output "db_secret_arn" {
  value = aws_secretsmanager_secret.db_password.arn
}
