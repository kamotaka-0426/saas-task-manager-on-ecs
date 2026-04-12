resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "random_id" "jwt_secret_suffix" {
  byte_length = 4
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "saas-task-manager-jwt-secret-${random_id.jwt_secret_suffix.hex}"
  description             = "JWT signing key for SaaS Task Manager"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}
