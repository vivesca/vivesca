---
name: docima
description: AI agent memory benchmark — compare 10 backends on storage, retrieval, and drift. For benchmarking/analysis only, not general memory work.
user_invocable: false
---

# docima — AI Agent Memory Benchmark

Comparative benchmark for AI agent memory backends. 10 backends, standardised interface, nightly drift tracking.

## Commands

```bash
# Add a fact to backends
docima add "The HKMA issued new AI guidance in March 2026" -b mem0
docima add "fact" -b all

# Query across backends
docima query "HKMA AI guidance" -b all

# List backends and their status
docima backends

# Count stored memories per backend
docima count -b all

# Run benchmark
docima benchmark --quick          # Smoke test: subset
docima benchmark --full           # Full corpus, all backends
docima benchmark --daily          # Nightly append mode

# Compare ranking drift across backends
docima drift

# Interactive blind evaluation
docima eval --blind

# Generate report from saved results
docima report

# Import facts from markdown files
docima import ~/notes/facts.md -b all
docima import ~/notes/facts/ -b all --dry-run
```

## Backends (10)

| Backend | Type | Status | Notes |
|---------|------|--------|-------|
| markdown | File | Always works | Baseline, no dependencies |
| mem0 | Framework | Local mode | `mem0ai` package |
| graphiti | Graph | KuzuDB + LLM | Needs Ollama running |
| cognee | Graph | Neo4j + embeddings | Heavy deps |
| letta | Agent | Letta server | Needs `letta server` running |
| langmem | Framework | LangChain-based | |
| memoryscope | Framework | ModelScope-based | |
| sqlite_vec | DB | SQLite + vectors | Lightweight |
| pgvector | DB | PostgreSQL + vectors | Needs pg running |
| neo4j | Graph DB | Cypher queries | Needs Neo4j running |

## Architecture

- **Interface:** `MemoryBackend` ABC — `add()`, `query()`, `count()`, `clear()`
- **Registry:** `BACKENDS` dict maps name → class path, lazy-loaded
- **Config:** `~/.config/docima/config.yaml` (backend-specific settings)
- **Data:** `~/.local/share/docima/` (results, corpus, queries)
- **Test corpus:** `data/corpus.yaml` (50 facts), `data/queries.yaml` (20 queries)

## Experiment Protocol

1. **Seed:** `docima import` with MEMORY.md + corpus.yaml
2. **Nightly:** legatus job runs `docima benchmark --daily` + `docima drift` at 02:50
3. **Weekly:** `docima report` for comparison table
4. **Calibration:** `docima eval --blind` for subjective quality check
5. **After 14 days:** enough data for publishable comparison

## MEMORY.md Replication Hook

PostToolUse hook (`~/.claude/hooks/docima-replicate.py`) — when MEMORY.md is edited, new bullet points are silently replicated to all docima backends. This gives the experiment real-world data alongside the synthetic corpus.

## Gotchas

- **Graphiti needs Ollama running** — `ollama serve` in background, model `qwen2.5:14b` pulled
- **Letta needs server** — `letta server` on port 8283
- **pgvector needs PostgreSQL** — `brew services start postgresql@16`
- **Neo4j needs server** — `neo4j start` (or Docker)
- **`available_backends()`** returns only backends whose deps are installed — safe to call without all backends set up
- **Dep pollution risk** — delegates may promote optional deps to main. Check `pyproject.toml` after any delegation.

## Source

`~/code/docima/` — Python, Click, hatchling. GitHub: `terry-li-hm/docima` (private).

## Consulting Angle

No independent AI agent memory benchmark exists. This fills the gap — the comparison table is a Capco differentiator for client conversations about agent architecture. See `~/docs/solutions/consulting-memory-backend-gap.md`.
