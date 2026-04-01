"""temporal-golem workflow — GolemDispatchWorkflow with per-provider concurrency."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from worker import TASK_QUEUE, run_golem_task


@dataclass
class GolemTaskSpec:
    """Specification for a single golem task."""
    task: str
    provider: str = "zhipu"
    max_turns: int = 50


@dataclass
class GolemTaskResult:
    """Result of a single golem task execution."""
    task: str
    provider: str
    success: bool = False
    exit_code: Optional[int] = None


@dataclass
class GolemBatchResult:
    """Aggregated result of a batch of golem tasks."""
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[GolemTaskResult] = field(default_factory=list)


# Retry policy: 3 attempts, exponential backoff (2x), 30-min timeout per attempt
_RETRY_POLICY_ARGS = {
    "start_to_close_timeout": 1800,  # 30 min per attempt
    "retry_policy": RetryPolicy(
        maximum_attempts=3,
        backoff_coefficient=2.0,
        initial_interval=10,
    ),
}


@workflow.defn
class GolemDispatchWorkflow:
    """Workflow that dispatches golem tasks with per-provider concurrency control."""

    @workflow.run
    async def run(self, specs: list[dict]) -> dict:
        """Accept a list of task specs, dispatch them, return batch result."""
        tasks = [GolemTaskSpec(**s) for s in specs]
        results: list[GolemTaskResult] = []

        # Group tasks by provider for concurrency control
        provider_tasks: dict[str, list[GolemTaskSpec]] = {}
        for spec in tasks:
            provider_tasks.setdefault(spec.provider, []).append(spec)

        # Execute all provider groups concurrently
        import asyncio
        coros = []
        for provider, provider_specs in provider_tasks.items():
            coros.append(self._run_provider_batch(provider, provider_specs, results))

        await asyncio.gather(*coros)

        succeeded = sum(1 for r in results if r.success)
        failed = len(results) - succeeded
        batch = GolemBatchResult(
            total=len(results),
            succeeded=succeeded,
            failed=failed,
            results=results,
        )
        return {
            "total": batch.total,
            "succeeded": batch.succeeded,
            "failed": batch.failed,
            "results": [
                {"task": r.task, "provider": r.provider, "success": r.success, "exit_code": r.exit_code}
                for r in batch.results
            ],
        }

    async def _run_provider_batch(
        self, provider: str, specs: list[GolemTaskSpec], results: list[GolemTaskResult],
    ) -> None:
        """Run a batch of tasks for one provider with concurrency limit."""
        import asyncio

        limits = {"zhipu": 8, "infini": 8, "volcano": 16}
        limit = limits.get(provider, 4)
        sem = asyncio.Semaphore(limit)

        async def _run_one(spec: GolemTaskSpec) -> None:
            async with sem:
                try:
                    result = await workflow.execute_activity(
                        run_golem_task,
                        args=[spec.task, spec.provider, spec.max_turns],
                        task_queue=TASK_QUEUE,
                        **_RETRY_POLICY_ARGS,
                    )
                    results.append(GolemTaskResult(
                        task=spec.task, provider=spec.provider,
                        success=True, exit_code=0,
                    ))
                except Exception:
                    results.append(GolemTaskResult(
                        task=spec.task, provider=spec.provider,
                        success=False, exit_code=1,
                    ))

        await asyncio.gather(*[_run_one(s) for s in specs])
