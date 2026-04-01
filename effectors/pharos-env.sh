#!/bin/bash
# Environment wrapper for systemd services on pharos (Ubuntu).
# systemd user services have minimal PATH and no .zshenv.
# Usage: pharos-env.sh <command> [args...]

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: pharos-env.sh <command> [args...]"
    echo ""
    echo "Environment wrapper for systemd services on pharos (Ubuntu)."
    echo "Sets up PATH and sources machine-local secrets before exec-ing the given command."
    exit 0
fi

export HOME="${HOME:-$(eval echo ~)}"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.bun/bin:$HOME/go/bin:$HOME/.nix-profile/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/usr/bin:/bin"

# Source machine-local secrets (API keys, etc.)
if [ -f "$HOME/.zshenv.local" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$HOME/.zshenv.local"
    set +a
fi

exec "$@"
