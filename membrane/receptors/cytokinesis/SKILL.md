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
| Tool gotcha | `~/germline/loci/antisera/` |
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

### 0. Unfinished work check (before consolidating)

Before capturing memories, check: **is there unfinished actionable work from this session?** Scan for:
- Open threads that were started but not completed (pending responses, half-done fixes)
- Items deferred to "later" or "next session" that could be finished now
- `cytokinesis gather` dirty repos that were touched this session

If unfinished work exists: **finish it or park it with context — don't consolidate over live work.** Context is hottest right now; wrapping up while actionable items remain wastes that heat. Only ask Terry for input if you've exhausted what you can do autonomously. Consolidation is for what's *done*, not a reason to stop early.

### 1. Consolidation (the point)

Three things in parallel:

1. **Ask Terry: "What's worth keeping?"** — the nucleus knows what mattered. **Wait for the answer.** Don't pre-empt with your own list. Terry's signal is higher-value than LLM extraction — things that felt important, surprising, or painful to the human are the highest-fidelity captures. Present your candidates *after* Terry's, as a "did I miss anything?" check.
2. **Run `cytokinesis gather`** — LLM extracts what it thinks is valuable.
3. **Source data check:** Were any factual data points (metrics, thresholds, figures, dates, decisions) entered by the user that fed deliverables (emails, gists, slides) but were not persisted to vault or histone? Route hits to `~/epigenome/chromatin/euchromatin/work/` vault notes via `emit_vault_note`.

Merge all three. Terry fills gaps the LLM missed. LLM catches things Terry forgot. Source data check catches what both missed. Route everything to the right places.

If continuous capture handled most of it → quick verification pass for all three.

**MEMORY.md ≥145 lines →** downregulate by recurrence signal, not by position. Check `hits:` and `last-seen:` in memory file frontmatter (updated automatically by dendrite.py on every Read). Lowest hits + oldest last-seen = downregulate candidate. Move to `~/germline/loci/antisera/memory-overflow.md` (reversible — re-promote if topic resurfaces).

### 1b. Methylation scan

Proactively scan the session for **vivesca improvement opportunities** — not just "did I learn something?" but "could the organism get stronger from what happened?"

| Signal | Question | Route to |
|---|---|---|
| Same manual step done 2+ times | "Why isn't this a hook?" | Hook (synapse/axon/dendrite) |
| LLM judgment that a rule could have decided | "Why isn't this deterministic?" | Pre-commit, ruff rule, or hook |
| Correction from Terry | "What rule would have prevented this?" | Genome edit or skill update |
| New capability built | "Does it have all three layers?" | MCP tool + skill + CLI check |
| Skill that didn't trigger when it should have | "Is the description wrong?" | Skill description edit |
| Prompt pattern that worked well | "Should this be a skill?" | New skill candidate |
| Tool/API gotcha discovered | "Will a future session hit this?" | `~/germline/loci/antisera/` |

**The test:** if this session replayed tomorrow with a fresh context, would the organism handle it better? If not, something wasn't methylated.

If nothing → good. If something → **build it now.** Context is hottest during the session that revealed the gap. Praxis.md is for things that genuinely can't be done now (external dependency, needs Terry's input, >30min build). Everything else ships before cytokinesis closes.

### 1c. Audit Signal

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

### 3. Daily note (last step — the output)

Append the session log to today's daily note using the **Edit tool** (not MCP `emit_daily_note` or CLI). The Edit diff is the final output — visible, persistent, and verifiable. If the Edit happened, cytokinesis is done. If it didn't, it's not.

Run `cytokinesis daily "title"` first — it pre-fills the deterministic sections (Filed, Published, Mechanised, Residual) from git diffs and session logs. Then Edit the daily note to fill the judgment sections (Outcomes, Parked, Arc).

All sections must be present even if empty — forcing function:

```markdown
## Session: [title]

### Outcomes
- [what was done — outcomes, not process] ← LLM

### Filed
- [memory/skill file paths] ← CLI: git diff on memory/ + receptors/

### Published
- [tweets/garden posts] ← CLI: grep session log for emit_tweet/emit_spark

### Mechanised
- [judgments → rules/hooks/skills] ← CLI: git diff on SKILL.md, hooks, genome.md

### Parked
- [unfinished items with context to resume] ← LLM

### Residual
filed=N, skipped=M ← CLI: count of Filed items

### Arc
[1-2 sentence session narrative] ← LLM
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
