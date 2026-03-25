---
module: AI Tooling
date: 2026-02-06
problem_type: best_practice
component: cli_tool
symptoms:
  - "Judge recommends 6 action items while saying 'minimum effective change'"
  - "Judge's diagnosis contradicts its own prescription"
  - "Council deliberation momentum pulls synthesizer into aggregation"
root_cause: mental_model_error
resolution_type: process_change
severity: medium
tags: [frontier-council, llm-council, judge-prompt, aggregation-bias, prompt-engineering]
related_files:
  - ~/code/frontier-council/frontier_council/council.py
  - ~/skills/frontier-council/SKILL.md
---

# LLM Council Judge Over-Aggregation

## Problem

The frontier-council judge (Claude Opus 4.5) correctly *diagnoses* the situation but *prescribes* too many actions. In a CV review session, the judge wrote "minimum effective change is the goal" and then recommended 6 changes including a title swap and summary rewrite.

The pattern: 4 council models produce detailed, confident suggestions → the volume creates gravitational pull → the judge aggregates instead of filtering → the output is a wish list, not a recommendation.

## Why It Happens

1. **Deliberation momentum.** Each council model generates 3-5 specific suggestions with justification. By the time the judge sees 15-20 suggestions, the implicit framing is "which of these excellent ideas should we include?" rather than "which of these are actually necessary?"
2. **Synthesizer bias.** The judge is prompted to "synthesize" — which defaults to inclusion, not exclusion. Synthesis ≠ filtering.
3. **No prescription budget.** Without a hard cap, there's no forcing function for prioritisation. Every suggestion can be rationalised as "worth doing."

## Solution

Added "Prescription Discipline" section to the judge system prompt in `council.py`:

```
CRITICAL — PRESCRIPTION DISCIPLINE:
Your job is to FILTER, not aggregate.

Rules:
- "Do Now" — MAX 3 items. For each, argue AGAINST including it first.
  Only include if it survives your own counter-argument.
- "Consider Later" — Items interesting but not worth doing now
- "Skip" — Explicitly list council suggestions you're DROPPING and why

The council's gravitational pull is toward "add more."
Your gravitational pull must be toward "do less."
A recommendation with 6 action items is not a recommendation — it's a wish list.
```

Key mechanisms:
- **Hard cap (3)** forces prioritisation
- **Argue against before including** creates friction against aggregation
- **Explicit "Skip" section** makes dropping visible (harder to silently include everything)

## Meta-Pattern for Callers

When presenting council results to the user:

1. **Trust the judge's framing over its action list.** If the framing says "mostly fine, small adjustments" but lists 6 items, the framing is right.
2. **Apply your own filter.** The council's value is in the *insights* (false-negative gap in AML metrics, translator USP), not in the action count.
3. **Match prescription to context.** "Simon already likes you" means the CV supports a decision already made — that's a 2-3 item fix, not a 6-item rewrite.

## Prevention

- When designing any multi-agent synthesis step, include an explicit cap on output actions
- Prompt the synthesiser to argue against its own recommendations before including them
- Elevate key constraints to "hard constraints" that the judge must reference, not just mention

## Verification

Next council invocation should produce a judge output with:
- Max 3 "Do Now" items
- Explicit "Skip" section listing dropped suggestions
- Each recommendation surviving an internal counter-argument
