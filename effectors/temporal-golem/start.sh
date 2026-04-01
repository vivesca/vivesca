#!/usr/bin/env bash
# start.sh — bring up Temporal stack and wait for health
set -euo pipefail
cd "$(dirname "$0")"

# Allow overriding via .env or environment
TEMPORAL_PORT="${TEMPORAL_PORT:-7233}"
TEMPORAL_WEB_PORT="${TEMPORAL_WEB_PORT:-8080}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

echo "Starting Temporal stack..."
docker compose up -d

echo "Waiting for Temporal server to become healthy..."
for i in $(seq 1 60); do
  if docker compose exec -T temporal-server temporal operator cluster health 2>/dev/null; then
    echo ""
    echo "Temporal is ready."
    echo "  Server:     localhost:${TEMPORAL_PORT}"
    echo "  Web UI:     http://localhost:${TEMPORAL_WEB_PORT}"
    echo "  PostgreSQL: localhost:${POSTGRES_PORT}"
    echo "  Admin CLI:  docker compose exec temporal-admin-tools temporal <command>"
    exit 0
  fi
  printf "."
  sleep 2
done

echo ""
echo "ERROR: Temporal did not become healthy within 120s." >&2
echo "Check logs with: docker compose logs temporal-server" >&2
exit 1
