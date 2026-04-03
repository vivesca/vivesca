---
name: bouleusis
description: Planning theory reference — goal clarity, simulation depth, failure modes, when to stop. Consulted by planning workflows and agent design.
version: 1
tags: [reference, planning, cognition, agents]
triggers:
  - bouleusis
  - planning
  - plan theory
  - deliberation
  - goal clarity
  - planning failure
disable-model-invocation: true
---

# Bouleusis — Theory of Planning

> βούλευσις (bouleusis): Aristotle's term for deliberation about how to achieve an end. The cognitive act of planning.

Reference skill. Consult when designing planning workflows, evaluating plans, or debugging why a plan failed.

## What Planning Is

Planning is **goal-directed simulation with commitment**.

- **Goal-directed** — starts from a desired end-state. No goal = no planning, just daydreaming. Separates planning from analysis (what is) and reasoning (what follows). Planning constructs what to do.
- **Simulation** — runs a mental model of the world forward. "If X, then Y. From Y, I can Z." This is the engine.
- **Commitment** — selects and locks in. A plan that doesn't narrow the action space hasn't done anything. Output = reduction of optionality.

## Anatomy of a Planning Act

Every planning act — human or agent — has the same bones:

1. **Goal clarification** — what does done look like? Testable exit condition.
2. **World modelling** — how does the environment behave? Constraints, resources, rules.
3. **Action generation** — what moves are available? Broader repertoire = better plans.
4. **Forward simulation** — if I do X, then what? (Scenario simulation lives here)
5. **Evaluation** — is that outcome acceptable? Against what criteria?
6. **Selection** — which path do I commit to, given uncertainty?
7. **Contingency** — what if my model is wrong? The plan's immune system.

Steps 4–5 loop. Quality correlates with iteration count and evaluation honesty.

## Planning Failure Modes

More useful than the theory:

| Failure | Description | Signal |
|---------|-------------|--------|
| **Goal fog** | Planning hard on an undefined goal | Detailed irrelevance; "busy but not converging" |
| **Bad world model** | Assumptions wrong, simulation wrong | Surprise at first contact with reality |
| **Narrow simulation** | Only one scenario run forward | Plan has no contingencies |
| **Over-planning** | Plan costs more than action | Diminishing detail returns; postponing action |
| **Plan worship** | Treating plan as truth, not hypothesis | Refusing to adapt when evidence contradicts |
| **Under-commitment** | Options generated but not selected | Analysis paralysis as thoroughness |

## Planning Depth

**How far ahead?** Match planning horizon to prediction horizon.

- Stable domain (house, bridge) → plan deep
- Volatile domain (startup, market) → plan shallow, replan often
- Planning horizon should not exceed world-model shelf life

This is why agile fits software and waterfall fits construction — world model stability differs, not methodology quality.

## Human vs Agent Planning

| Dimension | Human | Agent |
|-----------|-------|-------|
| Knowledge | Tacit + explicit | Explicit only |
| Constraints | Embodied (fatigue, emotion) | Computational (context, tools) |
| Simulation | Serial, one at a time | Parallel, many paths |
| Evaluation | Rich but biased | Precise but shallow |

**Key insight:** Human planning is bottlenecked by simulation bandwidth but rich in evaluation. Agent planning is the reverse. Best hybrid: agent generates options, human evaluates and selects. Not hierarchy — complementary machinery.

## Planning as Improvable Skill

Planning improves along five axes:

1. **Goal sharpening** — fuzzy intent → testable conditions, faster
2. **Model calibration** — noticing wrong assumptions earlier
3. **Repertoire expansion** — knowing more possible moves
4. **Simulation honesty** — not letting wishful thinking corrupt projection
5. **Commitment timing** — knowing when more planning yields less

## When to Consult This Skill

- Designing a planning workflow for agents (what steps, what order)
- Evaluating why a plan failed (check failure modes table)
- Deciding how deep to plan (match prediction horizon)
- Reviewing plan quality (does it have all 7 anatomy steps?)
- Building planning into a product (human-agent split)
