---
name: opifex
description: >
  AI agent orchestrator — delegates coding tasks to free tools (Gemini/Codex/OpenCode) with auto-routing, fallback chains, and optional 3-pass Opus planning (--plan).
  Use when delegating any implementation task. Default tool for rector Step 3.
user_invocable: true
---

# opifex — AI Agent Plan Executor

Executes implementation plans via free coding tools. Zero Max20 token cost.

## Commands

```bash
# Execute a plan file against a project
opifex exec plan.md -p ~/code/myproject

# Force a specific backend
opifex exec plan.md -p ~/code/myproject -b codex

# Decompose plan into parallel tasks (uses Gemini to split)
opifex exec plan.md -p ~/code/myproject --decompose

# Execute sequentially (default is parallel)
opifex exec plan.md -p ~/code/myproject --serial

# Run tests after execution
opifex exec plan.md -p ~/code/myproject --test-command "uv run pytest -v"

# Dry-run routing — see which tool would be picked
opifex route "implement Rust binary parser"

# Show execution history
opifex log

# Show aggregate stats (success rates, tool performance)
opifex log --stats

# Show currently running executions
opifex status
```

## Routing Rules

| Signal | Tool | Why |
|--------|------|-----|
| Rust/cargo/crate | Codex | Sandbox + DNS needed |
| Multi-file/refactor | Codex | Repo navigation |
| Algorithm/logic/compute | Gemini | Free, high benchmark (AA 57) |
| Boilerplate/template/scaffold | OpenCode | Free, unlimited |
| Default | Gemini | Best free default |

## Fallback Chain

Gemini → Codex → OpenCode. If one tool fails (quota, auth, timeout), automatically tries the next. Fallbacks logged for stats.

## Integration with rector

rector Step 3 delegates to opifex for plan execution. The typical flow:

```
/rector → CE plan → write plan.md → opifex exec plan.md -p ~/code/project
```

For parallel delegation, opifex `--decompose` splits the plan and routes each task independently.

## Log & Stats

Execution history at `~/.local/share/opifex/log.jsonl`. Each entry records: timestamp, plan, project, tool, fallbacks, duration, success, files changed, test results.

`opifex log --stats` shows per-tool success rates and failure reasons — this is the feedback loop that improves routing over time.

## Gotchas

- **Codex can't write across worktree boundaries** — always `cd` into the target repo first. Codex's `apply_patch` rejects writes to paths outside CWD.
- **Gemini free tier quota shared across parallel calls** — 3+ simultaneous Gemini calls burn through it. Mix tools when parallelising.
- **OpenCode prompt limit ~4K chars** — long plan files need splitting first.
- **plan-exec prototype still at `~/bin/plan-exec`** — deprecated, use opifex instead.

## Source

`~/code/opifex/` — Python, Click, Rich. GitHub: `terry-li-hm/opifex` (private).
