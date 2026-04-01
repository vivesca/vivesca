#!/bin/bash
source /home/terry/.env.fly
echo "HATCHET_CLIENT_TOKEN=${HATCHET_CLIENT_TOKEN:0:20}..." >&2
exec /home/terry/germline/.venv/bin/python3 /home/terry/germline/effectors/hatchet-golem/worker.py
