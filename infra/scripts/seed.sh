#!/bin/bash
set -euo pipefail

echo "Waiting for backend..."
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    sleep 2
done

echo "Running seed script..."
cd "$(dirname "${BASH_SOURCE[0]}")/../docker"
docker compose exec backend python -m scripts.seed_db
echo "Seed complete!"