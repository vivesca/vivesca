---
name: qmd
description: Semantic search over the vault using QMD. For conceptual queries beyond literal grep.
user_invocable: false
github_url: https://github.com/tobi/qmd
---

# QMD Vault Search

QMD indexes the vault for semantic search. Complements literal grep with "find notes *about* this topic" queries.

## When to Use

- **Grep fails** — Searching for concept, not exact phrase
- **Fuzzy matching** — "notes about interview prep" not just `[[Interview Prep]]`
- **Exploration** — "what do I know about HSBC?" across all notes

## Usage (CLI only — MCP disabled Feb 2026, saves ~1,300 tokens/turn)

```bash
# Keyword search — fast BM25 (use for exact terms)
qmd search "HSBC interview" -n 5

# Semantic search — vector similarity (use for concepts)
qmd vsearch "preparing for banking interviews"

# Hybrid with reranking — best quality (use for important queries)
qmd query "what's my relationship with Kelvin Chan"

# Get full document by path or docid
qmd get "notes/Capco Transition.md"

# Get multiple docs by glob
qmd multi-get "notes/Capco/*.md"

# Search specific collection
qmd search "recruiter" -c notes

# Output file paths only (for piping)
qmd search "recruiter" --files
```

## Maintenance

```bash
qmd update              # Re-index changed files
qmd status              # Check index health
qmd embed               # Update embeddings (slow)
nohup qmd embed &       # Background embedding
```

## Setup (Already Done)

```bash
bun install -g https://github.com/tobi/qmd
qmd collection add ~/epigenome/chromatin --name notes --exclude "Archive/**"
qmd context add qmd://notes "Terry's Obsidian vault"
qmd embed  # Generate vectors (one-time, slow)
# MCP removed: was `claude mcp add qmd -s user -- qmd mcp`
```

## Gotchas

- **Emoji filenames crash indexer** — Rename files like `🤑.md` to `money-emoji.md`
- **Archive excluded** — Old Eden notes not indexed (intentional)
- **Embeddings required for vsearch** — Keyword search works without them
- **Local models** — Uses node-llama-cpp with GGUF models, no API calls

## Related

- `/weekly` — Sunday maintenance checklist includes QMD reindex
