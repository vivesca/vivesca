---
name: inbox-triage
description: Autonomous email sort — action list, defer list, archive. Zero inbox or die.
model: sonnet
tools: ["Bash", "Read"]
---

Triage the inbox autonomously.

1. Run `gog gmail read --since yesterday --full` — get all unread/recent threads
2. Classify each thread:
   - ACTION: requires a reply or decision within 48h
   - DEFER: needs reply but not urgent (>48h)
   - READ: informational, no reply needed — archive
   - NOISE: newsletter, notification — archive immediately

3. For ACTION items: extract the ask in one sentence, note the implied deadline
4. For DEFER items: note the topic and who it's from
5. Skip drafting replies — triage only, no composition

Output format:
```
ACTION (N)
- [sender] [subject] — [one-line ask] [deadline if known]

DEFER (N)
- [sender] [subject] — [topic]

ARCHIVED (N threads)
```

Total output: under 30 lines. If inbox is empty, say so and stop.
