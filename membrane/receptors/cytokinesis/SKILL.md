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

## Auto-trigger Signals

Capture mid-session when you detect:
- **Resolution phrases** — "that worked", "it's fixed", "working now", "that's it" → capture the solve if non-trivial
- **Correction** — Terry corrects an assumption or approach → memory candidate
- **Surprise** — unexpected behavior, tool gotcha, undocumented constraint → antisera candidate
- **Repeated manual step** — same action done 2+ times → methylation candidate (hook/rule)

**Non-trivial gate:** Only capture solves that required multiple investigation steps, tricky debugging, or non-obvious reasoning. Skip: typo fixes, config changes, single-step obvious fixes. The test: "Would a fresh session benefit from knowing this?"

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

1. **Run `cytokinesis gather`** — deterministic pre-checks.
2. **LLM extraction** — scan session for candidates, classify each by selection priority.
3. **Source data check** — factual data points entered by user that fed deliverables but weren't persisted to vault or histone? Route to `~/epigenome/chromatin/euchromatin/work/` via `emit_vault_note`.
4. **Present candidates and act** — show the full list with routing decisions, file immediately, note anything Terry might want to review. Don't block on input — act-and-report. Terry corrects after if needed.

If continuous capture handled most of it → quick verification pass, report filed=0.

**MEMORY.md ≥145 lines →** downregulate by recurrence signal, not by position. Check `hits:` and `last-seen:` in memory file frontmatter (updated automatically by dendrite.py on every Read). Lowest hits + oldest last-seen = downregulate candidate. Move to `~/epigenome/chromatin/immunity/memory-overflow.md` (reversible — re-promote if topic resurfaces).

### 1a. Correction review (highest signal — do this explicitly)

Scan the session for every moment Terry **redirected, corrected, or pushed back**. Each one is a candidate lesson. Three questions per correction:
- What did I get wrong or miss?
- What's the generalizable principle?
- Would a future session benefit from knowing this?

Then six broader questions about the session:
- **"What assumptions were proven wrong?"** — not just user corrections, but factual discoveries (tools that don't work as expected, paths that don't exist, conventions that differ from assumed). These are easy to absorb silently without filing.
- **"What did we delete or remove?"** — every deletion is a potential lesson or future regret. Was value extracted first? Is the removal reversible? Does anything still reference the deleted thing?
- **"Where did I initially resist the user's direction?"** — resistance points signal miscalibrated defaults. If the user's alternative turned out better, the resistance was a bias worth examining.
- **"What took longer than it should have?"** — inefficiency is a signal. Repeated attempts, backtracking, or rework point to a missing check or wrong assumption that a rule could prevent.
- **"What patterns recurred?"** — if the same lesson appeared 2+ times in different guises, there's a deeper principle underneath. Extract that instead of filing N separate memories.
- **"What did we learn about external systems?"** — tool behavior, platform conventions, third-party architecture. Cross-ecosystem intelligence compounds, especially for consulting. Route to antisera or memory.

Finally, one integration question (not extraction — this is about updated judgment, not filed facts):
- **"What do I believe differently now than when this session started?"** — changed confidence levels matter more than changed facts. "I'm less confident in my assumptions about CLI behavior" applies to 100 future situations; "CC doesn't read .agents/" applies to 1. File the calibration shift, not just the fact.

**Guard rails:**
- **Time budget: 5 minutes max** for the full 1a review. If it takes longer, you're over-reflecting.
- **Scan the whole session, not just the end.** Recency bias makes the last event dominate. The most important correction often happened in the middle.
- **Resistance to filing IS signal.** If something feels too obvious or embarrassing to file, examine that — the most durable lessons often feel trivially simple.
- **Silent success scan.** Pain gets filed; quiet wins don't. Ask: "What worked unusually well that should be made repeatable?"
- **Near-miss review.** "What almost went wrong, and why didn't it?" Accidental prevention isn't reliable.
- **fact / hypothesis / policy.** Tag each capture. Most lessons start as `hypothesis` — only promote to `policy` (changes defaults) after recurrence or strong evidence. Over-ruling from one incident creates brittle systems.
- **Same insight 3 times → stop filing, change the system.** If a lesson keeps appearing, reflection has failed. Next step must be environmental: hook, automation, constraint — not another memory. See etiology's escalation table (1st = hypothesis, 2nd = structural cause, 3rd = mandatory system change).
- **IF X, THEN Y format.** Rewrite actionable lessons as implementation intentions, not prose principles. "When I'm about to delete managed state, check for automation first" beats "fix automation before deleting."

This is separate from the LLM extraction because corrections are easy to under-file. The LLM's instinct is to file facts and architecture but skip behavioral lessons — "I suggested X, user said Y instead" feels like ephemeral conversation, but the *why* behind the redirect is often the most durable insight.

For each correction, also classify the **taste calibration signal:**
- "I held back / asked permission, Terry said just do it" → recalibrate toward auto-apply. File as feedback memory.
- "I proposed X, Terry proposed better Y after discussion" → genuine ambiguity, no calibration needed. File the principle.
- "I auto-applied X, Terry rejected it" → recalibrate toward holding. File as feedback memory.

See `memory/feedback_poiesis_taste_calibration.md` for the threshold: auto-fix freely, hold only when judgment is genuinely ambiguous.

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
