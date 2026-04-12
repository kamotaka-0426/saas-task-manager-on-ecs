resource "aws_ecs_task_definition" "app" {
  family                   = "saas-task-manager-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.task_execution.arn

  container_definitions = jsonencode([{
    name  = "api"
    image = var.ecr_image_uri
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
    healthCheck = {
      command     = ["CMD-SHELL", "python3 -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health')\""]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
    environment = [
      { name = "DB_USER",              value = "postgres" },
      { name = "DB_NAME",              value = "taskdb" },
      { name = "DB_HOST",              value = var.db_host },
      { name = "ALLOWED_ORIGINS",      value = "https://${var.domain_name}" },
      { name = "ORIGIN_VERIFY_SECRET", value = var.origin_verify_secret },
    ]
    secrets = [
      {
        name      = "DB_PASSWORD"
        valueFrom = var.db_secret_arn
      },
      {
        name      = "JWT_SECRET_KEY"
        valueFrom = aws_secretsmanager_secret.jwt_secret.arn
      },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.app.name
        "awslogs-region"        = "ap-northeast-1"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}
