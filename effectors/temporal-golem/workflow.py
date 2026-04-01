#!/usr/bin/env python3
"""Temporal workflow for golem batch dispatch.

GolemDispatchWorkflow accepts a list of tasks, dispatches them as activities
respecting per-provider concurrency, and reports aggregate results.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

# Use string reference to avoid importing the activity at workflow-parse time.
# Temporal requires workflow code to be deterministic; importing worker.py
# (which has side effects) would break replay.
with workflow.unsafe.imports_passed_through():
    from worker import run_golem_task

# Retry policy: 3 attempts, exponential backoff
_RETRY_POLICY = RetryPolicy(
    maximum_attempts=3,
    initial_interval=timedelta(seconds=10),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
)


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
            }

    @workflow.run
    async def run(self, specs: list[dict]) -> dict:
        """Execute all task specs concurrently and return aggregate results."""
        results = await asyncio.gather(
            *[self._execute_one(s) for s in specs]
        )

        succeeded = sum(1 for r in results if r.get("success"))
        return {
            "total": len(results),
            "succeeded": succeeded,
            "failed": len(results) - succeeded,
            "results": [
                {
                    "task": r.get("task", "")[:100],
                    "provider": r.get("provider", ""),
                    "success": r.get("success", False),
                    "exit_code": r.get("exit_code", -1),
                }
                for r in results
            ],
        }
