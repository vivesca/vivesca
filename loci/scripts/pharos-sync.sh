#!/usr/bin/env bash
# Sync Claude config (MEMORY.md, settings.json) to reticulum repo.
# Runs every 15min via com.terry.pharos-sync LaunchAgent.
set -uo pipefail

OFFICINA="$HOME/reticulum"
CLAUDE_DIR="$HOME/.claude"

sync_file() {
    local src="$1" dst="$2"
    [ -f "$src" ] || return 1
    if [ ! -f "$dst" ] || ! diff -q "$src" "$dst" &>/dev/null; then
        cp "$src" "$dst"
        echo "updated: $(basename "$dst")"
        return 0
    fi
    return 1
}

changed=false

sync_file \
    "$CLAUDE_DIR/projects/-Users-terry/memory/MEMORY.md" \
    "$OFFICINA/claude/memory/MEMORY.md" && changed=true || true

sync_file \
    "$CLAUDE_DIR/settings.json" \
    "$OFFICINA/claude/settings.json" && changed=true || true

# Push credentials to pharos directly (not via git — sensitive)
if [ -f "$CLAUDE_DIR/.credentials.json" ]; then
    scp -q "$CLAUDE_DIR/.credentials.json" pharos:~/.claude/.credentials.json 2>/dev/null \
        && echo "updated: .credentials.json → pharos" || true
fi

# Push .zshenv to pharos (keys now plaintext in private reticulum repo)
if [ -f "$HOME/.zshenv" ]; then
    scp -q "$HOME/.zshenv" pharos:~/.zshenv 2>/dev/null \
        && echo "updated: .zshenv → pharos" || true
fi

$changed || exit 0

git -C "$OFFICINA" add claude/memory/MEMORY.md claude/settings.json
git -C "$OFFICINA" commit -m "sync: claude config $(date '+%Y-%m-%d %H:%M')" && \
    git -C "$OFFICINA" push
