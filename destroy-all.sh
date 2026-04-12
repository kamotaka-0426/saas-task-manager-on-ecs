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

# --- [STEP 1] ECSサービスをゼロにスケールダウン＋タスク・ECRを完全クリア ---
echo "=== [1/3] Cleaning up ECS tasks and ECR images... ==="
CLUSTER=$(terraform -chdir="$DEV_DIR" output -raw ecs_cluster_name 2>/dev/null || echo "")
SERVICE=$(terraform -chdir="$DEV_DIR" output -raw ecs_service_name 2>/dev/null || echo "")
ECR_REPO=$(terraform -chdir="$DEV_DIR" output -raw ecr_repository_name 2>/dev/null || echo "")

# サービスをゼロにスケールダウン
if [ -n "$CLUSTER" ] && [ -n "$SERVICE" ]; then
    aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" \
        --desired-count 0 --region ap-northeast-1 --profile dev-infra-01 > /dev/null 2>&1 || true
    echo "  Scaled down $SERVICE to 0"
fi

# 実行中・保留中のタスクをすべて強制停止
if [ -n "$CLUSTER" ]; then
    for STATUS in RUNNING PENDING; do
        TASKS=$(aws ecs list-tasks --cluster "$CLUSTER" --desired-status "$STATUS" \
            --region ap-northeast-1 --profile dev-infra-01 \
            --query 'taskArns' --output text 2>/dev/null || echo "")
        for TASK in $TASKS; do
            aws ecs stop-task --cluster "$CLUSTER" --task "$TASK" \
                --region ap-northeast-1 --profile dev-infra-01 > /dev/null 2>&1 || true
            echo "  Stopped task: $(basename $TASK)"
        done
    done

    # タスクが完全に停止するまで待機
    echo "  Waiting for all tasks to stop..."
    aws ecs wait tasks-stopped --cluster "$CLUSTER" \
        --tasks $(aws ecs list-tasks --cluster "$CLUSTER" \
            --region ap-northeast-1 --profile dev-infra-01 \
            --query 'taskArns' --output text 2>/dev/null) \
        --region ap-northeast-1 --profile dev-infra-01 2>/dev/null || true
    echo "  All tasks stopped."
fi

# ECRイメージを全削除（空でないと terraform destroy が失敗するため）
if [ -n "$ECR_REPO" ]; then
    IMAGE_IDS=$(aws ecr list-images --repository-name "$ECR_REPO" \
        --region ap-northeast-1 --profile dev-infra-01 \
        --query 'imageIds' --output json 2>/dev/null || echo "[]")
    if [ "$IMAGE_IDS" != "[]" ] && [ "$IMAGE_IDS" != "" ]; then
        aws ecr batch-delete-image --repository-name "$ECR_REPO" \
            --image-ids "$IMAGE_IDS" \
            --region ap-northeast-1 --profile dev-infra-01 > /dev/null 2>&1 || true
        echo "  Deleted all images from ECR: $ECR_REPO"
    fi
fi
echo "✅ ECS and ECR cleanup complete."

# --- [STEP 2] メインインフラ削除 ---
echo "=== [2/3] Destroying main infrastructure (envs/dev)... ==="
if [ ! -d "$DEV_DIR" ]; then
    echo "❌ Error: $DEV_DIR not found."
    exit 1
fi
cd "$DEV_DIR"

# S3ステートバケットが存在するか確認してからinitを実行
STATE_BUCKET=$(grep 'bucket' "$DEV_DIR/main.tf" | grep -o '"[^"]*tfstate[^"]*"' | tr -d '"' | head -1)
if [ -n "$STATE_BUCKET" ] && aws s3api head-bucket --bucket "$STATE_BUCKET" --profile dev-infra-01 2>/dev/null; then
    terraform init -input=false > /dev/null
    if ! terraform destroy -auto-approve; then
        echo "❌ Failed to destroy envs/dev. Check the AWS console for remaining resources."
        exit 1
    fi
    echo "✅ envs/dev has been destroyed."
else
    echo "⚠️  State bucket '$STATE_BUCKET' not found. Skipping terraform destroy for envs/dev."
    echo "   (Resources may have already been destroyed or require manual cleanup.)"
fi

# --- [STEP 3] Bootstrap 削除 ---
echo "=== [3/3] Destroying bootstrap layer (S3/DynamoDB/Route53)... ==="
if [ ! -d "$BOOTSTRAP_DIR" ]; then
    echo "❌ Error: $BOOTSTRAP_DIR not found."
    exit 1
fi

# Route53ホストゾーンのNS/SOA以外のレコードを削除（残存レコードがあると削除失敗するため）
ZONE_ID=$(terraform -chdir="$BOOTSTRAP_DIR" output -raw route53_zone_id 2>/dev/null || echo "")
if [ -n "$ZONE_ID" ]; then
    echo "  Cleaning up Route53 records in zone: $ZONE_ID"
    RECORDS=$(aws route53 list-resource-record-sets \
        --hosted-zone-id "$ZONE_ID" \
        --profile dev-infra-01 \
        --query 'ResourceRecordSets[?Type!=`NS` && Type!=`SOA`]' \
        --output json 2>/dev/null || echo "[]")
    if [ "$RECORDS" != "[]" ] && [ -n "$RECORDS" ]; then
        CHANGES=$(echo "$RECORDS" | python3 -c "
import sys, json
records = json.load(sys.stdin)
changes = [{'Action': 'DELETE', 'ResourceRecordSet': r} for r in records]
print(json.dumps({'Changes': changes}))
")
        aws route53 change-resource-record-sets \
            --hosted-zone-id "$ZONE_ID" \
            --change-batch "$CHANGES" \
            --profile dev-infra-01 > /dev/null 2>&1 || true
        echo "  Deleted $(echo "$RECORDS" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))") extra record(s)."
    else
        echo "  No extra records found."
    fi
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
