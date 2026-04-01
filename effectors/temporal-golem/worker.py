#!/usr/bin/env python3
from __future__ import annotations

"""Temporal worker for golem task execution.

Polls the 'golem-tasks' task queue and runs golem commands as activities.
Each activity heartbeats every 30s, has a 30min timeout, and a retry policy.
"""

import asyncio
import os
import sys
from datetime import timedelta
from pathlib import Path

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

# Make local imports work when run from any cwd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from models import GolemResult, GolemTaskSpec  # noqa: E402

with workflow.unsafe.imports_passed_through():
    pass  # future: import heavy deps here

TASK_QUEUE = "golem-tasks"

# Resolve germline root: two levels up from this file's parent directory
_GERMLINE_ROOT = str(Path(__file__).resolve().parent.parent.parent)

# Activity timeout
ACTIVITY_TIMEOUT = timedelta(minutes=30)
HEARTBEAT_INTERVAL_SECONDS = 30


@activity.defn
async def run_golem_task(provider: str, task: str) -> GolemResult:
    """Execute a single golem command as a Temporal activity.

    Runs ``bash effectors/golem --provider <provider> <task>``, heartbeating
    every 30 seconds while the subprocess runs.  The activity timeout is
    30 minutes (enforced by the workflow options layer).

    Returns a :class:`GolemResult` with exit code, stdout, stderr, and
    timeout status.
    """
    cmd = [
        "bash",
        str(Path(_GERMLINE_ROOT) / "effectors" / "golem"),
        "--provider", provider,
        task,
    ]
    env = {**os.environ, "GOLEM_PROVIDER": provider}

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=_GERMLINE_ROOT,
            env=env,
        )

        # Heartbeat loop — runs while subprocess is alive
        async def _heartbeat_loop() -> None:
            while proc.returncode is None:
                activity.heartbeat(f"provider={provider} task={task!r} running")
                await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)

        heartbeat_task = asyncio.create_task(_heartbeat_loop())

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=ACTIVITY_TIMEOUT.total_seconds()
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return GolemResult(
                provider=provider,
                task=task,
                exit_code=-1,
                stdout="",
                stderr="",
                timed_out=True,
            )
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

        return GolemResult(
            provider=provider,
            task=task,
            exit_code=proc.returncode if proc.returncode is not None else -1,
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
        )

    except Exception as exc:
        return GolemResult(
            provider=provider,
            task=task,
            exit_code=-1,
            stdout="",
            stderr=str(exc),
        )


async def main() -> None:
    """Start the Temporal worker process."""
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client=client,
        task_queue=TASK_QUEUE,
        activities=[run_golem_task],
    )
    print(f"Worker started, polling task queue: {TASK_QUEUE}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
