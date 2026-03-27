---
name: etiology
description: Root-cause-first debugging — no fixes without investigation.
model: sonnet
epistemics: [debug]
---

# Etiology — Root Cause Investigation

Etiology: the study of disease causation. Treat symptoms and the disease persists.

## Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

## Four Phases

Complete each before proceeding.

### Phase 1: Root Cause Investigation

BEFORE attempting ANY fix:

1. **Read error messages** — stack traces completely, line numbers, error codes
2. **Reproduce consistently** — exact steps, every time? If not reproducible, gather more data
3. **Check recent changes** — git diff, new deps, config, environment
4. **Gather evidence at boundaries** — in multi-component systems, log what enters/exits each component. Run once. The failing boundary IS the root cause location
5. **Trace data flow** — where does the bad value originate? Keep tracing up until you find the source. Fix at source, not symptom

### Phase 2: Pattern Analysis

1. Find working examples of similar code in the codebase
2. Compare working vs broken — list every difference
3. Understand dependencies, config, assumptions

### Phase 3: Hypothesis and Testing

1. State clearly: "I think X because Y"
2. Make the SMALLEST change to test — one variable at a time
3. Didn't work? New hypothesis. Don't stack fixes

### Phase 4: Implementation

1. Create failing test case first
2. ONE fix addressing root cause — no "while I'm here" changes
3. Verify: test passes, no regressions
4. If 3+ fixes failed: STOP — question the architecture, not the symptoms

## Red Flags — Return to Phase 1

- "Quick fix for now"
- "Just try changing X"
- "It's probably X, let me fix that"
- Proposing solutions before tracing data flow
- Each fix reveals a new problem elsewhere (architectural smell)

## Boundary

- 95% of "no root cause" is incomplete investigation
- Systematic is faster than thrashing — always
