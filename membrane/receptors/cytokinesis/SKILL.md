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

## Mid-Session Capture

Capture continuously — don't wait for `/cytokinesis`. The end-of-session pass is verification, not the main event.

| Signal | Route to | Gate |
|---|---|---|
| Resolution ("that worked", "it's fixed") | Antisera if non-trivial | Would a fresh session benefit? |
| Correction from Terry | Memory (feedback) | Always file |
| Surprise / unexpected behavior | Antisera | Always file |
| Repeated manual step (2+) | Hook candidate (methylation) | Always file |
| Workflow improvement idea | Skill edit (now, not deferred) | Always file |
| Publishable insight | Tweet / garden | Ship immediately |
| State change | Tonus.md | Always update |
| Commitment / action | Praxis.md (with context) | Always file |

**Default: FILE.** Over-filter is the LLM failure mode. A separate process handles forgetting. Priority: prediction errors > novelty > emotional weight > pattern completion > routine.

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

In parallel:

1. **`cytokinesis gather`** — deterministic pre-checks
2. **LLM extraction** — scan session for candidates, classify by priority
3. **Source data check** — user-provided facts that fed deliverables but weren't persisted to vault? Route via `emit_vault_note`

Then: **present candidates and act** — show the full list with routing decisions, file immediately. Act-and-report, don't block on input.

If continuous capture handled most of it → quick verification pass, report filed=0.

**MEMORY.md ≥145 lines →** downregulate by recurrence signal, not by position. Check `hits:` and `last-seen:` in memory file frontmatter (updated automatically by dendrite.py on every Read). Lowest hits + oldest last-seen = downregulate candidate. Move to `~/epigenome/chromatin/immunity/memory-overflow.md` (reversible — re-promote if topic resurfaces).

### 1a. Correction review (5 min max — checklist, not essay)

**Per correction** (scan for every redirect, correction, or pushback):

| Question | Routes to |
|---|---|
| What did I get wrong? | Principle extraction |
| What generalizes? | Memory or skill edit |
| Taste signal: too cautious, too aggressive, or genuine ambiguity? | Feedback memory (see `feedback_poiesis_taste_calibration.md`) |

**Session-wide** (scan beginning and middle, not just end):

| Question | What it catches |
|---|---|
| Wrong assumptions? | Silent factual discoveries — easy to absorb without filing |
| What was deleted/removed? | Lessons, regrets, dangling references |
| Where did I resist? | Miscalibrated defaults |
| What was inefficient? | Missing checks, wrong assumptions a rule could prevent |
| Recurring patterns? | Deeper principle underneath N separate incidents |
| External system learnings? | Cross-ecosystem intelligence — route to antisera/memory |
| What do I believe differently now? | Calibration shifts > facts (100 future situations vs 1) |
| What worked unusually well? | Silent successes that should be repeatable |
| What almost went wrong? | Near-misses — accidental prevention isn't reliable |

**Filing discipline:**
- Tag: `fact` / `hypothesis` / `policy`. Escalation: etiology's occurrence table.
- Format: `IF X, THEN Y` — not prose principles.
- Resistance to filing IS signal — the obvious/embarrassing lessons are often the most durable.

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

**Capture displacement check:** "If I deleted all memories filed this session, would my behavior change next session?" If yes, the memories are load-bearing. If no, they're theater — the real learning happened in the code/skill edits, and the memories are redundant narration.

### 2. Housekeeping (full mode only)

1. **Uncommitted?** Dirty repos touched this session → commit.
2. **TODO sweep:** `cytokinesis archive`
3. **Session log:** `cytokinesis daily "title"` — outcomes + session arc prose.
4. **Tonus.md** — update deltas. Max 15 lines, dual-ledger.

### 3. Daily note (last step — the output)

1. Run `cytokinesis daily "title"` — pre-fills deterministic sections (Filed, Published, Mechanised, Residual)
2. **Edit** the daily note to fill LLM sections (Outcomes, Parked, Arc). All sections present even if empty.
3. The Edit diff IS the completion signal. If it happened, cytokinesis is done.

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
