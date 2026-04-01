#!/bin/bash
source "$HOME/.env.fly"
if [ "$1" = "--help" ]; then
  exec "$HOME/germline/.venv/bin/python3" "$HOME/germline/effectors/hatchet-golem/worker.py" --help
fi
echo "HATCHET_CLIENT_TOKEN=${HATCHET_CLIENT_TOKEN:0:20}..." >&2
exec "$HOME/germline/.venv/bin/python3" "$HOME/germline/effectors/hatchet-golem/worker.py"
