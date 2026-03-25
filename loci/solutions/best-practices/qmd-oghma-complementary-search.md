---
module: Search
date: 2026-02-07
problem_type: best_practice
component: search
symptoms:
  - Oghma MCP defaulting to keyword-only search (missing vector matches)
  - docs/solutions/ not indexed by QMD (invisible to semantic search)
  - Two search systems running in parallel but not covering each other's gaps
root_cause: config_error
resolution_type: config_change
severity: medium
tags:
  - oghma
  - qmd
  - semantic-search
  - hybrid-search
  - rag
  - memory
related_files:
  - ~/code/oghma/src/oghma/mcp_server.py
  - ~/code/oghma/src/oghma/storage.py
---

# QMD + Oghma: Complementary Search Architecture

## Context

Two local search systems serve AI agents via MCP:

| System | What it searches | How |
|--------|-----------------|-----|
| **Oghma** | Extracted learnings from coding transcripts | FTS5 + sqlite-vec, structured metadata |
| **QMD** | Raw files (vault notes, docs) | BM25 + vector + Qwen reranker |

They're complementary, not redundant. Oghma's value is the extraction pipeline
(Gemini Flash distils insights from transcripts). QMD indexes files as-is with
better chunking (markdown-aware) and reranking (Qwen3 0.6B).

## Problem

Two gaps existed:

1. **Oghma defaulted to keyword search** — the hybrid BM25+vector+RRF mode existed
   in `storage.py` but the MCP tool's `search_mode` parameter defaulted to `"keyword"`.
   Agents had to explicitly request `search_mode="hybrid"` to get vector results.

2. **`~/docs/solutions/` not in QMD** — structured learnings from compound-engineering
   were only searchable via Oghma (if extracted) or direct grep. QMD only indexed
   `~/code/vivesca-terry/chromatin/`.

## Solution

### 1. Flip Oghma default to hybrid

One-line change in `mcp_server.py`:

```python
# Before
search_mode: str = "keyword",

# After
search_mode: str = "hybrid",
```

Since Oghma is editable-installed (`python3 -c "import oghma; print(oghma.__file__)"`
points to source), this is live immediately — no reinstall needed.

### 2. Add solutions collection to QMD

```bash
qmd collection add ~/docs/solutions/ --name solutions --mask "**/*.md"
qmd embed
```

This indexed 41 files into 63 chunks. Searchable via:
```bash
qmd search "browser automation" -c solutions
qmd vsearch "race condition fix" -c solutions
qmd query "how to handle N+1" -c solutions  # hybrid + rerank
```

## Key Insights

### Oghma's hybrid search is already good
The existing implementation in `storage.py` lines 596-651 uses:
- BM25 scoring via `bm25(memories_fts)` on the FTS5 table
- Vector cosine distance via sqlite-vec ANN search
- RRF (Reciprocal Rank Fusion) with K=60, equal 0.5/0.5 weighting
- Recency boost: `1.0 + 0.5 / (1.0 + days_old)`

Tuning constants at lines 55-59:
```python
MIN_HYBRID_QUERY_LENGTH = 3
VECTOR_K_MULTIPLIER = 4     # Retrieve 4x limit vectors before RRF
VECTOR_K_MIN = 25
RRF_K_DEFAULT = 60
```

### QMD collection management
- Add: `qmd collection add <path> --name <name> --mask "<glob>"`
- Remove: `qmd collection remove <name>`
- List: `qmd collection list`
- After adding, must run `qmd embed` to vectorise new chunks

### Editable installs survive source edits
If `pip show <pkg>` shows `Location:` pointing to your source tree, changes to
`.py` files are live immediately. No need to reinstall. The `pyproject.toml` can
even have build errors (stale license classifier) without affecting the running
installation.

## Prevention

- When adding new knowledge directories, add them to **both** QMD and ensure
  Oghma's extraction pipeline covers relevant sources
- Default search modes should always be the most capable mode — opt-out is
  safer than opt-in for quality
- Check `qmd status` periodically to verify collections are up to date
