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

### First-session-back protocol (>2 weeks since last log)

Don't anchor on a uniform deload (e.g., "5 weeks off = drop 15-20% across all lifts"). Detraining is non-uniform across movements — for Terry, shoulders and lats often hold baseline while bench detrains noticeably. Anchoring on a uniform drop forces 2-3 mid-session recalibrations.

Instead:
- Prescribe a **feel-out set 1** at the prior working weight (not a deloaded weight).
- Read the RPE feedback. RPE 9+ at expected reps → drop 15-20% for sets 2-3. RPE 7 with 2-3 RIR → hold weight. RPE <6 with 4+ RIR → bump or add tempo/pause for time-under-tension.
- Capture per-movement detraining in the log's "Notes for Next Session" — bench-sensitive vs shoulder-resistant becomes a known prior for the next break.

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

## Engagement-failure protocol

If athlete reports "can't feel the [target muscle]" during a set, the movement is failing its purpose — grinding more sets won't fix recruitment. Time-box the recovery: **one cue adjustment + one weight change**, then swap the movement. Don't iterate three+ cue/weight combinations chasing a feel that isn't coming.

Common failure-mode triggers: pallof press at light weight (insufficient rotational pull to brace against), lateral raises at heavy weight (front shoulder + tricep take over), bench at low weight (chest doesn't get loaded). Substitution candidates ready in the log: pallof → suitcase carry / dead bug; lateral raise → cable lateral / leaning DB raise; bench → DB floor press / push-up loaded.

Codifies failure caught in 2026-05-05 Slot 42: prescribed 5kg pallof, then bumped 8-10kg + cue stack, athlete still couldn't feel core. Should have swapped after first failed cue, not third.

## Resistance scaling

Core / accessory weight prescriptions must scale to the athlete's current compound working weights, not absolute floor numbers. If row working weight is 10kg/side, pallof at 5kg is under-prescribed by a factor of 2-4. Default starting point for unilateral / anti-rotation core work: ~50% of bilateral compound working weight.

## Safety

- **Scoliosis**: no heavy axial loading, no barbell squats/deadlifts, no rotational resistance. DBs over barbells.
- Pain → stop. Don't coach through it.
- Engagement-failure → swap, don't grind. See engagement-failure protocol above.
