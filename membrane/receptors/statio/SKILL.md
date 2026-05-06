---
name: statio
description: Start-of-work brief — priorities, gates, inbox triage. Use when sitting down to work. "statio", "start of work", "work brief"
effort: high
user_invocable: true
---

# Start-of-Work Brief

Run when you sit down and are ready to work. Loads your priority context, clears the overnight inbox, and sets the work agenda. Assumes `/auspex` already covered weather.

## Triggers

- `/statio` (user-invocable only)

## Compute routing

Soma is the primary compute node. Local iMac is the fallback.

**Step 0 — Probe soma:**
```bash
ssh -o ConnectTimeout=3 -o BatchMode=yes vivesca@soma echo ok 2>/dev/null
```
If this succeeds, set `SOMA=true`. Use `ssh vivesca@soma '<cmd>'` for data commands.
If it fails, set `SOMA=false` and run everything locally where possible.

**Routing rules:**
| Command | Soma | Local fallback |
|---------|------|----------------|
| `sopor scores` | `ssh vivesca@soma 'sopor scores'` | `sopor scores` (if available locally) |
| `amicus dossier` | `ssh vivesca@soma 'amicus dossier --today'` | Skip (no local DB) |
| `gog gmail search` | `ssh vivesca@soma 'gog gmail search ...'` | `gog gmail search ...` |

## Steps

1. **Get today's date and day of week**

2. **Health scores** (from Oura Ring via sopor):
   - Run: `sopor scores` (route per compute table)
   - Note sleep + readiness. If readiness <65, flag it — may affect how hard to push today.
   - If fails or returns all `--`, skip silently.

3. **Staleness check**:
   - Use python3 to check mtime of: `~/epigenome/TODO.md`, `~/epigenome/chromatin/Capco/Capco Transition.md`
   - If any file's last-modified date is >3d old, flag it as stale

4. **Yesterday's daily note** — carryover only:
   - Read `~/epigenome/chromatin/Daily/YYYY-MM-DD.md` (yesterday), pull `## Tomorrow` and `## Follow-ups` sections only
   - If yesterday's note is missing, skip silently

5. **Deadline scan**:
   - Run: `python3 ~/germline/effectors/deadline_scan.py`
   - If any deadlines within 7 days: surface them prominently at the top of the brief
   - If none: skip silently

6. **Work queue** — the core of this brief:
   - Primary: read g1.md (`~/epigenome/chromatin/g1.md` or from session state) for `## Progress (active)` items marked `[next]`
   - Secondary: check `~/epigenome/TODO.md` for items tagged with today's date
   - Surface all open items with their context. This is the work queue.

7. **Check cron logs** (overnight output):
   - Check `~/logs/` for any cron job failures from last 24h only (ignore older entries)
   - Note failures only; skip silently if all clean or all stale

8. **Check overnight legatus results**:
   - Check `~/.cache/legatus-runs/` for last night's run — read most recent `summary.md`
   - Flag NEEDS_ATTENTION or CRITICAL items; skip silently if none or missing

9. **Pre-meeting dossiers**:
   - Run: `amicus dossier --today 2>/dev/null` (route per compute table)
   - If output is non-empty, surface attendee context for any meeting today
   - Fail silently if amicus unavailable or DB empty

10. **Inbox check**:
   - Run: `gog gmail search "in:inbox" --limit 5 --json 2>/dev/null` or `gog gmail search "in:inbox" --limit 5`
   - If results: surface count and actionable items only (billing, replies, deadlines). Nudge `/endocrine` for full triage.
   - If empty: note "Inbox clear" and move on

11. **Capco day count + daily prep item**:
    - Calculate days since start: `python3 -c "from datetime import date; print((date.today()-date(2026,4,8)).days)"`
    - **Pick today's prep item** — rotate by day-of-week:
      - Mon: Capco methodology
      - Tue: client knowledge
      - Wed: AI governance frameworks
      - Thu: HK regulatory landscape
      - Fri: personal brand / intro pitch
    - One specific, 15-minute-doable item. No intel sweep unless there's a clear reason.

12. **Friday nudges** — if today is Friday:
    - Append: "It's Friday — run `/weekly` this afternoon."

13. **Deliver the brief**:

## Output

Start with the work queue — that's the work agenda. Weave in any inbox action items, meeting prep, and the Capco prep item. Friday reminders last.

Keep it focused: what do I need to do today, in what order? Not a report — a work queue with context.

**Example:**

> **Thursday, 17 April 2026** — Capco Day 10
>
> **On the plate:** ServiceNow data export is the main gate — follow up with Frankie. Simon email draft needs review and send. Thinh's MRM pain points email validates the framework — read it.
>
> 3 actionable emails in inbox — `/endocrine` to triage.
>
> Today's Capco prep: HK regulatory landscape — read the Jan 2026 HKMA/SFC joint fintech statement (15 min).

Skip empty sections. No padding. The point is to know what to open first.

## Boundaries

- Do NOT send weather or Tara messages — that's `/auspex`
- Do NOT create or edit vault notes
- Do NOT run intel sweeps unless there's a specific reason

## See also
- `/auspex` — wake-up brief (Oura, weather, calendar)
- `/kairos` — ad-hoc situational snapshot during the day
- `/cardo` — midday reflection
