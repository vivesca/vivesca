---
name: statio
description: Start-of-work brief — priorities, gates, inbox triage. Use when sitting down to work. "statio", "start of work", "work brief"
user_invocable: true
---

# Start-of-Work Brief

Run when you sit down and are ready to work. Loads your priority context, clears the overnight inbox, and sets the work agenda. Assumes `/auspex` already covered weather and Oura.

## Triggers

- `/statio` (user-invocable only)

## Steps

1. **Get today's date and day of week**

2. **Health scores** (from Oura Ring):
   - Run: `oura scores`
   - Note sleep + readiness. If readiness <65, flag it — may affect how hard to push today.
   - If fails or returns all `--`, skip silently.

3. **Staleness check**:
   - Run `stat -f '%Sm' -t '%Y-%m-%d' ~/epigenome/chromatin/NOW.md ~/epigenome/chromatin/Capco/Capco\ Transition.md ~/epigenome/TODO.md`
   - If any file's last-modified date is >24h old, flag it: "NOW.md last updated X — treat as stale"

3. **Yesterday's daily note** — carryover only:
   - Read `~/epigenome/chromatin/Daily/YYYY-MM-DD.md` (yesterday), pull `## Tomorrow` and `## Follow-ups` sections only
   - Cross-reference against NOW.md `[decided]` entries — skip anything already resolved
   - If yesterday's note is missing, skip silently

4. **NOW.md open gates** — the core of this brief:
   - Read `~/epigenome/chromatin/NOW.md`
   - Surface all `[open]` items with their context. This is the work queue.

5. **Check cron logs** (overnight output):
   - Check `~/logs/` for any cron job failures (oghma, vault-backup, legatus-*, etc.)
   - Note failures only; skip silently if all clean

6. **Check overnight OpenCode results**:
   - Check `~/cache/legatus-runs/` for last night's run — read most recent `summary.md`
   - Flag NEEDS_ATTENTION or CRITICAL items; skip silently if none or missing

7. **Pre-meeting dossiers**:
   - Run: `amicus dossier --today 2>/dev/null`
   - If output is non-empty, surface attendee context (name, last contact, recent subjects) for any meeting today
   - Fail silently if amicus unavailable or DB empty

8. **Inbox check**:
   - Run: `gog gmail search "in:inbox" --limit 5`
   - If results: surface count and nudge `/epistula` — don't triage here, just flag it
   - If empty: note "Inbox clear" and move on

10. **Capco countdown + daily prep item** (until start date):
    - Calculate days remaining: `python3 -c "from datetime import date; print((date(2026,4,8)-date.today()).days)"`
    - Check `~/epigenome/chromatin/Capco/Capco Transition.md` for confirmed start date if different
    - **Pick today's prep item** — rotate by day-of-week:
      - Mon: Capco methodology
      - Tue: client knowledge
      - Wed: AI governance frameworks
      - Thu: HK regulatory landscape
      - Fri: personal brand / intro pitch
    - One specific, 15-minute-doable item. No intel sweep unless there's a clear reason.

11. **GARP quiz check** (until Apr 4, 2026):
    - Check if already done today: `python3 -c "import json; d=json.load(open('$HOME/notes/.garp-fsrs-state.json')); today='$(date +%Y-%m-%d)'; print(sum(1 for e in d.get('review_log',[]) if e.get('date','').startswith(today)))"`
    - If already done, do NOT mention GARP at all
    - If not done and today is Mon/Wed/Fri: nudge "GARP quiz due today"
    - If state file missing/corrupt, skip silently

12. **Friday nudges** — if today is Friday:
    - Append: "It's Friday — run `/weekly` this afternoon."
    - Token budget: run `ccusage daily -s $(date -v-6d +%Y%m%d)` — if >20% of ~$1,050 weekly cap remains, nudge to burn it before Saturday 8pm reset

13. **Deliver the brief**:

## Output

Start with the open gates from NOW.md — that's the work agenda. Weave in any inbox action items, meeting prep, and the Capco prep item. GARP nudge if due. Friday reminders last.

Keep it focused: what do I need to do today, in what order? Not a report — a work queue with context.

**Example:**

> **Thursday, 5 March 2026** — 34 days to Capco
>
> **On the plate:** AML hibernation email is the main gate — needs CDSW run (Steps 1+2, 3b, 5) before it can go. Nicole usage report due at noon, alarm set. China Mobile and Eight Sleep both overdue — clear those first if they're quick.
>
> Cora handled the inbox cleanly, nothing flagged. No overnight action emails.
>
> Lunch with Tara at 12:15 — no prep needed. Physio at 16:00.
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
