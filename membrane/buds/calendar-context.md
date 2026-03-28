---
name: calendar-context
description: Surface relevant chromatin context for tomorrow's meetings. Prep without being asked.
model: sonnet
tools: ["Bash", "Read", "Grep", "Glob"]
---

Prepare context for tomorrow's calendar.

1. Read tomorrow's calendar: `fasti list tomorrow`
2. For each meeting/event:
   - Search ~/epigenome/chromatin/ for relevant chromatin notes (grep attendee names, topics)
   - Search ~/epigenome/chromatin/euchromatin/ for relevant reference docs
   - Check ~/docs/sparks/ for relevant consulting sparks
3. Output: per-meeting context card (5 lines max each):
   - Meeting: [title, time]
   - Relevant notes: [paths]
   - Key points to remember: [from notes]
   - Open questions: [from prior meetings]

Run as part of interphase (evening routine) so context is ready for morning.
