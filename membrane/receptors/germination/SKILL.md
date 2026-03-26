---
name: germination
description: Overnight results — surface NEEDS_ATTENTION flags from async agents before proceeding with morning work.
model: sonnet
---

# Germination — conditions-triggered surfacing

**Rule: check the flag before assuming overnight tasks completed cleanly.**

## When this fires

- Morning session start (alongside entrainment)
- User asks "what ran overnight?" or "did X finish?"
- Suspecting an automated task failed or is stuck
- Reviewing history of overnight runs for a pattern

## Discipline

1. **Check flag first** — `has_pending_germination()` is non-blocking; if the flag exists, surface summary before any other work.
2. **`germination_brief` for the dashboard** — shows latest run summary and NEEDS_ATTENTION status. Use this as the entry point.
3. **`germination_results` to drill** — pass a task name to isolate one output; empty string returns all. Only drill if the brief shows a problem or user asks specifically.
4. **`germination_list` for history** — use when diagnosing recurring failures across runs, not as default.
5. **Don't confuse germination with entrainment** — entrainment is biometric morning state; germination is automation output state. Both should fire at session start, in that order.

## Anti-patterns

| Don't | Do |
|-------|-----|
| Skip this if entrainment_brief mentioned overnight | Run both — they sense different systems |
| Assume "no flag" means everything passed | Call germination_brief to confirm |
| Drill into all tasks by default | Brief first, drill only on failures |
| Report raw output verbatim | Extract the NEEDS_ATTENTION lines; bury the noise |
