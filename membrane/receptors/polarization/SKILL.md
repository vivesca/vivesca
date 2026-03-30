---
name: polarization
description: Spawn agent teams for north-star goals overnight. "overnight", "vigilia"
user_invocable: true
epistemics: [delegate, plan]
---

# Poiesis — Agent Teams for North Stars

One pattern: **north stars → division of labour filter → shapes filter → sub-goals → agent teams → results.** Two modes: interactive (Terry at keyboard) and overnight (unattended flywheel).

**Core principle:** The system exists to free Terry's attention for what SHOULD be done by a human — not what can't be automated, but what he chooses to keep. Poiesis only dispatches Automated tasks. The task space is infinite. The stop criterion is budget, not task exhaustion.

## Pre-flight: Consumption Check

```bash
polarization-gather preflight
```

Runs all deterministic pre-flight checks (consumption count, budget, guard status, manifest, north stars, TODO `agent:claude` items, NOW.md). Use `--json` for structured parsing.

| Review queue | Signal | Action |
|---|---|---|
| **0-3** | Consumed. Produce more. | Run normally |
| **4-8** | Backlog building. | Self-sufficient outputs only (study materials, research answers). No drafts needing review. |
| **9+** | Overproduction. | Don't produce. Help Terry triage — which items are stale, agent-verifiable, or 5-minute fixes? |

**Target:** ~75% self-sufficient outputs. If most outputs need review, the prompts are wrong — make them more specific.

## Core Protocol

### Step 0: Activate Guard

```bash
polarization-gather guard on
polarization-gather manifest init
```

The guard is a flag file (`~/tmp/.polarization-guard-active`) managed by `polarization-gather`. While active, the model cannot stop while budget is green. Deactivate with `polarization-gather guard off` (done automatically in Wrap, or manually by Terry).

### Step 1: Load Context (parallel)

`~/epigenome/chromatin/North Star.md`, `~/epigenome/chromatin/euchromatin/epistemics/north-star-shapes.md`, `~/epigenome/chromatin/euchromatin/epistemics/division-of-labour.md`, `~/epigenome/chromatin/NOW.md`, `~/epigenome/chromatin/Praxis.md` (head 80), `date`.

### Step 2: Shape-to-Leverage Filter

| Shape | Agent Leverage | Action |
|---|---|---|
| **Flywheel** | High | Produce, compound, measure |
| **Checklist** | High | Research sprint, then done |
| **Decision** | Medium | Research phase only |
| **Habit** | Near-zero | **SKIP** — do the thing |
| **Attention** | Near-zero | **SKIP** — be present |

| North Star | Shape | Typical agent work |
|---|---|---|
| Career worth having | Flywheel | IP production, engagement prep, exam materials, research briefs |
| Financial resilience | Checklist | Fund verification, migration research |
| Raise Theo well | Decision + Attention | School research (decision phase only) |
| Protect health | Habit | **SKIP** |
| Strengthen marriage | Attention | **SKIP** |
| Knowledge system | Meta-flywheel | Only if it serves stars 1-5 |

### Step 2b: Division of Labour Filter

| Category | Poiesis action |
|---|---|
| **Presence** (Theo, Tara, being there) | Skip |
| **Sharpening** (drilling, forming views) | Skip — Terry does this to stay sharp |
| **Collaborative** (brainstorming, drills) | Skip — needs Terry at keyboard |
| **Automated** (research, synthesis, code, monitoring) | **Dispatch** |
| **Dropped** (doesn't serve a north star) | Drop |

### Step 3: Brainstorm Sub-Goals

For each high-leverage star, identify sub-goals that are: actionable now, Automated category, produce a concrete deliverable, completable in one agent session.

**Sources (priority order):**
1. Praxis.md items tagged `agent:claude` or where research/drafting is the bottleneck
2. What the north stars need now, even if not in Praxis.md
3. External signals (lustro outputs, calendar proximity)
4. What systole N outputs revealed as the next logical step

"Ran out of tasks" means "stopped looking." Ask: what would a good employee working on [star] do next?

### Step 4: Align & Dispatch

**Interactive:** Show mapping table, ask ONE clarifying question if ambiguity would waste an agent run. Cap at 3-5 teams.

**Overnight:** Classify TODO items into Tonight (fully autonomous) / Prep (draft for review) / Blocked (skip). Dispatch autonomously — no questions.

### Step 5: Execute Wave

Launch with `run_in_background: true`, `mode: bypassPermissions`. Every agent prompt includes: clear deliverable (file path + format), context file paths, "Read `~/tmp/polarization-session.md` first. Do not duplicate completed work."

**Model routing:** Research/collection → sonnet. Content/synthesis/judgment → opus. System audits → sonnet.

**File scoping:** Non-overlapping. One agent, one output file.

### Step 6: Flywheel (Overnight Mode)

After each systole, two phases:

**Phase A — Compound:** For each output, ask "what builds on this?" Research → synthesise → IP/publish → verify → cross-link.

**Phase B — Scout:** Ask "what new directions does this reveal?" Check lustro/transduction for external signals. Check all six north stars. If any star has zero dispatched tasks, ask why.

**Deliverables are functions, not documents.** "Give me market intel" → produce a fresh brief, not point to a stale file.

**Stop conditions (in order):**
- Budget yellow → finish current systole, then stop
- Budget red → stop immediately, report
- All remaining tasks require Presence/Sharpening/Collaborative → stop (only human work remains)
- **Task exhaustion is NOT a stop condition.**

### Step 7: Route Outputs

**Default: self-sufficient (~75%).** Study materials, research answers, meeting prep — archive to `~/epigenome/chromatin/Praxis Archive.md`, no TODO item.

**Needs review (~25%):** Only when: Terry's voice (content to publish), Terry's memory (facts only he knows), or Terry's hands (physical action). → Add to Praxis.md: `- [ ] **Review: [title].** [path]. [what to check]. \`agent:terry\``

**`agent:terry` is expensive.** Before tagging, ask: could another agent verify this? Is this really review, or studying/doing? Agents never block on Terry's review — the flywheel keeps spinning.

**Not `agent:terry`:** Study tasks, mechanical verification, physical actions, passive tracking.

### Step 8: Session Report

Write `~/epigenome/chromatin/Poiesis Reports/YYYY-MM-DD.md` with frontmatter (systoles, items\_produced, items\_for\_review) + Produced list + Review Queue + Flywheel Trace + Quality Gate Results.

**No separate notification.** Praxis.md is the one inbox.

## Mode Differences

| | Interactive | Overnight |
|---|---|---|
| **Trigger** | "polarization", "burn tokens", "stellae" | "overnight", "vigilia", "going to sleep" |
| **Mechanism** | This skill (in-session) | `lucerna` (fresh session per systole) |
| **Clarifying questions** | Yes (max 1) | Forbidden |
| **Agents per systole** | 3-5 | 8 (maintain thread pool) |
| **Systoles** | 1-2 | Flywheel until budget yellow |
| **Shared systems** | Ask first | Never touch |

## Manifest

`~/tmp/polarization-session.md` — ephemeral, one per run. Every agent prompt starts: **"Read `~/tmp/polarization-session.md`. Do not duplicate completed work. Build on listed outputs."**

## Quality Gate

Mandatory for: exam prep, client-facing research, skill files, anything published without human review. Optional for: system checks, drafts marked for editing.

Dispatch a Sonnet verification agent checking: source fidelity, internal consistency, hallucination scan, Obsidian hygiene, domain accuracy.

Verdict: PASS → proceed. PARTIAL → proceed, flag for Terry. FAIL → quarantine (`_UNVERIFIED` prefix), report.

## Overnight Specifics

**Archive loop (never skip):** As each agent completes — classify (self-sufficient or needs review) → quality gate if high-stakes → archive or add review TODO → update manifest → keep going. Always archive before removing from Praxis.md.

**Interactive session:** Maintain 6-8 running agents at all times. When count drops below 4, launch next systole immediately.

**Overnight runs use lucerna directly**, not this skill. Lucerna dispatches fresh CC sessions per systole; the manifest is memory between systoles; budget check is real code, not model judgment.

## Stopping Gate (mandatory before any stop)

**Your instinct to stop is wrong.** Pass all 6 before stopping:

```
1. Is budget yellow or red?                           → if green, KEEP GOING
2. Have all 6 north stars been checked for Automated  → if any unchecked, scout it
   tasks in the last 2 systoles?
3. Have you checked lustro/transduction for new signals?   → if not, check now
4. Have you checked the calendar for deadlines        → if not, check now
   within 14 days?
5. Did the last systole's outputs reveal ANY follow-on?  → if yes, dispatch it
6. Can you honestly say a good employee would have    → if no, think harder
   nothing to do for these north stars?
```

**Common rationalizations (not valid stop reasons):**
- "Diminishing returns" → you stopped scouting
- "Better to wait for Terry's input" → overnight means no input, keep going
- "I don't want to over-produce" → consumption check handles this
- "I should report what we have" → report AFTER budget turns yellow

## Wrap

1. Update `~/epigenome/chromatin/NOW.md`
2. `TeamDelete` if team was used
3. Delete `~/tmp/.polarization-guard-active` — deactivates the stop guard
4. Archive `~/tmp/polarization-session.md` to `~/tmp/polarization-session-YYYY-MM-DD.md`
5. List tmux panes, **ask Terry before killing any** — he has other live sessions

## Anti-Patterns

- **Meta-spiral:** Knowledge system work that doesn't serve stars 1-5
- **Habit displacement:** Building "health tracking" instead of going to the gym
- **Shape mismatch:** Treating a checklist as a flywheel
- **Ignoring Praxis.md:** Best sub-goals are often already queued there
- **Over-scoping agents:** Each agent = ONE deliverable
- **Inventing busywork:** Tasks discovered through navigation, not invented
- **Sending messages:** Draft-only. Never send WhatsApp, email, or LinkedIn
- **Pushing to shared repos:** Personal repos fine. Shared = ask first
- **Skipping archive (overnight):** Every completed task must be archived
