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

**Primary: golem** (headless CC + GLM-5.1, free, no size limits)

```bash
golem "Read X. Do Y. Write tests. Run pytest. Fix failures."           # single task
golem --max-turns 30 "Complex feature task"                            # more turns for features
golem --batch mod1.py mod2.py mod3.py                                  # sequential test gen
golem --full "Task needing MCP/skills"                                 # full organism access
```

Cap at 4-5 concurrent (ZhiPu 429 at ~10+). Use `run_in_background`.

**Fallback: sortase** — only when you need routing logic, worktree isolation, or specific backends.

```bash
sortase exec spec.md -p ~/germline -b golem --timeout 300
```

### Overnight mode

1. Fill `loci/golem-queue.md` with tasks
2. `golem-daemon start` — drains queue, 4 concurrent, 24/7
3. Review results in morning: `tail ~/.local/share/vivesca/golem.jsonl`

## Phase 3: Review

`tail ~/.local/share/vivesca/golem.jsonl` — check exit codes and output tails.

1. **Test results** — `uv run pytest -q`. Check counts match.
2. **New files** — `git status --short`. Verify golem created what was asked.
3. **Smoke test** — run the binary/hook/command with real input.
4. **Commit or discard** — good → `git add && commit`. Bad → redispatch with clearer prompt.

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
