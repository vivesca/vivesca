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

> The ideal cytokinesis has nothing left to do. Capture continuously using the routing table in genome — this skill is the verification pass, not the main event.

## Routing Table

This table lives in genome.md (always-loaded) so CC can act on signals mid-session. The copy here is reference.

| Signal | Route to | Gate |
|---|---|---|
| Correction from Terry | Memory (feedback, protected if architectural) | Always file |
| Surprise / unexpected behavior | Memory (finding) | Always file |
| Technical discovery (debugging, workarounds) | Memory (finding) | Would a fresh session hit the same wall? |
| Resolution ("that worked") | Memory (finding) if non-trivial | Would a fresh session benefit? |
| Repeated manual step (2+) | Hook candidate (methylation) | Always file |
| Workflow improvement idea | Skill edit (now, not deferred) | Always file |
| Taste / preference confirmed | Memory (feedback) | Non-obvious preference? File it |
| State change | Tonus.md | Always update |
| Commitment / action | Praxis.md (with context) | Always file |

**Default: FILE.** Over-filter is the LLM failure mode. Priority: prediction errors > novelty > emotional weight > pattern completion > routine.

**Mark type ordering (first match wins):**
1. Terry corrected CC? → `feedback`
2. Discovered how a system works? → `finding`
3. Learned about an initiative/deadline/team? → `project`
4. Found a pointer to external info? → `reference`
5. Learned about the user? → `user`

## Workflow

### 0. Unfinished work gate (mandatory)

**Do not consolidate over live work.** Before any memory capture:
- Scan for open threads, half-done fixes, deferred items
- If unfinished work exists: **finish it or park it with context.** Context is hottest now. Consolidation is for what's done.

### 1. Verification pass

**Correction backstop first:** scan the session for corrections you acknowledged but didn't route to a mark file. This is your dominant failure mode — you recognize corrections ("noted", "good point", "updated") but don't file them. Find those moments and file now. If any are found, set `late_correction=true`.

Then: run `cytokinesis gather --fast`. Scan session against the routing table for any other missed signals. Also scan for emergent patterns — cross-session insights that only crystallize at session end (these are legitimately wrap-only catches, not mid-session failures).

Present candidates with routing decisions. Act-and-report, don't block on input.

If a filed correction or learning invalidates a skill's instructions, edit the skill now — don't defer.

**MEMORY.md ≥145 lines →** downregulate by recurrence signal. Check `hits:` and `last-seen:` in mark frontmatter. Lowest hits + oldest last-seen → `~/epigenome/chromatin/immunity/memory-overflow.md`.

### 2. Audit signal (proprioception)

Count findings routed in this pass:

- `filed=N` — captured now (should have been mid-session)
- `late_correction=Y/N` — if Y, this is a mid-session capture failure, not a wrap success
- `skipped=M` — reviewed and correctly skipped
- If `filed > 0`: "Continuous capture missed N items. What blocked mid-session routing?"

This trends toward zero. `filed=0` is the ideal session.

**Sunset test:** when `late_correction=true` stays below 15% of sessions for 14 consecutive days, delete the correction backstop from Step 1 and rely on ambient routing.

### 3. Publish check

If the session produced a non-obvious insight that took >30 minutes to reach, draft and publish now. The insight is hottest in the session that produced it.

Test: "Would I explain this to a peer over coffee?"

If yes: CC drafts directly → `publish new "<title>"` → write to `~/epigenome/chromatin/secretome/` → `publish push`.

If no: state what was checked. Most infrastructure sessions genuinely don't yield posts — that's fine.

### 4. Housekeeping (full mode only)

1. **Uncommitted?** `cytokinesis flush` — commit atomically, don't bulk-flush
2. **Anatomy refresh:** `cd ~/germline && python3 -c "from metabolon.resources.anatomy import express_anatomy; open('anatomy.md','w').write(express_anatomy())"`
3. **TODO sweep:** `cytokinesis archive`
4. **Session log:** `cytokinesis daily "title"` — then edit to fill Outcomes, Parked, Arc
5. **Tonus.md** — update deltas (max 15 lines, dual-ledger)

The daily note edit IS the completion signal.

## CLI: `cytokinesis` (on PATH)

| Subcommand | Purpose |
|---|---|
| `gather --fast` | Deterministic checks: dirty repos, skill gaps, MEMORY.md line count, Tonus age (~1s) |
| `gather` | Full checks including LLM reflection + methylation audit (~60s) |
| `flush` | Warn about dirty repos |
| `archive` | Move `[x]` items from Praxis.md → Praxis Archive.md |
| `daily "title"` | Append session log template to today's daily note |

## Modes

- **Full** (`/cytokinesis`) — verification + housekeeping + daily note. Stop after writes.
- **Checkpoint** (`/cytokinesis checkpoint`) — verification only. Continue after output.

## Boundaries

- No deep audits or research — consolidation, not workstream.
- Process audits → `integrin`. Skill drift scans → `splicing`. Directory crystallization → do inline when you notice it.
- Stale marks >50? Pick 3 with most stale path references, update or delete.

## Motifs
- [audit-first](../motifs/audit-first.md)
- [verify-gate](../motifs/verify-gate.md)
