#!/usr/bin/env bash
# Pull config repos from GitHub and apply Claude config.
# Runs every 15min via agent-sync systemd timer on Pharos.
set -euo pipefail

usage() {
    cat <<'HELP'
Usage: agent-sync.sh [OPTIONS]

Pull agent config repos and sync MEMORY.md into Claude project dir.

Options:
  -h, --help    Show this help message
HELP
}

case "${1:-}" in
    -h|--help) usage; exit 0 ;;
esac

REPOS=("$HOME/agent-config" "$HOME/skills" "$HOME/epigenome/chromatin")

for repo in "${REPOS[@]}"; do
    [ -d "$repo/.git" ] || continue
    git -C "$repo" pull --rebase 2>/dev/null || git -C "$repo" pull 2>/dev/null || true
done

# MEMORY.md — derive Claude project dir from $HOME
PROJECT_SLASH="$(echo "$HOME" | sed 's|^/||')"
PROJECT_DASH="$(echo "$PROJECT_SLASH" | tr '/' '-')"
SRC="$HOME/agent-config/claude/memory/MEMORY.md"
DST="$HOME/.claude/projects/-${PROJECT_DASH}/memory/MEMORY.md"
if [ -f "$SRC" ]; then
    mkdir -p "$(dirname "$DST")"
    cp "$SRC" "$DST"
fi
