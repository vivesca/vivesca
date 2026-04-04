#!/usr/bin/env python3
"""Hatchet worker for golem task orchestration.

Uses @hatchet.task (standalone) and @hatchet.durable_task (checkpointed)
with per-provider concurrency. Durable tasks survive worker restarts by
resuming from the last aio_wait_for checkpoint.
Includes cron-triggered tasks for auto-requeue and health monitoring.
Compare with temporal-golem/ for head-to-head eval.
"""

from __future__ import annotations

import sys

# Early --help check to avoid initializing Hatchet client unnecessarily.
if "--help" in sys.argv or "-h" in sys.argv:
    print(__doc__)
    print("\nUsage:")
    print("    python worker.py           # Start the Hatchet golem worker")
    print("    python worker.py --help    # Show this help")
    sys.exit(0)

import asyncio
import os
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from hatchet_sdk import ConcurrencyExpression, ConcurrencyLimitStrategy, Hatchet
from hatchet_sdk.conditions import SleepCondition
from hatchet_sdk.rate_limit import RateLimit, RateLimitDuration

GOLEM_SCRIPT = Path(__file__).resolve().parent.parent / "golem"
QUEUE_FILE = Path.home() / "germline" / "loci" / "golem-queue.md"
HEALTH_SCRIPT = Path(__file__).resolve().parent.parent / "soma-health"
GEMMULE_HEALTH_SCRIPT = Path(__file__).resolve().parent.parent / "gemmule-health"
REQUEUE_THRESHOLD = 20

hatchet = Hatchet(debug=os.getenv("HATCHET_DEBUG", "").lower() in ("1", "true"))

# Register server-side rate limit keys (replaces manual cooldown in golem-daemon).
hatchet.rate_limits.put("zhipu-rpm", limit=200, duration=RateLimitDuration.HOUR)
hatchet.rate_limits.put("infini-rpm", limit=200, duration=RateLimitDuration.HOUR)
hatchet.rate_limits.put("volcano-rpm", limit=200, duration=RateLimitDuration.HOUR)
hatchet.rate_limits.put("gemini-rpm", limit=60, duration=RateLimitDuration.MINUTE)
hatchet.rate_limits.put("codex-rpm", limit=60, duration=RateLimitDuration.MINUTE)


async def save_state(context, key: str) -> None:
    """Create a durable checkpoint in task execution.

    On worker restart, Hatchet replays the task function from the start.
    Each save_state call returns instantly if the checkpoint was already
    reached in a previous invocation, letting execution effectively
    resume from the last completed checkpoint.
    """
    await context.aio_wait_for(
        key,
        SleepCondition(duration=timedelta(seconds=0)),
    )


def _run_golem(input, context, provider: str) -> dict:
    """Shared golem execution logic."""
    # Normalize input: Hatchet SDK passes pydantic EmptyModel for @hatchet.task,
    # dict for @hatchet.durable_task. Handle both.
    if hasattr(input, "task"):
        task = input.task or ""
        max_turns = getattr(input, "max_turns", 50) or 50
    elif isinstance(input, dict):
        if "input" in input and isinstance(input["input"], dict):
            input = input["input"]
        task = input.get("task", "")
        max_turns = input.get("max_turns", 50)
    else:
        task = str(input)
        max_turns = 50

    cmd = [
        "bash",
        str(GOLEM_SCRIPT),
        "--provider",
        provider,
        "--max-turns",
        str(max_turns),
        task,
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=1800,
        env={**os.environ, "GOLEM_PROVIDER": provider},
    )

    return {
        "task": task[:200],
        "provider": provider,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[:4000],
        "stderr": proc.stderr[:2000],
        "success": proc.returncode == 0,
    }


@hatchet.durable_task(
    name="golem-zhipu",
    execution_timeout="30m",
    retries=2,
    concurrency=ConcurrencyExpression(
        expression="'zhipu'",
        max_runs=4,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
    rate_limits=[RateLimit(static_key="zhipu-rpm", units=1)],
)
async def golem_zhipu(input, context):
    """Durable golem-zhipu task with save_state checkpoints.

    save_state before subprocess marks execution start; save_state after
    marks completion. On worker restart, Hatchet replays the task function;
    cached save_state calls return instantly, so execution progresses past
    already-completed sections. The subprocess re-runs only if the post-exec
    checkpoint was never reached (golem tasks are idempotent).
    """
    # Normalize input: EmptyModel or dict depending on task type
    if hasattr(input, "task"):
        task = input.task or ""
        max_turns = getattr(input, "max_turns", 50) or 50
    elif isinstance(input, dict):
        if "input" in input and isinstance(input["input"], dict):
            input = input["input"]
        task = input.get("task", "")
        max_turns = input.get("max_turns", 50)
    else:
        task = str(input)
        max_turns = 50

    # Save state: mark that execution has begun
    await save_state(context, "golem-zhipu-pre-exec")

    # Run subprocess in a thread to avoid blocking the event loop
    cmd = [
        "bash",
        str(GOLEM_SCRIPT),
        "--provider",
        "zhipu",
        "--max-turns",
        str(max_turns),
        task,
    ]
    proc = await asyncio.to_thread(
        subprocess.run,
        cmd,
        capture_output=True,
        text=True,
        timeout=1800,
        env={**os.environ, "GOLEM_PROVIDER": "zhipu"},
    )

    # Save state: mark that subprocess completed
    await save_state(context, "golem-zhipu-post-exec")

    return {
        "task": task[:200],
        "provider": "zhipu",
        "exit_code": proc.returncode,
        "stdout": proc.stdout[:4000],
        "stderr": proc.stderr[:2000],
        "success": proc.returncode == 0,
    }


@hatchet.task(
    name="golem-infini",
    execution_timeout="30m",
    retries=2,
    concurrency=ConcurrencyExpression(
        expression="'infini'",
        max_runs=4,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
    rate_limits=[RateLimit(static_key="infini-rpm", units=1)],
)
def golem_infini(input, context):
    return _run_golem(input, context, "infini")


@hatchet.task(
    name="golem-volcano",
    execution_timeout="30m",
    retries=2,
    concurrency=ConcurrencyExpression(
        expression="'volcano'",
        max_runs=6,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
    rate_limits=[RateLimit(static_key="volcano-rpm", units=1)],
)
def golem_volcano(input, context):
    return _run_golem(input, context, "volcano")


@hatchet.task(
    name="golem-gemini",
    execution_timeout="30m",
    retries=2,
    concurrency=ConcurrencyExpression(
        expression="'gemini'",
        max_runs=4,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
    rate_limits=[RateLimit(static_key="gemini-rpm", units=1)],
)
def golem_gemini(input, context):
    return _run_golem(input, context, "gemini")


@hatchet.task(
    name="golem-codex",
    execution_timeout="30m",
    retries=2,
    concurrency=ConcurrencyExpression(
        expression="'codex'",
        max_runs=4,
        limit_strategy=ConcurrencyLimitStrategy.GROUP_ROUND_ROBIN,
    ),
    rate_limits=[RateLimit(static_key="codex-rpm", units=1)],
)
def golem_codex(input, context):
    return _run_golem(input, context, "codex")


# ── Cron-triggered tasks ────────────────────────────────────────────────


def _count_pending(queue_file: Path = QUEUE_FILE) -> int:
    """Count pending ([ ] and [!!]) tasks in the queue file."""
    if not queue_file.exists():
        return 0
    text = queue_file.read_text()
    return sum(
        1
        for line in text.splitlines()
        if line.strip().startswith(("- [ ] ", "- [!!] ")) and "`" in line
    )


def _auto_requeue(
    min_pending: int = 10,
    queue_file: Path = QUEUE_FILE,
) -> int:
    """Generate diverse high-value tasks when queue runs low.

    Ported from golem-daemon auto_requeue. Returns count of tasks added.
    """
    # Only build tasks — maintenance (pyright/ruff/health) handled by cron
    pending = _count_pending(queue_file)
    if pending >= min_pending:
        return 0

    tasks: list[str] = []
    providers = ["zhipu", "infini", "volcano"]
    pi = random.randint(0, 2)

    def _add(prompt: str, turns: int = 25) -> None:
        nonlocal pi
        p = providers[pi % 3]
        pi += 1
        prompt = prompt.replace('"', '\\"')
        tasks.append(f'- [ ] `golem --provider {p} --max-turns {turns} "{prompt}"`')

    existing_tests: set[str] = set()
    assays_dir = Path.home() / "germline" / "assays"
    if assays_dir.exists():
        for f in assays_dir.glob("test_*.py"):
            existing_tests.add(f.stem)

    # === Fix failing tests ===
    _add(
        "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 "
        "| grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. "
        "For each: run pytest on it, read traceback, fix. Iterate until green. Commit.",
        turns=50,
    )

    # === System hardening ===
    hardening = [
        "Scan assays/ for hardcoded paths. Replace with Path.home(). Commit.",
        "Find test files with SyntaxError. Fix syntax. Commit.",
        "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit.",
    ]
    for h in random.sample(hardening, min(2, len(hardening))):
        _add(h, turns=25)

    if not tasks:
        return 0

    # Write to queue before ## Done section
    if not queue_file.exists():
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text("# Golem Task Queue\n\n## Pending\n\n## Done\n")

    lines = queue_file.read_text().splitlines()
    insert_idx = len(lines)
    for i, line in enumerate(lines):
        if line.strip().startswith("## Done"):
            insert_idx = i
            break

    ts = datetime.now().strftime("%H:%M")
    header = f"\n### Auto-requeue ({len(tasks)} tasks @ {ts})"
    lines.insert(insert_idx, header)
    for j, t in enumerate(tasks):
        lines.insert(insert_idx + 1 + j, t)
    queue_file.write_text("\n".join(lines) + "\n")

    return len(tasks)


@hatchet.task(
    name="golem-requeue",
    on_crons=["*/30 * * * *"],
    execution_timeout="5m",
)
def golem_requeue(input, context):
    """Cron: auto-generate tasks when queue has < 20 pending."""
    added = _auto_requeue(queue_file=QUEUE_FILE)
    return {"pending_count": _count_pending(QUEUE_FILE), "added": added}


@hatchet.task(
    name="golem-health",
    on_crons=["*/15 * * * *"],
    execution_timeout="3m",
)
def golem_health(input, context):
    """Cron: run gemmule-health --daemon and log result."""
    try:
        proc = subprocess.run(
            ["python3", str(GEMMULE_HEALTH_SCRIPT), "--daemon"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = proc.stdout.strip()
        return {
            "exit_code": proc.returncode,
            "output": output[:2000],
            "stderr": proc.stderr[:1000],
            "success": proc.returncode in (0, 2),
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "output": "", "error": "timeout", "success": False}
    except Exception as e:
        return {"exit_code": -1, "output": "", "error": str(e)[:200], "success": False}


def main():
    worker = hatchet.worker(
        "golem-worker",
        workflows=[
            golem_zhipu,
            golem_infini,
            golem_volcano,
            golem_gemini,
            golem_codex,
            golem_requeue,
            golem_health,
        ],
    )
    print("Hatchet golem worker started")
    worker.start()


if __name__ == "__main__":
    main()
