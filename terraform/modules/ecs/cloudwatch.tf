resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/saas-task-manager-api"
  retention_in_days = 7
}

resource "aws_sns_topic" "ecs_alarms" {
  name = "saas-task-manager-ecs-alarms"
}

resource "aws_cloudwatch_metric_alarm" "task_count" {
  alarm_name          = "saas-task-manager-no-running-tasks"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "RunningTaskCount"
  namespace           = "ECS/ContainerInsights"
  period              = 60
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "Alert when no ECS tasks are running"
  alarm_actions       = [aws_sns_topic.ecs_alarms.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.app.name
  }
}
