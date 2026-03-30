---
name: etiology
description: Root-cause diagnosis for bugs and process failures. "broken", "debug"
model: sonnet
epistemics: [debug, incident, postmortem, fix]
---

# Etiology — Systematic Diagnosis

Etiology: the study of disease causation. Treat symptoms and the disease persists.

Applies to **code failures** (bugs, regressions, errors) AND **systemic failures** (skill misfired, step got skipped, automation did the wrong thing, same mistake repeated). The process is the same — only the substrate differs.

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

0. **Gather context cheaply** — for unfamiliar components, use droid explore before burning CC tokens:
   ```bash
   droid exec -m "custom:glm-4.7" --cwd <project> "Read <files> and summarize: what it does, recent changes, dependencies, error handling patterns"
   ```
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

### Phase 6: Sweep, Risk, Immunise

Do NOT skip. These phases are where value compounds.

1. **Same-class sweep** — the bug you found is one instance. Grep for the same pattern everywhere. One correction = full sweep.
2. **Risk check** — could the fix break something? Validate (syntax check, smoke test, verify the user can still get in).
3. **Probe** — what deterministic check would detect this class of failure? integrin layer, test assertion, hook, health check. The probe is more valuable than the fix — it's amortised across all future changes.
4. **Generalise** — does the root cause reveal a principle? If the same "why?" keeps appearing across incidents, crystallise it: epistemics file for the thinking pattern, genome rule if it's universal enough. Silent failure → loud probe → permanent principle.

## Red Flags — Return to Phase 1

- "Quick fix for now"
- "Just try changing X"
- "It's probably X, let me fix that"
- Suggesting install/workaround before verifying the thing exists
- Proposing solutions before tracing data flow
- Each fix reveals a new problem elsewhere (architectural smell)
- Declaring done without sweep/risk/prevent

## Systemic Failures (not code — organism/process)

Same six phases, different substrate. When a skill misfires, a step gets skipped, or the organism fails:

### System or operator?

Default assumption: **system fault.** Ask in order:
1. **Was the step easy to skip?** (separate section, optional-sounding, buried) → fix the skill structure
2. **Was the automation wrong?** (syncing to wrong dir, repopulating deleted state) → fix the automation
3. **Was the protocol ambiguous?** (cross-model mining as detached section) → fold into numbered flow
4. Only if 1-3 are no: **operator error** → file feedback memory

### Trace the chain

Don't stop at the proximal cause. Trace back 3 steps:
- `.gemini/skills/` repopulated → (1) I deleted it, (2) I didn't check for automation, (3) phenotype_translate was force-syncing there
- I skipped cross-model mining → (1) I did a single-model mine, (2) endocytosis had it as a detached section, (3) the skill's structure made it optional-looking

The deepest link in the chain is where the fix belongs.

### Escalation from incident to principle

| Occurrence | Action |
|---|---|
| First time | Fix the instance, note as hypothesis |
| Second time | Look for structural cause, consider a rule |
| Third time | Mandatory system change — hook, automation, or constraint. No more notes. |

## Boundary

- 95% of "no root cause" is incomplete investigation
- Systematic is faster than thrashing — always
