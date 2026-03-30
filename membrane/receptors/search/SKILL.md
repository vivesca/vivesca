---
name: search
description: Information gathering — memory, web, AI briefing, polarity. Signal-routed.
user_invocable: true
triggers:
  - search
  - find
  - recall
  - ecphory
  - pinocytosis
  - browse
  - chemoreception
  - gradient
  - briefing
context: fork
model: sonnet
---

# /search

Information gathering — memory, web, AI briefing, polarity. Signal-routed.

## Router

| When | Sub-workflow | What it does | Doc |
|------|-------------|--------------|-----|
| Memory recall | **ecphory** | Cue-routed retrieval across memory stores | `ecphory.md` |
| Web fetch | **pinocytosis** | Fetch web content — route by cargo type | `pinocytosis.md` |
| AI briefing | **chemoreception** | On-demand briefing from stale signal | `chemoreception.md` |
| Polarity sensing | **gradient** | Detect co-trending domains before committing | `gradient.md` |

## How to use

1. Match the user's request to a row above
2. Read the matching doc (e.g., `ecphory.md` in this directory)
3. Follow the sub-workflow instructions
