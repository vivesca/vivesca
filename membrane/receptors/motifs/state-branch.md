# State-Gather-Then-Branch

Gather all state before deciding which path to take. Never interleave checks with actions.

## Pattern

```
Step 1: Gather state (run all checks in parallel)
  1. Check A
  2. Check B  
  3. Check C

Step 2: Branch on combination
  A + B     → Method 1 (self-contained)
  A + not B → Method 2 (self-contained)
  not A     → Method 3 (self-contained)
```

## Rules

- Checks are cheap and parallel. Run all before deciding.
- Each branch is self-contained. No "see above" cross-references.
- Branches are exhaustive. Every state combination has a path.
- The last branch is the fallback for the worst case.
- Use ### headings as the branching mechanism, not nested if/else prose.

## When to use

Any skill with 3+ execution paths. Examples: deploy (linked/unlinked/no-auth), dispatch (single/batch/overnight), auth (token/OAuth/cookie).

## Source

Extracted from vercel-labs/agent-skills deploy-to-vercel. Codified as organogenesis principle #22.
