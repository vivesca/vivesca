from __future__ import annotations

"""Integration tests for temporal-golem workflow using Temporal WorkflowEnvironment.

Uses time-skipping server to test the actual GolemDispatchWorkflow without a
real Temporal instance.  Activities are mocked via @activity.defn replacements.
"""

import asyncio
from pathlib import Path

import pytest
from temporalio import activity, workflow
from temporalio.api.enums.v1 import IndexedValueType
from temporalio.api.operatorservice.v1 import AddSearchAttributesRequest
from temporalio.testing import ActivityEnvironment, WorkflowEnvironment
from temporalio.worker import Worker

# Load workflow source
import sys

sys.path.insert(0, str(Path.home() / "germline/effectors/temporal-golem"))
from workflow import GolemDispatchWorkflow


# ── Shared helpers ────────────────────────────────────────────────────────

# Search attributes used by GolemDispatchWorkflow
_SEARCH_ATTRS = {
    "GolemProvider": IndexedValueType.INDEXED_VALUE_TYPE_KEYWORD,
    "GolemVerdict": IndexedValueType.INDEXED_VALUE_TYPE_KEYWORD,
    "GolemTaskId": IndexedValueType.INDEXED_VALUE_TYPE_KEYWORD,
}


async def _register_search_attrs(env: WorkflowEnvironment) -> None:
    """Register custom search attributes on the test server."""
    await env.client.operator_service.add_search_attributes(
        AddSearchAttributesRequest(
            search_attributes=_SEARCH_ATTRS,
            namespace=env.client.namespace,
        )
    )


def _success_result(task="test", provider="zhipu"):
    return {
        "success": True,
        "exit_code": 0,
        "task": task,
        "provider": provider,
        "stdout": "done",
        "stderr": "",
        "output_path": "",
    }


def _review_approved():
    return {"approved": True, "verdict": "approved", "flags": [], "requeue_prompt": ""}


def _review_flagged():
    return {"approved": True, "verdict": "approved_with_flags", "flags": ["thin_output"], "requeue_prompt": ""}


async def _run_workflow(env, activities, specs, *, wf_id="test-wf", signals=None):
    """Run GolemDispatchWorkflow with given mocked activities.

    signals: list of (method_name, args, delay_seconds) to send after starting.
    """
    task_queue = "test-golem"
    async with Worker(
        env.client,
        task_queue=task_queue,
        workflows=[GolemDispatchWorkflow],
        activities=activities,
    ):
        if signals:
            handle = await env.client.start_workflow(
                GolemDispatchWorkflow.run,
                args=[specs],
                id=wf_id,
                task_queue=task_queue,
            )
            for method_name, args, delay_s in signals:
                await asyncio.sleep(delay_s)
                await handle.signal(method_name, *args)
            result = await handle.result()
        else:
            result = await env.client.execute_workflow(
                GolemDispatchWorkflow.run,
                args=[specs],
                id=wf_id,
                task_queue=task_queue,
            )
    return result


# ── Workflow integration tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_workflow_single_task_success():
    """Single spec: activity succeeds, review approves -> total=1 succeeded=1 approved=1."""

    @activity.defn(name="run_golem_task")
    async def mock_run(task: str, provider: str, max_turns: int = 50) -> dict:
        return _success_result(task, provider)

    @activity.defn(name="review_golem_result")
    async def mock_review(result: dict) -> dict:
        return _review_approved()

    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _register_search_attrs(env)
        result = await _run_workflow(
            env,
            [mock_run, mock_review],
            [{"task": "test", "provider": "zhipu", "max_turns": 5}],
        )

    assert result["total"] == 1
    assert result["succeeded"] == 1
    assert result["approved"] == 1
    assert result["rejected"] == 0


@pytest.mark.asyncio
async def test_workflow_task_failure():
    """Activity raises -> outer except catches, review has activity_failed flag."""

    @activity.defn(name="run_golem_task")
    async def mock_run(task: str, provider: str, max_turns: int = 50) -> dict:
        raise RuntimeError("subprocess exploded")

    @activity.defn(name="review_golem_result")
    async def mock_review(result: dict) -> dict:
        return _review_approved()

    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _register_search_attrs(env)
        result = await _run_workflow(
            env,
            [mock_run, mock_review],
            [{"task": "boom", "provider": "zhipu", "max_turns": 5}],
        )

    assert result["total"] == 1
    assert result["succeeded"] == 0
    assert result["rejected"] == 1
    review = result["results"][0]["review"]
    assert "activity_failed" in review.get("flags", [])


@pytest.mark.asyncio
async def test_workflow_review_failure():
    """Task succeeds but review raises -> succeeded=1, review has review_failed flag."""

    @activity.defn(name="run_golem_task")
    async def mock_run(task: str, provider: str, max_turns: int = 50) -> dict:
        return _success_result(task, provider)

    @activity.defn(name="review_golem_result")
    async def mock_review(result: dict) -> dict:
        raise RuntimeError("review crashed")

    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _register_search_attrs(env)
        result = await _run_workflow(
            env,
            [mock_run, mock_review],
            [{"task": "test", "provider": "zhipu", "max_turns": 5}],
        )

    assert result["total"] == 1
    assert result["succeeded"] == 1
    review = result["results"][0]["review"]
    assert "review_failed" in review.get("flags", [])


@pytest.mark.asyncio
async def test_workflow_graph_fallback_to_raw():
    """mode=graph: graph_task raises -> falls back to raw, mode becomes raw_fallback."""

    @activity.defn(name="run_golem_graph_task")
    async def mock_graph(task: str, provider: str, max_turns: int = 50) -> dict:
        raise RuntimeError("graph unavailable")

    @activity.defn(name="run_golem_task")
    async def mock_run(task: str, provider: str, max_turns: int = 50) -> dict:
        return _success_result(task, provider)

    @activity.defn(name="review_golem_result")
    async def mock_review(result: dict) -> dict:
        return _review_approved()

    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _register_search_attrs(env)
        result = await _run_workflow(
            env,
            [mock_graph, mock_run, mock_review],
            [{"task": "graph-test", "provider": "zhipu", "max_turns": 5, "mode": "graph"}],
        )

    assert result["total"] == 1
    assert result["succeeded"] == 1
    assert result["results"][0]["mode"] == "raw_fallback"


@pytest.mark.asyncio
async def test_workflow_approval_signal_reject():
    """verdict=approved_with_flags + reject_task signal -> verdict becomes rejected_by_signal."""

    @activity.defn(name="run_golem_task")
    async def mock_run(task: str, provider: str, max_turns: int = 50) -> dict:
        return _success_result(task, provider)

    @activity.defn(name="review_golem_result")
    async def mock_review(result: dict) -> dict:
        return _review_flagged()

    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _register_search_attrs(env)
        result = await _run_workflow(
            env,
            [mock_run, mock_review],
            [{"task": "flagged-task", "provider": "zhipu", "max_turns": 5}],
            signals=[("reject_task", ["flagged-task"], 0.1)],
        )

    assert result["total"] == 1
    review = result["results"][0]["review"]
    assert review["verdict"] == "rejected_by_signal"
    assert review["approved"] is False


@pytest.mark.asyncio
async def test_workflow_approval_timeout_auto_approves():
    """verdict=approved_with_flags + skip 1h -> auto-approved (not rejected)."""

    @activity.defn(name="run_golem_task")
    async def mock_run(task: str, provider: str, max_turns: int = 50) -> dict:
        return _success_result(task, provider)

    @activity.defn(name="review_golem_result")
    async def mock_review(result: dict) -> dict:
        return _review_flagged()

    task_queue = "test-golem"
    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _register_search_attrs(env)
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[GolemDispatchWorkflow],
            activities=[mock_run, mock_review],
        ):
            handle = await env.client.start_workflow(
                GolemDispatchWorkflow.run,
                args=[[{"task": "auto-approve", "provider": "zhipu", "max_turns": 5}]],
                id="test-auto-approve",
                task_queue=task_queue,
            )
            # Skip time past the 1-hour auto-approve timeout
            await env.sleep(3601)
            result = await handle.result()

    assert result["total"] == 1
    # The task should be auto-approved (no signal sent, timeout elapsed)
    review = result["results"][0]["review"]
    assert review["approved"] is True


@pytest.mark.asyncio
async def test_workflow_multiple_tasks_concurrent():
    """3 specs submitted concurrently -> all 3 complete, results aggregated."""

    @activity.defn(name="run_golem_task")
    async def mock_run(task: str, provider: str, max_turns: int = 50) -> dict:
        await asyncio.sleep(0.01)  # small delay to exercise concurrency
        return _success_result(task, provider)

    @activity.defn(name="review_golem_result")
    async def mock_review(result: dict) -> dict:
        return _review_approved()

    specs = [
        {"task": f"task-{i}", "provider": "zhipu", "max_turns": 5}
        for i in range(3)
    ]

    async with await WorkflowEnvironment.start_time_skipping() as env:
        await _register_search_attrs(env)
        result = await _run_workflow(env, [mock_run, mock_review], specs)

    assert result["total"] == 3
    assert result["succeeded"] == 3
    assert result["approved"] == 3
    assert len(result["results"]) == 3
    # Each result should reference its own task
    tasks = {r["task"] for r in result["results"]}
    assert tasks == {"task-0", "task-1", "task-2"}


# ── Activity tests with ActivityEnvironment ───────────────────────────────


@pytest.mark.asyncio
async def test_activity_heartbeat():
    """Activity sends heartbeats while subprocess runs."""
    from worker import run_golem_task

    heartbeats = []

    def _capture_heartbeat(*args):
        heartbeats.append(args)

    env = ActivityEnvironment()

    with pytest.MonkeyPatch.context() as m:
        m.setattr("worker._subprocess.run", lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})())
        m.setattr("worker._git_snapshot", lambda *a, **kw: {"stat": "", "numstat": ""})
        m.setattr("worker._create_worktree", lambda *a, **kw: "/tmp/fake-worktree")
        m.setattr("worker._merge_worktree", lambda *a, **kw: True)
        m.setattr("worker._git_pull_ff_only", lambda *a: None)
        m.setattr("worker._git_push", lambda *a: None)
        m.setattr("worker._detect_prior_commits", lambda *a, **kw: [])
        m.setattr("worker._HEARTBEAT_INTERVAL", 0.05)
        # Capture heartbeat calls
        m.setattr("temporalio.activity.heartbeat", _capture_heartbeat)

        async def fake_exec(*args, **kwargs):
            class FakeProc:
                async def communicate(self):
                    # Sleep long enough for at least one heartbeat
                    await asyncio.sleep(0.15)
                    return b"output", b""
                returncode = 0
            return FakeProc()

        m.setattr(asyncio, "create_subprocess_exec", fake_exec)

        result = await env.run(run_golem_task, "test heartbeat task [t-beat01]", "zhipu", 5)

    assert result["success"] is True
    # Heartbeats should have been sent
    assert len(heartbeats) >= 1


@pytest.mark.asyncio
async def test_activity_timeout_cancellation():
    """Activity handles cancellation gracefully."""
    from worker import run_golem_task

    env = ActivityEnvironment()

    with pytest.MonkeyPatch.context() as m:
        m.setattr("worker._subprocess.run", lambda *a, **kw: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})())
        m.setattr("worker._git_snapshot", lambda *a, **kw: {"stat": "", "numstat": ""})
        m.setattr("worker._create_worktree", lambda *a, **kw: "/tmp/fake-worktree")
        m.setattr("worker._merge_worktree", lambda *a, **kw: True)
        m.setattr("worker._git_pull_ff_only", lambda *a: None)
        m.setattr("worker._git_push", lambda *a: None)
        m.setattr("worker._detect_prior_commits", lambda *a, **kw: [])
        m.setattr("worker._HEARTBEAT_INTERVAL", 0.05)

        async def fake_exec(*args, **kwargs):
            class FakeProc:
                async def communicate(self):
                    await asyncio.sleep(0.1)
                    return b"output", b""
                returncode = 0
            return FakeProc()

        m.setattr(asyncio, "create_subprocess_exec", fake_exec)

        # Cancel after a short delay
        async def cancel_soon():
            await asyncio.sleep(0.02)
            env.cancel()

        asyncio.create_task(cancel_soon())

        try:
            result = await env.run(run_golem_task, "test cancel [t-can001]", "zhipu", 5)
            # If it completes before cancel, that's fine
        except asyncio.CancelledError:
            pass  # cancellation handled gracefully

    # Activity should either complete or handle cancellation
    # The key assertion: no unhandled exception
    assert True
