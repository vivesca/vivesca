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

### Phase 1: Audit (CC, not GLM)

Use CC subagents (Explore type) to rapidly scan for gaps. Typical audit targets:

1. **Test coverage** — find untested modules via cross-referencing `assays/` against `metabolon/`
2. **Self-healing gaps** — missing health checks, monitors, recovery paths
3. **Skill gaps** — consulting tools, automation, missing capabilities
4. **Reliability debt** — hooks without tests, MCP tools without error handling

Run audits in parallel. Collect into a prioritized gap list.

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

Follow centrosome spec conventions:
- Self-contained specs (no dependencies between tasks)
- Name EVERY file to create/modify
- Include exact pytest verification commands
- Include exact code when possible (GLM copies, doesn't invent)
- Keep specs under 500 lines per plan file

## Gotchas (learned 2026-03-31)

- **GLM overdelivers** — Wave 1 may build files intended for Wave 2+. Check before dispatching redundant waves.
- **.venv corruption** — worktree merges can create circular symlinks. After merge conflicts, verify `.venv` resolves. Fix with `rm .venv && uv venv && uv sync`.
- **Wave cross-contamination** — uncommitted files from earlier waves get absorbed into later wave commits. Not harmful, but confusing for attribution.
- **Spec path** — always `~/germline/loci/plans/`, never centrosome-queue or /tmp.
- **Single-task treatment** — sortase treats markdown plans as single tasks. For true parallelism, dispatch separate plan files.
- **CC budget** — use CC for audit (fast, needs file access), GLM for generation (free, needs code writing). Don't use CC for code generation or GLM for exploration.

## Anti-patterns

- Don't dispatch all waves simultaneously — verify each before continuing
- Don't re-dispatch if GLM already built the file in an earlier wave
- Don't spend CC budget on exploration that GLM could do (but DO use CC for audits that need Glob/Grep/Read)
- Don't write specs without reading the target code first
