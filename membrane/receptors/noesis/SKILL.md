---
name: noesis
description: Web search tiering — match query urgency and cost to the right chemotaxis depth before calling.
model: sonnet
---

# Noesis — gradient-follow at the right cost

**Rule: cost must be justified by depth — default to search, escalate only when synthesis is needed.**

## When this fires

- Any factual claim that could be post-cutoff or model-confabulated (use alongside rheotaxis)
- Researching a topic where current state matters (model releases, regulatory updates, market data)
- Deep research that warrants a saved artifact (~$0.40)

## Discipline

1. **Three tiers — pick deliberately:**
   - `chemotaxis_search` (~$0.006): quick factual lookup, cited synthesis, fires fast. Default.
   - `chemotaxis_ask` (~$0.01): structured survey, more citations, better for "what are the options?" questions.
   - `chemotaxis_research` (~$0.40): deep exploration, saves to ~/genome/. Only when you'd pay $0.40 in human research time too.

2. **`chemotaxis_research` gate** — before calling, confirm: (a) the answer doesn't exist in anam/chromatin already, (b) the output will be reused across sessions (justifies saving to genome).

3. **Frame the query as a gradient** — the first framing rarely finds the answer; have 2-3 angles ready. If the first result scores poorly (short, no citations, hedged), reformulate before escalating tiers.

4. **Citations are the signal** — if a search result has < 3 URLs, treat it as weak confirmation. Cross-check or escalate.

5. **Never use noesis for personal system facts** — for how Vivesca works, use anam or read files directly. Noesis is for external world state.

## Anti-patterns

| Don't | Do |
|-------|-----|
| Default to chemotaxis_research | Default to chemotaxis_search; escalate on evidence |
| One query framing | 2-3 angles; reformulate before escalating |
| Use for internal system questions | Use for external world state only |
| Ignore citation count | Treat < 3 URLs as weak signal |
