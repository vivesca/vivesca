---
name: cytokinesis
description: Capture session learnings before context is lost. "wrap up", "end of session"
cli: cytokinesis
user_invocable: true
context: inline
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
| Domain knowhow discovered (3+ workarounds, fallback chains, per-target patterns) | **Proactively propose** skill + CLI split (see artifex §15-16) | Would next jurisdiction/batch benefit? |
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

1. **`cytokinesis gather --fast`** (CLI, ~1s) — deterministic pre-checks, returns structured Vital
2. **LLM extraction** — scan session for candidates, classify by priority
3. **Source data check** — user-provided facts that fed deliverables but weren't persisted to chromatin? Write directly using the Write tool

Then: **present candidates and act** — show the full list with routing decisions, file immediately. Act-and-report, don't block on input.

If continuous capture handled most of it → quick verification pass, report filed=0.

If gather reports >50 stale marks, pick the 3 with most stale path references and either update or delete them. Don't audit all — just keep the count trending down.

**MEMORY.md ≥145 lines →** downregulate by recurrence signal, not by position. Check `hits:` and `last-seen:` in memory file frontmatter (updated automatically by dendrite.py on every Read). Lowest hits + oldest last-seen = downregulate candidate. Move to `~/epigenome/chromatin/immunity/memory-overflow.md` (reversible — re-promote if topic resurfaces).

### 1a. Correction capture + taste calibration (5 min max)

Two scans:

**Corrections** — every instance where Terry stopped, corrected, or questioned CC:
- Rejected a tool call or approach ("no", "wait", "should we?")
- Questioned an assumption ("is this the best design?", "why not X?")
- Pointed out missed work ("did you actually read the files?")
For each: wrong assumption → generalizable principle → file as feedback (`protected: true` if architectural).

**Taste calibration** — the preference surface between Terry and CC:
- What did Terry prefer that wasn't obvious? (design choices, tool preferences, pacing)
- What approach did Terry confirm or accept without pushback?
- What tone/autonomy level worked this session?
For each: file as feedback with the preference and why, so future sessions match taste without re-learning.

**The test:** if this session replayed tomorrow with a fresh context, would CC make the same mistakes AND misjudge the same preferences? If yes, something wasn't methylated.

### 1b. Skill drift check (2 min max)

For each correction or learning filed this session, ask: **does this change how a skill operates?** Skills encode behavior; memories encode context. If the learning says "don't do X" and a skill currently says "do X", the skill is stale.

Scan:
- Feedback memories filed this session — grep the skill directory for the topic
- Behavioral corrections from Terry — which skill guided the wrong behavior?
- Surprising outcomes — did a skill's instructions cause the surprise?

For each match: **edit the skill now** (add gotcha, update anti-pattern, fix instruction). Don't defer — the session context makes the edit precise. A memory without the corresponding skill update is a band-aid; the skill will guide the same mistake next time.

**The test:** "If a fresh CC follows this skill tomorrow, will it repeat the mistake?" If yes, the skill needs updating, not just the memory.

### 1c. Directory context crystallization (2 min max)

Scan directories where this session did 3+ file reads or edits. For each, check: does a `CLAUDE.md` exist? If not, and the directory has non-obvious structure (multiple files, config, architecture worth explaining), write one.

**What to include:** what the system does, key files, infrastructure/config, decision rationale. Not obvious things derivable from `ls` or reading one file.

**Skip:** single-script directories, test directories, directories with <3 files, anything already documented by a parent CLAUDE.md.

**The test:** "If a fresh CC session `cd`'d here tomorrow, would it need an Explore agent or 5+ reads to understand this directory?" If yes, write the CLAUDE.md now — you already paid the context cost.

### 1d. Audit signal

After consolidation, count findings routed in this pass. This is the "cytokinesis residual" — findings that should have been captured mid-session but were not.

- `filed=N` — findings captured now (should have been captured mid-session)
- `skipped=M` — candidates reviewed and correctly skipped
- If `filed > 0`, note: "Continuous capture missed N items. What blocked mid-session routing?"

This is not a punishment — it's proprioception. The number trends toward zero as the protocol embeds. `filed=0` is the ideal session.

**Capture displacement check:** "If I deleted all memories filed this session, would my behavior change next session?" If yes, the memories are load-bearing. If no, they're theater — the real learning happened in the code/skill edits, and the memories are redundant narration.

### 1e. Publish (don't defer)

If the session produced a publishable insight — pattern, framework, lesson — draft and publish NOW. The insight is hottest in the session that produced it. Deferring to "tomorrow" kills 80% of posts.

Test: "Would I explain this to a peer over coffee?" If yes, it's a post.

**Mechanism:**
1. CC identifies the insight and frames it (judgment — what's the takeaway?)
2. `golem --full "Draft a garden post titled '<title>'. Core insight: <insight>. Use litura --platform garden to match Terry's voice. Then run: sarcio new '<title>' and write the post to the file sarcio created. 400-600 words, consulting-grade."` 
3. CC reviews the draft (judgment — does it land?)
4. `sarcio publish` — ship it

Don't ask permission. Don't defer. If the insight is real, publish it.

### 2. Housekeeping (full mode only)

1. **Uncommitted?** `cytokinesis flush` — commits dirty repos touched this session. PreCompact hook is the safety net if this is skipped.
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
| `gather --fast` | Deterministic pre-wrap checks: dirty repos, skill gaps, MEMORY.md line count, Tonus age (~1s) |
| `gather` | Full checks including LLM reflection + methylation audit (~60s) |
| `flush` | Commit dirty repos (git add -A + commit per repo) |
| `gather --syntactic` | JSON output (most token-efficient; use this in skill) |
| `archive` | Move `[x]` items from Praxis.md → Praxis Archive.md |
| `daily "title"` | Append session log template to today's daily note |
| `reflect <session-id>` | Scan transcript for reflection candidates (haiku) |
| `extract --input <json>` | Review candidates, recommend FILE/SKIP/PRINCIPLE (haiku) |

Note: gather may take 10+ seconds. If Bash backgrounds it, read the output file directly rather than waiting.

## Boundaries

- No deep audits or research — consolidation, not workstream.
- Full mode: stop after writes.
- Checkpoint mode: continue after output.
