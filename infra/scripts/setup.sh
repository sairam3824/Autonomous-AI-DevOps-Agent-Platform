#!/bin/bash
set -euo pipefail

echo "========================================"
echo "  DevOps Agent Platform - Setup"
echo "========================================"

command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting."; exit 1; }
command -v python >/dev/null 2>&1 || { echo "Python is required for setup checks. Aborting."; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
REDIS_PORT="${REDIS_PORT:-6379}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"

check_port_available() {
    local port="$1"
    local label="$2"
    if ! python - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("0.0.0.0", port))
    except OSError:
        sys.exit(1)
PY
    then
        echo ""
        echo "Port $port for $label is already in use."
        echo "Choose a free port and retry, for example:"
        echo "  ${label^^}_PORT=<free-port> make setup"
        if [ "$label" = "frontend" ]; then
            echo "  FRONTEND_PORT=3001 make setup"
        elif [ "$label" = "backend" ]; then
            echo "  BACKEND_PORT=8001 make setup"
        fi
        exit 1
    fi
}

echo "Running port availability checks..."
check_port_available "$BACKEND_PORT" "backend"
check_port_available "$FRONTEND_PORT" "frontend"
check_port_available "$REDIS_PORT" "redis"
check_port_available "$OLLAMA_PORT" "ollama"

if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
    cp "$PROJECT_ROOT/backend/.env.example" "$PROJECT_ROOT/backend/.env"
    echo "Created backend/.env from .env.example"
fi

echo "Building and starting services..."
cd "$PROJECT_ROOT/infra/docker"
docker compose up -d --build

echo "Waiting for backend to be healthy..."
MAX_RETRIES=30
RETRY_COUNT=0
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Backend failed to start after $MAX_RETRIES attempts"
        docker compose logs backend
        exit 1
    fi
    echo "  Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

echo "Seeding database..."
docker compose exec backend python -m scripts.seed_db || echo "Seeding skipped"

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo "  Frontend:  http://localhost:$FRONTEND_PORT"
echo "  Backend:   http://localhost:$BACKEND_PORT"
echo "  API Docs:  http://localhost:$BACKEND_PORT/docs"
echo "  Demo:      demo@devops.ai / demo1234"
echo "========================================"
