# cytoskeleton

Consolidated Claude Code hook handlers. Each file is a single Python script invoked by CC's hook system (settings.json). They run as subprocesses on every matching tool call.

## Hook event → handler map

| Event | Handler | Matcher | Purpose |
|-------|---------|---------|---------|
| UserPromptSubmit | synapse.py | all | Session state, date injection |
| PreToolUse | axon.py | Bash\|Glob\|Grep\|Read\|Write\|Edit\|MultiEdit\|Agent\|Skill\|WebSearch\|rheotaxis | Safety guards, metabolic gates, genome injection |
| PostToolUse | dendrite.py | Bash\|Read\|Write\|Edit\|MultiEdit\|Skill\|NotebookEdit | Chaperones (ruff/pyright), perseveration detection, memory management |
| Stop | terminus.py | all | Dirty repo warning, contract enforcement |
| StopFailure | apoptosis.py | all | API error logging (rate limit, auth, server) |
| PreCompact | compaction.py | all | Pre-compaction state preservation |
| Notification | interoceptor.py | all | Notification routing |
| InstructionsLoaded | morphogen.py | all | Dynamic instruction injection |

## SRP (Signal Recognition Particle)

`srp.py` is a special PreToolUse hook for ribosome `--supervised` mode only. Detects sensitive operations (git push, curl POST, SSH, docker, systemctl) and returns `defer` to pause headless execution. Zero overhead in normal mode (env var gate: `RIBOSOME_DEFER_ENABLED=1`).

## Conventions

- All handlers read JSON from stdin, write JSON to stdout
- `deny(reason)` → blocks the tool call
- `allow_msg(message)` → allows with advisory message
- Handlers must never crash — wrap in try/except, exit 0 on error
- Each handler routes internally by tool name (single process, multiple guards)
