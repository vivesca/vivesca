# Daily Loop System — Design Spec
*2026-03-10*

## Problem

Terry has a substantial overnight agent fleet (legatus, cron, LaunchAgents) but almost none of the output gets read. Mornings are packed — school drop-off until 8:45am, then commute once Capco starts Apr 8. There is no calm morning window for reading vault notes or digest files. The existing morning dashboard at 3:30am has 8/11 tasks failing silently.

The root issue: automation that produces outputs no one reads is theatre, not leverage.

## Design

A lightweight daily loop with two touchpoints, context-independent (works pre and post Capco):

```
9:30pm  → Evening push  (Telegram: tomorrow's 3 big things)
↓
sleep
↓
First quiet window (8:45am+ or MTR commute post-Apr 8)
        → Morning brief (Claude session: overnight + today + light action)
```

### Touchpoint 1: Evening Push

**What:** A Telegram notification at 9:30pm with tomorrow's 3 most important things.

**Contents (strictly limited):**
1. Tomorrow's calendar events (time + title only)
2. Hard deadlines from Praxis.md hitting tomorrow or next 48h
3. One overnight alert if anything genuinely urgent (praeco regulatory alert, speculor strong match, health flag)

**Format:** 3 bullets max. No padding. If nothing urgent in slot 3, omit it — don't fill with noise.

**Delivery:** LaunchAgent at 9:30pm → `deltos` Telegram push

**Purpose:** Offload "don't forget tomorrow" anxiety so sleep is uninterrupted. Passive consumption — read, put phone down.

**Hard constraint:** If it ever exceeds 5 lines, the filtering logic is wrong. Fix the filter, not the length.

### Touchpoint 2: Morning Brief (Phase 2)

**What:** A Claude session (`/brief` skill) at first quiet window — currently post-8:45am, post-Apr 8 on MTR commute over 5G via Blink.

**Structure (70% brief, 30% action):**
1. **Orient** (5 min): Claude reads overnight legatus results, speculor triage, praeco alerts, calendar, health signal → presents in 5-6 sentences
2. **Act** (10-15 min): surfaces only quick decisions — approve a TODO, queue a legatus task, 1-line reply. Anything requiring >2 messages → deferred to desk session

**Hard constraint:** If it takes more than 2 messages to resolve, defer it. No deep work on the train.

**Build timing:** Phase 2 — build after 2 weeks of evening push usage. Real data will show what the push misses.

## Build Phases

| Phase | What | When | Signal to proceed |
|-------|------|------|-------------------|
| 1 | Evening push (9:30pm Telegram) | Now | — |
| 2 | Morning brief (`/brief` skill) | +2 weeks | Evening push used consistently |
| 3 | 5-day domain split for `/weekly` | +6 weeks | Morning brief established |

## Out of Scope (for now)

- Per-job company research via legatus (speculor Strong Match briefings) — revisit if Capco not working after 3 months
- Fixing broken morning dashboard — separate task, not part of this loop
- Full 5-day `/weekly` decomposition — Phase 3

## Success Criteria

- Evening push read >5 out of 7 nights per week
- Morning brief used on commute days (post-Apr 8)
- No silent agent failures going unnoticed for >48h
- `/weekly` shortened by at least 30% once domain split is live

## Key Decisions

- **Telegram over vault note** for evening push: push model beats pull model for end-of-day consumption
- **Claude session over Obsidian mobile** for morning brief: conversational > passive reading
- **Phase 1 only for now**: Capco commute pattern not established until mid-April; validate evening push first
- **3-bullet hard limit**: notification fatigue is the #1 failure mode
