#!/usr/bin/env bash
# Upgrade Claude Code from GitHub releases on both soma and mac
set -euo pipefail

LATEST=$(curl -sI https://github.com/anthropics/claude-code/releases/latest | grep -i location | sed 's|.*/v||;s/\r//')
CURRENT=$(claude --version 2>&1 | awk '{print $1}')

if [ "$LATEST" = "$CURRENT" ]; then
  echo "Already on $CURRENT"
  exit 0
fi

echo "Upgrading $CURRENT → $LATEST"
TMPDIR=$(mktemp -d)

# Soma (linux-x64)
curl -sL "https://github.com/anthropics/claude-code/releases/download/v${LATEST}/claude-linux-x64.tar.gz" -o "$TMPDIR/claude-linux.tar.gz"
tar xzf "$TMPDIR/claude-linux.tar.gz" -C "$TMPDIR"
cp "$TMPDIR/claude" "$HOME/.local/share/claude/versions/$LATEST"
ln -sf "$HOME/.local/share/claude/versions/$LATEST" "$HOME/.local/bin/claude"
echo "Soma: $(claude --version)"

# Mac (darwin-arm64)
curl -sL "https://github.com/anthropics/claude-code/releases/download/v${LATEST}/claude-darwin-arm64.tar.gz" -o "$TMPDIR/claude-mac.tar.gz"
scp "$TMPDIR/claude-mac.tar.gz" mac:/tmp/
ssh mac "mkdir -p /tmp/claude-upg && tar xzf /tmp/claude-mac.tar.gz -C /tmp/claude-upg && cp /tmp/claude-upg/claude ~/.local/share/claude/versions/$LATEST && ln -sf ~/.local/share/claude/versions/$LATEST ~/.local/bin/claude && claude --version"

rm -rf "$TMPDIR"
