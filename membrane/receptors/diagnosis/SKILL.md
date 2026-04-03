---
name: diagnosis
description: Debugging as hypothesis-driven search — observation hierarchy, hypothesis discipline, when to abandon a theory. Reference skill. Not user-invocable.
version: 1
tags: [reference, debugging, cognition]
triggers:
  - diagnosis
  - debugging
  - debug
  - stuck
disable-model-invocation: true
---

# Diagnosis — Theory of Debugging

> Debugging is hypothesis-driven search through a causal chain. Diagnosis, not fixing.

Reference skill. Consult when debugging gets stuck, when designing debugging workflows, or when reviewing why a debugging session went poorly.

## What Debugging Is

**Hypothesis-driven search through a causal chain.** You have observed behavior, expected behavior, and a gap. Debugging finds where in the chain reality diverged from your mental model.

Debugging is NOT fixing. Debugging is diagnosis. The fix is almost always trivial once the cause is known. Invest in faster diagnosis, not faster typing.

**The bug isn't in the code — it's in the gap between the code and the mental model.** This is why you can't always find your own bug (you read through the same flawed model that wrote it) and why someone else finds it in five minutes (they don't share your model).

## Debugging as Search

The search space: the causal chain from input to wrong output. Every technique is a search strategy:

- **Binary search** — master technique. "Is state correct at this midpoint?" halves the space. Works on any system. `git bisect`, print-at-midpoint, all instances of this.
- **Reproduction** — most underrated step. If you can reproduce reliably, you've already constrained the space to trigger conditions. Writing a minimal repro often IS the diagnosis. Can't reproduce → can't verify the fix.
- **Observation beats reasoning** — direct observation (print the actual value) is more reliable than code reading (what should happen). Always.

## Hierarchy of Debugging Information

Most to least reliable:

1. **Direct observation** — actual value at actual moment
2. **Reproduction** — trigger on demand?
3. **Stack traces / errors** — system's own report
4. **Code reading** — what should happen
5. **Documentation** — what was intended
6. **Intuition** — what you think happened

Most people debug bottom-up (intuition first, observe last). **Invert this.** Observe first, theorise second — highest-leverage debugging habit.

## Hypothesis Discipline

- **Form hypothesis BEFORE looking at code.** Looking first → brain locks onto first wrong-looking thing.
- **Each observation must test the hypothesis.** "Interesting but doesn't test my theory" = wandering.
- **Most dangerous moment:** finding something wrong that isn't the bug. You fix it, feel progress, original bug remains.
- **Correct diagnosis explains ALL symptoms.** Partial explanation = usually wrong explanation.

## When to Abandon a Hypothesis

- Two contradictory observations → recheck observations or step back further
- Hypothesis can't explain all symptoms → probably wrong
- >15 minutes without narrowing → wrong part of the causal chain, zoom out

## Failure Modes

| Failure | Description | Signal |
|---------|-------------|--------|
| **Narrative debugging** | Story about what must be wrong, no observation | "It must be the database" — unchecked |
| **Fix-first** | Changing before understanding | Multiple "try this" commits, no diagnosis |
| **Scope creep** | Fixing unrelated issues, original bug persists | Feels productive, zero progress |
| **Confirmation bias** | Observations bent to fit theory | Ignoring contradictory evidence |
| **Environment blindness** | Assuming bug is in your code | Config, deps, state, infra missed |
| **Symptom treatment** | Fixing visible symptom, not root cause | Bug returns in different form |

## When Debugging Gets Hard

| Type | Why it's hard | Technique |
|------|--------------|-----------|
| **Non-deterministic** (race conditions) | Causal chain itself is unstable | Increase observation density |
| **Emergent** (components correct, aggregate wrong) | Binary search on components finds nothing | Trace data across boundaries, system-level view |
| **Heisenbugs** (observing changes behavior) | Observation tool is part of the system | Less invasive observation (logging > breakpoints) |
| **Historical** (it used to work) | Change is the cause | `git bisect` — purpose-built |

## Human vs Agent Debugging

Same asymmetry as planning: humans have rich intuition ("feels like a race condition") that skips 90% of search space. Agents have exhaustive systematic observation that never gets bored.

Best hybrid: human forms initial hypothesis (pattern recognition), agent tests systematically (exhaustive observation).

## When to Consult This Skill

- Debugging session stuck >30 minutes — check failure modes table
- Designing a debugging workflow or tool
- Post-mortem on a debugging session that went poorly
- Teaching debugging approach to a delegate/agent
