---
name: circadian
description: Daily rhythm — morning brief, what's next, evening wrap, overnight results. Time-routed.
user_invocable: true
triggers:
  - circadian
  - entrainment
  - ultradian
  - interphase
  - germination
  - what now
  - what's next
  - what should I do
  - morning brief
  - evening routine
  - what ran overnight
context: fork
epistemics: [plan, monitor]
model: sonnet
---

# Circadian — daily rhythm engine

One skill, four phases. Run `date` first, then route by time. All old trigger words still work.

## Router

| Time (HKT) | Phase | Old skill | Entry point |
|---|---|---|---|
| 06:00–10:00 | **Dawn** | entrainment + germination | `entrainment_brief` + `germination_brief` |
| 10:00–17:00 | **Day** | ultradian | `ultradian-gather` |
| 17:00–21:00 | **Dusk** | interphase | `gather_interphase` |
| On-demand | **Day** | ultradian | `ultradian-gather` (regardless of time) |

If the user explicitly says "morning brief" after 10am or "evening routine" before 5pm, honour the explicit request over the time router.

---

## Phase: Dawn (entrainment + germination)

**Rule: read biometric state before advising on the day's load.**

### Steps

1. **Call `entrainment_brief`** — aggregates sleep + overnight alerts in one call. Do not call sopor separately.
2. **Call `germination_brief`** — automation results, NEEDS_ATTENTION flags. Both always run; they sense different systems.
3. **Readiness < 65** → flag explicitly before discussing workload. Cross-ref `memory/user_health_exercise_readiness.md` (< 70 = light only, resume > 75).
4. **Active experiments** → `assay list` — surface experiment day and status.
5. **Right-sided morning headache** → check `memory/user_health_sleep_headache_pattern.md`.
6. **Overnight alerts** → any NEEDS_ATTENTION or CRITICAL lines surface immediately.
7. **"No overnight data"** → note automation may not have run.

### Anti-patterns
- Don't skip germination just because entrainment ran — they sense different systems
- Don't proceed with heavy planning at low readiness — recommend lighter day first
- Don't assume "no flag" means everything passed — call germination_brief to confirm

---

## Phase: Day (ultradian / kairos)

**Design principle:** single entry point for "what now?" Every automated system feeds into this — Terry never needs to remember what's running.

### Steps

1. **Run `ultradian-gather`** (or `ultradian-gather --json`)
2. **Time + Calendar + Reminders** — flag anything within 60min (imminent) or 2-4h (good to know)
3. **Active decisions and gates** — from NOW.md, pull open decisions
4. **LinkedIn job alerts** (post-noon only) — if unchecked flags exist, surface briefly
5. **Overdue and today's TODO** — from Praxis.md, max 5 items, most time-sensitive first
6. **Goose task queue** — surface count of done/ tasks needing review. If any exist, prompt CC to read `done/*.md`, check the `## Result` section, and approve or redispatch.

### Time-aware synthesis

| Context | Route |
|---|---|
| **Commute / transit** | Surface today's efferens (daily AI brief). Read and present key items. |
| **Pre-meeting (< 45 min)** | Lead with upcoming event + prep items. Brief. |
| **Post-meeting (< 30 min ago)** | Flag follow-up capture. |
| **Free block (2+ hours)** | Top 1-2 priorities. Prefer compounding outputs. Energy diagnostic: depletion → mechanical task; resistance → name what's avoided. |
| **Late afternoon (> 5pm)** | Flag EOD proximity. |
| **Nothing to surface** | Say so plainly. Offer inbox check or low-energy tasks. |

### Output format
One short paragraph. No headers, no bullets unless 3+ overdue items. Lead with time, close with clearest next action.

### Boundaries
- Do NOT scan engram/session history — Day phase is forward-looking
- Do NOT mutate files — read-only situational routing
- If entrainment ran recently (same session), skip repeat items, surface only what changed

---

## Phase: Dusk (interphase)

**Boundary:** Dusk = work closure on commute. If Terry is at home winding down, this phase ends. Phone-friendly (Blink/tmux). Target: one bus ride.

### Steps

0. **Gather** — call `gather_interphase` (inbox, WhatsApp, calendar, Praxis, budget, reminders, email threads, prospective memory)
1. **Inbox triage** — `sorting_thread` on every unread + Cora-archived Important Info/Context emails. Read Cora briefs. Decide: action_required / monitor / archive. Update Email Threads Tracker.
2. **Messages** — WhatsApp via `keryx read`, LinkedIn. Draft only, never send.
3. **Brain dump** — ask: "Anything still rattling around?" Capture to daily note.
4. **What shipped today** — read daily note cytokinesis logs. Write 2-3 line summary. If consulting-relevant, append spark to `_sparks.md`.
5. **Tomorrow prep** — calendar, checkpoint, Praxis, Schedule.md in parallel. One-line prep per meeting. Thursday: check token reset.
6. **Nudge** — blocked items needing follow-up. One-line per item.
7. **Daily note close** — call `interphase_close_daily_note` with shipped, tomorrow, open_threads, nudges, day_score (1-5). This is the canonical tool; do not write the daily note manually.
8. **Flush prospective** — check `WHEN: next session` triggers.
9. **Praxis sync** — update resolved, add new, mark blocked.

Then: **"You're done. Evening is yours."**

### Fail states
- `cora brief show` crashes → `porta run --domain cora.computer` fallback
- `gog gmail` fails → note "inbox skipped", continue
- Any step fails → skip it, never block the whole routine

### Boundaries
- Draft only — never send (WhatsApp, email, LinkedIn)
- No deep reflection or extended conversation
- Only update: daily note, Email Threads Tracker, Praxis

---

## Phase: Germination (overnight results detail)

Used by Dawn phase and also available standalone when diagnosing overnight automation.

1. **`germination_brief`** — dashboard, latest run summary, NEEDS_ATTENTION status
2. **`germination_results <task>`** — drill into one task's output (only on failure or user request)
3. **`germination_list`** — history across runs (only when diagnosing recurring failures)

### Anti-patterns
- Don't drill all tasks by default — brief first, drill only on failures
- Don't report raw output verbatim — extract NEEDS_ATTENTION lines, bury the noise
