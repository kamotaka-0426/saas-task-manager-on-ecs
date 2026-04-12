output "cluster_arn" {
  value       = aws_ecs_cluster.main.arn
  description = "ECS cluster ARN (used by Lambda EventBridge rule)"
}

output "cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "ECS cluster name"
}

output "service_name" {
  value       = aws_ecs_service.app.name
  description = "ECS service name"
}

output "task_execution_role_arn" {
  value       = aws_iam_role.task_execution.arn
  description = "ARN of ECS task execution role (needed for GitHub Actions run-task)"
}

output "task_definition_family" {
  value       = aws_ecs_task_definition.app.family
  description = "ECS task definition family name"
}

output "alarm_sns_topic_arn" {
  value       = aws_sns_topic.ecs_alarms.arn
  description = "SNS topic ARN for ECS alarms"
}
