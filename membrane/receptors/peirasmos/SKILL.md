---
name: peirasmos
description: Theory of experimentation for AI/LLM engineering — question design, confound detection, dual-purpose runs, evaluation. Reference skill consulted by peira, judex, and any experimental task.
user_invocable: false
disable-model-invocation: true
---

# Theory of Experimentation

> *Peirasmos: Greek "trial, test" — the act of putting something to proof.*

Stable principles for designing, running, and evaluating experiments on LLM systems. Complements `peira` (the execution engine) with the theory of what makes an experiment valid.

## The Question Hierarchy

Weak → strong:

1. **"Does X work?"** — binary, almost always yes-ish. Uninformative.
2. **"When does X work?"** — conditional. Identifies the boundary. Useful.
3. **"Why does X work when it does?"** — mechanistic. Reveals the causal variable. Publishable.

Always push past level 1. If your experiment can only answer "does X work?", redesign it.

## Single-Variable Isolation

The only experiments that teach you something: **one variable changes, everything else is held constant.**

When you think you've isolated one variable, check:
- Is the framework injecting something? (CrewAI adds persona framing even with empty fields)
- Is the variable confounded with length? (richer prompt → more output → looks "better")
- Is the variable confounded with cost? (better model ≠ better prompt technique)
- Are you comparing implementations or ideas? (CrewAI-with-personas vs raw-API-without is testing two things)

## The Confound Checklist

Before concluding, check each:

| Confound | Test |
|----------|------|
| **Framework injection** | Read the actual prompt sent to the API, not what you configured |
| **Verbosity = quality illusion** | More words ≠ better. Count distinct findings, not lines |
| **Model variance** | Run the same config 3x. If outputs differ meaningfully, n=1 is worthless |
| **Evaluator bias** | You know which is which. Blind the evaluation or use a judge model |
| **Task specificity swamping** | If the task prompt already specifies everything, the variable you're testing has no room to matter |
| **Capability ceiling** | Frontier models may be insensitive to your variable. Test on weaker models too |
| **Survivorship in reporting** | You notice what's different. What's the same across both runs? That's probably doing the real work |

## Dual-Purpose Design

Every experiment should produce:
1. **Scientific output** — did the hypothesis hold? What's the finding?
2. **Practical output** — a deliverable, a tool, a reference, a draft

Design experiments around real work. "Test persona effect on HSBC risk tiering P&P" produces both a finding AND a draft deliverable for Simon. Pure toy experiments (testing on "Is water wet?") waste the run.

## The Experimental Loop

```
Hypothesis → Design (single variable) → Pre-flight (check confounds) →
Run → Observe →
  → Surprising result? → Mine the surprise. The REAL question is hiding here.
  → Expected result? → Was the test valid? Check confounds before celebrating.
  → Null result? → This IS a finding. "No difference" changes what you build.
→ Record → Next experiment (informed by this one)
```

Each experiment's result should shape the next experiment's hypothesis. Sequential experiments > parallel experiments for learning (but parallel is fine for speed when hypotheses are independent).

## What Makes a Good LLM Experiment Question

- **Testable with API calls** — not philosophical, not taste-based
- **Has a measurable comparison** — A vs B, not just "is A good?"
- **The answer would change what you build** — if you'd build the same thing regardless, don't run the experiment
- **Confounds are identifiable** — you may not eliminate all of them, but you should be able to name them
- **The null result is informative** — "personas don't help" is as actionable as "personas help"

## Failure Modes

| Failure | Description | Fix |
|---------|-------------|-----|
| **Measuring the wrong thing** | Output length, word count, finding count as proxy for quality | Define quality criteria before running, not after |
| **Premature conclusion** | n=1 with strong narrative feels conclusive | Always state n and limitations. "Suggestive, not conclusive" |
| **Framework worship** | Using CrewAI because it's "proper" when raw API calls isolate better | Choose the tool that isolates your variable, not the fanciest tool |
| **Ignoring null results** | "No difference" feels like a failed experiment | No difference IS the finding. It saves you from building something useless |
| **Over-designing before running** | Perfect experimental plan, never executed | One dirty run teaches more than one perfect plan. Run first, refine second |
| **Narrative over evidence** | The story is compelling but the evidence is weak | Ask: "what would change my mind?" If nothing would, you're not experimenting |
| **Optimising the wrong level** | Tuning model selection when the prompt is the bottleneck | Identify which layer (model, prompt, framework, pipeline) has the most variance first |

## Evaluation Principles

- **Define criteria before running** — post-hoc criteria are biased by what you see
- **Blind when possible** — strip labels, randomise order, use judge model
- **Count distinct findings, not output volume** — a 200-line table with 41 findings > a 900-line narrative with 34
- **Compare intermediate outputs, not just final** — the pipeline may compensate for early weakness
- **The alternative hypothesis test** — before concluding X works, ask: could a simpler explanation (just adding one sentence to the prompt) achieve the same result?

## Known Findings (from experiments)

Empirically tested, directionally confirmed. Cite with caveats (n=1-2, single judge family).

| Finding | Rule | Source |
|---------|------|--------|
| **Persona effect is task-dependent** | Use personas for judgment-heavy tasks (gap analysis, assessment). Skip for structured output (policy docs, templates). | 2 experiments, blind-evaluated, Mar 2026 |
| **Personas amplify confident hallucination** | Persona runs generate fabricated institutional details (fake document names, false precision) that LLM judges score as "depth." | Verified: "Amy chatbot" real, "Group AI Governance Standard v2.1" fabricated |
| **Personas + LLM-as-judge is adversarial** | Don't use personas if your quality gate is automated LLM evaluation. The combination systematically inflates scores. Safe with human domain expert review. | Blind judge rewarded hallucinated specificity equally with real |
| **Mixed-model teams outperform homogeneous** | Use different vendors (not just different sizes). The debate/cross-critique round is where value emerges, not parallel-then-merge. | MoA ICLR 2025, X-MAS May 2025, own experiment Mar 2026 |

Full data: [[Persona vs Procedure Experiment Results]], [[Multi-Agent Mixed-LLM Research Synthesis]]

## Relationship to Other Skills

- **peira** — the execution engine for running experiments. Peirasmos provides the theory; peira provides the loop.
- **judex** — "can this be measured?" gate. Peirasmos assumes yes; judex decides whether to measure at all.
- **quorate** — for judgment calls where experiments aren't feasible. Peirasmos is for when they are.
- **topica** — mental models catalog. Experimental thinking is a meta-model that applies across domains.
- **examen** — premise audit. Run before experiments to surface load-bearing assumptions.
