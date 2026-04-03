# temporal-golem

Temporal.io-based workflow orchestrator for golem task dispatch. Replaces the markdown queue-based golem-daemon polling loop with durable workflows.

## Architecture

- **dispatch.py** — Reads `~/germline/loci/golem-queue.md`, submits tasks to Temporal on ganglion. Runs from soma.
- **worker.py** — Polls `golem-tasks` queue, executes `bash effectors/golem --provider X task`. Runs as systemd service on ganglion.
- **workflow.py** — `GolemDispatchWorkflow`: dispatches batch of activities via `asyncio.gather`, 3 retries, 35min timeout.
- **cli.py** — Click CLI: `submit`, `status`, `list` commands. Connects to `localhost:7233` (run on ganglion).

## Infrastructure (ganglion)

- Temporal server: Docker Compose, port 7233 (gRPC), 8233 (UI)
- Worker: systemd `temporal-worker.service`, env from `~/.temporal-worker.env`
- Ganglion: OCI ARM A1.Flex, Tailscale `ganglion` / `100.120.158.22`

## Queue format

```markdown
- [ ] `golem [t-XXXXXX] -b zhipu "Task prompt here"`
- [!!] `golem [t-XXXXXX] -b volcano "High priority task"` 
```

- `-b` or `--provider` for provider selection
- `[!!]` = high priority, `[ ]` = normal, `[x]` = done, `[!]` = failed
- Task IDs auto-generated if missing

## Key decisions

- Heartbeat interval: 30s (worker), timeout: 5min (workflow)
- Per-provider concurrency: zhipu=8, volcano=16, gemini=4, codex=4, infini=2
- dispatch.py connects to `TEMPORAL_HOST` (default: `ganglion:7233`)
- worker.py connects to `TEMPORAL_HOST` (default: `localhost:7233` via systemd env)
