variable "vpc_id"               { type = string }
variable "public_subnet_ids"    { type = list(string) }
variable "ecs_tasks_sg_id"      { type = string }
variable "ecr_image_uri"        { type = string }
variable "db_host"              { type = string }
variable "db_secret_arn"        { type = string }
variable "origin_verify_secret" {
  type      = string
  sensitive = true
}
variable "domain_name" {
  type        = string
  description = "Root domain for ALLOWED_ORIGINS"
}
