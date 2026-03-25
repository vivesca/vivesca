---
name: praxis-sweep
description: Check Praxis for overdue, stale, and zombie items. Flag what needs attention.
model: sonnet
tools: ["Bash", "Read"]
---

Sweep Praxis.md for hygiene.

1. Read ~/epigenome/chromatin/Praxis.md
2. Flag:
   - OVERDUE: items past their due date
   - STALE: items not touched in 14+ days (no edits, no mentions in daily notes)
   - ZOMBIE: items marked done but still appearing in active sections
   - ORPHAN: items with no context (who assigned? why?)

3. For overdue items: is the deadline real or soft? Check if it's perishable.
4. For stale items: should they be dismissed, rescheduled, or acted on now?

5. Output: action list sorted by urgency.

This runs as part of the weekly ecdysis review or on-demand when Praxis feels heavy.
