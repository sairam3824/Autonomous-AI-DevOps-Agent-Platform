#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    cd "$PROJECT_ROOT/infra/docker"
    docker compose stop redis ollama 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

echo "Starting Redis and Ollama via Docker..."
cd "$PROJECT_ROOT/infra/docker"
docker compose up -d redis ollama

echo "Starting backend..."
cd "$PROJECT_ROOT/backend"
cp .env.example .env 2>/dev/null || true
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting frontend..."
cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Dev mode running:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  Press Ctrl+C to stop"
echo ""

wait
