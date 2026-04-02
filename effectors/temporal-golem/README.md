# temporal-golem

Temporal.io-based orchestrator to replace the golem-daemon markdown queue.
Phase 1 scaffold — worker, workflow, CLI, and Docker Compose for local development.

## Architecture

```
CLI (cli.py) ──submit──> Temporal Server ──dispatch──> Worker (worker.py)
                              │                         │
                              │                    bash effectors/golem
                              │                         │
                              └──status/list────────────┘
```

- **worker.py** — Temporal worker that polls `golem-tasks` task queue. Each activity runs `bash effectors/golem --provider X --max-turns N "task"`, heartbeats every 30s during execution (via a background coroutine), has a 30min timeout, and retries up to 3 times with exponential backoff.
- **workflow.py** — `GolemDispatchWorkflow` accepts a list of task specs, dispatches them concurrently via `asyncio.gather` (per-provider concurrency enforced by semaphores in the worker), and returns an aggregate result.
- **cli.py** — Click CLI for submitting workflows and checking status.

## Per-provider concurrency

| Provider | Max concurrent tasks |
|----------|---------------------|
| zhipu    | 8                   |
| infini   | 8                   |
| volcano  | 16                  |

Concurrency is enforced via `asyncio.Semaphore` in the worker, one per provider. The workflow dispatches all tasks concurrently — the worker semaphores gate actual parallel execution per-provider.

## Quick start

### 1. Start Temporal server

```bash
cd effectors/temporal-golem
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Temporal server on port 7233
- Temporal Web UI on port 8080
- Admin tools container

### 2. Start the worker

```bash
python3 worker.py
```

Or use the combined script:

```bash
./start.sh
```

### 3. Submit tasks

```bash
# Single task
temporal-golem submit -p zhipu "Write tests for metabolon/foo.py"

# Multiple tasks
temporal-golem submit -p volcano "Task A" "Task B" "Task C"

# From file (one task per line, # comments supported)
temporal-golem submit -p infini -f tasks.txt

# Custom workflow ID
temporal-golem submit -p zhipu -w my-batch-001 "Do the thing"
```

### 4. Check status

```bash
temporal-golem status golem-zhipu-abcd1234
temporal-golem list -n 10
```

## Docker Compose services

| Service             | Port  | Purpose                |
|---------------------|-------|------------------------|
| postgresql          | 5432  | Persistence store      |
| temporal-server     | 7233  | Temporal server        |
| temporal-ui         | 8080  | Web UI                 |
| temporal-admin-tools| —     | `tctl` admin CLI       |

## Activity retry policy

- Maximum attempts: 3
- Initial interval: 10s
- Backoff coefficient: 2.0
- Maximum interval: 5m
- Start-to-close timeout: 30m

## Running tests

```bash
cd ~/germline
uv run pytest assays/test_temporal_golem.py -v --tb=short
```

All tests mock the Temporal client — no running server needed.
