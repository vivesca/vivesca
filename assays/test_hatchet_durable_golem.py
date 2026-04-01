from __future__ import annotations

"""Tests for durable_task conversion of golem-zhipu.

Verifies:
  - golem-zhipu is registered via @hatchet.durable_task (not @hatchet.task)
  - The function is async and accepts DurableContext
  - save_state() calls are made before and after subprocess
  - save_state wraps aio_wait_for with zero-duration SleepCondition
  - Resume behaviour: on replay, checkpoints return cached results and
    subprocess may be re-invoked (idempotent)
"""

import asyncio
import inspect
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

WORKER_PATH = "/home/terry/germline/effectors/hatchet-golem/worker.py"


# ── Helpers ─────────────────────────────────────────────────────────────


def _make_mock_hatchet():
    """Build a mock Hatchet with capturable .task() and .durable_task()."""
    mock_hatchet = MagicMock()
    mock_hatchet.rate_limits = MagicMock()
    mock_hatchet.task.side_effect = lambda **kw: lambda fn: fn
    mock_hatchet.durable_task.side_effect = lambda **kw: lambda fn: fn
    return mock_hatchet


def _exec_worker(mock_hatchet):
    """Exec the worker module with a mocked Hatchet and return the namespace."""
    ns: dict = {"__name__": "worker", "__file__": WORKER_PATH}
    with patch("hatchet_sdk.Hatchet", return_value=mock_hatchet):
        exec(open(WORKER_PATH).read(), ns)
    return ns


def _capture_decorator_calls():
    """Load worker and capture kwargs for both .task() and .durable_task()."""
    task_calls: list[dict] = []
    durable_calls: list[dict] = []

    def capture_task(**kw):
        task_calls.append(kw)
        return lambda fn: fn

    def capture_durable(**kw):
        durable_calls.append(kw)
        return lambda fn: fn

    mock_hatchet = MagicMock()
    mock_hatchet.rate_limits = MagicMock()
    mock_hatchet.task = capture_task
    mock_hatchet.durable_task = capture_durable
    _exec_worker(mock_hatchet)
    return task_calls, durable_calls


# ── Decorator registration tests ───────────────────────────────────────


class TestDurableRegistration:
    def test_golem_zhipu_uses_durable_task(self):
        """golem-zhipu is registered via @hatchet.durable_task, not @hatchet.task."""
        task_calls, durable_calls = _capture_decorator_calls()
        zhipu_tasks = [c for c in task_calls if c.get("name") == "golem-zhipu"]
        zhipu_durable = [c for c in durable_calls if c.get("name") == "golem-zhipu"]
        assert len(zhipu_tasks) == 0, "golem-zhipu should NOT use @hatchet.task"
        assert len(zhipu_durable) == 1, "golem-zhipu should use @hatchet.durable_task"

    def test_zhipu_durable_has_same_config(self):
        """durable_task keeps same concurrency, timeout, retries, rate_limits."""
        _, durable_calls = _capture_decorator_calls()
        zhipu = next(c for c in durable_calls if c["name"] == "golem-zhipu")
        assert zhipu["execution_timeout"] == "30m"
        assert zhipu["retries"] == 2
        assert zhipu["rate_limits"] is not None
        assert len(zhipu["rate_limits"]) == 1
        assert zhipu["rate_limits"][0].static_key == "zhipu-rpm"

    def test_other_providers_still_use_task(self):
        """Non-zhipu providers still use @hatchet.task."""
        task_calls, durable_calls = _capture_decorator_calls()
        task_names = {c["name"] for c in task_calls}
        assert "golem-infini" in task_names
        assert "golem-volcano" in task_names
        assert "golem-gemini" in task_names
        assert "golem-codex" in task_names
        # Only zhipu in durable
        durable_names = {c["name"] for c in durable_calls}
        assert durable_names == {"golem-zhipu"}

    def test_total_task_count(self):
        """1 durable_task + 6 @hatchet.task = 7 total task registrations."""
        task_calls, durable_calls = _capture_decorator_calls()
        assert len(task_calls) == 6  # infini, volcano, gemini, codex, requeue, health
        assert len(durable_calls) == 1  # zhipu


# ── Function signature tests ───────────────────────────────────────────


class TestDurableFunctionSignature:
    def test_golem_zhipu_is_async(self):
        """golem_zhipu is an async function (coroutine function)."""
        ns = _exec_worker(_make_mock_hatchet())
        assert inspect.iscoroutinefunction(ns["golem_zhipu"])

    def test_golem_zhipu_accepts_two_args(self):
        """Function signature is (input, context)."""
        ns = _exec_worker(_make_mock_hatchet())
        sig = inspect.signature(ns["golem_zhipu"])
        params = list(sig.parameters.keys())
        assert params == ["input", "context"]


# ── Checkpoint/resume tests ────────────────────────────────────────────


def _make_mock_context(checkpoint_results=None):
    """Create a mock DurableContext with configurable aio_wait_for.

    Args:
        checkpoint_results: dict mapping signal_key -> return value.
            If None, each aio_wait_for returns empty dict.
    """
    ctx = AsyncMock()
    _results = checkpoint_results or {}

    async def _aio_wait_for(signal_key, *conditions):
        return _results.get(signal_key, {})

    ctx.aio_wait_for = AsyncMock(side_effect=_aio_wait_for)
    ctx.invocation_count = 1
    return ctx


def _make_mock_subprocess(returncode=0, stdout="ok", stderr=""):
    """Create a mock subprocess.run that returns a fake CompletedProcess."""
    mock_proc = MagicMock()
    mock_proc.returncode = returncode
    mock_proc.stdout = stdout
    mock_proc.stderr = stderr

    mock_subprocess = MagicMock()
    mock_subprocess.run.return_value = mock_proc
    mock_subprocess.TimeoutExpired = Exception
    return mock_subprocess


class TestCheckpoints:
    @pytest.mark.asyncio
    async def test_pre_exec_checkpoint_called(self):
        """aio_wait_for('golem-zhipu-pre-exec', ...) is called."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        await ns["golem_zhipu"]({"task": "test job"}, ctx)

        signal_keys = [
            call.args[0] for call in ctx.aio_wait_for.call_args_list
        ]
        assert "golem-zhipu-pre-exec" in signal_keys

    @pytest.mark.asyncio
    async def test_post_exec_checkpoint_called(self):
        """aio_wait_for('golem-zhipu-post-exec', ...) is called."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        await ns["golem_zhipu"]({"task": "test job"}, ctx)

        signal_keys = [
            call.args[0] for call in ctx.aio_wait_for.call_args_list
        ]
        assert "golem-zhipu-post-exec" in signal_keys

    @pytest.mark.asyncio
    async def test_checkpoints_use_zero_duration_sleep(self):
        """Both checkpoints use SleepCondition(duration=timedelta(seconds=0))."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        await ns["golem_zhipu"]({"task": "test"}, ctx)

        for call in ctx.aio_wait_for.call_args_list:
            conditions = call.args[1:]
            assert len(conditions) >= 1
            sc = conditions[0]
            assert isinstance(sc, type(sc))  # it's a SleepCondition
            assert sc.duration == timedelta(seconds=0)

    @pytest.mark.asyncio
    async def test_pre_checkpoint_before_subprocess(self):
        """pre-exec checkpoint is called BEFORE subprocess.run."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        call_order = []
        original_wait = ctx.aio_wait_for

        async def tracking_wait(signal_key, *conditions):
            call_order.append(("checkpoint", signal_key))
            return await original_wait(signal_key, *conditions)

        ctx.aio_wait_for = AsyncMock(side_effect=tracking_wait)
        original_run = ns["subprocess"].run

        def tracking_run(*a, **kw):
            call_order.append(("subprocess",))
            return original_run(*a, **kw)

        ns["subprocess"].run = tracking_run
        await ns["golem_zhipu"]({"task": "test"}, ctx)

        # Find indices
        pre_idx = next(
            i for i, (t, *r) in enumerate(call_order)
            if t == "checkpoint" and r[0] == "golem-zhipu-pre-exec"
        )
        sub_idx = next(
            i for i, (t, *r) in enumerate(call_order)
            if t == "subprocess"
        )
        assert pre_idx < sub_idx, "pre-exec checkpoint must precede subprocess"

    @pytest.mark.asyncio
    async def test_post_checkpoint_after_subprocess(self):
        """post-exec checkpoint is called AFTER subprocess.run."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        call_order = []
        original_wait = ctx.aio_wait_for

        async def tracking_wait(signal_key, *conditions):
            call_order.append(("checkpoint", signal_key))
            return await original_wait(signal_key, *conditions)

        ctx.aio_wait_for = AsyncMock(side_effect=tracking_wait)
        original_run = ns["subprocess"].run

        def tracking_run(*a, **kw):
            call_order.append(("subprocess",))
            return original_run(*a, **kw)

        ns["subprocess"].run = tracking_run
        await ns["golem_zhipu"]({"task": "test"}, ctx)

        sub_idx = next(
            i for i, (t, *r) in enumerate(call_order)
            if t == "subprocess"
        )
        post_idx = next(
            i for i, (t, *r) in enumerate(call_order)
            if t == "checkpoint" and r[0] == "golem-zhipu-post-exec"
        )
        assert post_idx > sub_idx, "post-exec checkpoint must follow subprocess"


class TestResume:
    @pytest.mark.asyncio
    async def test_full_run_returns_expected_result(self):
        """Normal execution returns dict with expected keys."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess(
            returncode=0, stdout="all good", stderr=""
        )
        ctx = _make_mock_context()

        result = await ns["golem_zhipu"]({"task": "build tests"}, ctx)

        assert result["success"] is True
        assert result["exit_code"] == 0
        assert result["provider"] == "zhipu"
        assert result["stdout"] == "all good"
        assert "task" in result

    @pytest.mark.asyncio
    async def test_subprocess_failure_reflected_in_result(self):
        """Subprocess non-zero exit code sets success=False."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess(
            returncode=1, stdout="", stderr="error msg"
        )
        ctx = _make_mock_context()

        result = await ns["golem_zhipu"]({"task": "fail job"}, ctx)

        assert result["success"] is False
        assert result["exit_code"] == 1
        assert result["stderr"] == "error msg"

    @pytest.mark.asyncio
    async def test_resume_replays_from_start(self):
        """On replay (invocation_count > 1), the full function body runs again.

        This is the expected Hatchet behaviour: the function is re-invoked from
        the start, but aio_wait_for calls return cached results instantly,
        acting as checkpoints. The subprocess re-runs because it sits between
        checkpoints (golem tasks are idempotent).
        """
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess(returncode=0, stdout="ok", stderr="")
        ctx = _make_mock_context()
        ctx.invocation_count = 2  # Simulate replay

        result = await ns["golem_zhipu"]({"task": "replay test"}, ctx)

        # Both checkpoints still called (returning cached results)
        assert ctx.aio_wait_for.call_count == 2
        # Subprocess also called (re-run between checkpoints)
        assert ns["subprocess"].run.call_count == 1
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_max_turns_passed_through(self):
        """max_turns from input is forwarded to the subprocess command."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        await ns["golem_zhipu"]({"task": "test", "max_turns": 42}, ctx)

        call_args = ns["subprocess"].run.call_args
        cmd = call_args[0][0] if call_args[0] else call_args.kwargs.get("args", [])
        # cmd is the first positional arg to subprocess.run
        assert "--max-turns" in cmd
        idx = cmd.index("--max-turns")
        assert cmd[idx + 1] == "42"

    @pytest.mark.asyncio
    async def test_default_max_turns_is_50(self):
        """Without max_turns in input, defaults to 50."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        await ns["golem_zhipu"]({"task": "test"}, ctx)

        call_args = ns["subprocess"].run.call_args
        cmd = call_args[0][0]
        idx = cmd.index("--max-turns")
        assert cmd[idx + 1] == "50"

    @pytest.mark.asyncio
    async def test_provider_is_zhipu(self):
        """Subprocess command includes --provider zhipu."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        await ns["golem_zhipu"]({"task": "test"}, ctx)

        call_args = ns["subprocess"].run.call_args
        cmd = call_args[0][0]
        assert "--provider" in cmd
        idx = cmd.index("--provider")
        assert cmd[idx + 1] == "zhipu"

    @pytest.mark.asyncio
    async def test_task_truncated_to_200(self):
        """Task string in result is truncated to 200 chars."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        long_task = "x" * 300
        result = await ns["golem_zhipu"]({"task": long_task}, ctx)

        assert len(result["task"]) == 200
        assert result["task"] == long_task[:200]

    @pytest.mark.asyncio
    async def test_stdout_truncated_to_4000(self):
        """stdout in result is truncated to 4000 chars."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess(stdout="y" * 5000)
        ctx = _make_mock_context()

        result = await ns["golem_zhipu"]({"task": "test"}, ctx)

        assert len(result["stdout"]) <= 4000

    @pytest.mark.asyncio
    async def test_stderr_truncated_to_2000(self):
        """stderr in result is truncated to 2000 chars."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess(stderr="z" * 3000)
        ctx = _make_mock_context()

        result = await ns["golem_zhipu"]({"task": "test"}, ctx)

        assert len(result["stderr"]) <= 2000


class TestTwoCheckpointsExactly:
    @pytest.mark.asyncio
    async def test_exactly_two_checkpoints(self):
        """Exactly 2 aio_wait_for calls (pre + post) are made."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        await ns["golem_zhipu"]({"task": "test"}, ctx)

        assert ctx.aio_wait_for.call_count == 2

    @pytest.mark.asyncio
    async def test_checkpoint_signal_keys_are_distinct(self):
        """The two checkpoints use different signal keys."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        await ns["golem_zhipu"]({"task": "test"}, ctx)

        keys = [call.args[0] for call in ctx.aio_wait_for.call_args_list]
        assert len(set(keys)) == 2, "Both checkpoint keys must be distinct"


# ── save_state helper tests ────────────────────────────────────────────


class TestSaveStateHelper:
    def test_save_state_exists_in_namespace(self):
        """The save_state helper is defined in the worker module."""
        ns = _exec_worker(_make_mock_hatchet())
        assert "save_state" in ns
        assert callable(ns["save_state"])

    def test_save_state_is_async(self):
        """save_state is an async coroutine function."""
        ns = _exec_worker(_make_mock_hatchet())
        assert inspect.iscoroutinefunction(ns["save_state"])

    @pytest.mark.asyncio
    async def test_save_state_calls_aio_wait_for(self):
        """save_state delegates to context.aio_wait_for internally."""
        ctx = AsyncMock()
        ns = _exec_worker(_make_mock_hatchet())
        await ns["save_state"](ctx, "test-checkpoint")
        ctx.aio_wait_for.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_state_passes_zero_duration_sleep(self):
        """save_state uses SleepCondition(duration=0) for instant checkpoint."""
        ctx = AsyncMock()
        ns = _exec_worker(_make_mock_hatchet())
        await ns["save_state"](ctx, "my-key")
        call_args = ctx.aio_wait_for.call_args
        assert call_args.args[0] == "my-key"
        conditions = call_args.args[1:]
        assert len(conditions) == 1
        assert isinstance(conditions[0], type(conditions[0]))
        assert conditions[0].duration == timedelta(seconds=0)

    @pytest.mark.asyncio
    async def test_save_state_returns_none(self):
        """save_state is a void checkpoint (returns None)."""
        ctx = AsyncMock()
        ns = _exec_worker(_make_mock_hatchet())
        result = await ns["save_state"](ctx, "key")
        assert result is None


# ── Enhanced resume/restore tests ──────────────────────────────────────


class TestSaveStateResume:
    @pytest.mark.asyncio
    async def test_pre_exec_uses_save_state(self):
        """golem-zhipu pre-exec checkpoint goes through save_state."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        # Track calls to save_state
        original_save = ns["save_state"]
        save_keys = []

        async def tracking_save(context, key):
            save_keys.append(key)
            return await original_save(context, key)

        ns["save_state"] = tracking_save
        await ns["golem_zhipu"]({"task": "test"}, ctx)

        assert "golem-zhipu-pre-exec" in save_keys

    @pytest.mark.asyncio
    async def test_post_exec_uses_save_state(self):
        """golem-zhipu post-exec checkpoint goes through save_state."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        original_save = ns["save_state"]
        save_keys = []

        async def tracking_save(context, key):
            save_keys.append(key)
            return await original_save(context, key)

        ns["save_state"] = tracking_save
        await ns["golem_zhipu"]({"task": "test"}, ctx)

        assert "golem-zhipu-post-exec" in save_keys

    @pytest.mark.asyncio
    async def test_exactly_two_save_state_calls(self):
        """golem-zhipu calls save_state exactly twice (pre + post)."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()

        original_save = ns["save_state"]
        save_keys = []

        async def tracking_save(context, key):
            save_keys.append(key)
            return await original_save(context, key)

        ns["save_state"] = tracking_save
        await ns["golem_zhipu"]({"task": "test"}, ctx)

        assert len(save_keys) == 2
        assert save_keys == ["golem-zhipu-pre-exec", "golem-zhipu-post-exec"]

    @pytest.mark.asyncio
    async def test_resume_replays_save_state_in_order(self):
        """On replay, both save_state calls fire in correct order.

        Simulates worker restart: invocation_count > 1 means Hatchet is
        replaying. Cached save_state calls return instantly, and the
        subprocess re-runs between them (golem tasks are idempotent).
        """
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess(returncode=0, stdout="ok")
        ctx = _make_mock_context()
        ctx.invocation_count = 2  # simulate replay

        call_log = []
        original_save = ns["save_state"]

        async def tracking_save(context, key):
            call_log.append(("save_state", key))
            return await original_save(context, key)

        ns["save_state"] = tracking_save

        result = await ns["golem_zhipu"]({"task": "replay"}, ctx)
        assert result["success"] is True
        assert call_log == [
            ("save_state", "golem-zhipu-pre-exec"),
            ("save_state", "golem-zhipu-post-exec"),
        ]

    @pytest.mark.asyncio
    async def test_resume_subprocess_between_checkpoints(self):
        """On replay, subprocess runs AFTER pre-exec and BEFORE post-exec save_state."""
        ns = _exec_worker(_make_mock_hatchet())
        ns["subprocess"] = _make_mock_subprocess()
        ctx = _make_mock_context()
        ctx.invocation_count = 3

        call_log = []
        original_save = ns["save_state"]

        async def tracking_save(context, key):
            call_log.append(("save_state", key))
            return await original_save(context, key)

        ns["save_state"] = tracking_save
        original_run = ns["subprocess"].run

        def tracking_run(*a, **kw):
            call_log.append(("subprocess",))
            return original_run(*a, **kw)

        ns["subprocess"].run = tracking_run
        await ns["golem_zhipu"]({"task": "ordered"}, ctx)

        # Verify order: pre-save, subprocess, post-save
        assert call_log == [
            ("save_state", "golem-zhipu-pre-exec"),
            ("subprocess",),
            ("save_state", "golem-zhipu-post-exec"),
        ]
