#!/usr/bin/env python3
"""Temporal workflow for golem batch dispatch.

GolemDispatchWorkflow accepts a list of tasks, dispatches them as activities
respecting per-provider concurrency (matching golem-daemon limits), and
reports aggregate results.

Ported from golem-daemon: per-provider concurrency, rate-limit aware retry,
adaptive throttling.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import timedelta
from itertools import islice

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from worker import run_golem_task, PROVIDER_LIMITS, DEFAULT_LIMIT

# Retry policy: 5 attempts (up from 3), longer backoff for rate limits
_RETRY_POLICY = RetryPolicy(
    maximum_attempts=5,
    initial_interval=timedelta(seconds=30),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=30),
)


def _chunked(iterable, size):
    """Yield successive chunks of `size` from iterable."""
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk


@workflow.defn
class GolemDispatchWorkflow:
    """Dispatch a batch of golem tasks, respecting per-provider concurrency."""

    async def _execute_one(self, spec: dict) -> dict:
        """Execute a single spec, converting exceptions to failed results."""
        task = spec.get("task", "")
        provider = spec.get("provider", "zhipu")
        max_turns = spec.get("max_turns", 50)

        try:
            result = await workflow.execute_activity(
                run_golem_task,
                args=[task, provider, max_turns],
                start_to_close_timeout=timedelta(minutes=35),
                heartbeat_timeout=timedelta(seconds=90),
                retry_policy=_RETRY_POLICY,
            )
            return result
        except Exception as exc:
            return {
                "task": task[:200],
                "provider": provider,
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(exc)[:2000],
                "rate_limited": "RATE_LIMITED" in str(exc),
            }

    async def _execute_provider_batch(
        self, provider: str, specs: list[dict]
    ) -> list[dict]:
        """Execute tasks for a single provider, respecting concurrency limit.

        Runs tasks in chunks of the provider's concurrency limit.
        Each chunk runs in parallel; chunks are sequential.
        """
        limit = PROVIDER_LIMITS.get(provider, DEFAULT_LIMIT)
        results = []
        for chunk in _chunked(specs, limit):
            chunk_results = await asyncio.gather(
                *[self._execute_one(s) for s in chunk]
            )
            results.extend(chunk_results)
        return results

    @workflow.run
    async def run(self, specs: list[dict]) -> dict:
        """Execute all task specs with per-provider concurrency control."""
        # Group tasks by provider
        by_provider: dict[str, list[dict]] = defaultdict(list)
        for spec in specs:
            provider = spec.get("provider", "zhipu")
            by_provider[provider].append(spec)

        workflow.logger.info(
            f"Dispatching {len(specs)} tasks across {len(by_provider)} providers: "
            + ", ".join(f"{p}={len(s)}" for p, s in by_provider.items())
        )

        # Run all providers in parallel, each respecting its own concurrency limit
        provider_results = await asyncio.gather(
            *[
                self._execute_provider_batch(provider, provider_specs)
                for provider, provider_specs in by_provider.items()
            ]
        )

        # Flatten results
        results = []
        for batch in provider_results:
            results.extend(batch)

        succeeded = sum(1 for r in results if r.get("success"))
        rate_limited = sum(1 for r in results if r.get("rate_limited"))
        return {
            "total": len(results),
            "succeeded": succeeded,
            "failed": len(results) - succeeded,
            "rate_limited": rate_limited,
            "results": [
                {
                    "task": r.get("task", "")[:100],
                    "provider": r.get("provider", ""),
                    "success": r.get("success", False),
                    "exit_code": r.get("exit_code", -1),
                    "rate_limited": r.get("rate_limited", False),
                }
                for r in results
            ],
        }
