"""GolemDispatchWorkflow — accepts a task list, dispatches with per-provider concurrency."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities (resolved at runtime by Temporal worker)
with workflow.unsafe.imports_passed_through():
    from worker import run_golem_task

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class GolemTaskSpec:
    """A single task to be dispatched to a golem worker."""
    task: str
    provider: str = "zhipu"
    max_turns: int = 50


@dataclass
class GolemTaskResult:
    """Result from a single golem execution."""
    task: str
    provider: str
    success: bool
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""


@dataclass
class GolemBatchResult:
    """Aggregated result for a whole batch."""
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[GolemTaskResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Retry policy (shared)
# ---------------------------------------------------------------------------

_RETRY_POLICY_ARGS = dict(
    start_to_close_timeout=timedelta(minutes=30),
    heartbeat_timeout=timedelta(seconds=90),
    retry_policy=RetryPolicy(
        maximum_attempts=3,
        initial_interval=timedelta(seconds=10),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(minutes=5),
    ),
)


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

@workflow.defn
class GolemDispatchWorkflow:
    """Dispatch a list of golem tasks, respecting per-provider concurrency.

    The workflow groups tasks by provider and dispatches them as parallel
    activity calls.  It collects all results and returns a
    ``GolemBatchResult``.
    """

    @workflow.run
    async def run(self, specs: list[dict]) -> dict:
        """Accept a list of task dicts ``[{task, provider, max_turns}]``."""
        parsed = [GolemTaskSpec(**s) for s in specs]

        # Launch all activities concurrently — per-provider concurrency is
        # enforced by semaphores in the worker.
        futures: list[asyncio.Coroutine] = []
        for spec in parsed:
            fut = workflow.execute_activity(
                run_golem_task,
                args=[spec.task, spec.provider, spec.max_turns],
                **_RETRY_POLICY_ARGS,
            )
            futures.append(fut)

        raw_results = await asyncio.gather(*futures, return_exceptions=True)

        results: list[GolemTaskResult] = []
        for spec, raw in zip(parsed, raw_results):
            if isinstance(raw, Exception):
                results.append(GolemTaskResult(
                    task=spec.task[:200],
                    provider=spec.provider,
                    success=False,
                    exit_code=-1,
                    stderr=str(raw)[:2000],
                ))
            else:
                results.append(GolemTaskResult(
                    task=raw.get("task", spec.task[:200]),
                    provider=raw.get("provider", spec.provider),
                    success=raw.get("success", False),
                    exit_code=raw.get("exit_code", -1),
                    stdout=raw.get("stdout", ""),
                    stderr=raw.get("stderr", ""),
                ))

        succeeded = sum(1 for r in results if r.success)
        batch = GolemBatchResult(
            total=len(results),
            succeeded=succeeded,
            failed=len(results) - succeeded,
            results=results,
        )
        # Return as plain dicts for Temporal serialisation
        return {
            "total": batch.total,
            "succeeded": batch.succeeded,
            "failed": batch.failed,
            "results": [
                {
                    "task": r.task,
                    "provider": r.provider,
                    "success": r.success,
                    "exit_code": r.exit_code,
                    "stdout": r.stdout,
                    "stderr": r.stderr,
                }
                for r in batch.results
            ],
        }
