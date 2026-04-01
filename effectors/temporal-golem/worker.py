"""Temporal worker that polls 'golem-tasks' and executes golem commands as activities."""
from __future__ import annotations

import asyncio
import subprocess
import os
import sys
from pathlib import Path
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.worker import Worker

# ---------------------------------------------------------------------------
# Activity — run a single golem command
# ---------------------------------------------------------------------------

GOLEM_SCRIPT = Path(__file__).resolve().parent.parent / "golem"

# Per-provider concurrency limits (shared via module-level semaphore dict)
_PROVIDER_SEMAPHORES: dict[str, asyncio.Semaphore] = {
    "zhipu": asyncio.Semaphore(8),
    "infini": asyncio.Semaphore(8),
    "volcano": asyncio.Semaphore(16),
}


@activity.defn
async def run_golem_task(task: str, provider: str, max_turns: int = 50) -> dict:
    """Execute a single golem task.

    Runs ``bash effectors/golem --provider <provider> --max-turns <N> <task>``.
    Heartbeats every 30 s while the subprocess is alive.  Raises
    ``temporalio.exceptions.ActivityError`` on non-zero exit so Temporal
    triggers the retry policy.
    """
    semaphore = _PROVIDER_SEMAPHORES.get(provider, asyncio.Semaphore(4))
    async with semaphore:
        cmd = [
            "bash",
            str(GOLEM_SCRIPT),
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

        async def _heartbeat_loop() -> None:
            while proc.returncode is None:
                try:
                    activity.heartbeat("golem-running")
                except Exception:
                    pass
                await asyncio.sleep(30)

        heartbeat_task = asyncio.create_task(_heartbeat_loop())

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timedelta(minutes=30).total_seconds()
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError(f"Golem task timed out after 30 min: {task[:80]}")
        finally:
            heartbeat_task.cancel()

        exit_code = proc.returncode or 0
        result = {
            "task": task[:200],
            "provider": provider,
            "exit_code": exit_code,
            "stdout": (stdout or b"").decode(errors="replace")[:4000],
            "stderr": (stderr or b"").decode(errors="replace")[:2000],
            "success": exit_code == 0,
        }

        if exit_code != 0:
            raise RuntimeError(
                f"Golem exited {exit_code}: {(stderr or b'').decode(errors='replace')[:300]}"
            )

        return result


# ---------------------------------------------------------------------------
# Worker entry-point
# ---------------------------------------------------------------------------

TASK_QUEUE = "golem-tasks"


async def main() -> None:
    """Start the Temporal worker."""
    from workflow import GolemDispatchWorkflow

    worker = Worker(
        client=await _connect_client(),
        task_queue=TASK_QUEUE,
        workflows=[GolemDispatchWorkflow],
        activities=[run_golem_task],
    )
    print(f"Temporal worker started on queue '{TASK_QUEUE}'")
    await worker.run()


async def _connect_client():
    from temporalio.client import Client

    host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    return await Client.connect(host, namespace=namespace)


if __name__ == "__main__":
    asyncio.run(main())
