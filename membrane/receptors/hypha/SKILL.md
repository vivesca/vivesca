---
name: hypha
description: "Obsidian vault link graph traversal — navigate links from a note, explore to depth N, find shortest path. \"trace links\", \"link graph\", \"path between notes\""
user_invocable: true
disable-model-invocation: true
cli: hypha
cli_version: 0.1.4
crates_io: https://crates.io/crates/hypha
---

# hypha — Vault Link Graph Traverser

nexis handles vault health. hypha navigates the graph: given a note, explore what connects to it and trace paths between notes.

Name: fungal network filaments — spreads outward from any point.

## CLI

```
hypha <vault_path> --from "Note Name" [--depth N] [--exclude <dir>] [--format human|json]
hypha <vault_path> --path "Note A" "Note B"   [--exclude <dir>] [--format human|json]
```

## Mode: Neighborhood (`--from`)

Show outgoing and incoming links from a note, BFS to depth N (default 1).

```bash
# Depth 1 — direct connections
hypha ~/epigenome/chromatin --from "Capco Theoria Intelligence"

# Depth 2 — direct + one hop out
hypha ~/epigenome/chromatin --from "Capco Theoria Intelligence" --depth 2

# Exclude noisy dirs
hypha ~/epigenome/chromatin --from "Capco Transition" --exclude Archive --exclude "Waking Up"

# JSON output
hypha ~/epigenome/chromatin --from "Capco Theoria Intelligence" --format json | jq .
```

**Output (depth 1):**
```
=== Capco Theoria Intelligence ===

Outgoing (6):
  Bertie Haskins Profile
  GenAI Document Processing One-Pager
  ...

Incoming (10):
  Capco - First 30 Days
  Capco Transition
  ...
```

**Output (depth 2+):** adds `── Depth N ──` sections with deduplicated new nodes at each level.

## Mode: Suggest (`--suggest`)

Surface notes that probably should connect to a note but don't yet. Scoring: **Resource Allocation** — each shared neighbor k contributes `1/degree(k)`. Penalises hub notes harder than Adamic-Adar; empirically outperforms it on sparse graphs. Calendrical notes (YYYY-MM-DD, YYYY-WXX) excluded — temporal hubs, not semantic signal.

```bash
hypha ~/epigenome/chromatin --suggest "Capco Theoria Intelligence"

# Limit results (default 15)
hypha ~/epigenome/chromatin --suggest "Capco Theoria Intelligence" --top 5

# Exclude noisy dirs
hypha ~/epigenome/chromatin --suggest "Capco Theoria Intelligence" --exclude Archive --exclude "Waking Up"

# JSON
hypha ~/epigenome/chromatin --suggest "Capco Theoria Intelligence" --format json | jq .
```

**Output:**
```
=== Suggested links for: Capco Theoria Intelligence ===

  HSBC AI Risk Tiering Framework - Strawman
    → Capco Prep - AI Governance Research, Responsible AI and MRM, ...

  Capco Transition
    → Capco - First 30 Days, Capco Day 1 Strategy, ...
```

Shared neighbors shown under each suggestion — makes signal vs noise judgment instant. Pure graph topology, no NLP.

## Mode: Path (`--path`)

Find shortest directed path from Note A to Note B (follows outgoing links).

```bash
hypha ~/epigenome/chromatin --path "Capco Transition" "Bertie Haskins Profile"
```

**Output:**
```
=== Path: Capco Transition → Bertie Haskins Profile (2 hops) ===
  Capco Transition → Capco Day 1 Strategy → Bertie Haskins Profile
```

If no path exists: exits 1 with "No directed path found from X to Y".

## Note Resolution

Case-insensitive stem match. Three outcomes:
1. Exact match → proceed
2. No match → "Note not found: X" (exit 1)
3. Ambiguous match → lists candidates (exit 1)

Quotes required for multi-word note names.

## Exit Codes

- 0: success
- 1: note not found, ambiguous, or no path
- 2: fatal (invalid vault path)

## Source

`~/code/hypha/` — single-file Rust CLI, same parsing layer as nexis (shared verbatim).
