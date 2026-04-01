# temporal-golem

Temporal.io-based orchestrator that replaces the golem-daemon markdown queue.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  cli.py     │────>│  Temporal Server  │<────│  worker.py   │
│  (submit /  │     │  (task queue:     │     │  (polls &    │
│   status)   │     │   golem-tasks)    │     │   executes)  │
└─────────────┘     └──────────────────┘     └──────┬───────┘
                                                     │
                                                     ▼
                                              bash effectors/golem
                                              --provider X task
```

### Components

| File | Purpose |
|------|---------|
| `models.py` | Shared data classes (`GolemResult`, `GolemTaskSpec`, etc.) |
| `worker.py` | Temporal worker; runs `golem` as an activity |
| `workflow.py` | `GolemDispatchWorkflow` with per-provider concurrency |
| `cli.py` | CLI: `submit` and `status` commands |
| `docker-compose.yml` | Temporal server + PostgreSQL + Web UI |
| `start.sh` | One-command local development startup |

### Per-provider concurrency

| Provider | Max concurrent tasks |
|----------|---------------------|
| zhipu    | 8                   |
| infini   | 8                   |
| volcano  | 16                  |

### Retry policy

- **Maximum attempts:** 3
- **Initial backoff:** 10s
- **Backoff coefficient:** 2.0 (10s → 20s → 40s)
- **Max interval:** 5 minutes
- **Non-retryable:** `ActivityError`

### Activity configuration

- **Timeout:** 30 minutes (start-to-close)
- **Heartbeat:** every 60 seconds (activity heartbeats on completion)
- **Task queue:** `golem-tasks`

## Quick start

### 1. Start Temporal server

```bash
cd effectors/temporal-golem
bash start.sh
```

Or manually:

```bash
docker compose up -d
```

### 2. Start the worker

```bash
cd ~/germline
uv run python effectors/temporal-golem/worker.py
```

### 3. Submit tasks

```bash
# Single task
temporal-golem submit --provider zhipu --task "Write tests for metabolon/foo.py"

# Multiple tasks
temporal-golem submit --provider infini --task "task one" --task "task two"

# From a file (provider|task per line)
temporal-golem submit --provider zhipu --file tasks.txt

# Custom workflow ID
temporal-golem submit --provider volcano --task "refactor" --workflow-id my-run-001
```

### 4. Check status

```bash
temporal-golem status my-run-001
temporal-golem status my-run-001 --json
```

### Task file format

```
# Lines starting with # are comments; blank lines are skipped.
zhipu|Write tests for foo.py
infini|Refactor bar.py
# Bare lines default to provider=zhipu:
Write tests for baz.py
```

## Ports

| Service | Port |
|---------|------|
| Temporal gRPC | 7233 |
| Temporal Web UI | 8080 |
| PostgreSQL | 5432 |

## Testing

```bash
cd ~/germline
uv run pytest assays/test_temporal_golem.py -v
```

All tests mock the Temporal client — no live server required.

## Migration from markdown queue

The existing `loci/golem-queue.md` can be converted to a task file:

```bash
grep -E '^\w+\|' loci/golem-queue.md > tasks.txt
temporal-golem submit --provider zhipu --file tasks.txt
```
