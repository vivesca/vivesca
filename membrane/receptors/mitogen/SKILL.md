---
name: mitogen
description: Autonomous bulk improvement campaign — audit gaps, wave-dispatch to GLM, verify, iterate. "go build", "work on everything", "blitz"
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
context: inline
epistemics: [audit, plan, delegate, verify]
---

# /mitogen — Autonomous Bulk Dispatch Campaign

Biology: a mitogen is a signal that triggers rapid cell proliferation. `/mitogen` is the signal that tells the organism to mass-produce improvements autonomously.

## When to trigger

User says any of: "go build", "work on everything", "blitz", "keep going while I'm away", "dispatch campaign", or invokes `/mitogen` directly.

## Process

### Phase 1: Audit (GLM exploration specs)

Write exploration specs and dispatch to goose. GLM CAN explore — the key is spec design.

**Typical audit targets:**
1. **Test coverage** — cross-reference `assays/` against `metabolon/`
2. **Self-healing gaps** — missing health checks, monitors, recovery paths
3. **Skill gaps** — consulting tools, automation, missing capabilities
4. **Reliability debt** — hooks without tests, MCP tools without error handling

**Exploration spec rules (learned 2026-03-31):**
- **Bounded reads work natively.** Specs that name 4-10 specific files succeed without tricks.
- **Cross-referencing → embed a script.** If the task matches set A to set B (e.g., modules vs tests), write a Python script in the spec that does the matching. GLM copies and runs it. Shell redirect (`> file.md`) for output.
- **Large output → shell redirect, not write_file.** Goose's `write_file` tool chokes on payloads >100 lines (error -32602). Use `python3 -c "..." > file.md` or `cat << 'EOF' > file.md`.
- **Batch commands over individual reads.** `grep -c "def test_" assays/*.py` replaces 100 file reads. `wc -l metabolon/**/*.py` replaces opening each file.
- **Turn budgeting.** Tell GLM to reserve last 3 turns for writing. "Partial > nothing."

Dispatch exploration specs in parallel via sortase. Collect reports into a prioritized gap list.

### Phase 2: Prioritize into waves

Organize gaps into waves of 5-7 tasks each, ordered by impact:

- **Wave 1:** Quick wins (small files, high coverage gain)
- **Wave 2-3:** Medium complexity (new modules + tests)
- **Wave 4+:** Ambitious builds (new subsystems, consulting tools)

### Phase 3: Progressive dispatch

**Critical rule: dispatch one wave, verify, then next.**

For each wave:

1. **Spec** — write plan file to `~/germline/loci/plans/` (not centrosome-queue, not /tmp)
2. **Dispatch** — `sortase exec <plan> -p ~/germline -b goose` (defaults: --commit --worktree --retries 1)
3. **Verify** — run `uv run pytest <new-test-files> -v --tb=short`
4. **Fix** — if tests fail, fix directly (don't re-dispatch for 1-2 line fixes)
5. **Commit** — ensure all files are committed
6. **Next wave** — only after verification passes

### Phase 4: Report

When all waves complete (or user returns), report:

```
## Mitogen Report
- Waves dispatched: N
- Tests before/after: X → Y (+Z)
- New modules: [list]
- New test files: [list]  
- Pass rate: N/N
- Failures fixed: N
- Duration: Xm
```

## Spec writing rules

For test specs, use `test-spec-gen`:
```bash
test-spec-gen --wave N module1.py module2.py  # generates specs with embedded source
sortase exec loci/plans/wave-N-test-*.md -p ~/germline -b goose  # dispatch
```

CC's role is **judgment only**: which modules, verify results, coach failures.
GLM's role is **everything else**: reading, writing, testing.

For non-test specs, follow centrosome conventions:
- Self-contained specs (no dependencies between tasks)
- Name EVERY file to create/modify
- Include exact pytest verification commands
- Include exact code when possible (GLM copies, doesn't invent)
- Keep specs under 500 lines per plan file
- Embed source code for any file goose needs to understand

## Gotchas (learned 2026-03-31)

- **GLM overdelivers** — Wave 1 may build files intended for Wave 2+. Check before dispatching redundant waves.
- **.venv corruption** — worktree merges can create circular symlinks. After merge conflicts, verify `.venv` resolves. Fix with `rm .venv && uv venv && uv sync`.
- **Wave cross-contamination** — uncommitted files from earlier waves get absorbed into later wave commits. Not harmful, but confusing for attribution.
- **Spec path** — always `~/germline/loci/plans/`, never centrosome-queue or /tmp.
- **Single-task treatment** — sortase treats markdown plans as single tasks. For true parallelism, dispatch separate plan files.
- **GLM for everything.** Both exploration and generation go to GLM (free, unlimited ZhiPu plan). CC is for orchestration, verification, and coaching only.

## Anti-patterns

- Don't dispatch all waves simultaneously — verify each before continuing
- Don't re-dispatch if GLM already built the file in an earlier wave
- Don't use CC subagents for audits — write GLM exploration specs instead
- Don't write specs without reading the target code first
- Don't ask GLM to cross-reference in its head — embed a script
