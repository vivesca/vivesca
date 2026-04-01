#!/usr/bin/env python3
from __future__ import annotations

"""GolemDispatchWorkflow — dispatches golem tasks with per-provider concurrency.

Accepts a list of tasks, groups them by provider, and runs each group
concurrently up to the provider's concurrency limit.  Results are collected
and returned as a :class:`GolemDispatchOutput`.
"""

from datetime import timedelta
from typing import List

from temporalio import workflow
from temporalio.common import RetryPolicy

# Re-export models for convenience (tests import from here)
from models import GolemDispatchInput, GolemDispatchOutput, GolemResult, GolemTaskSpec  # noqa: F401

with workflow.unsafe.imports_passed_through():
    from worker import run_golem_task

# ── Per-provider concurrency limits ───────────────────────────────────
PROVIDER_CONCURRENCY = {
    "zhipu": 8,
    "infini": 8,
    "volcano": 16,
}
DEFAULT_CONCURRENCY = 4

# ── Retry policy ──────────────────────────────────────────────────────
GOLEM_RETRY = RetryPolicy(
    maximum_attempts=3,
    initial_interval=timedelta(seconds=10),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=300),
    non_retryable_error_types=["temporalio.exceptions.ActivityError"],
)


@workflow.defn
class GolemDispatchWorkflow:
    """Workflow that dispatches a batch of golem tasks.

    Tasks are grouped by provider.  Within each provider group, up to
    ``PROVIDER_CONCURRENCY[provider]`` tasks run concurrently.  Provider
    groups run in parallel.
    """

    @workflow.run
    async def run(self, inp: GolemDispatchInput) -> GolemDispatchOutput:
        results: List[GolemResult] = []

        # Group tasks by provider
        provider_groups: dict[str, List[GolemTaskSpec]] = {}
        for spec in inp.tasks:
            provider_groups.setdefault(spec.provider, []).append(spec)

        # Dispatch each provider group concurrently
        async def _run_group(provider: str, specs: List[GolemTaskSpec]) -> None:
            concurrency = PROVIDER_CONCURRENCY.get(provider, DEFAULT_CONCURRENCY)
            semaphore = asyncio.Semaphore(concurrency)

            async def _run_one(spec: GolemTaskSpec) -> None:
                async with semaphore:
                    result = await workflow.execute_activity(
                        run_golem_task,
                        spec.provider,
                        spec.task,
                        start_to_close_timeout=timedelta(minutes=30),
                        heartbeat_timeout=timedelta(seconds=60),
                        retry_policy=GOLEM_RETRY,
                    )
                    results.append(result)

            await asyncio.gather(*[_run_one(s) for s in specs])

        import asyncio
        await asyncio.gather(*[
            _run_group(p, specs) for p, specs in provider_groups.items()
        ])

        succeeded = sum(1 for r in results if r.ok)
        return GolemDispatchOutput(
            results=results,
            total=len(results),
            succeeded=succeeded,
            failed=len(results) - succeeded,
        )
