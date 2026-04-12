#!/bin/bash
set -euo pipefail

trap '
    echo ""
    echo "=========================================="
    echo "❌ Script failed."
    echo "   Check the AWS console for any resources that were created."
    echo "=========================================="
' ERR

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
DEV_DIR="$PROJECT_ROOT/terraform/envs/dev"
BOOTSTRAP_DIR="$PROJECT_ROOT/terraform/bootstrap"
TFVARS="$DEV_DIR/terraform.tfvars"
TFVARS_EXAMPLE="$DEV_DIR/terraform.tfvars.example"
DEV_MAIN_TF="$DEV_DIR/main.tf"
BOOTSTRAP_TFVARS="$BOOTSTRAP_DIR/terraform.tfvars"
BOOTSTRAP_TFVARS_EXAMPLE="$BOOTSTRAP_DIR/terraform.tfvars.example"

echo "=========================================="
echo "  SaaS Task Manager on ECS - Setup Script"
echo "=========================================="
echo ""

echo "=== Checking prerequisites... ==="
for cmd in terraform aws; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "❌ Error: '$cmd' is not installed."
        exit 1
    fi
done
echo "✅ All required tools are available."

if [ ! -f "$TFVARS" ]; then
    echo ""
    echo "⚠️  $TFVARS not found."
    echo "   Copy the example file and fill in your values:"
    echo ""
    echo "   cp $TFVARS_EXAMPLE $TFVARS"
    echo "   # Then edit $TFVARS"
    echo ""
    exit 1
fi
echo "✅ terraform.tfvars found."

if [ ! -f "$BOOTSTRAP_TFVARS" ]; then
    echo ""
    echo "⚠️  $BOOTSTRAP_TFVARS not found."
    echo "   Copy the example file:"
    echo ""
    echo "   cp $BOOTSTRAP_TFVARS_EXAMPLE $BOOTSTRAP_TFVARS"
    echo "   # Then edit $BOOTSTRAP_TFVARS"
    echo ""
    exit 1
fi
echo "✅ bootstrap/terraform.tfvars found."

echo ""
echo "Starting in 5 seconds... (Press Ctrl+C to cancel)"
sleep 5

# --- [STEP 1] Bootstrap ---
echo ""
echo "=== [1/3] Deploying bootstrap layer (S3/DynamoDB/Route53)... ==="
cd "$BOOTSTRAP_DIR"
terraform init -input=false
if ! terraform apply -auto-approve; then
    echo "❌ Failed to apply bootstrap layer."
    exit 1
fi
echo "✅ Bootstrap layer deployed successfully."

# --- [STEP 1b] S3バケット名を main.tf に自動反映 ---
echo ""
echo "=== Updating backend config with the new S3 state bucket name... ==="
BUCKET_NAME=$(terraform -chdir="$BOOTSTRAP_DIR" output -raw terraform_state_bucket_name)
echo "  State bucket: $BUCKET_NAME"
sed -i "s|^\( *\)bucket *=.*\".*tfstate.*\"|\1bucket         = \"$BUCKET_NAME\"|" "$DEV_MAIN_TF"
echo "✅ $DEV_MAIN_TF backend bucket updated to: $BUCKET_NAME"

# --- NS レコードの登録案内 ---
echo ""
echo "=========================================="
echo "  ⚠️  ACTION REQUIRED: Register NS Records"
echo "=========================================="
echo ""
DOMAIN=$(terraform -chdir="$BOOTSTRAP_DIR" output -raw domain_name)
echo "  Domain: $DOMAIN"
echo ""
echo "  Name Servers:"
terraform -chdir="$BOOTSTRAP_DIR" output -json route53_name_servers \
    | tr -d '[]"' | tr ',' '\n' | sed 's/^ */    /; s/[[:space:]]*$//'
echo ""
echo "Note: DNS propagation may take a few minutes up to 48 hours."
echo "=========================================="
echo ""
echo "Press Enter once you have registered the NS records at your registrar..."
read -r

# --- [STEP 2] メインインフラのデプロイ ---
echo ""
echo "=== [2/3] Deploying main infrastructure (ECS / RDS / Lambda / CloudFront)... ==="
cd "$DEV_DIR"
terraform init -input=false -reconfigure
if ! terraform apply -auto-approve; then
    echo "❌ Main infrastructure deployment failed."
    exit 1
fi
echo "✅ Main infrastructure deployed successfully."

# --- [STEP 3] GitHub Actionsシークレットの表示 ---
echo ""
echo "=========================================="
echo "🎉 Setup complete!"
echo "=========================================="
echo ""
echo "--- GitHub Actions Secrets ---"
echo "  Set the following in your repository: Settings > Secrets and variables > Actions"
echo ""
terraform -chdir="$DEV_DIR" output -raw github_actions_role_arn          | awk '{print "  AWS_ROLE_ARN                  = " $0}'
terraform -chdir="$DEV_DIR" output -raw ecr_repository_name              | awk '{print "  ECR_REPOSITORY                = " $0}'
terraform -chdir="$DEV_DIR" output -raw ecs_cluster_name                 | awk '{print "  ECS_CLUSTER                   = " $0}'
terraform -chdir="$DEV_DIR" output -raw ecs_service_name                 | awk '{print "  ECS_SERVICE                   = " $0}'
terraform -chdir="$DEV_DIR" output -raw ecs_task_definition_family       | awk '{print "  ECS_TASK_DEFINITION           = " $0}'
terraform -chdir="$DEV_DIR" output -raw ecs_task_execution_role_arn      | awk '{print "  ECS_TASK_EXECUTION_ROLE_ARN   = " $0}'
terraform -chdir="$DEV_DIR" output -raw ecs_public_subnet_id             | awk '{print "  ECS_SUBNET_ID                 = " $0}'
terraform -chdir="$DEV_DIR" output -raw ecs_security_group_id            | awk '{print "  ECS_SECURITY_GROUP_ID         = " $0}'
terraform -chdir="$DEV_DIR" output -raw frontend_s3_bucket_name          | awk '{print "  S3_BUCKET_NAME                = " $0}'
terraform -chdir="$DEV_DIR" output -raw frontend_cloudfront_distribution_id | awk '{print "  CLOUDFRONT_DISTRIBUTION_ID    = " $0}'
terraform -chdir="$DEV_DIR" output -raw api_url                          | awk '{print "  VITE_API_URL                  = " $0}'
echo ""
echo "--- Terraform State Bucket ---"
echo "  Bucket: $BUCKET_NAME  (already written to $DEV_MAIN_TF)"
echo ""
echo "--- Access URLs ---"
terraform -chdir="$DEV_DIR" output -raw frontend_url | awk '{print "  Frontend : " $0}'
terraform -chdir="$DEV_DIR" output -raw api_url      | awk '{print "  API      : " $0 "/health"}'
echo ""
echo "--- Next Steps ---"
echo "  1. Set the GitHub Secrets above"
echo "  2. Push app code to trigger the backend-deploy workflow"
echo "     The workflow will automatically run Alembic migrations then deploy"
echo ""
