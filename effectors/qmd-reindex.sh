#!/bin/bash
# QMD re-index — embed new/changed vault notes for semantic search
# Runs separately from vault backup (embedding is slow)

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: qmd-reindex.sh"
    echo ""
    echo "Re-index vault notes for semantic search via 'qmd update && qmd embed'."
    echo "Skips if a qmd embed is already running."
    exit 0
fi

export PATH="$HOME/.bun/bin:$PATH"

# Skip if qmd embed is already running
if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

qmd update 2>/dev/null
qmd embed 2>/dev/null
