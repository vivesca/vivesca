#!/usr/bin/env python3
from __future__ import annotations

"""Temporal worker for golem task execution.

Polls the 'golem-tasks' task queue and executes golem commands as activities.
Each activity runs ``bash effectors/golem --provider X <task>``, heartbeats
every 30 s, has a 30 min timeout, and retries up to 3 times with exponential
backoff.
"""

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from workflow import GolemDispatchWorkflow

logger = logging.getLogger(__name__)

GERMLINE_ROOT = Path(__file__).resolve().parent.parent.parent
GOLEM_BIN = GERMLINE_ROOT / "effectors" / "golem"

TASK_QUEUE = "golem-tasks"

# ── Activity result ──────────────────────────────────────────────────


@dataclass
class GolemResult:
    """Outcome of a single golem invocation."""

    provider: str
    task: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def __str__(self) -> str:
        status = "OK" if self.ok else "FAIL"
        return (
            f"[{status}] provider={self.provider} exit={self.exit_code} "
            f"task={self.task!r}"
        )


# ── Activity ─────────────────────────────────────────────────────────


@activity.defn
async def run_golem_task(provider: str, task: str) -> GolemResult:
    """Run a single golem command as a subprocess.

    Heartbeats every 30 s so Temporal knows the activity is alive.
    Enforced timeout is handled by the activity's schedule-to-close
    timeout (30 min) configured on the worker.
    """
    cmd = ["bash", str(GOLEM_BIN), "--provider", provider, task]
    logger.info("Starting golem task: %s", " ".join(cmd))

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(GERMLINE_ROOT),
        env={**os.environ, "GOLEM_PROVIDER": provider},
    )

    async def _heartbeat_loop() -> None:
        while proc.returncode is None:
            try:
                activity.heartbeat(f"running: provider={provider} task={task!r}")
            except Exception:
                logger.debug("heartbeat failed (activity may be cancelled)")
                break
            await asyncio.sleep(30)

    hb_task = asyncio.create_task(_heartbeat_loop())
    timed_out = False

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=1800  # 30 min hard cap
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        stdout_bytes, stderr_bytes = b"", b"timeout after 1800s"
        timed_out = True
    finally:
        hb_task.cancel()
        try:
            await hb_task
        except asyncio.CancelledError:
            pass

    result = GolemResult(
        provider=provider,
        task=task,
        exit_code=proc.returncode or 1,
        stdout=stdout_bytes.decode(errors="replace"),
        stderr=stderr_bytes.decode(errors="replace"),
        timed_out=timed_out,
    )
    logger.info("Golem task finished: %s", result)
    return result


# ── Worker entrypoint ────────────────────────────────────────────────

async def run_worker(temporal_address: str = "localhost:7233") -> None:
    """Start the Temporal worker, polling *golem-tasks*."""
    client = await Client.connect(temporal_address)

    worker = Worker(
        client=client,
        task_queue=TASK_QUEUE,
        workflows=[GolemDispatchWorkflow],
        activities=[run_golem_task],
        activity_executor=None,  # use default asyncio executor
        max_concurrent_activities=50,
    )

    logger.info("Worker started, polling task queue: %s", TASK_QUEUE)
    await worker.run()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    addr = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    asyncio.run(run_worker(addr))


if __name__ == "__main__":
    main()
