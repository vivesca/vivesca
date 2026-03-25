# Systematic Debugging Patterns

Distilled from [obra/superpowers](https://github.com/obra/superpowers) systematic-debugging skill.

## Four Phases

1. **Root Cause Investigation** — before ANY fix attempt
   - Read error messages completely (stack traces, line numbers, exit codes)
   - Reproduce consistently — if not reproducible, gather more data, don't guess
   - Check recent changes (`git diff`, new deps, config changes)
   - In multi-component systems: add diagnostic logging at each boundary, run once, identify which layer breaks

2. **Pattern Analysis**
   - Find working examples of similar code in the same codebase
   - Compare working vs broken — list every difference
   - Understand dependencies and assumptions

3. **Hypothesis Testing**
   - State clearly: "I think X because Y"
   - Make the SMALLEST change to test — one variable at a time
   - Didn't work? New hypothesis. Don't stack fixes.

4. **Implementation**
   - Fix the root cause, not the symptom
   - ONE change at a time, no "while I'm here" improvements

## The 3-Fix Escalation Rule

After 3 failed fix attempts: **STOP and question the architecture.**

Signals of an architectural problem (not a bug):
- Each fix reveals new shared state/coupling
- Fixes require "massive refactoring"
- Each fix creates new symptoms elsewhere

At this point: discuss with the user. This is a wrong architecture, not a failed hypothesis.

## Red Flags (Return to Phase 1)

- "Quick fix for now, investigate later"
- "Just try changing X and see"
- Proposing solutions before tracing data flow
- "I don't fully understand but this might work"
- Adding multiple changes at once

## Data Flow Tracing (Multi-Component)

When error is deep in a call stack:
```
Where does the bad value originate?
  → What called this with the bad value?
    → Keep tracing up until you find the source
      → Fix at source, not at symptom
```

For multi-layer systems (CI → build → signing, API → service → DB):
```
For EACH component boundary:
  - Log what enters
  - Log what exits
  - Run once → find WHERE it breaks
  - THEN investigate that specific component
```
