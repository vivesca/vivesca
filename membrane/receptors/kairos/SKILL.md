---
name: kairos
description: "Any-time situational snapshot — what's actionable right now. Use when user says 'kairos', 'what now', 'what should I do', 'what's next', or needs a mid-session priority check."
effort: high
user_invocable: true
triggers:
  - kairos
  - what now
  - what should I do
  - what's next
  - what do I do
  - priority check
---

# Kairos — The Opportune Moment

*Kairos* (Greek: καιρός) — qualitative time, not clock time. Not "what time is it?" but "given this moment, what's the right action?"

Unlike `auspex` (morning delta) or `cardo` (midday reflection), Kairos is stateless and anytime. No session scanning, no reflection on what shipped — just the live situation and what to do next.

**Design principle:** Kairos is the single entry point for "what now?" Every automated system (speculor, praeco, cron jobs) feeds into kairos — Terry never needs to remember what's running. When he says "should I check X?", confirm the system already covers it or flag the gap as a build signal. New tools surface through kairos, not their own invocation.

## Triggers

- "kairos"
- "what now"
- "what should I do"
- "what's next"
- "priority check"

## Steps

Run steps 1–4 in parallel.

### 1. Get current time + day

```bash
date
```

Note: day of week, time of day (HKT), proximity to end of day.
If `date` fails, use system-provided current time and continue.

### 2. Today's calendar + Due reminders

Always run both — Due reminders are not visible in fasti, calendar events are not visible in pacemaker:

```bash
fasti list        # Google Calendar events (today by default)
pacemaker ls          # Due app reminders
```

- If `fasti` fails, fall back to `gog calendar list`. Note "Calendar unavailable" and continue if both fail.

- Extract remaining calendar events for today
- Surface Due reminders due **today** — merge with calendar results for synthesis
- Flag: anything within the next 60 minutes (needs prep or imminent)
- Flag: anything within 2–4 hours (good to know)
- If nothing remaining on either, note "clear"
- If pacemaker fails or isn't installed, skip silently

### 3. Active decisions and gates — NOW.md

Read `~/epigenome/chromatin/NOW.md`.

- If file is missing/unreadable, note "NOW.md unavailable" and continue.

- Pull any open decisions (not yet `[decided]` or `[done]`)
- Pull any active processes or waiting-on states
- If a PID is mentioned, skip process check — too slow for a quick snapshot

### 4. LinkedIn job alerts (post-noon only)

If current time is after 12:00 HKT, check `~/epigenome/chromatin/Job Hunting/Job Alerts YYYY-MM-DD.md`:
- Count unchecked flagged roles (`- [ ]` lines)
- If any exist, surface briefly: "X job alerts flagged — `/adhesion` when you have a moment"
- Skip silently if file missing or all items checked

### 5. Overdue and today's TODO items

Read `~/epigenome/TODO.md`.

- If file is missing/unreadable, note "TODO.md unavailable" and continue.

- Surface only: items with `due:` <= today, items with `when:` <= today that are not completed
- Also surface `recurring:daily` items and day-of-week recurring items that match today (e.g. `recurring:3x-week` on Mon/Wed/Fri, `recurring:weekly` on the matching weekday, `recurring:biweekly` if applicable). Cross-reference with the current day from step 1.
- Skip `someday` items, skip items due later in the week
- Max 5 items — if more qualify, pick the most time-sensitive

### 6. Synthesise — time-aware routing

Based on current time and what was found:

**Commute / transit (morning, before first meeting, no desk):**
→ Surface today's acta (daily AI brief). Check: `ls ~/epigenome/chromatin/Theoria/Daily/$(date -v-1d +%Y-%m-%d).md 2>/dev/null || ls ~/epigenome/chromatin/Theoria/Daily/$(date +%Y-%m-%d).md 2>/dev/null`. Read and present key items grouped by lens. Flag any 🚨 READ ORIGINAL with links. If first meeting is soon, also surface one-line prep for it. This is the primary reading window — give the full brief, not a teaser.

**Pre-meeting (< 45 min to next calendar event):**
→ Lead with the upcoming event. Surface any prep items. Keep it brief — they're about to be in a meeting.

**Post-meeting block (event ended < 30 min ago):**
→ Flag follow-up capture: "Just finished X — anything to log or action from that?"

**Free block (no meeting for 2+ hours):**
→ Surface top 1–2 priorities from NOW.md + overdue TODO. Concrete, doable.

**Late afternoon (after 5pm HKT) or pre-EOD:**
→ Flag EOD proximity: "< N hours left — what needs wrapping before you close?"

**No context to surface:**
→ Say so plainly: "Calendar clear, nothing overdue, no open gates in NOW.md — you've got a clean slate." Then offer: "Want me to check inbox or surface low-energy tasks?"

## Output

One short paragraph. No headers, no bullets unless there are 3+ overdue items. Lead with time context, close with the clearest next action.

**Example outputs:**

> **3:15pm Tuesday** — Meeting-free until 5pm. One open gate in NOW.md: the Lacuna Railway deployment (waiting on Terry to test the new endpoint). Two overdue: school research checklist (since Feb 28), SmarTone bill. The deployment test is the sharpest thing — 20 minutes to close that loop.

> **10:45am Wednesday** — Standup in 12 minutes. After that you're free until 2pm. Nothing in NOW.md flagged as urgent. Clean slate post-standup.

> **6:20pm Thursday** — EOD in sight. Two open decisions in NOW.md: Capco start date (waiting on Gavin) and lucus Phase 2 design. Neither is closeable today — flag both in daily note and call it. One overdue TODO: AXA insurance form (since Mar 1).

## Notes

- Do NOT scan anam/session history — that's cardo's job. Kairos is forward-looking.
- Do NOT reflect on what was shipped this session. Pure situational read.
- If keychain is locked and gog fails, note it and skip calendar gracefully.
- Keep it under 5 sentences. The point is to decide and move, not to read a report.
- If the user just ran `auspex` or `cardo` recently (same session), skip NOW.md/TODO repeat and just surface what's changed: new calendar events or new open gates since then.

## Boundaries

- Do NOT scan anam/session history; `/cardo` owns reflection.
- Do NOT mutate files (TODO/NOW/daily); this skill is read-only situational routing.
- Do NOT run deep research or inbox triage; only time/calendar/NOW/TODO snapshot.

## Called by
- `auspex` — today's plate section
- `cardo` — afternoon priorities section
