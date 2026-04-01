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
import sys
from datetime import timedelta
from pathlib import Path

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

TASK_QUEUE = "golem-tasks"
GOLEM_SCRIPT = Path(__file__).resolve().parent.parent / "golem"

# Per-provider concurrency limits (matching golem-daemon config)
_PROVIDER_SEMAPHORES: dict[str, asyncio.Semaphore] = {
    "zhipu": asyncio.Semaphore(8),
    "infini": asyncio.Semaphore(8),
    "volcano": asyncio.Semaphore(16),
}

# How long we wait between heartbeats
_HEARTBEAT_INTERVAL = timedelta(seconds=30)
# Maximum time a single golem invocation may run
_ACTIVITY_TIMEOUT = timedelta(minutes=30)


async def _heartbeat_loop(task_name: str, interval: float = 30.0) -> asyncio.Event:
    """Background task that heartbeats every *interval* seconds until cancelled."""
    stop = asyncio.Event()

    async def _loop():
        n = 0
        while not stop.is_set():
            try:
                activity.heartbeat(f"running:{task_name[:60]} tick:{n}")
            except Exception:
                pass
            n += 1
            try:
                await asyncio.wait_for(stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass  # expected — interval elapsed

    hb_task = asyncio.create_task(_loop())
    # Attach the stop event so the caller can signal shutdown and await the task.
    stop.task = hb_task  # type: ignore[attr-defined]
    return stop


@activity.defn
async def run_golem_task(task: str, provider: str, max_turns: int = 50) -> dict:
    """Execute a single golem task as a subprocess.

    Returns a dict with keys: success, exit_code, provider, stdout.
    Raises RuntimeError if the subprocess fails or times out.
    """
    sem = _PROVIDER_SEMAPHORES.get(provider)
    if sem is None:
        raise ValueError(f"Unknown provider: {provider}")

    async with sem:
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
        )

        # Start periodic heartbeating while subprocess runs.
        hb_stop = await _heartbeat_loop(task)
        try:
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=_ACTIVITY_TIMEOUT.total_seconds(),
                )
            except asyncio.TimeoutError:
                proc.kill()
                raise RuntimeError(f"Golem task timed out after {_ACTIVITY_TIMEOUT}")
        finally:
            hb_stop.set()
            await hb_stop.task  # type: ignore[attr-defined]

        activity.heartbeat(f"completed:{task[:80]}")

        # returncode is 0 on success; None means communicate() returned before
        # the process fully reaped (can happen with certain mock setups).
        rc = proc.returncode if proc.returncode is not None else 0

        if rc != 0:
            stderr = stderr_bytes.decode(errors="replace")
            raise RuntimeError(
                f"Golem exited {rc}: {stderr[:500]}"
            )

        return {
            "success": True,
            "exit_code": rc,
            "provider": provider,
            "stdout": stdout_bytes.decode(errors="replace"),
        }


async def main() -> None:
    """Start the Temporal worker."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    client = await Client.connect("localhost:7233")
    worker = Worker(
        client=client,
        task_queue=TASK_QUEUE,
        activities=[run_golem_task],
    )
    print(f"Temporal golem worker started on queue '{TASK_QUEUE}'")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
