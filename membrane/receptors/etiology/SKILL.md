---
name: etiology
description: Systematic diagnosis — broken, stopped working, not found, regression, error, bug, debugging.
model: sonnet
epistemics: [debug]
---

# Etiology — Systematic Diagnosis

Etiology: the study of disease causation. Treat symptoms and the disease persists.

## Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

## Six Phases

Complete each before proceeding.

### Phase 1: Intake — Frame the Problem

BEFORE investigating:

1. **Classify**: Is this a regression ("worked before"), a new issue, or a misunderstanding?
2. **Regression? → diff what changed.** Never suggest reinstalling or workarounds. Check git history, config changes, recent migrations, env changes.
3. **"Command not found"? → check it exists** before suggesting install. Verify PATH, shell context (interactive vs non-interactive), aliases.
4. **Reproduce consistently** — exact steps, every time? If not reproducible, gather more data.

### Phase 2: Root Cause Investigation

BEFORE attempting ANY fix:

1. **Read error messages** — stack traces completely, line numbers, error codes
2. **Check recent changes** — git diff, new deps, config, environment
3. **Gather evidence at boundaries** — in multi-component systems, log what enters/exits each component. Run once. The failing boundary IS the root cause location
4. **Trace data flow** — where does the bad value originate? Keep tracing up until you find the source. Fix at source, not symptom

### Phase 3: Pattern Analysis

1. Find working examples of similar code in the codebase
2. Compare working vs broken — list every difference
3. Understand dependencies, config, assumptions

### Phase 4: Hypothesis and Testing

1. State clearly: "I think X because Y"
2. Make the SMALLEST change to test — one variable at a time
3. Didn't work? New hypothesis. Don't stack fixes

### Phase 5: Implementation

1. Create failing test case first (when applicable)
2. ONE fix addressing root cause — no "while I'm here" changes
3. Verify: test passes, no regressions
4. If 3+ fixes failed: STOP — question the architecture, not the symptoms

### Phase 6: Sweep, Risk, Prevent

Do NOT skip. These phases are where value compounds.

1. **Same-class sweep** — the bug you found is one instance. Grep for the same pattern everywhere. One correction = full sweep.
2. **Risk check** — could the fix break something? Validate (syntax check, smoke test, verify the user can still get in).
3. **Prevention** — what structural change stops this class of bug from recurring? Comment guards, linter rules, hook enforcement. If nothing structural works, at minimum document why.

## Red Flags — Return to Phase 1

- "Quick fix for now"
- "Just try changing X"
- "It's probably X, let me fix that"
- Suggesting install/workaround before verifying the thing exists
- Proposing solutions before tracing data flow
- Each fix reveals a new problem elsewhere (architectural smell)
- Declaring done without sweep/risk/prevent

## Boundary

- 95% of "no root cause" is incomplete investigation
- Systematic is faster than thrashing — always
