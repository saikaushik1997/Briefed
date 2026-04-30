#!/usr/bin/env bash
# First-time Fly.io setup. Run once from repo root after `fly auth login`.
set -euo pipefail

echo "==> Creating Fly.io apps..."
fly apps create briefed-mlflow --machines || true
fly apps create briefed-backend --machines || true

echo "==> Creating MLflow persistent volume (1GB)..."
fly volumes create mlflow_data --app briefed-mlflow --size 1 --region ord || true

echo "==> Creating managed Postgres database..."
fly postgres create \
  --name briefed-db \
  --region ord \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 1

echo ""
echo "==> Attach Postgres to backend (copy the DATABASE_URL printed above):"
echo "    fly postgres attach briefed-db --app briefed-backend"
echo ""
echo "==> Set backend secrets (replace placeholders):"
echo "    fly secrets set --app briefed-backend \\"
echo "      OPENAI_API_KEY=sk-... \\"
echo "      LANGSMITH_API_KEY=lsv2_... \\"
echo "      LANGSMITH_TRACING_V2=true \\"
echo "      LANGSMITH_PROJECT=Briefed \\"
echo "      REDIS_URL=redis://... \\"
echo "      MLFLOW_TRACKING_URI=https://briefed-mlflow.fly.dev"
echo ""
echo "==> For Redis, use Upstash (free tier): https://upstash.com"
echo "    Then set REDIS_URL=rediss://... in the secrets above"
echo ""
echo "==> Deploy MLflow first, then backend:"
echo "    flyctl deploy --remote-only --app briefed-mlflow --config mlflow/fly.toml"
echo "    flyctl deploy --remote-only --app briefed-backend --config backend/fly.toml"
