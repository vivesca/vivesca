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

1. **`cytokinesis gather --syntactic`** — deterministic pre-checks (JSON)
2. **LLM extraction** — scan session for candidates, classify by priority
3. **Source data check** — user-provided facts that fed deliverables but weren't persisted to chromatin? Write directly using the Write tool

Then: **present candidates and act** — show the full list with routing decisions, file immediately. Act-and-report, don't block on input.

If continuous capture handled most of it → quick verification pass, report filed=0.

**MEMORY.md ≥145 lines →** downregulate by recurrence signal, not by position. Check `hits:` and `last-seen:` in memory file frontmatter (updated automatically by dendrite.py on every Read). Lowest hits + oldest last-seen = downregulate candidate. Move to `~/epigenome/chromatin/immunity/memory-overflow.md` (reversible — re-promote if topic resurfaces).

### 1a. Correction review + methylation (5 min max)

Read `references/review-checklist.md` — covers per-correction questions, 9 session-wide questions, filing discipline, and methylation scan.

**The test:** if this session replayed tomorrow with a fresh context, would the organism handle it better? If not, something wasn't methylated. Build it now — context is hottest during the session that revealed the gap.

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
| `gather --syntactic` | JSON output (most token-efficient; use this in skill) |
| `archive` | Move `[x]` items from Praxis.md → Praxis Archive.md |
| `daily "title"` | Append session log template to today's daily note |
| `reflect <session-id>` | Scan transcript for reflection candidates (haiku) |
| `extract --input <json>` | Review candidates, recommend FILE/SKIP/PRINCIPLE (haiku) |

## Boundaries

- No deep audits or research — consolidation, not workstream.
- Full mode: stop after writes.
- Checkpoint mode: continue after output.
