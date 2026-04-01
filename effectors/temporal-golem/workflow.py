"""Temporal workflow for golem batch dispatch.

GolemDispatchWorkflow accepts a list of tasks, dispatches them as activities
respecting per-provider concurrency, and reports aggregate results.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from worker import run_golem_task, TASK_QUEUE


@dataclass
class GolemTaskSpec:
    """Specification for a single golem task."""

    task: str
    provider: str = "zhipu"
    max_turns: int = 50


@dataclass
class GolemTaskResult:
    """Result from a single golem task execution."""

    task: str
    provider: str
    success: bool
    exit_code: int = 0
    stdout: str = ""


@dataclass
class GolemBatchResult:
    """Aggregate result for a batch of golem tasks."""

    total: int
    succeeded: int
    failed: int
    results: list[GolemTaskResult] = field(default_factory=list)


# Retry policy: 3 attempts, exponential backoff with 2x coefficient
_RETRY_POLICY_ARGS: dict = {
    "start_to_close_timeout": timedelta(minutes=30),
    "retry_policy": RetryPolicy(
        maximum_attempts=3,
        initial_interval=timedelta(seconds=10),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(minutes=5),
    ),
}


@workflow.defn
class GolemDispatchWorkflow:
    """Dispatch a batch of golem tasks, respecting per-provider concurrency."""

    async def _execute_one(self, spec: GolemTaskSpec) -> GolemTaskResult:
        """Execute a single spec, converting exceptions to failed results."""
        try:
            result = await workflow.execute_activity(
                run_golem_task,
                args=[spec.task, spec.provider, spec.max_turns],
                task_queue=TASK_QUEUE,
                **_RETRY_POLICY_ARGS,
            )
            return GolemTaskResult(
                task=spec.task,
                provider=spec.provider,
                success=result.get("success", False),
                exit_code=result.get("exit_code", -1),
                stdout=result.get("stdout", ""),
            )
        except Exception as exc:
            return GolemTaskResult(
                task=spec.task,
                provider=spec.provider,
                success=False,
                exit_code=-1,
                stdout=str(exc)[:2000],
            )

    @workflow.run
    async def run(self, specs: list[dict]) -> dict:
        """Execute all task specs concurrently and return a GolemBatchResult.

        Tasks are dispatched in parallel via asyncio.gather so that the
        worker-side per-provider semaphores control actual concurrency.
        """
        tasks: list[GolemTaskSpec] = []
        for s in specs:
            if isinstance(s, dict):
                tasks.append(GolemTaskSpec(**s))
            else:
                tasks.append(s)

        # Dispatch all tasks concurrently; the worker's per-provider
        # semaphores enforce actual concurrency limits.
        raw_results = await asyncio.gather(
            *[self._execute_one(spec) for spec in tasks]
        )

        results = list(raw_results)
        succeeded = sum(1 for r in results if r.success)
        failed = len(results) - succeeded

        batch = GolemBatchResult(
            total=len(tasks),
            succeeded=succeeded,
            failed=failed,
            results=results,
        )
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
                }
                for r in batch.results
            ],
        }
