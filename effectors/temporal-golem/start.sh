#!/usr/bin/env bash
# start.sh — Spin up Temporal server + dependencies and wait for health
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Starting Temporal server stack..."
docker compose up -d

echo "==> Waiting for Temporal server to be healthy..."
for i in $(seq 1 30); do
    if docker compose exec -T temporal-server temporal operator cluster health 2>/dev/null; then
        echo "==> Temporal server is healthy!"
        echo "==> Web UI: http://localhost:8080"
        echo "==> gRPC endpoint: localhost:7233"
        exit 0
    fi
    echo "  Waiting... ($i/30)"
    sleep 5
done

echo "ERROR: Temporal server did not become healthy within 150s"
exit 1
