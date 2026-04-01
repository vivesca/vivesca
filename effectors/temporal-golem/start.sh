#!/usr/bin/env bash
# start.sh — launch Temporal infrastructure and golem worker.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Starting Temporal server (docker-compose)..."
docker-compose up -d

echo "==> Waiting for Temporal server to be healthy..."
for i in $(seq 1 30); do
    if docker-compose exec -T temporal-server tctl --address localhost:7233 cluster health >/dev/null 2>&1; then
        echo "    Temporal server is healthy."
        break
    fi
    echo "    Waiting... ($i/30)"
    sleep 2
done

echo "==> Starting golem worker..."
python3 worker.py
