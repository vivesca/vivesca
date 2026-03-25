---
name: cytokinesis
description: Consolidate while context is hot — capture what dies with the session
cli: cytokinesis
user_invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
---

# Cytokinesis — Session Memory Consolidation

> Cytokinesis is continuous, not terminal. Capture anything useful to vivesca the moment it surfaces — don't wait for the session to die. The end-of-session invocation is a verification pass, not the main event. The ideal cytokinesis has nothing left to do.

**One test:** is this useful to vivesca? If yes, route it:

| What | Where |
|---|---|
| Learning / correction | Memory file + MEMORY.md index |
| Workflow improvement | Skill update (edit now, don't defer) |
| Commitment / action | Praxis.md (with full context — hot todos > cold stubs) |
| Publishable insight | Tweet / garden / announce (draft and ship) |
| Tool gotcha | `~/vivesca/loci/solutions/` |
| State change | Tonus.md |

**Capture generously — this means FILE MORE, not less.** Default is FILE. Only SKIP what is duplicated verbatim in an existing memory. If in doubt, file. The LLM's default is to over-filter; fight that instinct. A separate process handles forgetting.

**Selection priority** (when triaging candidates):
1. **Prediction errors** — corrections, wrong assumptions. Highest signal.
2. **Novelty** — first time this came up.
3. **Emotional weight** — strong pushback, repeated insistence.
4. **Pattern completion** — reinforces existing memory. Update, don't duplicate.
5. **Routine/expected** — only skip if obviously already known.

**Full** (`/cytokinesis`) — consolidation + housekeeping.
**Checkpoint** (`/cytokinesis checkpoint`, auto at gear shifts) — consolidation only.

## Workflow

### 1. Consolidation (the point)

Three things in parallel:

1. **Ask Terry: "What's worth keeping?"** — the nucleus knows what mattered.
2. **Run `cytokinesis gather`** — LLM extracts what it thinks is valuable.
3. **Source data check:** Were any factual data points (metrics, thresholds, figures, dates, decisions) entered by the user that fed deliverables (emails, gists, slides) but were not persisted to vault or histone? Route hits to `~/epigenome/chromatin/Reference/work/` vault notes via `emit_vault_note`.

Merge all three. Terry fills gaps the LLM missed. LLM catches things Terry forgot. Source data check catches what both missed. Route everything to the right places.

If continuous capture handled most of it → quick verification pass for all three.

**MEMORY.md ≥145 lines →** downregulate by recurrence signal, not by position. Check `hits:` and `last-seen:` in memory file frontmatter (updated automatically by dendrite.py on every Read). Lowest hits + oldest last-seen = downregulate candidate. Move to `~/vivesca/loci/solutions/memory-overflow.md` (reversible — re-promote if topic resurfaces).

### 1b. Audit Signal

After consolidation, count findings routed in this pass. This is the "cytokinesis residual" — findings that should have been captured mid-session but were not.

- `filed=N` — findings captured now (should have been captured mid-session)
- `skipped=M` — candidates reviewed and correctly skipped
- If `filed > 0`, note: "Continuous capture missed N items. What blocked mid-session routing?"

This is not a punishment — it's proprioception. The number trends toward zero as the protocol embeds. `filed=0` is the ideal session.

### 2. Housekeeping (full mode only)

1. **Uncommitted?** Dirty repos touched this session → commit.
2. **TODO sweep:** `cytokinesis archive`
3. **Session log:** `cytokinesis daily "title"` — outcomes + session arc prose.
4. **Tonus.md** — update deltas. Max 15 lines, dual-ledger.

## Output

```
─── Cytokinesis ──────────────────────────────────
Filed: [exact file paths]
Published: [tweets/garden posts or "none"]
Done.
─────────────────────────────────────────────────
```

## CLI: `cytokinesis` (on PATH)

| Subcommand | Purpose |
|---|---|
| `gather` | Deterministic pre-wrap checks: dirty repos, skill gaps, MEMORY.md line count, Tonus age, dep-check, reflection scan |
| `gather --perceptual` | Human-readable terminal output |
| `gather --syntactic` | JSON output (for piping to `extract`) |
| `archive` | Move `[x]` items from Praxis.md → Praxis Archive.md |
| `daily "title"` | Append session log template to today's daily note |
| `reflect <session-id>` | Scan transcript for reflection candidates (haiku) |
| `extract --input <json>` | Review candidates, recommend FILE/SKIP/PRINCIPLE (haiku) |

## Boundaries

- No deep audits or research — consolidation, not workstream.
- Full mode: stop after writes.
- Checkpoint mode: continue after output.
