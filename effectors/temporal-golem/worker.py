#!/usr/bin/env python3
"""Temporal worker for golem task orchestration.

Polls the 'golem-tasks' task queue and executes golem commands as activities.
Each activity runs `bash effectors/golem --provider X task`, heartbeats every
30s, has a 30min timeout, and a retry policy (3 attempts, exponential backoff).

Usage:
    python worker.py                # Start worker
    python worker.py --help         # Show this help
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import timedelta
from pathlib import Path

from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

TASK_QUEUE = "golem-tasks"
GOLEM_SCRIPT = Path(__file__).resolve().parent.parent / "golem"

# Per-provider concurrency limits (matching golem-daemon config)
PROVIDER_LIMITS = {
    "zhipu": 8,
    "infini": 8,
    "volcano": 16,
    "gemini": 4,
    "codex": 4,
}

# How long we wait between heartbeats
_HEARTBEAT_INTERVAL = 30.0
# Maximum time a single golem invocation may run
_ACTIVITY_TIMEOUT = timedelta(minutes=30)


@activity.defn
async def run_golem_task(task: str, provider: str, max_turns: int = 50) -> dict:
    """Execute a single golem task as a subprocess."""
    cmd = [
        "bash", str(GOLEM_SCRIPT),
        "--provider", provider,
        "--max-turns", str(max_turns),
        task,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, "GOLEM_PROVIDER": provider},
    )

    # Heartbeat while subprocess runs
    async def _heartbeat():
        n = 0
        while True:
            await asyncio.sleep(_HEARTBEAT_INTERVAL)
            n += 1
            try:
                activity.heartbeat(f"{provider}:{task[:60]} tick:{n}")
            except Exception:
                pass

    hb_task = asyncio.create_task(_heartbeat())
    try:
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=_ACTIVITY_TIMEOUT.total_seconds(),
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return {
                "success": False,
                "exit_code": -1,
                "provider": provider,
                "task": task[:200],
                "stdout": "",
                "stderr": "timeout after 30m",
            }
    finally:
        hb_task.cancel()
        try:
            await hb_task
        except asyncio.CancelledError:
            pass

    rc = proc.returncode or 0
    stdout = stdout_bytes.decode(errors="replace")
    stderr = stderr_bytes.decode(errors="replace")

    return {
        "success": rc == 0,
        "exit_code": rc,
        "provider": provider,
        "task": task[:200],
        "stdout": stdout[:4000],
        "stderr": stderr[:2000],
    }


async def main() -> None:
    """Start the Temporal worker."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    # Import workflow here to avoid circular import at module level
    from workflow import GolemDispatchWorkflow

    host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(host)

    # Total concurrent activities across all providers
    max_concurrent = sum(PROVIDER_LIMITS.values())

    worker = Worker(
        client=client,
        task_queue=TASK_QUEUE,
        workflows=[GolemDispatchWorkflow],
        activities=[run_golem_task],
        max_concurrent_activities=max_concurrent,
    )
    print(f"Temporal golem worker started on queue '{TASK_QUEUE}' (max_concurrent={max_concurrent})")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
