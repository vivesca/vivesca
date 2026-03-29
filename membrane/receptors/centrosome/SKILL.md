---
name: centrosome
description: Batch-dispatch tasks to droid, monitor completions, review output, write coaching notes.
model: opus
user_invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
context: fork
epistemics: [delegate, review]
---

# /centrosome — Batch Dispatch & Monitor

CC designs specs. Droid executes. CC reviews and coaches. 20-40x token savings vs doing it all in-session.

Biology: the centrosome organizes the mitotic spindle, coordinating work distribution to daughter cells. Here, CC is the centrosome — it doesn't do the work, it designs, dispatches, monitors, and learns.

## When to Use

- Batch of 3+ tasks that droid can handle (code edits, scripts, audits)
- Overnight or background execution while user does other work
- Any time CC token budget matters more than speed
- Stress-testing a backend with coaching feedback

**Not for:** single tasks (use `/folding`), planning/prose (route to gemini/codex), tasks needing live decisions.

## Inputs

Accept any of:
- A list of task descriptions from the user
- A backlog file (praxis.md, consolidation plan, etc.)
- "Queue up N tasks for droid" — CC selects from known backlog

## Phase 1: Spec Design (the expensive thinking)

Write one plan file per task in `/tmp/centrosome-<session>/`. This is where CC tokens go — precise specs yield fast, reliable droid execution.

### Spec quality rules

| Element | Effect on droid |
|---------|----------------|
| Exact before/after code snippets | ~37s, near-100% success |
| Clear instructions, file paths, no code | ~120s, high success |
| Open-ended analysis/prose | Fails, falls back to codex |

**Always:**
- Inline the actual instructions (never "read this file and do what it says")
- Specify exact file paths to edit
- Include a verification command (`python3 -c "import ast; ..."`, test command, etc.)
- Add a "Do NOT" section to constrain scope

**Template:**
```markdown
# Task title

In `<exact file path>`, <what to change>.

## What it does
<3-5 bullet points>

## Implementation
<Exact code or precise instructions>

## Do NOT
- <Constraint 1>
- <Constraint 2>

## Verification
<Command to run after>
```

## Phase 2: Dispatch Chain

Queue tasks sequentially via background execution:

```bash
sortase exec /tmp/centrosome-<session>/<plan>.md -p <project> -b droid -v --timeout 300
```

Use `run_in_background` for each task. On completion notification:

1. Read the output (tail last 15-20 lines)
2. Verify syntax/tests if applicable
3. Note coaching observations
4. Dispatch next task

**Do NOT parallelize** unless tasks touch different projects. Droid changes accumulate in the working tree.

## Phase 3: Review & Coach

After each task completion:

### Quick review checklist
- [ ] Exit code 0 + "Success=True"
- [ ] Syntax verification passes
- [ ] No unexpected file changes (check git diff if concerned)
- [ ] Output makes sense (droid sometimes "succeeds" with wrong approach)

### Coaching extraction

Watch for these known GLM-5.1 failure patterns:
- Import hallucination (invents modules)
- Return type flattening (collapses distinct types)
- Verbose descriptions (defeats token economy)
- `str(dict)` rendering (raw repr instead of formatted)
- File indirection failure (reads but doesn't execute)

If a new pattern appears, append to `~/epigenome/marks/feedback_glm_coaching.md`:
```markdown
### Pattern name
GLM does X.
**Fix:** "Instruction to avoid X."
```

The `_analyze_for_coaching` hook in sortase also does this automatically via `channel`, but CC's review catches subtler patterns.

## Phase 4: Report

After all tasks complete, produce a summary:

| # | Task | Backend | Duration | Status |
|---|------|---------|----------|--------|
| ... | ... | ... | ...s | ok/failed |

Note:
- Total wall time
- Success rate
- Any fallbacks triggered
- New coaching entries written
- Files that need committing

## Overnight Mode

If the user is going to sleep:

1. Run `caffeinate -d` to prevent Mac sleep
2. Dispatch all tasks in chain (background notifications keep the session alive)
3. Write coaching notes between tasks
4. Produce summary report — user reads it in the morning

## Token Budget

Approximate per task:
- Spec writing: ~500-1000 tokens
- Output review: ~500 tokens
- Coaching note: ~200 tokens
- **Total: ~1.5-2K CC tokens per task**

vs headless CC doing the work: ~50-100K tokens per task.

## Backend Selection

| Task type | Backend | Reason |
|-----------|---------|--------|
| Code edits with exact spec | droid | Fastest (P50: 58s), free |
| From-scratch scripts | droid | Reliable with good specs |
| Read-only audits | droid | Correctly identifies "no action needed" |
| Planning/analysis/prose | gemini or codex | GLM-5.1 fails on open-ended tasks |
| Rust code | codex | Sandbox + language strength |

## Hard Rules

- **Spec quality is the bottleneck.** Invest CC tokens here, not on execution.
- **One task per plan file.** Don't bundle.
- **Verify after each task.** Don't batch-verify at the end.
- **Write coaching notes in-flight.** Don't wait for the batch to finish.
- **Chain sequentially.** Background notification → review → next. Don't fire-and-forget all at once.
