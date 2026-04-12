terraform {
  required_version = ">=0.13"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
  backend "s3" {
    bucket         = "saas-task-manager-on-ecs-tfstate-12c298a4"
    key            = "dev/terraform.tfstate"
    region         = "ap-northeast-1"
    dynamodb_table = "terraform-state-locking"
    encrypt        = true
    profile        = "dev-infra-01"
  }
}

provider "aws" {
  region  = "ap-northeast-1"
  profile = "dev-infra-01"
}

provider "aws" {
  alias   = "us_east_1"
  region  = "us-east-1"
  profile = "dev-infra-01"
}

# ---------------------------------------------
# CloudFront origin verify secret
# ---------------------------------------------
resource "random_uuid" "origin_verify_secret" {}

# ---------------------------------------------
# Data: Route53 zone (created in bootstrap)
# ---------------------------------------------
data "aws_route53_zone" "main" {
  name         = "${var.domain_name}."
  private_zone = false
}

# ---------------------------------------------
# Modules
# ---------------------------------------------
module "nw" {
  source = "../../modules/nw"
}

module "ecr" {
  source = "../../modules/ecr"
}

module "iam_oidc" {
  source      = "../../modules/iam_oidc"
  github_repo = var.github_repo
}

module "rds" {
  source             = "../../modules/rds"
  vpc_id             = module.nw.vpc_id
  private_subnet_ids = module.nw.private_subnet_ids
  db_sg_id           = module.nw.db_sg_id
}

module "ecs" {
  source               = "../../modules/ecs"
  vpc_id               = module.nw.vpc_id
  public_subnet_ids    = module.nw.public_subnet_ids
  ecs_tasks_sg_id      = module.nw.ecs_tasks_sg_id
  ecr_image_uri        = "${module.ecr.repository_url}:latest"
  db_host              = module.rds.db_instance_endpoint
  db_secret_arn        = module.rds.db_secret_arn
  origin_verify_secret = random_uuid.origin_verify_secret.result
  domain_name          = var.domain_name
}

# CloudFront for API — origin IP updated by Lambda
module "cloudfront" {
  source               = "../../modules/cloudfront"
  route53_zone_id      = data.aws_route53_zone.main.zone_id
  origin_verify_secret = random_uuid.origin_verify_secret.result
  domain_name          = "api.${var.domain_name}"
  origin_domain_name   = "ecs-origin.${var.domain_name}"

  providers = {
    aws           = aws
    aws.us_east_1 = aws.us_east_1
  }
}

module "lambda" {
  source          = "../../modules/lambda"
  route53_zone_id = data.aws_route53_zone.main.zone_id
  origin_hostname = "ecs-origin.${var.domain_name}"
  ecs_cluster_arn = module.ecs.cluster_arn
}

module "frontend" {
  source          = "../../modules/frontend"
  domain_name     = var.domain_name
  route53_zone_id = data.aws_route53_zone.main.zone_id

  providers = {
    aws           = aws
    aws.us_east_1 = aws.us_east_1
  }
}

# ---------------------------------------------
# Outputs
# ---------------------------------------------
output "github_actions_role_arn" {
  value       = module.iam_oidc.github_actions_role_arn
  description = "GitHub Secret: AWS_ROLE_ARN"
}

output "ecr_repository_name" {
  value       = module.ecr.repository_name
  description = "GitHub Secret: ECR_REPOSITORY"
}

output "ecs_cluster_name" {
  value       = module.ecs.cluster_name
  description = "GitHub Secret: ECS_CLUSTER"
}

output "ecs_service_name" {
  value       = module.ecs.service_name
  description = "GitHub Secret: ECS_SERVICE"
}

output "ecs_task_definition_family" {
  value       = module.ecs.task_definition_family
  description = "ECS task definition family name (for migration task)"
}

output "ecs_task_execution_role_arn" {
  value       = module.ecs.task_execution_role_arn
  description = "GitHub Secret: ECS_TASK_EXECUTION_ROLE_ARN (for run-task migration)"
}

output "ecs_public_subnet_id" {
  value       = module.nw.public_subnet_id_a
  description = "GitHub Secret: ECS_SUBNET_ID (for migration run-task)"
}

output "ecs_security_group_id" {
  value       = module.nw.ecs_tasks_sg_id
  description = "GitHub Secret: ECS_SECURITY_GROUP_ID (for migration run-task)"
}

output "frontend_s3_bucket_name" {
  value       = module.frontend.s3_bucket_name
  description = "GitHub Secret: S3_BUCKET_NAME"
}

output "frontend_cloudfront_distribution_id" {
  value       = module.frontend.distribution_id
  description = "GitHub Secret: CLOUDFRONT_DISTRIBUTION_ID"
}

output "frontend_url" {
  value = "https://${var.domain_name}"
}

output "api_url" {
  value = "https://api.${var.domain_name}"
}

output "temporary_db_password" {
  value     = module.rds.db_password_raw
  sensitive = true
}

output "alarm_sns_topic_arn" {
  value       = module.ecs.alarm_sns_topic_arn
  description = "Subscribe email: aws sns subscribe --topic-arn <arn> --protocol email --notification-endpoint you@example.com"
}
