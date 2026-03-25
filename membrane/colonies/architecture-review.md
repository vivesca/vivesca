---
name: architecture-review
description: Multi-perspective system review — security, performance, correctness, maintainability merged into one deliverable.
product: architecture review document with ranked findings
trigger: reviewing a system too complex for a single biopsy bud
---

## Lead (opus)
Synthesizes findings from workers into one ranked deliverable.
Resolves contradictions (security vs performance trade-offs).
Produces the final Architecture Biopsy document.

## Workers (sonnet, parallel)
- **security-lens**: auth, data exposure, API surface, injection vectors
- **performance-lens**: queries, loops, caching, memory, scalability
- **correctness-lens**: logic errors, edge cases, state management
- **maintainability-lens**: coupling, naming, dead code, abstraction debt

## Protocol
1. Lead scopes the review target and distributes to workers
2. Workers run in parallel (independent files/concerns)
3. Workers report findings with severity (critical/high/medium/low)
4. Lead merges, deduplicates, resolves contradictions
5. Lead ranks by operational impact, produces final document
6. Colony dissolves

## Cost gate
~$2-4 per review. Justify: is this system complex enough that one bud would miss cross-cutting concerns?
