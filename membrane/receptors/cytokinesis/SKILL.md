---
name: cytokinesis
description: >
  Use when ending a session or wrapping up work. "wrap up", "end of session", "cytokinesis".
  Finishes outstanding work before consolidating — "wrap up" means complete then close.
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

# Cytokinesis — Session Consolidation

> The ideal cytokinesis has nothing left to do. Capture continuously using the routing table in genome — this skill is the verification pass, not the main event.

## Routing Table

**Lives in genome.md (always-loaded).** Don't duplicate here — `grep "Session Capture" ~/germline/genome.md` if you need it mid-skill. The table routes corrections, findings, state changes, and substance to the right persistence layer as they happen during the session.

**Key defaults:** FILE over skip. Mark type ordering: feedback → finding → project → reference → user (first match wins). Substance (conclusions, framings, positioning decisions) = intellectual output that must survive — test: "could Terry reference this tomorrow without re-deriving it?"

## Workflow

### 0. Finish outstanding work (mandatory)

**"Wrap up" means complete, then close — not stop and summarize.**
- Scan for open threads, half-done fixes, deferred items
- **Default: finish them now.** Context is hottest now — the next session starts cold. Quick fixes (<5 min), uncommitted changes, pending dispatches with known specs → do them.
- Park only if the work genuinely needs Terry's input or would take >15 min.
- Then consolidate what's done.

### 1. Verification pass

**Correction backstop first:** scan the session for corrections you acknowledged but didn't route to a mark file. This is your dominant failure mode — you recognize corrections ("noted", "good point", "updated") but don't file them. Find those moments and file now. If any are found, set `late_correction=true`.

Then: run `cytokinesis gather`. Scan session against the routing table for any other missed signals. Also scan for emergent patterns — cross-session insights that only crystallize at session end.

Present candidates with routing decisions. Act-and-report, don't block on input.

If a filed correction or learning invalidates a skill's instructions, edit the skill now — don't defer. Skills over marks for durable instructions.

**MEMORY.md ≥145 lines →** downregulate by recurrence signal. Lowest hits + oldest last-seen → `~/epigenome/chromatin/immunity/memory-overflow.md`.

### 1a. Substance-capture verification (six structured questions)

The routing table catches obvious signals (corrections, surprises, state changes). It misses *substance that emerged from the session's working method*. Run these six questions explicitly — each maps to a destination already in the genome architecture:

1. **Skill edits surfaced?** Did this session reveal a recurring pattern that should methylate back to a SKILL.md (new section, new anti-pattern, new sub-step)? Test: "Would a fresh session approach this worse without the change?" If yes — edit now, don't defer.

2. **Epistemics edits surfaced?** Did the session reveal a working method or rule that crosses multiple skills? Test: "Does this rule apply to induction *and* secretion *and* censor — or just one?" If multi-skill — promote to `~/epigenome/chromatin/euchromatin/epistemics/` with `situations:` tags + `skills:` bridge. If single-skill — embed in that skill's SKILL.md instead.

3. **Profile gaps surfaced?** Did any stakeholder, principal, organisation, or system reveal that we don't have enough recorded about it? Subagents (especially principal-lens, opsonization) explicitly return PROFILE GAP findings — those flow back to the relevant `chromatin/immunity/<name>-profile.md` as the next maintenance step.

4. **Profile interlinks needed?** Did a new profile reference relate to existing notes that should now cross-link? Three-direction check: profile↔profile, profile↔project notes, profile↔chromatin reference notes. Add `**Related:**` lines per chromatin convention.

5. **Rejection-rule entries to capture?** Did Terry reject a CC-proposed patch / approach / framing with a *reason* that the lens (principal-lens, multi-persona reviewer, etc.) didn't yet have? Reject reasons are the discriminator's training data — capture as imperative DO/DO NOT rules on the relevant principal profile or epistemics file. See `induction/SKILL.md` §10 for the full protocol.

6. **Trigger collisions detected?** Did two skills fire on the same trigger this session? Same-trigger-one-skill is genome-protected (`feedback_same_trigger_one_skill.md`). Candidates for merge or trigger sharpening — file as a finding for next skill-review cycle.

7. **Outbound senior comms captured as standalone notes?** `feedback_standalone_correspondence_notes.md` (PROTECTED) requires every sent email / Teams / WhatsApp / partner-comms message to land as its own file with frontmatter + interlinks — NOT just a summary line in the daily note. Inbound is usually transcribed correctly; outbound is the recurring violation point. Check this session's outbound: each sent message has a standalone `chromatin/immunity/YYYY-MM-DD-<recipient>-<subject>.md` file? If summarised-only, backfill now via anam search of session JSONL for verbatim text. The asymmetry (inbound captured, outbound summarised) is the failure mode that bit on 2026-04-27 (Terry's Friday reply to Simon committing to Mon AM BST draft was only in daily note, surfaced 3 days later when traceability was needed).

**These run AFTER §1's correction backstop and BEFORE §2's audit signal.** They catch substance that the routing table doesn't have a column for. If any return non-empty, do the routing now (skill edit, epistemics file, profile update, marks entry) before proceeding to §2.

### 2. Audit signal (proprioception)

Count findings routed in this pass:

- `filed=N` — captured now (should have been mid-session)
- `late_correction=Y/N` — if Y, this is a mid-session capture failure, not a wrap success
- `skipped=M` — reviewed and correctly skipped
- If `filed > 0`: "Continuous capture missed N items. What blocked mid-session routing?"

This trends toward zero. `filed=0` is the ideal session.

### 3. Publish check

If the session produced a non-obvious insight that took >30 minutes to reach, draft and publish now. Test: "Would I explain this to a peer over coffee?"

If yes: draft → `~/epigenome/chromatin/secretome/` → publish. "Client-adjacent" is NOT a reason to defer — generalise and ship. If no: state what was checked.

### 4. Housekeeping (full mode only)

1. **Uncommitted?** `cytokinesis flush` — commit atomically, don't bulk-flush
2. **Anatomy refresh:** `cd ~/germline && python3 -c "from metabolon.resources.anatomy import express_anatomy; open('anatomy.md','w').write(express_anatomy())"`
3. **TODO sweep:** `cytokinesis archive`

**Complete all housekeeping — every commit pushed, every skill edit saved — before step 5.**

### 4a. Anomaly parking rule (wrap-mode reflex)

If `git status`, `cytokinesis gather`, or any tooling check surfaces weird state that **does not block the commit** — file showing untracked then tracked, stale lockfile, half-applied diff that resolves itself, ghost entries — **park as a one-line note. Do NOT investigate live during wrap.**

- Anomaly blocks the wrap (won't commit, hook fails, real conflict) → resolve, since wrap can't complete otherwise.
- Anomaly is just weird-looking state that the commit succeeds despite → one-line park in daily Residual or Tonus parked list. Move on.
- Park format: `Parked: <observed weirdness> at <timestamp> — investigate next session if it recurs.`
- If the same anomaly appears across 2+ sessions → THEN investigate, file finding. First occurrence = park.

Why: wrap mode has a different cost function than working mode. Every minute spent investigating non-blocking weirdness during wrap is a minute *not* spent on the next-session priority. CC's reflex to "understand the anomaly before moving on" fights against wrap's "ship the commit and close" mode. Different mode, different reflex.

### 5. Tonus first, then daily note as the visible wrap artefact

Two writes, in this order:

**5a. Write Tonus.** `~/epigenome/chromatin/Tonus.md` is the next session's handoff (synapse injects it at session start). Facts (established) + Progress (active), open items first (`[next]`, `[waiting]`, `[parked]`).

**5b. Write the daily-note session block LAST.** Append a `## Session N — title` block to `~/epigenome/chromatin/Daily/YYYY-MM-DD.md` covering Outcomes / Filed / Published / Publishable? / Mechanised / Parked / Residual / Arc. Use `cytokinesis daily "title"` to insert a template, then Edit/Write to fill it. **The daily note is the visible terminal artefact** — Terry sees it as the diff in the UI when the wrap finishes, so writing it last preserves the session arc as the closing image. Gate enforces daily mtime > Tonus mtime; this ordering also satisfies the gate naturally without needing a separate `touch` to bump mtime.

If a daily file already has earlier session blocks captured at compact, this session gets its own appended block — never overwrite.

**HARD GATE before 5a.** Run `cytokinesis verify`. If `all_passed != true` (after housekeeping but before Tonus), stop and complete the PENDING gates — do NOT write Tonus. Recurring failure mode: CC sees PENDING in `gather`, notes it, then writes Tonus anyway. The gate is deterministic — use it.

**If you genuinely must skip a gate** (rare — e.g., `daily_note` when the session was <3 minutes of reversible chat), state the gate name and the reason explicitly in the wrap output so Terry can see what was bypassed.

**Display order in wrap output:** state skipped gates with rationale, then the daily-note Arc paragraph (or a one-line pointer to the daily note path). Tonus is the next-session handoff, not the wrap display — the daily Arc is what Terry reads as the close.

### 6. Prompt retrospective (final step)

Cytokinesis consolidates state. **Retrospective consolidates judgment about state** — what went well, what failed, Terry-pattern observations, what to do differently, session quality grade. They are two separate passes for a reason.

**If invoked via `/telophase`:** retrospective runs automatically next — skip this step.

**If invoked via bare `/cytokinesis`:** at the end of the wrap output, append exactly one line: `Run /retrospective next? (or use /telophase to run both as one cycle).` This is the gentle nudge — don't auto-run, don't pad. Let Terry decide.

**Skip the prompt only when** the session was <3 substantial exchanges (truly trivial). State that as the rationale in the skipped-gates line.

Recurring failure mode this prevents: Terry types `/cytokinesis` directly (muscle memory), state gets consolidated, judgment-about-state gets lost. The retrospective grade trend is the autopoiesis feedback signal — losing it silently is worse than a verbose wrap.

## CLI: `cytokinesis` (on PATH)

| Subcommand | Purpose |
|---|---|
| `gather` | Deterministic checks: dirty repos, skill gaps, MEMORY.md line count, Tonus age, gate status |
| `flush` | Warn about dirty repos |
| `archive` | Move `[x]` items from Praxis.md → Praxis Archive.md |
| `daily "title"` | Append session log template to today's daily note |
| `reflect --session <id>` | Scan transcript for reflection candidates |
| `extract --input <json>` | Review candidates, recommend FILE/SKIP |

## Modes

- **Full** (`/cytokinesis`) — finish work + verification + housekeeping + Tonus. Stop after Tonus.
- **Checkpoint** (`/cytokinesis checkpoint`) — verification only. Continue after output.

## Boundaries

- No deep audits or research — consolidation, not workstream.
- Process audits → `integrin`. Skill drift → `splicing`.

## Motifs
- [audit-first](../motifs/audit-first.md)
- [verify-gate](../motifs/verify-gate.md)
