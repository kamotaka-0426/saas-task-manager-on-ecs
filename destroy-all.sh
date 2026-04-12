#!/bin/bash
set -euo pipefail

trap '
    echo ""
    echo "=========================================="
    echo "❌ Script failed."
    echo "   Check the AWS console for remaining resources."
    echo "=========================================="
' ERR

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
DEV_DIR="$PROJECT_ROOT/terraform/envs/dev"
BOOTSTRAP_DIR="$PROJECT_ROOT/terraform/bootstrap"

echo "⚠️  Warning: This script will delete ALL infrastructure. This cannot be undone."
echo "Starting in 5 seconds... (Press Ctrl+C to cancel)"
sleep 5

# --- [STEP 1] ECSサービスをゼロにスケールダウン（ALB削除待ち不要だが念のため）---
echo "=== [1/3] Scaling down ECS service... ==="
CLUSTER=$(terraform -chdir="$DEV_DIR" output -raw ecs_cluster_name 2>/dev/null || echo "")
SERVICE=$(terraform -chdir="$DEV_DIR" output -raw ecs_service_name 2>/dev/null || echo "")
if [ -n "$CLUSTER" ] && [ -n "$SERVICE" ]; then
    aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" \
        --desired-count 0 --region ap-northeast-1 --profile dev-infra-01 2>/dev/null || true
    echo "  Scaled down $SERVICE to 0"
fi

# --- [STEP 2] メインインフラ削除 ---
echo "=== [2/3] Destroying main infrastructure (envs/dev)... ==="
if [ ! -d "$DEV_DIR" ]; then
    echo "❌ Error: $DEV_DIR not found."
    exit 1
fi
cd "$DEV_DIR"
terraform init -input=false > /dev/null
if ! terraform destroy -auto-approve; then
    echo "❌ Failed to destroy envs/dev. Check the AWS console for remaining resources."
    exit 1
fi
echo "✅ envs/dev has been destroyed."

# --- [STEP 3] Bootstrap 削除 ---
echo "=== [3/3] Destroying bootstrap layer (S3/DynamoDB)... ==="
if [ ! -d "$BOOTSTRAP_DIR" ]; then
    echo "❌ Error: $BOOTSTRAP_DIR not found."
    exit 1
fi
cd "$BOOTSTRAP_DIR"
if ! terraform destroy -auto-approve; then
    echo "❌ Failed to destroy bootstrap layer."
    exit 1
fi
echo "✅ Bootstrap layer has been destroyed."

echo "=========================================="
echo "🎉 All resources have been successfully deleted."
echo "=========================================="
