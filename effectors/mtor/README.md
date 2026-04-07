# mtor

**Agent-first translation controller** — dispatch, inspect, and manage ribosome workflows via Temporal.

Every response is a JSON envelope designed for programmatic consumption by agents and tools:

```json
{"ok": true, "command": "mtor list", "result": {...}, "next_actions": [...]}
{"ok": false, "command": "mtor status", "error": {"message": "...", "code": "..."}, "fix": "...", "next_actions": [...]}
```

## Install

```bash
pip install mtor
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install mtor
```

## Requirements

- Python ≥ 3.11
- A Temporal server reachable at `TEMPORAL_HOST` (default: `ganglion:7233`)
- A ribosome worker running on the Temporal task queue `translation-queue`

## Usage

### Show available commands

```bash
mtor
```

Returns a JSON command tree for agent self-discovery.

### Dispatch a task

```bash
mtor "Write unit tests for the authentication module"
mtor "Refactor the database layer" --provider zhipu
mtor ./path/to/spec.md
```

If the prompt argument is a file path, mtor reads the file contents as the task spec.

### List workflows

```bash
mtor list
mtor list --status RUNNING --count 20
```

### Check workflow status

```bash
mtor status ribosome-zhipu-af3c43d1
```

### Fetch workflow logs

```bash
mtor logs ribosome-zhipu-af3c43d1
```

Retrieves the last 30 lines of output from ganglion.

### Cancel a workflow

```bash
mtor cancel ribosome-zhipu-af3c43d1
```

Idempotent — cancelling an already-terminal workflow returns success.

### Approve / Deny deferred tasks

```bash
mtor approve ribosome-zhipu-af3c43d1
mtor deny ribosome-zhipu-af3c43d1
```

### Health check

```bash
mtor doctor
```

Checks Temporal connectivity, worker liveness, coaching file presence, and provider availability on ganglion.

### Schema

```bash
mtor schema
```

Emits a full JSON schema of all commands with params, types, enums, and defaults.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Generic error |
| 2 | Usage error (missing required arguments) |
| 3 | Temporal unreachable |
| 4 | Workflow not found |

## Architecture

```
mtor/
├── __init__.py     # VERSION, constants (TEMPORAL_HOST, TASK_QUEUE, etc.)
├── cli.py          # Cyclopts app + command handlers (thin dispatch)
├── client.py       # Temporal connection logic
├── envelope.py     # JSON envelope helpers (_ok, _err, _extract_first_result)
├── dispatch.py     # Core prompt dispatch logic
├── doctor.py       # Health check logic
└── tree.py         # CommandTree definition for agent self-discovery
```

Dependency direction: `cli → {dispatch, doctor} → {client, envelope} → {tree, __init__}`

## Development

```bash
cd effectors/mtor
uv sync --group dev
uv run pytest assays/
uv run mtor
```

## License

MIT
