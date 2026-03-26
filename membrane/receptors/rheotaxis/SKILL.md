---
name: rheotaxis
description: Search discipline for real-world facts. Use before asserting locations, hours, specs, availability, or any claim the model might confabulate.
model: sonnet
---

# Rheotaxis — search before asserting

**Rule: never assert real-world facts from model memory. Search first.**

## When this fires

Any factual claim about the physical world — store locations, opening hours, product specs, event dates, prices, availability.

## Discipline

1. **Frame 2-3 queries** from different angles. The framing that finds the answer is rarely the obvious one.
2. **Use `rheotaxis_multi` MCP tool** (or `rheotaxis` CLI) — fires all backends in parallel.
3. **Cross-check**: backends agree → state confidently. Disagree → state the conflict. None confirm → say "could not confirm."
4. **Cite** at least one URL.

## Anti-patterns

| Don't | Do |
|-------|-----|
| Assert from memory | Search first |
| One query framing | 2-3 angles |
| "Doesn't exist" | "Not found in results" |
| Trust synthesised answers alone | Cross-check against raw results |
