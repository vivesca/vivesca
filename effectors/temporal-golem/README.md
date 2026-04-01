# temporal-golem

Temporal.io-based orchestrator that replaces the golem-daemon markdown queue
with a durable, observable workflow engine.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌────────────────┐
│  cli.py     │────>│  Temporal Server  │<────│  worker.py     │
│  (submit /  │     │  (gRPC :7233)    │     │  (activities)  │
│   status)   │     │                  │     │                │
└─────────────┘     └──────────────────┘     └───────┬────────┘
                           │                         │
                    ┌──────┴───────┐          bash effectors/golem
                    │  PostgreSQL  │          --provider X <task>
                    │  (:5432)     │
                    └──────────────┘
```

- **worker.py** — Temporal worker that polls the `golem-tasks` task queue.
  Each activity runs `bash effectors/golem --provider X <task>`, heartbeats
  every 30 s, has a 30 min timeout, and retries up to 3 times with
  exponential backoff (10 s → 5 min).

- **workflow.py** — `GolemDispatchWorkflow` accepts a list of tasks and
  dispatches them respecting per-provider concurrency limits:

  | Provider | Concurrency |
  |----------|-------------|
  | zhipu    | 8           |
  | infini   | 8           |
  | volcano  | 16          |

- **cli.py** — CLI to submit workflows and check status.

## Prerequisites

- Docker + Docker Compose
- Python 3.11+
- The golem effector at `effectors/golem`

## Quick Start

### 1. Start Temporal Server

```bash
cd effectors/temporal-golem
bash start.sh
```

This brings up:
- PostgreSQL on `:5432`
- Temporal Server gRPC on `:7233`
- Temporal Web UI at `http://localhost:8080`

### 2. Start the Worker

```bash
cd ~/germline
uv run python effectors/temporal-golem/worker.py
```

### 3. Submit Tasks

```bash
# Single task
uv run python effectors/temporal-golem/cli.py submit \
    --provider zhipu \
    --task "Write tests for metabolon/foo.py"

# Multiple tasks
uv run python effectors/temporal-golem/cli.py submit \
    --provider zhipu \
    --task "Write tests for foo.py" \
    --task "Write tests for bar.py"

# From a file (format: provider|task per line)
uv run python effectors/temporal-golem/cli.py submit --file tasks.txt

# With custom workflow ID
uv run python effectors/temporal-golem/cli.py submit \
    --provider infini \
    --task "Refactor baz.py" \
    --workflow-id my-custom-id
```

### 4. Check Status

```bash
uv run python effectors/temporal-golem/cli.py status <workflow-id>
uv run python effectors/temporal-golem/cli.py status <workflow-id> --json
```

### 5. Web UI

Open `http://localhost:8080` to browse workflows, activities, and events
in the Temporal Web UI.

## Teardown

```bash
cd effectors/temporal-golem
docker compose down      # stop containers
docker compose down -v   # stop and wipe data
```

## Testing

```bash
cd ~/germline
uv run pytest assays/test_temporal_golem.py -v --tb=short
```

Tests mock the Temporal client and verify activity logic, workflow
dispatch, CLI commands, and retry policies without a live server.

## File Layout

```
effectors/temporal-golem/
├── cli.py                 # CLI: submit, status
├── config/
│   └── dynamicconfig/
│       └── development-sql.yaml
├── docker-compose.yml     # Temporal + PostgreSQL + Web UI
├── pyproject.toml         # temporalio SDK dependency
├── start.sh               # One-command stack startup
├── worker.py              # Temporal worker + activities
├── workflow.py            # GolemDispatchWorkflow
└── README.md
```
