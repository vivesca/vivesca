---
name: palpation
description: Deep-probe a single component by hand — deeper than integrin scan. Use when a specific subsystem needs manual investigation. "deep probe", "palpation", "investigate component"
user_invocable: true
model: sonnet
context: fork
---

# Palpation — Manual Deep Probing

A physician palpates: hands on the body, applying pressure, feeling for rigidity, tenderness, masses. Not instrument-mediated — direct contact, manual sensitivity, depth through pressure.

Palpation is targeted manual investigation of a specific organism component. You already know where to look (from auscultation, or integrin, or a hunch). Now you go in with your hands.

## When to Use

- Auscultation identified a concerning sound in a specific area
- A component is behaving unexpectedly and automated probes haven't caught it
- A bug report points to a specific subsystem
- Pre-surgery: before refactoring a component, manually verify its actual behavior
- Suspicion without evidence — palpation either confirms or clears

## Method

### Step 1 — Name the component under investigation

Be precise: not "the intake pipeline" but "the transduction job's extraction step for RSS items from feed X." Specificity determines probe depth.

### Step 2 — Read the component fully

**Use droid explore for initial read** — free recon before CC applies judgment:
```bash
ribosome -m "custom:glm-4.7" --cwd <project> \
  "Read <component files>, config, and recent logs. Summarize: architecture, dependencies, hardcoded paths, error handling, recent output patterns."
```

Then CC reads the droid summary and probes deeper only where needed. Don't burn CC tokens reading 500 lines when droid can summarize for free.

No probing without reading. Palpating without reading is guessing.

### Step 3 — Apply pressure (active probing)

Run the component in isolation with known inputs:
```bash
# Dry run / debug mode
python3 component.py --debug --input test_fixture

# Trace execution
python3 -m trace --trace component.py 2>&1 | head -100

# Check what it actually calls
strace / dtrace / logging instrumentation

# Test with edge case input
python3 component.py --input edge_case_fixture
```

### Step 4 — Feel for resistance

Resistance signals:
- Unexpected exceptions on valid input
- Slow response on simple cases (CPU? I/O? network?)
- Output that doesn't match input transformation spec
- State that persists unexpectedly between invocations
- Silent success with wrong output (the hardest to find)

### Step 5 — Document what you found

Palpation finding format:
```
Component: [name]
Input tested: [what you fed it]
Expected behavior: [what the spec says]
Observed behavior: [what actually happened]
Tenderness location: [the specific line / condition / state]
Severity: [blocks operation / degrades / cosmetic]
```

### Step 6 — Hand off to repair or clear

If finding confirmed: hand off to the appropriate repair skill (thrombin if urgent, debridement if dead tissue, direct fix if known).

If cleared: document the clearance. "Palpated [component] on [date]. No findings. Behavior matches spec." Negative results are data.

## Palpation vs Auscultation vs Integrin

| Skill | Trigger | Approach | Output |
|-------|---------|----------|--------|
| auscultation | Routine / anomaly detected | Passive listening | Soundscape + patterns |
| integrin | Scheduled / systematic | Automated probes | Health signal |
| palpation | Targeted suspicion | Manual deep-probe | Specific finding or clearance |

## Anti-patterns

- **Palpating without reading:** jumping to active probing without understanding what the component is supposed to do.
- **Palpating everything:** palpation is targeted. If you don't know what you're feeling for, use auscultation first.
- **Forgetting to clear:** a cleared component is as important as a finding. Document both.
