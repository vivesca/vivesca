#!/usr/bin/env bash
# Select a URL from the current tmux pane and copy to clipboard via OSC 52.
# Designed for Blink (iOS) where tap-to-open URLs doesn't work inside tmux.

set -euo pipefail

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Usage: tmux-url-select.sh"
    echo ""
    echo "Interactively select a URL from the current tmux pane and copy"
    echo "it to the clipboard via OSC 52 (works in Blink/tmux)."
    echo ""
    echo "Requires: fzf, tmux, /tmp/tmux-url-buffer populated by a key binding."
    exit 0
fi

urls=$(grep -oE 'https?://[^ >)"'"'"']+' /tmp/tmux-url-buffer | awk '!seen[$0]++')

if [ -z "$urls" ]; then
    echo "No URLs found in pane"
    sleep 1
    exit 0
fi

selected=$(echo "$urls" | fzf --reverse --prompt="Copy URL: " --no-info)

if [ -n "$selected" ]; then
    # Emit OSC 52 directly — works through tmux passthrough to Blink
    encoded=$(printf '%s' "$selected" | base64)
    printf '\033]52;c;%s\a' "$encoded"
    tmux display-message "Copied: $selected"
fi
