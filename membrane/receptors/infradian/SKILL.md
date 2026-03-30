---
name: infradian
description: Weekly review — reflect on the week, plan the next one. Saturday rhythm.
user_invocable: true
triggers:
  - infradian
  - weekly review
  - how was the week
  - plan the week
epistemics: [review, plan]
model: sonnet
---

# Infradian — weekly rhythm

Two halves: reflect (what happened), then plan (what matters next). Keep it under 15 minutes.

Design input: [[weekly-review-frameworks]] — Newport (calendar-based planning, week's character), GTD (list hygiene), Forte (intention-setting). We took Newport's structure, replaced his lists with tonus/prospective, and cut scope to 15 minutes.

## Phase 1: Reflect

### Steps

1. **Sleep trend** — call `circadian_sleep` with period `week`. Flag any night below 65 or readiness below 60. Note the week's average and direction (improving/declining/flat).
2. **Tonus review** — call `tonus_status`. For each item:
   - `done` → acknowledge, consider if it should be removed from tonus
   - `in-progress` → how long has it been in-progress? Flag anything stale (>2 weeks with no visible movement)
   - `todo` → still relevant? If not, remove
3. **What shipped** — the done items are the week's output. State them plainly.
4. **What surprised** — anything unexpected that emerged this week? A broken tool, a new opportunity, a pattern in the data. This is the most valuable part — don't skip it.
5. **Active experiments** — check `assay list` if any experiments are running. Report day count and any observations.

### Output format

Short narrative, not a table. Two paragraphs max. Lead with the headline ("productive infra week" or "recovery week" or "scattered"). Then the specifics.

---

## Phase 2: Plan

### Steps

1. **Calendar lookahead** — call `circadian_list` for next 7 days. Surface fixed commitments.
2. **Prospective check** — read `~/epigenome/marks/prospective.md`. Flag any items whose trigger has arrived or is imminent. Flag any expired items for cleanup.
3. **Big rocks** — given tonus in-progress items + calendar constraints, what are the 1-3 things that matter most next week? Name them.
4. **Week's character** — one sentence describing what kind of week this should be. ("Closing out CNCBI, protect Wednesday for farewell." or "First Capco week — absorb, don't produce.")
5. **Propose tonus updates** — suggest additions, removals, or status changes. Don't apply without confirmation.

### Output format

Calendar summary as a short list. Then big rocks. Then the character sentence. Keep it tight.

---

## Phase 3: Maintain (optional, if time)

1. **Prospective cleanup** — delete actioned or expired items from prospective.md
2. **Tonus cleanup** — remove done items that have been acknowledged
3. **Memory check** — any corrections or findings from this week that should be saved?

Only run Phase 3 if the user has energy for it. Don't force it.

---

## Do NOT

- Turn this into a 2-hour GTD ceremony — 15 minutes is the target
- Skip the "what surprised" step — it's where the real signal lives
- Auto-update tonus without confirmation
- Run methylation or expression from here — they're independent skills with their own cadence
- Add items to prospective.md without the user's input
