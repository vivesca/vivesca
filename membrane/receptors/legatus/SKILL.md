---
name: legatus
description: Session-independent AI agent dispatcher — list tasks, dispatch immediately, cancel, view results. Use for any background AI job that should run detached from the current CC session.
triggers:
  - legatus
  - dispatch
  - background
  - detached
  - overnight
  - queue
---

# legatus — Session-Independent AI Agent Dispatcher

Dispatch any AI agent job detached from the current session — overnight tasks, long research, post-meeting work, slow delegations. Scheduling (if needed) is handled by CalendarInterval LaunchAgents; legatus itself is scheduling-agnostic.

## Quick Reference

| Command | What it does |
|---------|-------------|
| `legatus list` | Show all tasks + schedule + status |
| `legatus run <name>` | Dispatch immediately (detached, survives session close) |
| `legatus cancel <name>` | Disable task, clear run_now |
| `legatus results <name>` | Show latest run output |
| `legatus results` | List all tasks with results |

## Common Patterns

### Dispatch immediately (detached)
```bash
legatus run vault-health-check
# Survives CC session close — check results after:
legatus results vault-health-check
```

### Check what's configured
```bash
legatus list
# Shows: name, backend, status, timeout, schedule (doc only)
```

## Architecture

- **Queue file:** `~/notes/opencode-queue.yaml` — task definitions
- **Scheduling:** individual CalendarInterval LaunchAgents per task (`~/officina/launchd/com.terry.legatus-*.plist`)
- **Output:** `~/.cache/legatus-runs/<YYYY-MM-DD-HHMM>/<task>/stdout.txt`
- **Hot dispatch logs:** `~/.cache/legatus-runs/hot-<name>.log`

## `output_dir` — Auto-Copy Results to Vault

Add `output_dir` to any task definition to auto-copy output files to a persistent location after a successful run:

```yaml
- name: hsbc-desk-research
  output_dir: ~/notes/Capco
  backend: gemini
  ...
```

- If set: copies all files from `~/.cache/legatus-runs/<timestamp>/<name>/` to `output_dir` on success
- If unset: output stays in cache only (ephemeral — fine for health checks)
- Tilde expansion handled automatically
- Copy failure prints a warning but doesn't fail the run

**Rule of thumb:** health checks → no `output_dir` (disposable). Research deliverables → set `output_dir` (durable).

## Adding a New Task

1. Add entry to `~/notes/opencode-queue.yaml`
2. Create `~/officina/launchd/com.terry.legatus-<name>.plist` with CalendarInterval
3. `cp ~/officina/launchd/com.terry.legatus-<name>.plist ~/Library/LaunchAgents/`
4. `launchctl load ~/Library/LaunchAgents/com.terry.legatus-<name>.plist`
5. Verify: `legatus list`

## Backend Options
- `opencode` (default) — free, unlimited (GLM-5)
- `claude` — Claude Code CLI, uses Max plan credits
- `gemini` — Gemini CLI, `--yolo` mode, has web access
- `codex` — Codex CLI, `--sandbox danger-full-access`, good for Rust/multi-file

## Gotchas
- **Session independence:** `legatus run` spawns a detached subprocess. Session can close; job keeps running.
- **CLAUDECODE env:** stripped for Backend::Claude so nested claude invocations aren't blocked.
- **Results location:** `legatus run` → `hot-<name>.log` (live tail); scheduled → `~/.cache/legatus-runs/<timestamp>/<name>/stdout.txt`. If `output_dir` set, also copied there.
- **No batch command** — removed. Use `legatus run <name>` for on-demand dispatch; LaunchAgents handle scheduling.
- **Codex from CC background:** Use `codex exec --full-auto`, NOT interactive `codex "prompt"` (needs TTY). Don't pass `-a never` — conflicts with `--dangerously-bypass-approvals-and-sandbox` in config. See `~/docs/solutions/delegation-reference.md`.
- **Scheduled runs need `legatus-env` wrapper:** LaunchAgents don't source `.zshenv`, so backends have no API keys. All plists now call `~/bin/legatus-env` (sources `.zshenv` then exec's legatus). Fixed Mar 12.

## Source
`~/code/legatus/` — Rust, clap 4, serde_yaml 0.9. GitHub: `terry-li-hm/legatus` (private).
