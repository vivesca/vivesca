---
name: scrinium
description: Route captured knowledge to the right storage layer — MEMORY.md, CLAUDE.md, docs/solutions/, vault, or skill. Consult before writing any persistent note or memory.
user_invocable: false
epistemics: [knowledge-capture, delegate]
---

# Scrinium — Knowledge Routing

When capturing a lesson, correction, or discovery, route it here first.

## Decision Table

| What is it? | Where |
|-------------|-------|
| Hard rule / prohibition ("never do X") | `genome.md` (or `CLAUDE.md` if multi-client) |
| Recurring gotcha / tool quirk (one-liner) | `MEMORY.md` only if fires weekly+; otherwise mark file (grep-on-demand) |
| **Exception to a skill's normal behavior** | **The skill itself** (Gotchas section) — store only the deviation, not the whole pattern |
| How-to / workflow with steps | `~/docs/solutions/` |
| Changes *how to act* next time | Skill (update or create) |
| Temporary "next time X, do Y" | `memory/priming.md` (expires when actioned) |
| Insight / opinion / analysis / op-ed | Garden post (`publish new`, `draft: false`) — low bar, publish by default |
| Reference data (facts, trackers, account details) | Vault note (the "other" bucket) |
| One-off correction, not generalizable | Daily note only |

## Overlap Check Before Creating

Before creating a new mark, solution doc, or chromatin note, score against existing ones on five dimensions: problem statement, root cause, solution approach, referenced files, prevention rules.

- **4-5 match** → update existing doc in place, don't create a duplicate
- **2-3 match** → create new, note the overlap
- **0-1 match** → create new

Two docs describing the same problem will inevitably drift apart. Update > duplicate.

## Worth Noting At All?

Before routing, ask: is this **important, easy to forget, and hard to rediscover?** All three must be true. Don't note the obvious (how to breathe), the ephemeral (today's mood), or the easily re-derived (what a function does — read the code). Note the things your future self will need and won't think to look for.

**Save conclusions that required reasoning, not just rules.** If the answer took a multi-step reasoning chain to reach and a fresh session wouldn't reliably reproduce it, save the conclusion. Example: "when on antibiotics → ginseng chicken soup + kimchi" isn't obvious — it took reasoning through medication interactions, nutrition, and stomach buffering to get past the naive answer (congee). Without the saved conclusion, future sessions will re-derive badly.

## The One-Sentence Test

Can the lesson be stated in one sentence? → `MEMORY.md` bullet.
Does it have a trigger + multiple steps or variants? → Skill.
Is it rationale or research? → `~/docs/solutions/` or vault.
Does it change a standing rule? → `CLAUDE.md`.

## Skill vs MEMORY.md

**Skill** when the lesson changes *how to act* — it fires automatically next time via the trigger.
**MEMORY.md** when it's a fact or gotcha that informs judgment but doesn't prescribe steps.

If in doubt: skill holds the rule, docs holds the *why*. Non-exclusive.

**Gate before writing to MEMORY.md:** Ask — "does an existing skill own this behaviour?" If yes, update the skill instead. MEMORY.md is the last resort, not the default capture target. Writing to MEMORY.md without checking skills first is a miss.

## CLAUDE.md Rules

- Rules only — no time-sensitive facts (dates, status, amounts).
- Facts age fast; rules age slowly. Any fact → replace with a vault pointer.
- Hard rules go here; soft guidance goes in a skill where it can evolve.

## MEMORY.md Budget

- ~80 lines target (content beyond line 200 silently dropped).
- One-liners only. If it needs more than one line, it belongs in a mark file or `~/docs/solutions/`.
- **Gate:** only add to MEMORY.md if the gotcha fires weekly+. Everything else lives in marks/ (surfaced by grep-on-demand per genome rule).
- After writing: ask "is this hook-able?" — mechanical rules should be enforced, not just documented.
- Stale marks → `~/epigenome/marks/archive/`. Decay tracked in `decay-tracker.md`, reviewed by `/weekly`.

## docs/solutions/ Conventions

- Use typed IDs: `ERR-YYYYMMDD-NNN` (tool failure), `LRN-YYYYMMDD-NNN` (correction), `REQ-YYYYMMDD-NNN` (feature).
- Dedup before writing: `ls ~/docs/solutions/ | grep -i <topic>` first.
- Operational how-tos → `~/docs/solutions/operational/`.
- Save research *before* acting on it — findings first, then action.

## Principles (accumulate here over time)

- **Garden posts are the most valuable layer.** They're Terry's published thinking — searchable, shareable, compounding. Low bar to publish. When in doubt between vault note and garden post, choose garden post.
- **Skill > docs for behavioural lessons.** If it changes how to act → skill. If it's context → docs. **If a relevant skill already exists, update it directly — don't create an intermediate feedback memory that restates a skill rule.**
- **One-off corrections stay in the daily note.** Don't inflate MEMORY.md with single incidents.
- **MEMORY.md ≠ notebook.** Reference data (passwords, specs, account numbers) → vault.
- **Blink Shell config questions → search online first.** Its shell is non-standard; aliases don't work. Full setup: `~/docs/solutions/blink-shell-setup.md`.
