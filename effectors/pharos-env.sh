#!/bin/bash
# Environment wrapper for systemd services on pharos (Ubuntu).
# systemd user services have minimal PATH and no .zshenv.
# Usage: pharos-env.sh <command> [args...]

set -euo pipefail

export HOME="/home/terry"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.bun/bin:$HOME/go/bin:$HOME/.nix-profile/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/usr/bin:/bin"

# Source machine-local secrets (API keys, etc.)
if [ -f "$HOME/.zshenv.local" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$HOME/.zshenv.local"
    set +a
fi

exec "$@"
