#!/bin/bash
# Copy current tmux pane content to iOS clipboard via OSC 52
# Usage: tmux-osc52.sh <pane_id> <pane_tty>

case "${1:-}" in
  -h|--help)
    sed -n '2,3p' "$0"
    exit 0
    ;;
esac

PANE="$1"
TTY="$2"
DATA=$(tmux capture-pane -p -t "$PANE" | base64 | tr -d '\n')
printf '\033]52;c;%s\007' "$DATA" > "$TTY"
