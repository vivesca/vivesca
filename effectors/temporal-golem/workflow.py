#!/usr/bin/env python3
from __future__ import annotations

"""GolemDispatchWorkflow — dispatches golem tasks respecting per-provider concurrency.

Usage from a client::

    result = await client.execute_workflow(
        GolemDispatchWorkflow.run,
        GolemDispatchInput(tasks=[...]),
        id="golem-dispatch-2026-04-01-001",
        task_queue="golem-tasks",
    )
"""

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from models import GolemDispatchInput, GolemDispatchOutput, GolemResult, GolemTaskSpec

# ── Provider concurrency limits ──────────────────────────────────────

PROVIDER_CONCURRENCY: dict[str, int] = {
    "zhipu": 8,
    "infini": 8,
    "volcano": 16,
}
DEFAULT_CONCURRENCY = 4


# ── Retry policy (shared) ────────────────────────────────────────────

GOLEM_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=10),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=3,
    non_retryable_error_types=["temporalio.exceptions.ActivityError"],
)

# ── Workflow ─────────────────────────────────────────────────────────


@workflow.defn
class GolemDispatchWorkflow:
    """Dispatch golem tasks, respecting per-provider concurrency."""

    @workflow.run
    async def run(self, params: GolemDispatchInput) -> GolemDispatchOutput:
        results: list[GolemResult] = []

        # Bucket tasks by provider.
        buckets: dict[str, list[GolemTaskSpec]] = {}
        for spec in params.tasks:
            buckets.setdefault(spec.provider, []).append(spec)

        async def _run_one(spec: GolemTaskSpec) -> GolemResult:
            return await workflow.execute_activity(
                "run_golem_task",
                args=[spec.provider, spec.task],
                schedule_to_close_timeout=timedelta(minutes=30),
                heartbeat_timeout=timedelta(seconds=90),
                retry_policy=GOLEM_RETRY,
            )

        async def _run_bucket(provider: str, tasks: list[GolemTaskSpec]) -> None:
            limit = PROVIDER_CONCURRENCY.get(provider, DEFAULT_CONCURRENCY)
            sem = asyncio.Semaphore(limit)
            pending: list[asyncio.Task[GolemResult]] = []

            async def _guarded(spec: GolemTaskSpec) -> GolemResult:
                async with sem:
                    return await _run_one(spec)

            for t in tasks:
                pending.append(asyncio.create_task(_guarded(t)))

            for coro in asyncio.as_completed(pending):
                res = await coro
                results.append(res)

        # Run all provider buckets concurrently.
        bucket_tasks = [
            asyncio.create_task(_run_bucket(p, ts))
            for p, ts in buckets.items()
        ]
        await asyncio.gather(*bucket_tasks)

        output = GolemDispatchOutput(
            results=results,
            total=len(results),
            succeeded=sum(1 for r in results if r.ok),
            failed=sum(1 for r in results if not r.ok),
        )
        return output
