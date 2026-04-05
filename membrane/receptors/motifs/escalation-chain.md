# Escalation Chain

Try the simplest approach first. Escalate only on failure.

## Pattern

```
Tier 1: Direct/simple (free, fast, no dependencies)
  ↓ fails
Tier 2: Intermediate (some setup, moderate cost)
  ↓ fails
Tier 3: Heavy (full setup, expensive, last resort)
```

## Rules

- Always start at Tier 1. Never skip to Tier 3 because "it'll probably fail."
- Each tier must produce a clear failure signal before escalating.
- Log which tier succeeded — this becomes routing data for next time.
- The chain is the skill's decision tree. Document all tiers, not just the happy path.

## Examples

Web extraction: defuddle → Firecrawl → Jina → headless browser
Authentication: token env var → cookie bridge → headed login
Search: grep → rheotaxis → noesis → elencho (parallel multi-source)
Dispatch: sortase → ribosome → manual CC session

## When to use

Any skill that has a "try X, if that fails try Y" pattern. Especially: web access (nauta), authentication (tessera), content extraction, tool dispatch.

## Source

Reference: reference_web_extraction.md. Skills: nauta, tessera, indago.
