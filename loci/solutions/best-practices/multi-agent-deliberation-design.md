---
module: Multi-Agent Systems
date: 2026-02-05
problem_type: best_practice
component: skill
symptoms:
  - "Multi-agent councils reach premature consensus"
  - "Debate lacks genuine disagreement"
  - "Devil's advocate roles feel performative"
  - "All agents converge to same position within 1-2 rounds"
  - "Judge evaluates its own arguments (conflict of interest)"
root_cause: mental_model_error
resolution_type: process_change
severity: medium
tags: [multi-agent, deliberation, llm-council, debate, frontier-council, consensus, disagreement]
related_files:
  - /Users/terry/skills/frontier-council/SKILL.md
---

# Multi-agent deliberation: sustaining productive disagreement

## Problem

Multi-agent deliberation systems (where multiple LLMs debate a question) suffer from premature convergence. LLMs are trained to be agreeable and find common ground — the opposite of what creates valuable debate. Common failure patterns:

1. **Judge-as-participant conflict**: If the same model both debates and judges, it evaluates its own arguments favorably
2. **Redundant roles**: "Devil's advocate" and "challenger" roles sound different but behave identically
3. **Role decay**: Special roles only fire in round 1, then models revert to agreeable defaults
4. **Anchoring bias**: Serial speaking order causes later speakers to anchor on earlier arguments
5. **Natural convergence**: Despite prompts to disagree, LLMs default to "I largely agree with X, but..."

## Root Cause

LLMs are fundamentally trained to be helpful and agreeable. Asking them to disagree via prompting fights against their fine-tuning. The disagreement needs to be structural, not just prompted.

## Solution: Structural Disagreement

### 1. Separate judge from deliberators

Bad:
```
Council: [Claude, GPT, Gemini, Grok]
Judge: Claude (same as participant)
```

Good:
```
Council: [GPT, Gemini, Grok, Kimi]  # 4 deliberators
Judge: Claude Opus 4.5              # Judge-only, never deliberates
```

The judge should synthesize AND contribute original perspective ("Judge's Own Take") rather than just summarize.

### 2. Rotating challenger, not static roles

Bad:
```python
# Devil's advocate AND challenger — redundant
devil_advocate = council[0]  # Always round 1 only
challenger = council[1]      # Never rotates
```

Good:
```python
# Single challenger role that rotates
challenger_idx = (initial_challenger + round_num) % len(council)
challenger = council[challenger_idx]
```

Rotation ensures someone is always playing challenger fresh, not decaying into agreeable mode.

### 3. Explicit prompt constraints for challengers

Weak prompt:
```
You should challenge the consensus and play devil's advocate.
```

Strong prompt:
```
CRITICAL: You are the designated challenger this round.

Requirements:
- You MUST identify weaknesses in the strongest argument so far
- You MUST propose an alternative that others haven't considered
- You MAY NOT start with "I largely agree" or similar hedging
- If you find yourself agreeing, dig deeper until you find genuine disagreement
```

### 4. Exclude challenger from consensus detection

If the challenger is forced to disagree, their disagreement shouldn't block early consensus exit:

```python
def check_consensus(positions, challenger_id):
    # Exclude forced disagreement from consensus check
    non_challenger_positions = [p for p in positions if p.model_id != challenger_id]
    return all_agree(non_challenger_positions)
```

### 5. Use naturally contrarian models strategically

Some models are more naturally contrarian (e.g., Grok). Layer this with explicit challenger prompting:
- **GPT as default challenger**: Practical skepticism + explicit contrarian framing
- **Grok as natural contrarian**: Pushes back regardless of role assignment
- Result: Two sources of pushback (prompted + natural)

## Prevention Strategies

When designing multi-agent deliberation systems:

1. **Ask "What creates genuine tension?"** — Disagreement should be structural, not just prompted
2. **Test for convergence speed** — If all models agree within 1-2 rounds, the design is broken
3. **Separate synthesis from participation** — The entity that judges shouldn't be defending its own position
4. **Rotate adversarial roles** — Static roles decay; rotation keeps pushback fresh
5. **Strengthen disagreement prompts explicitly** — "You MAY NOT agree" is stronger than "You should challenge"
6. **Measure dissent quality** — Track whether challengers surface genuinely new concerns or just restate known risks

## Testing Your Design

Indicators of healthy disagreement:
- Debate continues past round 2 with genuine new arguments
- Challenger surfaces concerns not raised by others
- Final synthesis includes non-trivial dissents
- Judge's own take adds perspective not present in debate

Indicators of premature convergence:
- "I largely agree with [previous speaker]" appearing regularly
- Challenger arguments repeat what others said
- Debate converges to same conclusion as parallel (non-debate) asking
- Dissent section is empty or trivial

## Related

- Skill: `/frontier-council` — Implementation of these patterns
- Pattern: [Structured disagreement in AI systems](https://www.anthropic.com/research/collective-intelligence)
- Book: "Superforecasting" — Importance of adversarial reasoning in prediction
