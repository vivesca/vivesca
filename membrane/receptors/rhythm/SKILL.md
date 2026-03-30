---
name: rhythm
description: Time-based workflows — daily, weekly, quarterly. Time-routed.
user_invocable: true
triggers:
  - morning
  - evening
  - weekly
  - quarterly
  - what now
  - what's next
  - circadian
  - infradian
  - meiosis
context: fork
model: sonnet
---

# /rhythm

Time-based workflows — daily, weekly, quarterly. Time-routed.

## Router

| When | Sub-workflow | What it does | Doc |
|------|-------------|--------------|-----|
| 06:00-22:00 daily | **circadian** | Daily rhythm — dawn/day/evening/night phases | `circadian.md` |
| Saturday | **infradian** | Weekly review — reflect and plan | `infradian.md` |
| Sunday | **ecdysis** | Weekly planning — plan next week, prune TODOs | `ecdysis.md` |
| Evening pre-sleep | **involution** | Evening wind-down routine | `involution.md` |
| Weekly | **methylation** | Weekly crystallization — turn experience into probes | `methylation.md` |
| Quarterly | **meiosis** | Quarterly review — direction, career, finances | `meiosis.md` |

## How to use

1. Match the user's request to a row above
2. Read the matching doc (e.g., `circadian.md` in this directory)
3. Follow the sub-workflow instructions
