#!/usr/bin/env python3
"""Temporal workflow for golem batch dispatch.

GolemDispatchWorkflow accepts a list of tasks, dispatches them as activities
respecting per-provider concurrency, and reviews results before reporting.

Supports two execution modes:
  - "raw" (default): subprocess via `claude --print` (fast, battle-tested)
  - "graph": LangGraph agent with plan→execute→verify→review (structured, auditable)
"""
from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy, TypedSearchAttributes, SearchAttributeKey

with workflow.unsafe.imports_passed_through():
    from worker import run_golem_task, run_golem_graph_task, review_golem_result

# #6: Custom search attributes for Temporal UI filtering
SA_PROVIDER = SearchAttributeKey.for_keyword("GolemProvider")
SA_VERDICT = SearchAttributeKey.for_keyword("GolemVerdict")
SA_TASK_ID = SearchAttributeKey.for_keyword("GolemTaskId")

# Retry policy: 2 attempts max (golem tasks mutate files, not safely retriable)
_RETRY_POLICY = RetryPolicy(
    maximum_attempts=2,
    initial_interval=timedelta(seconds=10),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
)

# Review has no retries — it's local and fast
_REVIEW_RETRY = RetryPolicy(maximum_attempts=1)



@workflow.defn
class GolemDispatchWorkflow:
    """Dispatch a batch of golem tasks, review results, report aggregate."""

    def __init__(self) -> None:
        self._approval_signals: dict[str, str] = {}  # task_id -> "approve"|"reject"

    @workflow.signal
    async def approve_task(self, task_id: str) -> None:
        """Signal to approve a held task."""
        self._approval_signals[task_id] = "approve"

    @workflow.signal
    async def reject_task(self, task_id: str) -> None:
        """Signal to reject a held task."""
        self._approval_signals[task_id] = "reject"

    async def _execute_one(self, spec: dict) -> dict:
        """Execute a single spec, then review the result."""
        task = spec.get("task", "")
        provider = spec.get("provider", "zhipu")
        max_turns = spec.get("max_turns", 50)
        mode = spec.get("mode", "raw")

        # #3: Version guard — new code paths gated behind patched()
        use_review_v2 = workflow.patched("review-v2-slim-payload")

        try:
            if mode == "graph":
                # LangGraph agent: plan→execute→verify→review (review built-in)
                try:
                    result = await workflow.execute_activity(
                        run_golem_graph_task,
                        args=[task, provider, max_turns],
                        start_to_close_timeout=timedelta(minutes=35),
                        heartbeat_timeout=timedelta(minutes=10),
                        retry_policy=_RETRY_POLICY,
                    )
                    review = result.get("review", {"approved": result.get("success", False), "flags": [], "verdict": "unknown"})
                except Exception:
                    # Graph failed (e.g. 429 rate limit) — fall back to raw mode
                    mode = "raw_fallback"
                    result = await workflow.execute_activity(
                        run_golem_task,
                        args=[task, provider, max_turns],
                        start_to_close_timeout=timedelta(minutes=35),
                        heartbeat_timeout=timedelta(minutes=5),
                        retry_policy=_RETRY_POLICY,
                    )
                    try:
                        review = await workflow.execute_activity(
                            review_golem_result,
                            args=[result],
                            start_to_close_timeout=timedelta(minutes=2),
                            retry_policy=_REVIEW_RETRY,
                        )
                    except Exception:
                        review = {"approved": result.get("success", False), "flags": ["review_failed"], "verdict": "review_error"}
            else:
                # Raw subprocess mode (default)
                result = await workflow.execute_activity(
                    run_golem_task,
                    args=[task, provider, max_turns],
                    start_to_close_timeout=timedelta(minutes=35),
                    heartbeat_timeout=timedelta(minutes=5),
                    retry_policy=_RETRY_POLICY,
                )
                try:
                    review = await workflow.execute_activity(
                        review_golem_result,
                        args=[result],
                        start_to_close_timeout=timedelta(minutes=2),
                        retry_policy=_REVIEW_RETRY,
                    )
                except Exception:
                    review = {"approved": result.get("success", False), "flags": ["review_failed"], "verdict": "review_error"}

        except Exception as exc:
            result = {
                "task": task[:200],
                "provider": provider,
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(exc)[:2000],
            }
            review = {"approved": False, "flags": ["activity_failed"], "verdict": "rejected"}

        # #6: Upsert search attributes for Temporal UI
        try:
            workflow.upsert_search_attributes(
                [
                    SA_PROVIDER.value_set(provider),
                    SA_VERDICT.value_set(review.get("verdict", "unknown")),
                    SA_TASK_ID.value_set(task[:50]),
                ]
            )
        except Exception:
            pass  # search attributes may not be registered yet

        # #5: If flagged, wait for approval signal (timeout 1h, auto-approve)
        if review.get("verdict") == "approved_with_flags":
            task_id = spec.get("task", "")[:50]
            try:
                await workflow.wait_condition(
                    lambda: task_id in self._approval_signals,
                    timeout=timedelta(hours=1),
                )
                decision = self._approval_signals.get(task_id, "approve")
                if decision == "reject":
                    review = {**review, "approved": False, "verdict": "rejected_by_signal"}
            except asyncio.TimeoutError:
                pass  # auto-approve after 1h

        return {**result, "review": review, "mode": mode, "requeue_prompt": review.get("requeue_prompt", "")}

    @workflow.run
    async def run(self, specs: list[dict]) -> dict:
        """Execute all task specs concurrently, review each, return aggregate."""
        results = await asyncio.gather(
            *[self._execute_one(s) for s in specs]
        )

        succeeded = sum(1 for r in results if r.get("success"))
        approved = sum(1 for r in results if r.get("review", {}).get("approved"))
        flagged = sum(
            1 for r in results
            if r.get("review", {}).get("verdict") == "approved_with_flags"
        )
        rejected = sum(1 for r in results if not r.get("review", {}).get("approved"))

        return {
            "total": len(results),
            "succeeded": succeeded,
            "approved": approved,
            "flagged": flagged,
            "rejected": rejected,
            "results": [
                {
                    "task": r.get("task", "")[:100],
                    "provider": r.get("provider", ""),
                    "success": r.get("success", False),
                    "exit_code": r.get("exit_code", -1),
                    "mode": r.get("mode", "raw"),
                    "review": r.get("review", {}),
                }
                for r in results
            ],
        }
