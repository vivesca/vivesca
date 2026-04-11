---
name: cytokinesis
description: Session memory consolidation — end-of-session close (full mode) and mid-session gear shifts (checkpoint mode). Absorbed legatum 2026-04-11. "wrap up", "wrap", "end of session", "legatum", "checkpoint", "what did we learn"
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

Two modes:
- **Full** (`/cytokinesis` or `/wrap`) — end-of-session close. All steps.
- **Checkpoint** (`/cytokinesis checkpoint` or `/wrap checkpoint`, auto at gear shifts) — consolidation only. Skip housekeeping. Preserves context — no /compact, no closure framing.

Session scope = files modified + tool calls + conversation turns since this session began (or since last checkpoint).

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
| Domain knowhow discovered (3+ workarounds, fallback chains, per-target patterns) | **Proactively propose** skill + CLI split (see organogenesis §15-16) | Would next jurisdiction/batch benefit? |
| Publishable insight | Tweet / garden | Ship immediately |
| State change | Tonus.md | Always update |
| Commitment / action | Praxis.md (with context) | Always file |

**Default: FILE.** Over-filter is the LLM failure mode. A separate process handles forgetting. Priority: prediction errors > novelty > emotional weight > pattern completion > routine.

**Mark type ordering (forced checklist — work top-to-bottom, first match wins):**
1. Terry corrected CC's approach or assumption? → `feedback` (protected if architectural)
2. Discovered how a system/tool actually behaves? → `finding`
3. Learned about an ongoing initiative, deadline, or team state? → `project`
4. Found a pointer to external info (URL, portal, channel)? → `reference`
5. Learned about the user's role, preferences, or context? → `user`
6. ONLY if none above → generic note (should be rare — challenge yourself before accepting)

**Full** (`/cytokinesis`) — consolidation + housekeeping.
**Checkpoint** (`/cytokinesis checkpoint`, auto at gear shifts) — consolidation only.

## Workflow

### 0. Pre-wrap check + unfinished work (absorbed from legatum)

**Skip gate:** If NOW.md is <15 minutes old AND user did not explicitly invoke `/wrap`, skip to Step 4 briefly, then Output. Explicit invocation always runs all steps.

**Run `prewrap` + peira status** and answer these five questions. Complete blocking actions (garden post, arsenal) *before* outputting the block — the block is a receipt, not a plan.

```bash
prewrap
peira status 2>/dev/null || true
```

**Questions (explicit yes/no for Q4–5, silence is not "no"):**
1. **Unverified?** Any tool output this session that wasn't checked?
2. **Deferred?** Anything mentioned as "later/next/TODO" not yet captured? Route by type: deadline → TODO.md; context trigger → `memory/priming.md`; neither → daily note.
3. **Uncommitted?** Dirty repos *touched this session*? → offer to commit (leave other repos alone).
4. **Garden posts + consulting arsenal?** Replay the session arc. What did we *learn*, not just *do*? Give yourself 30 seconds of generative thinking. Garden test: non-obvious insight, clear thesis, Terry's lane, no unverified facts → publish immediately via `publish new → write → publish publish --push`. Arsenal test: concretely applicable to a bank/client AI engagement → add to `[[Capco Transition]]`.
5. **CLAUDE.md modified?** Does the edit belong in CLAUDE.md or in a skill / MEMORY.md / `~/docs/solutions/`?

**Unfinished actionable work?** Scan for open threads, items deferred to "later", dirty repos from `cytokinesis gather`. If unfinished work exists: **finish it or park it with context — don't consolidate over live work.** Context is hottest right now. Only ask Terry if you've exhausted what you can do autonomously.

**CLI friction review:** If `~/.claude/cli-friction.jsonl` has entries, group by CLI tool. For each tool with 2+ friction events (or 1 obvious fix), suggest a concrete improvement. Full mode: truncate file after processing. Checkpoint mode: leave intact.

**Background dispatches** — fire with `run_in_background: true`:
| Audit | When |
|-------|------|
| MEMORY.md hook coverage | MEMORY.md modified AND <145 lines |
| Skill staleness | Any skill edited or added |
| Solutions KB dedup | `~/docs/solutions/` modified |
| Vault orphan links (nexis) | Monthly only |

**Output — light or full:**

If all checks clean and no blocking actions: `✓ Clean — [prewrap summary]. Garden: no — [reason]. Arsenal: no — [reason].`

Otherwise, full block:
```
─── Pre-Cytokinesis ─────────────────────────────
⚠  [only if action needed]
→  Deferred: [items or "none"]
✓  [clean checks summary]
Garden:      published → <slug>, <slug>, ... | no — [reason]
Arsenal:     added → [[Capco Transition]] | no — [reason]
Dispatched:  <audit> (<task-id>) | none
──────────────────────────────────────────────────
```

### 1. Consolidation (the point)

In parallel:

1. **`cytokinesis gather`** (CLI, full mode always) — deterministic + LLM reflection + methylation audit (JSON by default)
2. **LLM extraction** — scan session for candidates, classify by priority
3. **Source data check** — user-provided facts that fed deliverables but weren't persisted to chromatin? Write directly using the Write tool

Then: **present candidates and act** — show the full list with routing decisions, file immediately. Act-and-report, don't block on input.

**Hard gates:** The gather output includes a `gates` object with 4 mandatory checks (publish_check, corrections_filed, tonus_updated, process_audit). Each starts as PENDING. CC must complete ALL gates before cytokinesis is done. No gate may be skipped. If a gate finds nothing to do (e.g. no publishable insights), report that explicitly — "no publishable insights" is a completed gate, silence is not.

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

### 1b. Knowhow extraction (3 min max)

Scan the session for **technical discoveries** — things that were learned by debugging, experimenting, or hitting walls. These are different from corrections (behavioral) and taste (preference). They're facts about how systems work.

Examples: "asyncio.run() inside an existing event loop silently fails subprocess backends", "Cloudflare blocks urllib without User-Agent", "op run conceals values in stdout".

For each:
- Would a fresh session hit the same wall without this knowledge? → File as finding
- Is the knowledge specific to one tool or generalizable? → Generalizable findings are higher priority
- Did we spend >30 minutes on something that a one-paragraph finding would prevent? → Definitely file

Route: `finding_*.md` in memory, with the pattern, the symptom, the root cause, and the fix.

**The test:** "If a fresh CC hit the same error tomorrow, would it spend 2 hours debugging or 2 minutes reading the finding?" The delta is the value.

**Troubleshooting audit:** Did we spend disproportionate time debugging this session? If >1 hour on a single issue:
- What was the wrong assumption that led to the long path? File it.
- Were we testing at the wrong abstraction layer? (curl works but urllib doesn't = layer mismatch)
- Could a 5-line diagnostic script have found the root cause in 5 minutes? Write that script or add it to integrin.

### 1c. Skill drift check (2 min max)

For each correction or learning filed this session, ask: **does this change how a skill operates?** Skills encode behavior; memories encode context. If the learning says "don't do X" and a skill currently says "do X", the skill is stale.

Scan:
- Feedback memories filed this session — grep the skill directory for the topic
- Behavioral corrections from Terry — which skill guided the wrong behavior?
- Surprising outcomes — did a skill's instructions cause the surprise?

For each match: **edit the skill now** (add gotcha, update anti-pattern, fix instruction). Don't defer — the session context makes the edit precise. A memory without the corresponding skill update is a band-aid; the skill will guide the same mistake next time.

**The test:** "If a fresh CC follows this skill tomorrow, will it repeat the mistake?" If yes, the skill needs updating, not just the memory.

### 1c. Process audit (3 min max)

Five questions to catch meta-failures:

1. **Repeated patterns:** Did CC run the same ad-hoc command 2+ times? (restart a service, check a status, transform files) → Build an effector. The genome says "if recurs, build a tool."

2. **Misallocated work:** Did CC write >50 lines of implementation code? Was any of it mechanical enough for ribosome? The scarcity is model quality, not tokens. Ribosome should do mechanical work; CC should judge.

3. **Lazy avoidance:** Is there something broken that we worked around instead of fixing? A flaky test we excluded instead of root-causing? A lint warning we suppressed instead of resolving? The genome says "fix, don't patch."

4. **Branch discipline:** Did we work on main during exploratory changes? Did we amend+force-push repeatedly? Should we have branched, explored, and squashed?

5. **Best practices skipped:** Did we run the full test suite before pushing? Did we test locally before committing (`pre-commit run --all-files`)? Did we review our own diff before committing?

For each "yes": file a feedback memory with the specific failure and the fix. These compound — a session that catches zero process failures is the goal.

### 1c2. Directory context crystallization (2 min max)

Scan directories where this session did 3+ file reads or edits. For each, check: does a `CLAUDE.md` exist? If not, and the directory has non-obvious structure (multiple files, config, architecture worth explaining), write one.

**What to include:** what the system does, key files, infrastructure/config, decision rationale. Not obvious things derivable from `ls` or reading one file.

**Skip:** single-script directories, test directories, directories with <3 files, anything already documented by a parent CLAUDE.md.

**The test:** "If a fresh CC session `cd`'d here tomorrow, would it need an Explore agent or 5+ reads to understand this directory?" If yes, write the CLAUDE.md now — you already paid the context cost.

**Update existing CLAUDE.md files** with session findings: new conventions discovered, gotchas hit, key rules learned. If you corrected a GLM mistake pattern, add it to the relevant CLAUDE.md's "Key rules" or "Gotchas" section — that's where dispatch tasks read it. Memory marks are for CC; CLAUDE.md is for GLM.

**Enforce triple-symlink rule:** Every repo with a CLAUDE.md must also have `AGENTS.md → CLAUDE.md` and `GEMINI.md → CLAUDE.md` symlinks. Check during cytokinesis; create if missing. This ensures all 4 harnesses (CC, Codex, Gemini CLI, Goose/Droid) read the same instructions.

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
2. CC drafts the post directly (judgment work — CC writes these, not ribosome)
3. `publish new "<title>"` then write content to the file in `~/epigenome/chromatin/secretome/`
4. `publish push` — syncs to Astro, commits, deploys

Don't ask permission. Don't defer. Don't say "no publishable insights" as a default — that's the avoidance pattern. If the session produced design decisions, architecture changes, or debugging stories, there IS a post. Write it. "Infrastructure session" is not an excuse — infrastructure decisions ARE the content.

If genuinely nothing (pure ops, zero learning): state explicitly what was checked and why it's not publishable.

### 2. Housekeeping (full mode only)

1. **Uncommitted?** `cytokinesis flush` — warns about dirty repos. Commit atomically with meaningful messages; don't bulk-flush.
2. **Anatomy refresh:** `cd ~/germline && python3 -c "from metabolon.resources.anatomy import express_anatomy; open('anatomy.md','w').write(express_anatomy())"` — keeps anatomy.md current without a cron job.
3. **TODO sweep:** `cytokinesis archive`
4. **Session log:** `cytokinesis daily "title"` — outcomes + session arc prose.
5. **Tonus.md** — update deltas. Max 15 lines, dual-ledger.

### 3. Daily note (last step — the output)

1. Run `cytokinesis daily "title"` — pre-fills deterministic sections (Filed, Published, Mechanised, Residual)
2. **Edit** the daily note to fill LLM sections (Outcomes, Parked, Arc). All sections present even if empty.
3. The Edit diff IS the completion signal. If it happened, cytokinesis is done.

## CLI: `cytokinesis` (on PATH)

| Subcommand | Purpose |
|---|---|
| `gather --fast` | Deterministic pre-wrap checks: dirty repos, skill gaps, MEMORY.md line count, Tonus age (~1s) |
| `gather` | Full checks including LLM reflection + methylation audit (~60s) |
| `flush` | Warn about dirty repos (no longer auto-commits) |
| `gather --semantic` | Human-readable output (JSON is default) |
| `archive` | Move `[x]` items from Praxis.md → Praxis Archive.md |
| `daily "title"` | Append session log template to today's daily note |
| `reflect <session-id>` | Scan transcript for reflection candidates (haiku) |
| `extract --input <json>` | Review candidates, recommend FILE/SKIP/PRINCIPLE (haiku) |

Note: gather may take 10+ seconds. If Bash backgrounds it, read the output file directly rather than waiting.

## Boundaries

- No deep audits or research — consolidation, not workstream.
- Full mode: stop after writes.
- Checkpoint mode: continue after output.

## Motifs
- [audit-first](../motifs/audit-first.md)
- [verify-gate](../motifs/verify-gate.md)
