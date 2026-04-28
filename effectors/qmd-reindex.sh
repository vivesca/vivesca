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

# To upgrade to Qwen3-Embedding-0.6B (MTEB top-ranked, multilingual), uncomment
# the line below AND run `qmd embed -f` ONCE manually after enabling. Vectors
# are not cross-compatible between models — without -f, you get a mixed-model
# index where new docs use Qwen3 and existing docs use embeddinggemma-300M.
# export QMD_EMBED_MODEL="hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"

# Skip if qmd embed is already running
if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

qmd update 2>/dev/null
qmd embed 2>/dev/null
