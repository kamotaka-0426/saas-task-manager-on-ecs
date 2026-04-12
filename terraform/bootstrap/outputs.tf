output "terraform_state_bucket_name" {
  value       = aws_s3_bucket.terraform_state.bucket
  description = "S3 bucket name for Terraform remote state"
}

output "terraform_locks_table_name" {
  value       = aws_dynamodb_table.terraform_locks.name
  description = "DynamoDB table name for Terraform state locking"
}

output "route53_zone_id" {
  value       = aws_route53_zone.main.zone_id
  description = "Route53 hosted zone ID"
}

output "route53_name_servers" {
  value       = aws_route53_zone.main.name_servers
  description = "Name servers for the Route53 hosted zone"
}

output "domain_name" {
  value       = var.domain_name
  description = "Root domain name"
}
