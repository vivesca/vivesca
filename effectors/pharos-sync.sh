#!/usr/bin/env bash
# Sync Claude config (MEMORY.md, settings.json) to officina repo.
# Runs every 15min via com.terry.pharos-sync LaunchAgent.
set -uo pipefail

OFFICINA="$HOME/officina"
CLAUDE_DIR="$HOME/.claude"

sync_file() {
    local src="$1" dst="$2"
    [ -f "$src" ] || return 1
    if [ ! -f "$dst" ] || ! diff -q "$src" "$dst" &>/dev/null; then
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
        echo "updated: $(basename "$dst")"
        return 0
    fi
    return 1
}

changed=false

# Sync entire memory directory
MEMORY_SRC="$CLAUDE_DIR/projects/-Users-terry/memory"
MEMORY_DST="$OFFICINA/claude/memory"
if [ -d "$MEMORY_SRC" ]; then
    mkdir -p "$MEMORY_DST"
    rsync -a --delete "$MEMORY_SRC/" "$MEMORY_DST/" \
        && echo "synced: memory/" && changed=true || true
fi

sync_file \
    "$CLAUDE_DIR/settings.json" \
    "$OFFICINA/claude/settings.json" && changed=true || true

# Push credentials to Fly.io pharos
if [ -f "$CLAUDE_DIR/.credentials.json" ]; then
    CREDS=$(cat "$CLAUDE_DIR/.credentials.json")
    flyctl ssh console -a lucerna -C "bash -c 'cat > /home/terry/.claude/.credentials.json << ENDCREDS
${CREDS}
ENDCREDS
chown terry:terry /home/terry/.claude/.credentials.json'" 2>/dev/null \
        && echo "updated: .credentials.json → lucerna" || true
fi

# Push credentials to MacBooks (via Tailscale)
for host in m2 m3; do
    scp -q -o ConnectTimeout=3 "$CLAUDE_DIR/.credentials.json" "$host":~/.claude/.credentials.json 2>/dev/null \
        && echo "updated: .credentials.json → $host" || true
done

# Push .zshenv + .zshenv.tpl to pharos EC2 (legacy, remove after EC2 termination)
if [ -f "$HOME/.zshenv" ]; then
    scp -q "$HOME/.zshenv" pharos:~/.zshenv 2>/dev/null \
        && echo "updated: .zshenv → pharos" || true
fi
if [ -f "$HOME/.zshenv.tpl" ]; then
    scp -q "$HOME/.zshenv.tpl" pharos:~/.zshenv.tpl 2>/dev/null \
        && echo "updated: .zshenv.tpl → pharos" || true
fi

$changed || exit 0

git -C "$OFFICINA" add claude/memory/ claude/settings.json
git -C "$OFFICINA" commit -m "sync: claude config $(date '+%Y-%m-%d %H:%M')" || true
git -C "$OFFICINA" push || true
