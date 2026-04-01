#!/usr/bin/env bash
# start.sh — Bring up Temporal stack and wait for health
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if present
if [[ -f .env ]]; then
    set -a; source .env; set +a
fi

echo "==> Starting Temporal stack..."
docker compose up -d

echo "==> Waiting for PostgreSQL..."
until docker compose exec -T postgresql pg_isready -U "${TEMPORAL_DB_USER:-temporal}" >/dev/null 2>&1; do
    sleep 2
done
echo "    PostgreSQL ready."

echo "==> Waiting for Temporal server health..."
retries=0
max_retries=60
until docker compose exec -T temporal-server temporal operator cluster health >/dev/null 2>&1; do
    retries=$((retries + 1))
    if [[ $retries -ge $max_retries ]]; then
        echo "ERROR: Temporal server did not become healthy after $max_retries attempts." >&2
        echo "Check logs: docker compose logs temporal-server" >&2
        exit 1
    fi
    sleep 3
    echo "    attempt $retries/$max_retries..."
done
echo "    Temporal server healthy."

echo "==> Waiting for Temporal Web..."
retries=0
max_retries=30
until curl -sf "http://localhost:${TEMPORAL_WEB_PORT:-8080}" >/dev/null 2>&1; do
    retries=$((retries + 1))
    if [[ $retries -ge $max_retries ]]; then
        echo "WARN: Temporal Web not reachable after $max_retries attempts." >&2
        break
    fi
    sleep 2
done
if [[ $retries -lt $max_retries ]]; then
    echo "    Temporal Web ready."
fi

echo ""
echo "==> Temporal stack is up!"
echo "    Server gRPC:  localhost:${TEMPORAL_GRPC_PORT:-7233}"
echo "    Web UI:       http://localhost:${TEMPORAL_WEB_PORT:-8080}"
echo "    Admin tools:  docker compose exec temporal-admin-tools tctl --help"
echo ""
echo "To stop:  docker compose down"
echo "To wipe:  docker compose down -v"
