---
name: differentiation
description: Coach a live gym session — prescribe sets, track reps, log workout. "gym", "workout", "gym session"
user_invocable: true
epistemics: [monitor, learn]
---

# gym-coach — live session coaching

## Before the session

1. Run `check-exercise-readiness` skill. Honour thresholds (<70 light, 70-75 moderate, >75 full).
2. Find the latest gym log: `~/epigenome/chromatin/Health/Gym Log - *.md`. Read it for working weights, notes for next session, and any form fixes flagged.
3. Prescribe today's exercises with target weights and rep ranges based on the log. Don't hardcode a programme — read from chromatin each time.

## During the session

4. **Every set**: run `date '+%H:%M:%S'` to timestamp it. Record weight, reps achieved.
5. **After each set**: ask "how many more could you do?" (maps to difficulty: 0 = failure, 4+ = too light).
6. **Between sets**: track rest. Compounds 2min, accessories 60-90s, dead hangs 30-45s. Check elapsed time with `date` when Terry says ready.
7. Answer form questions inline. Note any cues that helped for the log.

## Progression

- ≥4 spare reps consistently → flag weight increase next session. Max one increase per session.
- 0-1 spare on multiple sets → hold weight or deload.

## After the session

8. Write the completed log to `~/epigenome/chromatin/Health/Gym Log - YYYY-MM-DD.md` using this format:

```
---
tags: [health, exercise, gym, pure-fitness]
created: YYYY-MM-DD
type: session-log
---

# Gym Session — YYYY-MM-DD (Day)

**Location:** PURE Fitness
**Oura Readiness:** [score]
**Duration:** ~Xmin (HH:MM–HH:MM)
**Focus:** [focus]

## Exercises

| # | Exercise | Weight | Sets × Reps | Notes |
|---|----------|--------|-------------|-------|

## Working Weights
## Notes for Next Session

**Related:** [[Fitness Restart Plan - Scoliosis Safe - 2026-03]]
```

## Safety

- **Scoliosis**: no heavy axial loading, no barbell squats/deadlifts, no rotational resistance. DBs over barbells.
- Pain → stop. Don't coach through it.
