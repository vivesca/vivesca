#!/usr/bin/env bash
# start.sh — bring up Temporal stack and wait for health
set -euo pipefail
cd "$(dirname "$0")"

echo "Starting Temporal stack..."
docker compose up -d

echo "Waiting for Temporal server to become healthy..."
for i in $(seq 1 60); do
  if docker compose exec -T temporal-server tctl --address localhost:7233 operator cluster health 2>/dev/null; then
    echo ""
    echo "Temporal is ready."
    echo "  Server:   localhost:7233"
    echo "  Web UI:   http://localhost:8080"
    echo "  PostgreSQL: localhost:5432"
    exit 0
  fi
  printf "."
  sleep 2
done

echo ""
echo "ERROR: Temporal did not become healthy within 120s." >&2
exit 1
