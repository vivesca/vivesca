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
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from worker import (
        DEFAULT_LIMIT,
        PROVIDER_LIMITS,
        PROVIDER_RATE_WINDOWS,
        run_golem_task,
    )

# Retry policy: 5 attempts (up from 3), longer backoff for rate limits
_RETRY_POLICY = RetryPolicy(
    maximum_attempts=5,
    initial_interval=timedelta(seconds=30),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=30),
)
@workflow.defn
class GolemDispatchWorkflow:
    """Dispatch a batch of golem tasks, respecting per-provider concurrency."""

    def _dispatch_candidates(self, affinity_provider: str) -> list[str]:
        """Return candidate runtime providers for a task affinity."""
        candidates = [affinity_provider]
        for provider_name in PROVIDER_LIMITS:
            if provider_name != affinity_provider:
                candidates.append(provider_name)
        return candidates

    def _pick_dispatch_provider(
        self,
        affinity_provider: str,
        provider_cooldown_until: dict[str, float],
        provider_running: dict[str, int],
    ) -> str | None:
        """Pick a runtime provider, preserving affinity unless it is cooled down."""
        affinity_cooldown = provider_cooldown_until.get(affinity_provider, 0)
        if affinity_cooldown <= workflow.time():
            running_count = provider_running.get(affinity_provider, 0)
            if running_count < PROVIDER_LIMITS.get(affinity_provider, DEFAULT_LIMIT):
                return affinity_provider
            return None

        for candidate in self._dispatch_candidates(affinity_provider)[1:]:
            cooldown_until = provider_cooldown_until.get(candidate, 0)
            if cooldown_until > workflow.time():
                continue
            running_count = provider_running.get(candidate, 0)
            if running_count < PROVIDER_LIMITS.get(candidate, DEFAULT_LIMIT):
                return candidate
        return None

    @staticmethod
    def _cooldown_seconds_from_error(error_message: str, dispatch_provider: str) -> int:
        """Extract the cooldown window embedded in a rate-limit error."""
        marker = "reset in "
        if marker in error_message:
            seconds_fragment = error_message.split(marker, 1)[1].split("s", 1)[0]
            if seconds_fragment.isdigit():
                return int(seconds_fragment)
        return PROVIDER_RATE_WINDOWS.get(dispatch_provider, 1800)

    async def _execute_one(self, spec: dict, dispatch_provider: str) -> dict:
        """Execute a single spec, converting exceptions to failed results."""
        task = spec.get("task", "")
        affinity_provider = spec.get("provider", "zhipu")
        max_turns = spec.get("max_turns", 50)

        try:
            result = await workflow.execute_activity(
                run_golem_task,
                args=[task, dispatch_provider, max_turns],
                start_to_close_timeout=timedelta(minutes=35),
                heartbeat_timeout=timedelta(seconds=90),
                retry_policy=_RETRY_POLICY,
            )
            result["provider"] = affinity_provider
            result["dispatch_provider"] = dispatch_provider
            return result
        except Exception as exc:
            error_message = str(exc)
            rate_limited = "RATE_LIMITED" in error_message
            return {
                "task": task[:200],
                "provider": affinity_provider,
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": error_message[:2000],
                "rate_limited": rate_limited,
                "dispatch_provider": dispatch_provider,
                "cooldown_seconds": (
                    self._cooldown_seconds_from_error(error_message, dispatch_provider)
                    if rate_limited
                    else 0
                ),
            }

    async def _run_pending_queue(
        self,
        specs: list[dict],
        provider_cooldown_until: dict[str, float] | None = None,
    ) -> list[dict]:
        """Run pending tasks with cooldown-aware cross-provider migration."""
        pending_specs = list(specs)
        results: list[dict] = []
        running_tasks: dict[asyncio.Task, tuple[str, dict]] = {}
        provider_running: dict[str, int] = {}
        provider_cooldown_until = dict(provider_cooldown_until or {})

        while pending_specs or running_tasks:
            current_time = workflow.time()
            for provider_name, cooldown_until in list(provider_cooldown_until.items()):
                if cooldown_until <= current_time:
                    del provider_cooldown_until[provider_name]

            dispatched_any = False
            remaining_specs: list[dict] = []
            for spec in pending_specs:
                affinity_provider = spec.get("provider", "zhipu")
                dispatch_provider = self._pick_dispatch_provider(
                    affinity_provider,
                    provider_cooldown_until,
                    provider_running,
                )
                if dispatch_provider is None:
                    remaining_specs.append(spec)
                    continue

                task_handle = asyncio.create_task(self._execute_one(spec, dispatch_provider))
                running_tasks[task_handle] = (dispatch_provider, spec)
                provider_running[dispatch_provider] = provider_running.get(dispatch_provider, 0) + 1
                dispatched_any = True

            pending_specs = remaining_specs
            if not running_tasks:
                break

            if dispatched_any:
                done_tasks, _ = await asyncio.wait(
                    running_tasks.keys(),
                    return_when=asyncio.FIRST_COMPLETED,
                )
            else:
                if provider_cooldown_until:
                    earliest_cooldown = min(provider_cooldown_until.values())
                    sleep_seconds = max(earliest_cooldown - workflow.time(), 0.01)
                    await asyncio.sleep(sleep_seconds)
                    continue
                done_tasks, _ = await asyncio.wait(
                    running_tasks.keys(),
                    return_when=asyncio.FIRST_COMPLETED,
                )

            for completed_task in done_tasks:
                dispatch_provider, _ = running_tasks.pop(completed_task)
                provider_running[dispatch_provider] = max(
                    0,
                    provider_running.get(dispatch_provider, 0) - 1,
                )
                result = await completed_task
                if result.get("rate_limited"):
                    cooldown_seconds = result.get("cooldown_seconds") or PROVIDER_RATE_WINDOWS.get(
                        dispatch_provider,
                        1800,
                    )
                    provider_cooldown_until[dispatch_provider] = workflow.time() + cooldown_seconds
                results.append(result)

        return results

    @workflow.run
    async def run(self, specs: list[dict]) -> dict:
        """Execute all task specs with cooldown-aware provider dispatch."""
        workflow.logger.info(
            f"Dispatching {len(specs)} tasks across providers: "
            + ", ".join(spec.get("provider", "zhipu") for spec in specs)
        )
        results = await self._run_pending_queue(specs)

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
                    "dispatch_provider": r.get("dispatch_provider", r.get("provider", "")),
                    "success": r.get("success", False),
                    "exit_code": r.get("exit_code", -1),
                    "rate_limited": r.get("rate_limited", False),
                }
                for r in results
            ],
        }
