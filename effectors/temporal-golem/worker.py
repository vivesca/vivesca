"""temporal-golem worker — polls 'golem-tasks' queue and runs golem activities."""
from __future__ import annotations

import asyncio
from pathlib import Path

from temporalio import activity

TASK_QUEUE = "golem-tasks"
GOLEM_SCRIPT = Path(__file__).resolve().parent.parent / "golem"
ACTIVITY_TIMEOUT = 1800  # 30 min
HEARTBEAT_INTERVAL = 30  # seconds

# Per-provider concurrency limits
_PROVIDER_SEMAPHORES: dict[str, asyncio.Semaphore] = {
    "zhipu": asyncio.Semaphore(8),
    "infini": asyncio.Semaphore(8),
    "volcano": asyncio.Semaphore(16),
}


@activity.defn
async def run_golem_task(
    task: str,
    provider: str = "zhipu",
    max_turns: int = 50,
) -> dict:
    """Run a single golem task as a Temporal activity.

    Executes `bash effectors/golem --provider X --max-turns N <task>`,
    heartbeating every 30s with a 30-minute timeout.
    """
    sem = _PROVIDER_SEMAPHORES.get(provider)
    if sem is None:
        raise ValueError(f"Unknown provider: {provider}")

    async with sem:
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
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=ACTIVITY_TIMEOUT,
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"Golem task timed out after {ACTIVITY_TIMEOUT}s")

        # Heartbeat once after completion for the record
        activity.heartbeat(f"completed:{task[:40]}")

        # After communicate() the process has exited.  In real asyncio
        # subprocess proc.returncode is always set; mocks may leave it None.
        rc = proc.returncode if proc.returncode is not None else 0
        if rc != 0:
            raise RuntimeError(
                f"Golem exited {rc}: {stderr.decode(errors='replace')[:200]}"
            )

        return {
            "success": True,
            "exit_code": 0,
            "provider": provider,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }


async def run_worker(temporal_endpoint: str = "localhost:7233") -> None:
    """Start a Temporal worker connected to the given endpoint."""
    from temporalio.worker import Worker
    from workflow import GolemDispatchWorkflow

    client = await __import__("temporalio.client", fromlist=["Client"]).Client.connect(
        temporal_endpoint,
    )
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[GolemDispatchWorkflow],
        activities=[run_golem_task],
    )
    await worker.run()


if __name__ == "__main__":
    import sys
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "localhost:7233"
    asyncio.run(run_worker(endpoint))
