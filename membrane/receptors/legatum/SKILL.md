---
name: legatum
description: State-transfer for impending session death — bequeath context before /clear, or auto-fire at gear shifts (checkpoint mode). NOT for graceful session-end (use telophase) or day-level close (eow/daily).
user_invocable: true
---

# Legatum — Session State Transfer

A dying session bequeaths its knowledge forward. Two modes:

> **Core framing:** This is state transfer, not documentation. The session holds volatile state — decisions, understanding, corrections — that dies with `/clear`. The legatum's job is to move what matters to durable storage. Everything else is theatre.

- **Full** (`/legatum` or `/wrap`) — end-of-session close. All steps.
- **Checkpoint** (`/legatum checkpoint` or `/wrap checkpoint`, auto-triggered at gear shifts) — capture learnings + sweep TODOs, skip session-end bookkeeping. Preserves context — no /compact, no closure framing.

Session scope = files modified + tool calls + conversation turns since this session began (or since last checkpoint).

## Triggers

- "wrap", "wrap up", "let's wrap", "legatum" → full mode
- "checkpoint", "wrap checkpoint" → checkpoint mode
- **Auto-trigger (Claude-initiated):** When detecting a significant gear shift (different project, different domain, switching from building to admin, etc.), run checkpoint mode silently before proceeding. Don't ask — just capture.
- "what did we learn" → checkpoint mode

## Mode Detection

If invoked as checkpoint or auto-triggered at a gear shift → **checkpoint mode**.
If invoked at session end → **full mode**.

**Checkpoint mode runs:** Step 0 (pre-wrap), Step 0.5 (friction review, but don't truncate log), Step 1 (TODO sweep), Step 4 (learning capture).
**Checkpoint mode skips:** Step 2 (session log), Step 3 (NOW.md rewrite — delta update only if needed).

## Workflow

### Skip gate

```bash
now-age
```
If NOW.md is **<15 minutes old** AND user did not explicitly invoke `/legatum`, skip to Step 4 briefly, then Output. Explicit invocation always runs all steps.

### Step 0: Pre-Wrap Check

Run `prewrap` and answer these five questions. Complete blocking actions (garden post, arsenal) *before* outputting the block — the block is a receipt, not a plan.

```bash
prewrap
peira status 2>/dev/null || true
```

**Questions (explicit yes/no for Q4–5, silence is not "no"):**
1. **Unverified?** Any tool output this session that wasn't checked?
2. **Deferred?** Anything mentioned as "later/next/TODO" not yet captured? Route by type: has a deadline → TODO.md. Has a context trigger ("next time I'm in X") → `memory/priming.md`. Neither → daily note.
3. **Uncommitted?** Dirty repos *touched this session*? → offer to commit (leave other repos alone)
4. **Garden posts + consulting arsenal?** Pause and replay the session arc (or arc since last checkpoint). What did we *learn*, not just *do*? What surprised us? What principle emerged that wasn't obvious at the start? Give yourself 30 seconds of generative thinking before answering — the best posts come from connections between topics, not from any single task.
   - **Garden test:** Non-obvious insight, clear thesis, Terry's lane, no unverified facts? Publish immediately via `publish new` → write → `publish publish --push`. Multiple posts per session is normal for meaty sessions.
   - **Arsenal test:** Concretely applicable to a bank/client AI engagement? If yes → add bullet to `[[Capco Transition]]` now.

**CLAUDE.md modified?** One-line tightening check: does it belong in CLAUDE.md or in a skill / MEMORY.md / `~/docs/solutions/`?

**Background dispatches** — fire with `run_in_background: true` when the session touched the relevant area:

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
─── Pre-Legatum ─────────────────────────────────
⚠  [only if action needed]
→  Deferred: [items or "none"]
✓  [clean checks summary]
Garden:      published → <slug>, <slug>, ... | no — [reason]
Arsenal:     added → [[Capco Transition]] | no — [reason]
Dispatched:  <audit> (<task-id>) | none
──────────────────────────────────────────────────
```

Then proceed to remaining steps.

### Step 0.5: CLI Friction Review

```bash
cat ~/.claude/cli-friction.jsonl 2>/dev/null | wc -l
```

If `~/.claude/cli-friction.jsonl` has entries: read the file, group errors by CLI tool, and for each tool with 2+ friction events (or 1 event with an obvious fix), suggest a concrete improvement (alias, positional arg, better error message). Output as a fenced block. If any fix is trivial (< 20 lines), implement it or add to TODO.md with `agent:claude`. **Full mode:** truncate the file after processing (`> ~/.claude/cli-friction.jsonl`). **Checkpoint mode:** leave the file intact (accumulate across checkpoints, truncate only at session end).

### Step 1: TODO Sweep

Read `~/epigenome/TODO.md`. Skip if missing.

- **Complete:** Done items → `[x]` with note and `done:YYYY-MM-DD`. Hard test: truly done, or just "dev done"? Move checked items to `~/epigenome/TODO Archive.md`.
- **Create:** New commitments or interrupted WIP → add with verb + concrete next action. Tag `agent:` if Claude can resume.

### Step 2: Session Log (full mode only)

Append to `~/epigenome/chromatin/Daily/YYYY-MM-DD.md`:

```markdown
### HH:MM–HH:MM — [Brief title]
- Key outcome or decision (1-3 bullets)
- Abandoned: X because Y  ← if a path was explored and dropped
```

### Step 3: NOW.md + Trackers (full mode only)

```bash
now-age
```

**NOW.md** — read from disk first. If recent (<1h), update only deltas. If light session (<3 files, no decisions) and still accurate, skip.

Max 15 lines. Resume points must pass cold-start test. Use `[decided]` vs `[open]`. Prune `[decided]` items that no longer gate future action.

**Vault flush:** Update canonical tracker notes (e.g. `[[Capco Transition]]`) if the session advanced them.

**Project CONTEXT.md** — if cwd is `~/code/<project>/` and meaningful progress was made, update State/Last session/Next/Open questions sections. Commit after writing.

### Step 4: Learning Capture (always runs)

Single pass. If nothing surfaces: "Nothing to generalise."

**Scope:** Since last checkpoint (if any), otherwise since session start.

**Failure mode check** (scan before writing):

| Smell | Fix |
|-------|-----|
| "Updated X" with no what/why | State what changed and why — cold reader test |
| "TODO: consider whether..." | Decide now or delete. Legatum is not a parking lot |
| >3 "filed to X" items | Over-capturing. Prioritise |
| Recording what happened, not what was learned | Logs → daily note. Insights → skill/memory/garden |
| Legatum takes >10 minutes | You're writing, not closing. Stop |
| "Fixed the bug" without generalising | Capture the pattern, not the instance |

**Belief corrections?** Did a prior get challenged this session — something Terry (or I) assumed that turned out wrong? Not just career — technical assumptions, how things work, self-knowledge, anything. If yes → append to `[[Priors Worth Correcting]]` with: old belief, the correction, and when the old belief would reassert.

**Scan → Route → Implement:**
- Scan for non-obvious patterns, friction, corrections, gotchas, and new user preferences or personal context
- Route each finding to the most specific destination:
  - Tool gotcha → `~/docs/solutions/`
  - Cross-session context → MEMORY.md
  - Workflow change → the relevant skill's SKILL.md
  - Same mistake twice → escalate per `~/docs/solutions/enforcement-ladder.md`
- **Default: implement now.** Skill edits, MEMORY.md additions, solutions files, small hooks — do them, don't propose them. "Needs design input" is not a valid reason to defer a 20-line improvement. Propose only if: touches shared infrastructure, irreversible, or genuinely ambiguous (and state which). If you wrote "propose" in the output, ask: could I have just done it? If yes, go back and do it.
- **Persistence gate:** Consult `custodia` before routing. One home per insight, never point to a pointer, count layers.

**MEMORY.md ≥145 lines + entries added this session →** demote lowest-recurrence entry to `~/docs/solutions/memory-overflow.md` now. Don't ask — pick it yourself.

**Decay tracker:** If any MEMORY.md entries prevented mistakes this session, update `memory/decay-tracker.md` with today's date. This is the empirical signal for what to keep vs demote.

**Legatum audit: log, don't essay.** Instead of launching verbose audit agents, do a quick self-scan and append one-liners to `~/docs/solutions/operational/wrap-violations.jsonl`. Pattern detection happens in `/weekly`, not per-session.

**Self-scan checklist (30 seconds, no agents):**
1. Did any CLAUDE.md rule get violated AND cause a worse outcome? (Not "technically violated but fine")
2. Did anything compound (insight, tool, framework) that wasn't captured?
3. Were garden posts published? If 3+, flag for quality cull.
4. **Ad-hoc script spiral?** Were 5+ consecutive tool calls spent working around a broken CLI/tool (different keychain lookups, manual API calls, alternative scripts for the same goal)? If yes → file the root-cause fix as a priming entry or TODO, and log to `wrap-violations.jsonl` with `"rule": "ad-hoc-spiral"`.

**If a violation caused harm:** append to `wrap-violations.jsonl`:
```json
{"date": "YYYY-MM-DD", "rule": "rule name", "harm": "what went wrong", "hookable": true/false}
```

**If something compounded but wasn't captured:** just capture it now (skill, garden, arsenal, vault). Don't log it — act on it.

**Garden cull:** If 3+ posts published this session, launch one haiku agent: "Review these posts. Flag weak ones (no thesis, generic, restating others) for removal or merge." Present in output.

**Garden quality cull (weekly only):** If this is a `/weekly` session, also scan *all* posts from the week — not just this session's.

**`/weekly` pattern detection:** Read `wrap-violations.jsonl`, group by rule. Any rule with 3+ violations → escalate per enforcement ladder. Any rule with 0 violations over 4 weeks → candidate for removal (dead rule).

**All file writes must complete before the output.**

## Output

**Full mode:** Bordered prose. Handoff note to tomorrow-you — arc, what's staged/unfinished, learnings captured. 2-3 sentences for light sessions, up to 6 for heavy. Don't hard-wrap.

```
─── Legatum ────────────────────────────────────

[Prose summary]

Filed: [exact file path or "nothing to generalise"]
Session: [honest 1-line judgment — real output vs theatre, what moved vs what just felt productive]
─────────────────────────────────────────────────
```

**Checkpoint mode:** Lighter border. What was captured, then move on. No handoff framing.

```
─── Checkpoint ─────────────────────────────────
[1-2 sentences: what was captured/filed]
─────────────────────────────────────────────────
```

## Boundaries

- Do NOT perform external sends (messages, emails, posts) during legatum.
- Do NOT run deep audits or long research — legatum is a close-out, not a new workstream.
- **Full mode:** Stop after writes + summary unless explicitly asked to continue.
- **Checkpoint mode:** Continue with the next task after output. No stopping.
