# temporal-golem

A Temporal.io-based orchestrator to replace the golem-daemon markdown queue.
Provides durable execution, heartbeating, per-provider concurrency control,
automatic retries, and a web UI for task visibility.

## Architecture

```
CLI (cli.py)  ──submit──>  Temporal Server  <──poll──  Worker (worker.py)
                                │                         │
                                │   Workflow (workflow.py) │
                                │   GolemDispatchWorkflow  │
                                │                         │
                          PostgreSQL              Activity: run_golem_task
                          (persistence)                    │
                                                     bash effectors/golem
```

## Quick Start

### 1. Start Temporal Server

```bash
cd effectors/temporal-golem
./start.sh
```

This launches:
- **Temporal Server** on `localhost:7233`
- **PostgreSQL 15** on `localhost:5432`
- **Temporal Web UI** on `http://localhost:8080`

### 2. Start the Worker

```bash
cd effectors/temporal-golem
pip install temporalio click
python worker.py
```

The worker polls the `golem-tasks` task queue and executes golem commands
as Temporal activities with:
- 30-second heartbeats
- 30-minute timeout per task
- 3 retry attempts with exponential backoff

### 3. Submit Tasks

```bash
# Single task
temporal-golem submit --provider zhipu "Write tests for metabolon/foo.py"

# Multiple tasks
temporal-golem submit --provider infini "Task one" "Task two" "Task three"

# From file (one task per line)
temporal-golem submit --provider volcano --file tasks.txt

# Custom workflow ID
temporal-golem submit -p zhipu -w my-batch-001 "Do the thing"
```

### 4. Check Status

```bash
# Single workflow
temporal-golem status <workflow-id>

# List recent workflows
temporal-golem list
```

## Per-Provider Concurrency

| Provider | Max Concurrent Tasks |
|----------|---------------------|
| zhipu    | 8                   |
| infini   | 8                   |
| volcano  | 16                  |

Concurrency is enforced via asyncio semaphores in the worker. The workflow
dispatches all tasks in parallel; the worker-level semaphore gates execution.

## Retry Policy

- **Maximum attempts:** 3
- **Initial backoff:** 10 seconds
- **Backoff coefficient:** 2.0
- **Maximum backoff:** 5 minutes
- **Heartbeat timeout:** 90 seconds (worker must heartbeat within this window)

## Configuration

| Environment Variable   | Default            | Description                  |
|------------------------|--------------------|------------------------------|
| `TEMPORAL_HOST`        | `localhost:7233`   | Temporal server address      |
| `TEMPORAL_NAMESPACE`   | `default`          | Temporal namespace           |
| `GOLEM_PROVIDER`       | `zhipu`            | Default provider (fallback)  |

## File Layout

```
effectors/temporal-golem/
├── pyproject.toml          # Dependencies: temporalio, click
├── worker.py               # Temporal worker + activity definitions
├── workflow.py             # GolemDispatchWorkflow definition
├── cli.py                  # CLI: submit, status, list commands
├── docker-compose.yml      # Temporal server + PostgreSQL + Web UI
├── start.sh                # One-command startup script
├── config/
│   └── dynamicconfig/
│       └── development-sql.yaml
└── README.md               # This file
```

## Migration from golem-daemon

The markdown queue (`loci/golem-queue.md`) is replaced by Temporal's durable
task queue. Key differences:

| Feature              | golem-daemon              | temporal-golem                |
|----------------------|---------------------------|-------------------------------|
| Task queue           | Markdown file             | Temporal task queue           |
| Persistence          | File-based, fragile       | PostgreSQL-backed             |
| Visibility           | `cat golem-queue.md`      | Web UI + CLI                  |
| Heartbeating         | None                      | 30s heartbeats                |
| Retry                | Manual requeue            | Automatic (3 attempts)        |
| Concurrency control  | ThreadPoolExecutor        | asyncio semaphores            |
| Durable execution    | No (lost on crash)        | Yes (server-side history)     |

Phase 1 is scaffold only — the golem-daemon remains active until Phase 2
adds the migration path.
