---
name: entrainment
description: Morning brief — call at session start to surface sleep scores and overnight system alerts before any work begins.
model: sonnet
---

# Entrainment — phase-lock before work

**Rule: read biometric state before advising on the day's load or schedule.**

## When this fires

- First substantive message in a morning session
- User mentions feeling tired, headache, or asks about training readiness
- Planning the day's priorities or gym session
- Checking if overnight automation ran cleanly

## Discipline

1. **Call `entrainment_brief` once** — it aggregates sleep + overnight in a single call; do not call sopor separately if you've already called this.
2. **Readiness < 65** → flag explicitly before discussing workload; don't bury it in the output. Cross-reference `memory/user_health_exercise_readiness.md` (< 70 = light only, resume > 75).
3. **Overnight alerts** → any NEEDS_ATTENTION or CRITICAL lines surface immediately, not after other topics.
4. **Right-sided morning headache** → check `memory/user_health_sleep_headache_pattern.md`; it's sleep quality not sinusitis.
5. **Stale data** — entrainment_brief silently skips overnight files older than 24h; if overnight is "No overnight data", note that automation may not have run.

## Anti-patterns

| Don't | Do |
|-------|-----|
| Call sopor separately after entrainment_brief | Use entrainment_brief as the single call |
| Skip readiness when < 65 | Surface it immediately |
| Proceed with heavy planning at low readiness | Recommend lighter day first |
| Ignore "No overnight data" | Note the gap, check if automation is healthy |
