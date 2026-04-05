---
name: auspex
description: Wake-up brief — weather, calendar, key deadlines today. Use when waking up. "morning brief", "wake-up brief", "auspex"
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

## Compute routing

Soma is the primary compute node. Local iMac is the fallback.

**Step 0 — Probe soma:**
```bash
ssh -o ConnectTimeout=3 -o BatchMode=yes vivesca@soma echo ok 2>/dev/null
```
If this succeeds, set `SOMA=true`. Use `ssh vivesca@soma '<cmd>'` for data commands.
If it fails, set `SOMA=false` and run everything locally.

**Routing rules:**
| Command | Soma | Local fallback |
|---------|------|----------------|
| `hygroreception` | `ssh vivesca@soma 'hygroreception'` | `hygroreception` |
| Endocytosis top | `ssh vivesca@soma 'cd ~/germline && python3 -m metabolon.organelles.endocytosis_rss.cli top --limit 10 --days 1'` | MCP: `mcp__vivesca__endocytosis action=top` |
| Gmail scan | `ssh vivesca@soma 'cd ~/germline && python3 -c "..."'` | Skip (no local auth) |
| iMessage to Tara | Always local: `osascript -e 'tell application "Messages" to send "TEXT" to buddy "taracny@gmail.com"'` | — |
| Calendar, TODO, overnight | Always local (local files/MCP) | — |

## Steps

1. **Get today's date and day of week**

2. **Probe soma** (step 0 above). Log result silently — don't surface to user unless it fails.

3. **Weather**:
   - Run `hygroreception` (on soma if available, else local)
   - Always include in the brief
   - **Send to Tara**: send the raw hygroreception output directly — no prose, no greeting, no personality. Just the factual weather line(s) as-is.
     - Always via local osascript: `osascript -e 'tell application "Messages" to send "WEATHER_TEXT" to buddy "taracny@gmail.com"'`
   - If send fails, note briefly — don't retry.
   - If `hygroreception` fails, note "Weather unavailable" and continue.

4. **Today's calendar**:
   - Use MCP tool: `mcp__vivesca__circadian action=list date=today`
   - List events with times. Flag anything before 10am that requires prep.

5. **Key deadlines today** — a quick scan of TODO.md:
   - Grep `~/epigenome/TODO.md` for items tagged `when: <today's date>` or `due: <today>`
   - Surface only hard deadlines — things with a specific date on them today
   - Skip someday/low-energy/undated items entirely — those are statio's job
   - If nothing due today, skip silently

6. **Overnight results** (if recent run):
   - Find latest morning-dashboard output: `LATEST=$(ls -dt ~/.cache/legatus-runs/2[0-9]*/ 2>/dev/null | head -1) && cat "$LATEST/morning-dashboard/stdout.txt" 2>/dev/null`
   - If found and the run dir is from last night (within 12h): surface as one line (e.g. "Overnight: vault HEALTHY, 2 git issues — /overnight for details")
   - If nothing found: skip silently — don't mention the queue

7. **Landscape teaser** (don't read the full brief — that's for commute):
   - Route via soma or MCP per routing table above
   - Count items by score tier: high (8+), medium (6-7), total
   - Surface as one line: "Landscape: 2 high-signal, 3 medium from last 24h — review on commute"
   - If no items in last 24h, try `days=3` for a wider window and note the staleness
   - Do NOT list or summarise individual items — just the count. Morning is Theo time, not reading time.
   - If endocytosis returns nothing: skip silently

8. **Missed email scan** (known Cora blind spot):
   - Route via soma per routing table. Query: `category:personal -label:Cora/Action -label:Cora/Important\ Info -label:Cora/Other -label:Cora/Newsletter -label:Cora/Payments -label:Cora/Promotion -label:Cora/Packages newer_than:1d`
   - If soma unavailable: skip (no local gmail auth)
   - If any results: flag them by sender + subject. These are emails Cora received but never labelled — the same failure mode that swallowed two interview invitations (Mar 2026).
   - If no results: skip silently.

9. **Deliver the brief**:

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
