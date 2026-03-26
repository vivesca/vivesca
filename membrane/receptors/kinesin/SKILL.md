---
name: kinesin
description: Session-independent task dispatch — run, monitor, or cancel async agents that must survive session end.
model: sonnet
---

# Kinesin — transport beyond the session

**Rule: use kinesin when the work must continue after this conversation ends.**

## When this fires

- Task takes longer than a typical session (data collection, long crawls, batch processing)
- User asks to "run X tonight" or "schedule X for later"
- Checking if a previously dispatched task is still running or has results
- Canceling a runaway or stale task

## Discipline

1. **`translocation_list` first** — always check what's configured and what state tasks are in before dispatching. Don't run a task that's already running.
2. **`translocation_run` dispatches detached** — the task survives session end. Confirm the task name exactly matches the listed name (case-sensitive).
3. **`translocation_results` to read output** — pass task name for targeted output; empty string returns all. Pair with `germination_brief` at morning session start rather than polling throughout the day.
4. **`translocation_cancel` is permanent for the run** — it cancels/disables the task, not just pauses it. Confirm intent before calling.
5. **Don't poll** — kinesin tasks report through germination; check results at natural session boundaries, not on demand.

## Anti-patterns

| Don't | Do |
|-------|-----|
| Dispatch without checking list first | translocation_list → then run |
| Use kinesin for sub-60-second tasks | Run inline; kinesin is for async durability |
| Poll translocation_results mid-session | Wait for germination_brief at session start |
| Cancel when results are missing | Check translocation_results first — task may still be running |
