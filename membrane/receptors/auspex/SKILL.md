---
name: auspex
description: Wake-up brief — weather, calendar, key deadlines today. Run when you wake up. Invoke with /auspex.
user_invocable: true
triggers:
  - auspex
  - wake-up
  - morning brief
---

# Wake-Up Brief

A 60-second brief for the moment you wake up. Weather, what's on today, anything due today. That's it — work priorities belong to `/statio` when you sit down.

## Triggers

- `/auspex` (user-invocable only)

## Steps

1. **Get today's date and day of week**

2. **Weather**:
   - Run: `caelum`
   - Always include in the brief
   - **Send to Tara**: send the raw caelum output directly — no prose, no greeting, no personality. Just the factual weather line(s) as-is.
     - On macOS: `~/scripts/imessage.sh "$(caelum)"`
     - On soma/Linux: SSH relay — `ssh mac '~/scripts/imessage.sh "WEATHER_TEXT"'` (requires mac online on Tailscale; check `tailscale ping mac -c 1 --timeout 3s` first)
   - If send fails or mac offline, note briefly — don't retry.
   - If `caelum` fails, note "Weather unavailable" and continue.

3. **Today's calendar**:
   - Use MCP tool: `mcp__vivesca__circadian action=list date=today`
   - List events with times. Flag anything before 10am that requires prep.

4. **Key deadlines today** — a quick scan of TODO.md:
   - Grep `~/epigenome/TODO.md` for items tagged `when: <today's date>` or `due: <today>`
   - Surface only hard deadlines — things with a specific date on them today
   - Skip someday/low-energy/undated items entirely — those are statio's job
   - If nothing due today, skip silently

5. **Overnight results** (if recent run):
   - Find latest morning-dashboard output: `LATEST=$(ls -dt ~/.cache/legatus-runs/2[0-9]*/ 2>/dev/null | head -1) && cat "$LATEST/morning-dashboard/stdout.txt" 2>/dev/null`
   - If found and the run dir is from last night (within 12h): surface as one line (e.g. "Overnight: vault HEALTHY, 2 git issues — /overnight for details")
   - If nothing found: skip silently — don't mention the queue

6. **Landscape teaser** (don't read the full brief — that's for commute):
   - Use MCP tool: `mcp__vivesca__endocytosis action=top limit=10 days=1`
   - Count items by score tier: high (8+), medium (6-7), total
   - Surface as one line: "Landscape: 2 high-signal, 3 medium from last 24h — review on commute"
   - If no items in last 24h, try `days=3` for a wider window and note the staleness
   - Do NOT list or summarise individual items — just the count. Morning is Theo time, not reading time.
   - If endocytosis returns nothing: skip silently

7. **Missed email scan** (known Cora blind spot):
   - Run via gmail organelle: `python3 -c "from metabolon.organelles.gmail import search; print(search('category:personal -label:Cora/Action -label:Cora/Important\\ Info -label:Cora/Other -label:Cora/Newsletter -label:Cora/Payments -label:Cora/Promotion -label:Cora/Packages newer_than:1d', max_results=10))"`
   - If any results: flag them by sender + subject. These are emails Cora received but never labelled — the same failure mode that swallowed two interview invitations (Mar 2026).
   - If no results: skip silently.

8. **Deliver the brief**:

## Output

Weather, calendar, any hard deadlines today. Two short paragraphs max. Short enough to read while still in bed.

**Example:**

> **Thursday, 5 March 2026**
>
> Mainly cloudy, 16–21°C, light rain early then sunny intervals. Weather sent to Tara ✓
>
> Lunch with Tara 12:15, physio 16:00. Nicole usage report due today. Landscape: 2 high-signal, 3 medium from last 24h — review on commute.

## Boundaries

- Do NOT surface work priorities, NOW.md gates, or full task queues — that's `/statio`
- Do NOT check inbox — no email, no Cora
- Do NOT run Oura, Capco intel, GARP, or token budget — those belong in `/statio`
- Do NOT create or edit vault notes

## See also
- `/statio` — start-of-work brief (Oura, priorities, gates, prep items)
- `/kairos` — ad-hoc situational snapshot any time of day
