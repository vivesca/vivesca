---
name: ultradian
description: "Any-time situational snapshot — what's actionable right now. Use when user says 'ultradian', 'what now', 'what should I do', 'what's next', or needs a mid-session priority check."
user_invocable: true
triggers:
  - ultradian
  - what now
  - what should I do
  - what's next
  - what do I do
  - priority check
context: fork
epistemics: [plan, monitor]
---

# Kairos — The Opportune Moment

*Kairos* (Greek: καιρός) — qualitative time, not clock time. Not "what time is it?" but "given this moment, what's the right action?"

Unlike `entrainment` (morning delta), Kairos is stateless and anytime. No session scanning, no reflection on what shipped — just the live situation and what to do next.

**Design principle:** Kairos is the single entry point for "what now?" Every automated system (speculor, praeco, cron jobs) feeds into ultradian — Terry never needs to remember what's running. When he says "should I check X?", confirm the system already covers it or flag the gap as a build signal. New tools surface through ultradian, not their own invocation.

**Task routing:** When surfacing items, distinguish committed vs uncommitted paths, flag zombie tasks (snoozed 3+ times), and bias toward dropping rather than escalating.

## Live Context (injected at invocation)

```bash
ultradian-gather
```

This runs all deterministic gathering in parallel (date, calendar, reminders, NOW.md, TODO today, job alerts, efferens). Use `--json` for structured parsing.

## Steps

Using the gathered context:

### 1. Time + Calendar + Reminders

Already injected. Note: day of week, proximity to end of day. Flag anything within 60 minutes (imminent) or 2-4 hours (good to know). Merge calendar + Due for synthesis.

### 2. Active decisions and gates

Already injected via NOW.md. Pull open decisions (not `[decided]` or `[done]`)
- Pull any active processes or waiting-on states
- If a PID is mentioned, skip process check — too slow for a quick snapshot

### 3. LinkedIn job alerts (post-noon only)

If current time is after 12:00 HKT, check `~/epigenome/chromatin/Job Hunting/Job Alerts YYYY-MM-DD.md`:
- Count unchecked flagged roles (`- [ ]` lines)
- If any exist, surface briefly: "X job alerts flagged — `/adhesion` when you have a moment"
- Skip silently if file missing or all items checked

### 4. Overdue and today's TODO items

Read `~/epigenome/chromatin/Praxis.md`.

- If file is missing/unreadable, note "Praxis.md unavailable" and continue.

- Surface only: items with `due:` <= today, items with `when:` <= today that are not completed
- Also surface `recurring:daily` items and day-of-week recurring items that match today (e.g. `recurring:3x-week` on Mon/Wed/Fri, `recurring:weekly` on the matching weekday, `recurring:biweekly` if applicable). Cross-reference with the current day from step 1.
- Skip `someday` items, skip items due later in the week
- Max 5 items — if more qualify, pick the most time-sensitive

### 5. Synthesise — time-aware routing

Based on current time and what was found:

**Commute / transit (morning, before first meeting, no desk):**
→ Surface today's efferens (daily AI brief). Check: `ls ~/epigenome/chromatin/Thalamus/Daily/$(date -v-1d +%Y-%m-%d).md 2>/dev/null || ls ~/epigenome/chromatin/Thalamus/Daily/$(date +%Y-%m-%d).md 2>/dev/null`. Read and present key items grouped by lens. Flag any 🚨 READ ORIGINAL with links. If first meeting is soon, also surface one-line prep for it. This is the primary reading window — give the full brief, not a teaser.

**Pre-meeting (< 45 min to next calendar event):**
→ Lead with the upcoming event. Surface any prep items. Keep it brief — they're about to be in a meeting.

**Post-meeting block (event ended < 30 min ago):**
→ Flag follow-up capture: "Just finished X — anything to log or action from that?"

**Free block (no meeting for 2+ hours):**
→ Surface top 1–2 priorities from NOW.md + overdue TODO. Concrete, doable. Tiebreaker between equal-urgency items: prefer the one whose output compounds (skill > script, vault note > chat explanation, research > re-research). Test: "will this still be useful in April?"
→ **Energy diagnostic:** Is the block running low-energy (depleted, post-meeting, sick) or blocked (stuck, avoiding)? These look the same but route differently. *Depletion* → route to a low-stakes, mechanical task that still advances something. *Resistance* → name what's being avoided; the item with friction is usually the one that matters. Don't let depletion masquerade as resistance or vice versa.

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

- Do NOT scan engram/session history. Kairos is forward-looking.
- Do NOT reflect on what was shipped this session. Pure situational read.
- If keychain is locked and gog fails, note it and skip calendar gracefully.
- Keep it under 5 sentences. The point is to decide and move, not to read a report.
- If the user just ran `entrainment` recently (same session), skip NOW.md/TODO repeat and just surface what's changed: new calendar events or new open gates since then.

## Boundaries

- Do NOT mutate files (TODO/NOW/daily); this skill is read-only situational routing.
- Do NOT run deep research or inbox triage; only time/calendar/NOW/TODO snapshot.

## Called by
- `entrainment` — today's plate section
