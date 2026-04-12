# No ALB; tasks are assigned public IPs.
# CloudFront origin IP is updated dynamically by Lambda when a new task starts.
# The second task exists to reduce downtime during rolling deployments.
resource "aws_ecs_service" "app" {
  name            = "saas-task-manager-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  network_configuration {
    subnets          = var.public_subnet_ids
    security_groups  = [var.ecs_tasks_sg_id]
    assign_public_ip = true
  }
}
