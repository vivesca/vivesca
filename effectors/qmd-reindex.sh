#!/bin/bash
# QMD re-index — embed new/changed vault notes for semantic search
# Runs separately from vault backup (embedding is slow)

export PATH="$HOME/.bun/bin:$PATH"

# Skip if qmd embed is already running
if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

qmd update 2>/dev/null
qmd embed 2>/dev/null
