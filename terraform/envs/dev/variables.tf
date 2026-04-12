variable "github_repo" {
  type        = string
  description = "GitHub repository in 'owner/repo' format (e.g. 'kamotaka-0426/saas-task-manager-on-ecs')"
}

variable "domain_name" {
  type        = string
  description = "Root domain name (e.g. example.com)"
}
