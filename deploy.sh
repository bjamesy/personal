#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Pulling latest code..."
git pull origin main

echo "==> Building images..."
docker compose -f docker-compose.prod.yml build

echo "==> Starting services..."
docker compose -f docker-compose.prod.yml up -d

echo "==> Running migrations..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

echo "==> Done. Services:"
docker compose -f docker-compose.prod.yml ps
