#!/usr/bin/env bash
# Pull config repos from GitHub and apply Claude config.
# Runs every 15min via agent-sync systemd timer on Pharos.
set -uo pipefail

REPOS=("$HOME/agent-config" "$HOME/skills" "$HOME/code/epigenome/chromatin")

for repo in "${REPOS[@]}"; do
    [ -d "$repo/.git" ] || continue
    git -C "$repo" pull --rebase 2>/dev/null || git -C "$repo" pull 2>/dev/null || true
done

# MEMORY.md — path differs by OS (macOS: -Users-terry, Linux: -home-terry)
SRC="$HOME/agent-config/claude/memory/MEMORY.md"
DST="$HOME/.claude/projects/-home-terry/memory/MEMORY.md"
if [ -f "$SRC" ]; then
    mkdir -p "$(dirname "$DST")"
    cp "$SRC" "$DST"
fi
