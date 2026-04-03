# temporal-golem

Temporal.io-based workflow orchestrator for golem task dispatch.
Runs from **soma** (dispatch) through **ganglion** (Temporal + worker).

## Architecture

```
soma                           ganglion
dispatch.py ──submit──> Temporal Server ──dispatch──> worker.py
               (gRPC)    (ganglion:7233)    (poll)    (golem-tasks Q)
                                                    │
                                               bash effectors/golem
                                                    │
                                               review_golem_result
                                                    │
                                  ┌─── verdict ────┤
                                  ▼                ▼
                             approved         rejected / flagged
                                  │                │
                                  ▼                ▼
                        mark_done [x]  mark_failed [!] ──> auto-requeue
                                                              │
                                                 _sync_reviews() ──> rsync + git pull
```

## Dispatching tasks

```bash
python3 dispatch.py                  # One-shot: dispatch all pending
python3 dispatch.py --poll           # Daemon mode: poll every 30s
python3 dispatch.py --poll --interval 60
python3 dispatch.py --dry-run        # Preview without dispatching
python3 dispatch.py --graph          # Use LangGraph agent (plan→execute→verify)
python3 dispatch.py --json           # JSON output
```

Tasks live in `~/germline/loci/golem-queue.md`:

```markdown
- [ ]  `golem --provider zhipu [t-abc123] "Write tests for foo.py"`
- [!!] `golem --provider volcano [t-def456] "High priority fix"`
```

## Checking status

```bash
python3 dispatch.py --status         # List recent workflows
python3 dispatch.py --status --json  # JSON output
```

Connects to `TEMPORAL_HOST` (default: `ganglion:7233`). Web UI at `ganglion:8233`.

## Review pipeline

Every task flows through two activities:

1. **Execute** (`run_golem_task`) — runs golem subprocess, captures
   stdout/stderr/exit-code, snapshots `git diff` before and after.
2. **Review** (`review_golem_result`) — checks for:
   non-zero exit, destruction patterns (`rm -rf`, `overwrote`), error patterns
   (`SyntaxError`, `Traceback`), git diff shrinkage, thin output for complex prompts.

**Verdicts:** `approved` → `[x]`, `approved_with_flags` → hold 1h then auto-approve,
`rejected` → `[!]` with optional auto-requeue + coaching prompt.

Reviews persist to `~/germline/loci/golem-reviews.jsonl`.

## Provider configuration

| Provider | Concurrency | Fallback chain       |
|----------|-------------|----------------------|
| zhipu    | 8           | codex → gemini       |
| infini   | 2           | codex → gemini       |
| volcano  | 16          | codex → gemini       |
| gemini   | 4           | codex → zhipu        |
| codex    | 4           | gemini → zhipu       |

- **Rate-limit cooldown:** 5h default (parsed per-provider from error text); adaptive throttle on repeated failures; auto-fallback to next provider in chain.
