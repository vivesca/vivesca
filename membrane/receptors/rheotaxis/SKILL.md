---
name: rheotaxis
description: Multi-backend factual search with query reframing and cross-checking. Use for any factual claim about the real world — locations, store hours, product specs, current events.
model: sonnet
---

# Rheotaxis — sense the current before asserting

**Never assert real-world facts from memory. Search first, cross-check, then state.**

## When to invoke

- Any factual question about the real world (locations, hours, prices, specs)
- Before asserting something the model might confabulate (store locations, product availability)
- When a single WebSearch returned sparse or contradictory results
- When the user pushes back on a factual claim — escalate to multi-backend

## Protocol

### 1. Frame multiple queries

One question, 2-3 angles. The framing that finds the answer is rarely the first one you'd try.

Example — "Where is JINS near me?":
- `"JINS glasses store Hong Kong Island"`
- `"JINS Wan Chai Causeway Bay location"`
- `"JINS store locator HK 2026"`

### 2. Search across backends

Run the `rheotaxis` CLI for programmatic backends (Perplexity, Tavily, Serper):

```bash
eval "$(importin)" && rheotaxis -q "framing 1" -q "framing 2" -q "framing 3"
```

Optionally also fire WebSearch as a CC tool for a parallel signal.

**Backend strengths:**
- **Serper**: Best for local/maps queries (Google SERP data)
- **Tavily**: Returns synthesised answers, good general coverage
- **Perplexity**: Synthesised but can hallucinate — always cross-check
- **Exa**: Neural search, good for entities (may 403 — degrade gracefully)

### 3. Cross-check before asserting

- If backends agree → state with confidence
- If backends disagree → state the disagreement, cite sources
- If no backend confirms → say "could not confirm" — don't guess
- **Never** say "X doesn't exist" when you mean "X wasn't in results"

### 4. Cite sources

Always include at least one URL. The user should be able to verify.

## Anti-patterns (from the lesion that created this skill)

| Failure | Fix |
|---------|-----|
| "Cityplaza has a JINS" (confabulated) | Search before asserting ANY location |
| "No stores on HK Island" (single framing) | Try area-specific framings |
| Took 3 rounds of pushback to find answer | Multi-query upfront, not reactive |
| Perplexity said TST is on HK Island | Cross-check synthesised answers against raw results |

## Cost

Typical search: 3 queries x 3 backends = ~$0.05-0.10. Cheap insurance against confabulation.
