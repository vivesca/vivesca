#!/usr/bin/env bash
# Wrapper for golem-daemon under supervisor.
# Sources ~/.env.fly for API keys before launching the daemon in foreground mode.
set -euo pipefail

# Handle --help without starting the daemon
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "golem-daemon-wrapper — sources API keys then launches golem-daemon in foreground"
    echo "Usage: golem-daemon-wrapper"
    echo "  No user-facing options. Managed by launchd/supervisor."
    exit 0
fi

# Source environment file if it exists
if [ -f "$HOME/.env.fly" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$HOME/.env.fly"
    set +a
fi

exec python3 "$HOME/germline/effectors/golem-daemon" start --foreground
