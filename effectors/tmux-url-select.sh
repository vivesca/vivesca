#!/usr/bin/env bash
# Select a URL from the current tmux pane and copy to clipboard via OSC 52.
# Designed for Blink (iOS) where tap-to-open URLs doesn't work inside tmux.

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
