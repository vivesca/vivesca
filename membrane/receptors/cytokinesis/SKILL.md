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
4. **Session log:** `cytokinesis daily "title"` — then edit to fill Outcomes, Parked, Arc

**Complete all housekeeping — every commit pushed, every skill edit saved — before step 5.**

### 5. Tonus = wrap summary (last step)

**Tonus IS the summary.** Write `~/epigenome/chromatin/Tonus.md` first, then display it as the wrap output. Single source — no separate summary that could diverge from what the next session reads.

Tonus format: Facts (established) + Progress (active). Progress leads with open items (`[next]`, `[waiting]`, `[parked]`), then completed (`[done]`). Synapse injects this at session start — what you write here is the handoff.

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
