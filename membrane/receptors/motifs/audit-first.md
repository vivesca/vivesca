# Audit-First Implementation

Before modifying anything, produce a map of what exists. The map IS the spec.

## Pattern

```
Step 1: Audit — scan and produce a table

| Current State | Target State | Pattern to Apply |
|---------------|-------------|-----------------|
| (what exists) | (what we want) | (how to get there) |

Step 2: Execute against the table, row by row
Step 3: Verify each row was applied correctly
```

## Rules

- Step 1 must complete before Step 2 starts. No interleaving.
- The table is the deliverable of Step 1 — show it to the user before proceeding.
- Every row in the table must be addressed in Step 2. No silent skips.
- Step 3 re-reads the targets and confirms the change landed.

## When to use

Any skill that transforms existing state: renames (transposase), migrations, regulatory audits, refactoring, configuration changes. If you're modifying N things, audit all N first.

## Source

Extracted from vercel-labs/agent-skills implementation.md (view transitions). Codified in organogenesis REFERENCE.md.
