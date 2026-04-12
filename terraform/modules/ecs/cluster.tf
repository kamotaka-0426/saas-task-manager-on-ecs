resource "aws_ecs_cluster" "main" {
  name = "saas-task-manager-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}
