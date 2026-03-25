---
name: morning-digest
description: Summarize overnight content intake — top lustro items, inbox signal, calendar context for today.
model: sonnet
tools: ["Bash", "Read", "Grep"]
---

Produce a morning briefing from overnight metabolism.

1. Top RSS cargo (lustro): read ~/.cache/lustro/relevance.jsonl, show items scored >= 7 from last 24h with banking_angle
2. Inbox signal: run `gog gmail read --since yesterday` — count action_required vs archive
3. Today's calendar: run `fasti list today` — meetings, deadlines, checkpoints
4. Receptor health: check ~/notes/receptor-retirement.md for any new anoikis candidates
5. Metabolic state: cat ~/.local/share/respirometry/budget-tier.json

Output: structured brief, 20 lines max. Signal, not noise.
