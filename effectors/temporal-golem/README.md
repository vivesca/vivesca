# temporal-golem

Temporal.io-based orchestrator to replace the golem-daemon markdown queue.

## Architecture

- **worker.py** — Temporal worker that polls `golem-tasks` task queue and runs golem commands as activities
- **workflow.py** — `GolemDispatchWorkflow` that accepts task lists, dispatches with per-provider concurrency limits
- **cli.py** — CLI to submit workflows and check status
- **docker-compose.yml** — Temporal server + PostgreSQL + Web UI

## Per-provider concurrency

| Provider | Max concurrent |
|----------|---------------|
| zhipu    | 8             |
| infini   | 8             |
| volcano  | 16            |

## Activity details

- Runs `bash effectors/golem --provider X --max-turns N <task>`
- Heartbeats every 30s
- 30-minute timeout per attempt
- Retry policy: 3 attempts, exponential backoff (2x), starting at 10s

## Quick start

### 1. Start Temporal server

```bash
cd effectors/temporal-golem
./start.sh
```

Or manually:

```bash
docker compose up -d
```

### 2. Start the worker

```bash
cd effectors/temporal-golem
python worker.py  # connects to localhost:7233
```

### 3. Submit tasks

```bash
# Single task
python cli.py submit -p zhipu "Write tests for foo.py"

# Multiple tasks
python cli.py submit -p infini "Task A" "Task B" "Task C"

# From file
python cli.py submit -p volcano -f tasks.txt

# Custom workflow ID
python cli.py submit -p zhipu -w my-batch "Do the thing"
```

### 4. Check status

```bash
python cli.py status golem-zhipu-abcd1234
python cli.py list -n 5
```

### 5. Web UI

Open http://localhost:8080 for the Temporal Web UI.

## Services

| Service            | Port  | Purpose           |
|--------------------|-------|-------------------|
| PostgreSQL         | 5432  | Persistence       |
| Temporal Server    | 7233  | gRPC endpoint     |
| Temporal Web UI    | 8080  | Visual dashboard  |
| Admin Tools        | —     | CLI management    |

## Migration from golem-daemon

This is Phase 1 (scaffold). The golem-daemon markdown queue still works. Once Temporal is validated:

1. Worker replaces the daemon's `run_golem()` subprocess loop
2. Workflow replaces the daemon's queue parsing + concurrency management
3. CLI replaces `golem-daemon status` / manual queue edits
4. Temporal Web UI replaces `golem-top` for visibility

## Testing

```bash
cd ~/germline
uv run pytest assays/test_temporal_golem.py -v --tb=short
```

All tests mock the Temporal client — no running server needed.
