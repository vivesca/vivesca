#!/usr/bin/env bash
# Wrapper for golem-daemon under supervisor.
# Sources ~/.env.fly for API keys before launching the daemon in foreground mode.
set -euo pipefail

# Source environment file if it exists
if [ -f "$HOME/.env.fly" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$HOME/.env.fly"
    set +a
fi

exec python3 "$HOME/germline/effectors/golem-daemon" start --foreground
