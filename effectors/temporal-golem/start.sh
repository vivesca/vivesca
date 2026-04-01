#!/usr/bin/env bash
# start.sh — launch Temporal server + worker for local development.
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Starting Temporal server (PostgreSQL + server + Web UI)..."
docker compose up -d

echo "==> Waiting for Temporal server to be healthy..."
for i in $(seq 1 30); do
    if docker compose exec -T temporal-server tctl --address localhost:7233 cluster health 2>/dev/null; then
        echo "    Server is healthy."
        break
    fi
    echo "    Waiting... ($i/30)"
    sleep 2
done

echo "==> Starting worker..."
echo "    Run:  uv run python worker.py"
echo "    Or:   bash start.sh --worker  (to auto-start)"
if [[ "${1:-}" == "--worker" ]]; then
    exec uv run python worker.py
fi

echo ""
echo "Temporal server:  http://localhost:7233"
echo "Temporal Web UI:  http://localhost:8080"
echo "Task queue:       golem-tasks"
echo ""
echo "Submit tasks:     temporal-golem submit --provider zhipu --task 'hello'"
echo "Check status:     temporal-golem status <workflow-id>"
