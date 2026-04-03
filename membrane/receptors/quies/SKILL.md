---
name: quies
description: Evening wind-down ritual — brain dump, overnight queue, screens-off gate. NOT for work closure (use eow) or daily reflection (use daily).
user_invocable: true
triggers:
  - quies
  - wind down
  - bedtime
  - brain dump
  - screens off
  - sleep
---

# quies — Evening Wind-Down

Personal close-of-day ritual for sleep hygiene. Distinct from `/eow` (work closure) — this closes the *day*, not the workday.

## Context

- Theo bedtime routine runs ~9:30–10pm
- Dinner ~7:30pm at Tara's parents' (social, noisy)
- Brain dump ideally on the bus home (~6:15pm Due reminder)
- 10pm Due reminder: "Shutdown — screens off, wind down"
- Mind-racing is the primary sleep disruptor — externalising thoughts is the fix

## Steps

### 1. Tomorrow's calendar (10 seconds)

```bash
fasti list tomorrow
```

Read the output aloud in one line: *"Tomorrow: [events]"* or *"Nothing on the calendar tomorrow."*

This is orientation only — no action, no planning. Just close the loop so your brain isn't guessing.

**Fail clause:** If `fasti` errors, skip silently.

### 2. Scan open items (30 seconds)

Read `~/notes/NOW.md` — look for anything unresolved that might race tonight.

- If anything is genuinely urgent for tomorrow → note it explicitly below
- If it can wait → name it out loud and let it go

**Fail clause:** If NOW.md is stale (>24h) or missing, skip and go to Step 2.

### 3. Brain dump

Ask Terry: *"What's on your mind right now? Anything you're worried about forgetting or not solving?"*

- Capture free-text response
- Save to today's daily note under `## Evening brain dump`
- Explicitly confirm: "Logged. Your brain can let this go now."

**Fail clause:** If Terry says "nothing" — take it at face value, move on. Don't probe.

### 4. Overnight agent queue

Review the brain dump + NOW.md items. For anything that:
- Requires research or analysis (not a quick action)
- Terry would otherwise lie awake problem-solving

→ Propose as an overnight agent task. Be specific: *"Want me to queue an agent to research X tonight?"*

Offer 1–3 concrete tasks max. Don't over-queue — more tasks = more to review tomorrow.

**Fail clause:** If nothing qualifies, skip this step. Don't manufacture tasks.

### 5. Screens-off gate

Ask: *"Anything blocking you from putting the phone down?"*

- If yes → resolve it now (quick action) or defer explicitly to tomorrow
- If no → confirm shutdown: "Good. Screens off. Sleep when you feel it, not before."

Remind if relevant: lying awake >20min → get up, dim light, no screens, back when sleepy.

### 6. Optional — nyx tomorrow

Only if Terry had a notable night (poor sleep flagged, travel, alcohol, late night):

```bash
nyx
```

Offer to check tomorrow morning. Don't run now — data isn't in yet.

## Boundaries

- Do NOT review TODO.md or task lists — that's `/eow` territory
- Do NOT surface new work items — wind-down direction only
- Do NOT run `nyx` during quies — data for tonight isn't captured yet
- Stop after Step 5 (or 6 if relevant). Do not loop back.

## Calls
- `due` — if adding a reminder during the ritual
- `oura` / `nyx` — tomorrow morning follow-up only
