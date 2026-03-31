---
name: centrosome
description: Write specs, batch-dispatch to goose/droid, review, coach. The full dispatch lifecycle. "batch", "dispatch", "spec", "build"
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
epistemics: [plan, delegate, build, review]
---

# /centrosome — Dispatch Lifecycle

CC designs specs. Goose/droid executes. CC reviews and coaches. One entry point for all delegated work.

Biology: the centrosome organizes the mitotic spindle, coordinating work distribution to daughter cells.

## When to Use

- "Build", "implement", "spec this", "dispatch", "add a feature", "batch"
- After `/transcription` when design is approved
- Proactively when user asks to build, port, fix, refactor, or add a feature
- **Not for:** single-file trivial edits (do directly), planning/prose (route to gemini), tasks needing frontier reasoning

## Pre-flight

### North star orientation

Before selecting what to dispatch, read `~/epigenome/chromatin/North Star.md`. Ask: "which north star does this batch serve?" If the answer is only #6 (maintain the system), ask: "does this measurably improve throughput on #1-5?" Unlimited tokens doesn't mean spray everywhere — it means do the highest-value work thoroughly.

### Weight class

| Task size | Route |
|-----------|-------|
| **Trivial** (<=20 lines, single file) | Build directly in-session, skip spec |
| **Unclear requirements** | `/transcription` first, then return here |
| **Everything else** | Full pipeline (below) |

### Checks

- **Protected paths:** genome.md and epigenome/marks/ are CC-only. NEVER dispatch goose to edit these.
- **Naming:** name before code. `lysin "<term>"` for bio names.
- **Parallel sessions?** → `lucus new <branch>` first.

## Phase 1: Spec Design

Batch-write 5-6 specs to `~/germline/loci/plans/` in one burst. **Never write-one-dispatch-one.** While goose runs batch N, write batch N+1.

### Spec template

```markdown
---
status: ready
---

# <Name> -- <one-line description>

## Context
What exists. What's changing. Why.

## Task 1: <verb> <object>
Exact instructions. Absolute file paths. Before/after snippets for files >200 lines.

## Task N: Run tests
MANDATORY last task.
\```bash
cd ~/germline && uv run pytest <test_file> -x
\```

## Constraints
- Write tests BEFORE implementation (TDD red/green)
- Specs to ~/germline/loci/plans/, never /tmp
- Scripts must be Python (nociceptor)
- Do NOT <scope constraint>

## Passing Criteria
- [ ] All tests pass -- paste output
- [ ] <specific verify command>
```

### Spec quality tiers (measured)

| Spec type | P50 duration | Success rate |
|-----------|-------------|--------------|
| Exact before/after code | **20-40s** | ~100% |
| Clear instructions + file paths | **60-120s** | ~95% |
| Multi-file sweep | **120-290s** | ~90% |
| From-scratch script | **100-140s** | ~90% |
| Open-ended analysis/prose | **fails** | ~0% |

### Signals that predict success

- "YOUR ONLY JOB: write one file" — highest for content tasks
- "EXACTLY 1 tool call: write_file" — prevents turn exhaustion
- "Do NOT read any files" — for generative tasks
- Explicit output path (absolute)
- `--timeout 600` for ambitious tasks

### Signals that predict failure

- "Read these 3 source files then produce X" — exhausts turns reading
- Append to large existing file (>200 lines) — unreliable past ~56 items
- No explicit output path
- Route everything through `-p ~/germline` (coaching + context lives there)

### Foldability (complex specs only)

Score each requirement: 5=fully specified, 4=minor gaps, 3=ambiguous (ask), 2=underspecified (block), 1=contradictory (reject). All 4+: proceed. Any 2-: resolve first.

## Phase 2: Dispatch

### Batch (primary mode)

```bash
sortase exec --batch 'loci/plans/dispatch-*.md' -p ~/germline -b goose --timeout 300 --retries 1
```

### Single task

```bash
sortase exec <spec>.md -p ~/germline -b goose -v --timeout 300
```

Use `run_in_background`. Write next batch while goose runs.

### Parallel with worktrees (independent tasks, same project)

```bash
sortase exec batch-plan.md -p ~/germline -b goose --decompose --timeout 300
```

Or fire 3 staggered `sortase exec` calls concurrently. Cap at 6-7 concurrent (ZhiPu rate limits).

### Backend selection

| Task type | Backend | Reason |
|-----------|---------|--------|
| Code edits, tests, scripts | goose | Fastest (P50: 42s), free |
| Multi-file sweep | goose or droid | Both reliable with `--build` |
| Planning/analysis/prose | gemini or codex | GLM fails on open-ended |
| Shell execution tasks | gemini | Droid struggles with complex shell |

### Overnight mode

1. `caffeinate -d` — prevent Mac sleep
2. Batch-dispatch all tasks as background chain
3. Summary report ready in the morning

## Phase 3: Review & Coach

Goose output is a claim, not evidence.

1. **Test results** — `uv run pytest -q` once per batch. Check counts match.
2. **Read modified files** — open actual files, verify they match spec. Grep is sampling, not reviewing.
3. **Smoke test** (code only) — run the binary/hook/command with real input.
4. **Coach** — new failure pattern? → append to `~/epigenome/marks/feedback_glm_coaching.md` (format: pattern → what GLM does wrong → fix instruction). This file compounds.
5. **Approve or redispatch** — correct → commit. Wrong → follow-up spec targeting the gap.

## Phase 4: Report

| # | Task | Backend | Duration | Status |
|---|------|---------|----------|--------|
| ... | ... | ... | ...s | ok/failed |

Include: total wall time, success rate, new coaching entries, test delta.

## Hard Rules

- **Pipeline: batch-write specs THEN batch-dispatch.** Never write-one-dispatch-one. Keep goose saturated.
- **Spec quality is the bottleneck.** Invest CC tokens in design, not execution.
- **Specs go in `~/germline/loci/plans/`.** Never `/tmp/`.
- **Verify after each batch.** `uv run pytest -q` once, not per-task.
- **Parallel when independent.** 3 staggered concurrent (safe). Push to 6-7 if no 429s.
- **Write coaching notes in-flight.** Patterns are freshest right after observation.
- **`--auto high` for file creation.** Medium blocks new file creation.
- **`--commit` for trusted batches.** Skip for risky/experimental.
- **Don't fix goose mistakes in-session.** Write a follow-up spec and redispatch.

## Known GLM-5.1 Failure Patterns

- **Import hallucination** — invents modules that don't exist
- **Return type flattening** — collapses distinct types into generic
- **`str(dict)` rendering** — raw repr instead of formatted output
- **File indirection** — treats target file as instructions
- **Prose/planning tasks fail** — route to gemini/codex
