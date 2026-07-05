#!/usr/bin/env bash
# Development server startup script
set -euo pipefail

cd "$(dirname "$0")/../backend"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

mkdir -p data logs
cp -n .env.example .env 2>/dev/null || true

echo "Starting AI Trading Assistant API (DEMO mode)..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
