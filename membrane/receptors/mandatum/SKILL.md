---
name: mandatum
description: Delegation theory — spec quality, decomposition depth, when ambiguity helps vs hurts. Use when writing delegate specs or debugging poor delegation results. "delegation theory"
version: 1
tags: [reference, delegation, cognition, agents]
disable-model-invocation: true
---

# Mandatum — Theory of Delegation

> *Mandatum: Latin "commission, charge" — the act of entrusting a task to another.*

Delegation is **transferring execution while retaining accountability**. The quality of delegation is almost entirely determined by the quality of the spec.

Reference skill. Consult when writing delegate specs, when delegation results disappoint, or when deciding decomposition depth.

## The Principal-Agent Problem

Principal (you) and agent (delegate) have different information. With humans, also different incentives. With AI, incentive gap disappears but information gap is worse — the AI works from a lossy compression of what you meant.

**Implication:** the spec is the entire interface. Every gap in the spec is a place where the delegate's default diverges from your intent.

## What Makes a Good Spec

Three questions, in order:

1. **What does done look like?** — testable acceptance criteria. Not what to do, but what the result must satisfy.
2. **What's off the table?** — constraints. What NOT to do is often more important. Prevents solving a different problem.
3. **What context would a stranger need?** — minimum viable context. Things not discoverable from code: architecture decisions, naming conventions, past-attempt gotchas.

**NOT on the list: how to do it.** Specifying implementation = most common delegation mistake. Produces worse results, costs more time, makes delegate brittle.

## When Ambiguity Helps

- **Tight problems** (fix this bug) → tight spec. Test should pass.
- **Open problems** (build a CLI) → **specify ends tightly, leave means loose.** "Output must be valid JSON with these fields" + "use whatever parsing works."
- **Exception:** when delegate lacks ecosystem context → specify means to prevent architecturally incompatible choices. This is what AGENTS.md files are for.

## Delegation Depth

| Level | Problem | Signal |
|-------|---------|--------|
| **Too coarse** | Delegate makes architectural decisions without context | Reasonable but wrong structural choices |
| **Too fine** | You've done all intellectual work, delegation saves only typing | You specified the function signature |
| **Right** | One clear deliverable, implementation decisions but not architectural ones | Delegate thinks about *how* but not *what* or *why* |

Maps to `bouleusis`: delegate at the boundary where your world model is reliable (architecture) but theirs can operate (implementation).

## Failure Modes

| Failure | Description | Signal |
|---------|-------------|--------|
| **Spec amnesia** | Omitting context you know but delegate doesn't | "Obvious" mistakes that need your context |
| **Implementation prescription** | Specifying how, not what | Delegate can't adapt to obstacles |
| **Over-decomposition** | Pieces too small for coherent intent | Questions about how pieces fit |
| **Under-decomposition** | Architectural decisions delegated | Wrong structural choices |
| **Verification gap** | No way to check result mechanically | "Looks right" instead of "test passes" |
| **Delegation theater** | Delegating then watching/re-doing | More time than doing it yourself |
| **Context hoarding** | "Faster to do it myself" | Bottleneck, no leverage |

## The Feedback Loop

Delegate → inspect result → identify spec gap → improve future specs. Delegate mistakes are spec failures.

Over time: AGENTS.md files, skill files, conventions docs — persistent context loaded automatically. The spec improves even when you don't write it.

## Human vs AI Delegation

- **Humans:** compensate for bad specs via questions, shared context, cultural norms
- **AI:** executes spec literally. Every ambiguity resolved by training distribution, not by asking.
- AI requires better specs but produces more consistent results
- **Leverage:** AI delegates are parallelizable. Better spec ROI = saves all N runs, not just one.

## When to Consult This Skill

- Writing a delegate spec (rector Step 3–4)
- Delegation result was poor — check failure modes
- Deciding how coarsely to decompose work
- Writing AGENTS.md or persistent delegate context
