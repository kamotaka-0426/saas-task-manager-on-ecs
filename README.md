# SaaS Task Manager on ECS

[日本語版 README はこちら](README.ja.md)

A production-ready, secure, and scalable multi-tenant SaaS task management system built on AWS ECS Fargate — a minimal Linear/Asana clone.
All infrastructure layers are managed with Terraform, and continuous delivery is achieved through GitHub Actions.

## Architecture

```
Users
  │
  ▼
CloudFront (HTTPS, CDN)
  ├── /          → S3 (React frontend, OAC-secured)
  └── /api/*     → ALB (custom header verification)
                      │
                      ▼
                ECS Fargate (FastAPI)
                        │
                        ├── AWS Secrets Manager (DB credentials)
                        │
                        ▼
                  RDS PostgreSQL (Private Subnet)

EventBridge (scheduled)
  └── Lambda → updates CloudFront origin on schedule
```

| Layer | Technology |
|---|---|
| Frontend | React (Vite) + S3 + CloudFront (OAC) |
| Backend | FastAPI (Python 3.12) on ECS Fargate |
| Database | Amazon RDS for PostgreSQL (Private Subnet) |
| Migrations | Alembic (run as a one-off ECS task on each deploy) |
| Networking | VPC, ALB, Route53, ACM |
| Security | IRSA-equivalent task roles, ACM (TLS 1.2+), AWS Secrets Manager, custom origin header |
| IaC | Terraform (fully modular) |
| CI/CD | GitHub Actions (OIDC — no stored AWS credentials) |

## Application Features

**Multi-tenant SaaS** — every resource is scoped to an Organization.

| Feature | Details |
|---|---|
| Organizations | Multi-tenant isolation; invite members by role |
| Projects | Group issues by project within an org |
| Issues | Full CRUD with status and priority tracking |
| Comments | Threaded comments per issue |
| Activity logs | Automatic audit trail on every change |
| Labels | Org-scoped labels attached to issues (many-to-many) |
| Assignees | Assign multiple org members to an issue (many-to-many) |
| Full-text search | `?q=` searches title + description (tsvector/GIN on PostgreSQL) |
| Filters & sort | `?status=`, `?priority=`, `?assignee_id=`, `?label_id=`, `?sort=` |
| Cursor pagination | Stable keyset pagination via `next_cursor` |

**RBAC** — role-based access control per organization.

| Role | Create/Update | Delete | Manage labels/assignees |
|---|---|---|---|
| member | No | No | No |
| admin | Yes | No | Yes |
| owner | Yes | Yes | Yes |

## Key Design Decisions

**1. Full Infrastructure as Code**
Everything from the VPC to ECS task definitions to CloudFront distributions is managed in Terraform. No manual AWS console operations.

**2. Database Migrations as ECS One-off Tasks**
Alembic migrations run as a standalone ECS Fargate task on each backend deploy — before the new application version is rolled out. The CI pipeline waits for the migration task to exit successfully before proceeding to `update-service`.

**3. Secure Origin Protection**
Direct access to the ALB is blocked. CloudFront attaches a random secret to the `X-Origin-Verify` header on every request. The FastAPI middleware rejects any request missing this header (except `/health`), preventing users from bypassing CloudFront.

**4. Keyless AWS Authentication**
GitHub Actions assumes an IAM role via OIDC federation — no long-lived AWS access keys stored as secrets. The IAM role is scoped to only the specific GitHub repository.

**5. Secrets Management via AWS Secrets Manager**
Database credentials and application secrets are stored in AWS Secrets Manager and injected into the ECS task as environment variables at runtime — never baked into the container image.

**6. Lightweight, Reproducible Docker Images**
Multi-stage builds separate the build environment from the runtime image. A Python virtual environment (`venv`) is copied between stages, producing a small and secure final image.

## Repository Structure

```
.
├── terraform/
│   ├── bootstrap/          # S3 backend, DynamoDB lock table, Route53 hosted zone
│   ├── envs/dev/           # Environment entrypoint (main.tf, variables.tf, outputs.tf)
│   └── modules/            # Reusable modules
│       ├── nw/             # VPC, subnets, security groups, ALB
│       ├── ecs/            # ECS cluster, Fargate service, task definition, CloudWatch
│       ├── rds/            # RDS PostgreSQL
│       ├── ecr/            # ECR repository
│       ├── cloudfront/     # CloudFront distribution for API
│       ├── frontend/       # S3 bucket + CloudFront OAC for React
│       ├── lambda/         # Lambda function (CloudFront origin updater)
│       └── iam_oidc/       # GitHub Actions OIDC IAM role
├── app/                    # FastAPI backend (Python 3.12)
│   ├── routers/            # Auth, Organizations, Projects, Issues, Labels
│   ├── services/           # Business logic
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── core/config.py      # Settings (pydantic-settings)
│   ├── Dockerfile          # Multi-stage build
│   └── tests/              # pytest test suite
├── frontend/               # React (Vite) frontend
├── migrations/             # Alembic migration scripts
├── lambda/                 # Lambda function source (CloudFront origin updater)
├── .github/workflows/
│   ├── backend-deploy.yml  # Test → Build → Push ECR → Migrate → Deploy ECS
│   └── frontend-deploy.yml # Build → S3 sync → CloudFront invalidation
├── setup-all.sh            # Automated full infrastructure setup script
└── destroy-all.sh          # Safe full teardown script
```

## CI/CD Pipeline

### Backend (`app/**`, `migrations/**` push to `main`)

```
Push to main
    │
    ▼
[test]  pytest (Python 3.12)
    │
    ▼ (on success)
[deploy]
    ├── Configure AWS (OIDC)
    ├── docker build & push → ECR (tagged with git SHA + latest)
    ├── Run Alembic migrations (ECS one-off task, waits for exit 0)
    └── aws ecs update-service --force-new-deployment
```

### Frontend (`frontend/**` push to `main`)

```
Push to main
    │
    ▼
[deploy]
    ├── npm ci & build (Vite)
    ├── Configure AWS (OIDC)
    ├── aws s3 sync → S3
    └── CloudFront cache invalidation
```

## Security Highlights

| Concern | Implementation |
|---|---|
| No stored AWS credentials | GitHub Actions OIDC → IAM role assumption |
| Secret management | AWS Secrets Manager (injected as env vars into ECS tasks) |
| ALB direct-access bypass | `X-Origin-Verify` custom header validated in FastAPI middleware |
| TLS everywhere | ACM certificates, CloudFront enforces HTTPS redirect, TLS 1.2+ minimum |
| Private database | RDS in private subnets, no public endpoint |
| Container isolation | ECS Fargate — no shared host, no node-level instance profile access |

## Deploy Guide

### Prerequisites
- AWS CLI configured with a profile named `dev-infra-01`
- Terraform >= 1.9

### Automated Setup (Recommended)

Use the setup script to provision all infrastructure in the correct order:

```bash
# 1. Copy and fill in your Terraform variables
cp terraform/bootstrap/terraform.tfvars.example terraform/bootstrap/terraform.tfvars
cp terraform/envs/dev/terraform.tfvars.example terraform/envs/dev/terraform.tfvars

# 2. Run the setup script
./setup-all.sh
```

The script performs the following steps automatically:
1. Checks that all required tools are installed (`terraform`, `aws`)
2. Deploys the bootstrap layer (S3 state backend, DynamoDB lock table, Route53 hosted zone)
3. Displays the Route53 name servers and pauses — register these at your domain registrar before continuing
4. Runs `terraform apply` to provision VPC, ECS, RDS, ECR, Lambda, and CloudFront
5. Prints all values needed for GitHub Actions Secrets and the access URLs

> **Note:** The script stops immediately on any error and displays a failure message. If it fails mid-way, check the AWS console for any partially created resources before re-running.

### Manual Setup

<details>
<summary>Click to expand manual steps</summary>

#### Step 1 — Bootstrap (S3 state backend + Route53)
```bash
cd terraform/bootstrap
cp terraform.tfvars.example terraform.tfvars  # fill in your values
terraform init && terraform apply
```

After applying, register the displayed Route53 name servers at your domain registrar.

#### Step 2 — Core Infrastructure (ECS, RDS, CloudFront)
```bash
cd terraform/envs/dev
cp terraform.tfvars.example terraform.tfvars  # fill in your values
terraform init
terraform apply
```

</details>

### Step 3 — CI/CD Secrets (GitHub Actions)

Set the following repository secrets in GitHub:

| Secret | Description |
|---|---|
| `AWS_ROLE_ARN` | IAM role ARN output from `terraform output github_actions_role_arn` |
| `ECR_REPOSITORY` | ECR repository name |
| `ECS_CLUSTER` | ECS cluster name |
| `ECS_SERVICE` | ECS service name |
| `ECS_TASK_DEFINITION` | ECS task definition family name (for migration task) |
| `ECS_SUBNET_ID` | Public subnet ID (for migration run-task) |
| `ECS_SECURITY_GROUP_ID` | ECS tasks security group ID |
| `S3_BUCKET_NAME` | Frontend S3 bucket name |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront distribution ID for the frontend |
| `VITE_API_URL` | Backend API URL (e.g. `https://api.example.com`) |

When using `setup-all.sh`, all of these values are printed automatically at the end of the script.

Push to `main` to trigger the pipeline.

## Teardown

```bash
./destroy-all.sh
```

The script performs teardown in the correct order to avoid dependency errors:
1. Scales down the ECS service to zero and stops all running tasks
2. Deletes all ECR images (required before Terraform can remove the repository)
3. Runs `terraform destroy` on the main infrastructure (`envs/dev`)
4. Cleans up Route53 records added by ECS/ALB, then destroys the bootstrap layer

> **Note:** The script stops immediately on any error and displays a failure message, so a successful "All resources have been successfully deleted." message confirms full teardown.
>
> **If the script fails mid-way** (some resources deleted, some remaining), simply re-run `./destroy-all.sh`. Terraform reads the state file to determine what still exists and will only attempt to destroy the remaining resources — it is safe to re-run.

---

**Author:** Takayuki Kotani ([GitHub](https://github.com/kamotaka-0426))
