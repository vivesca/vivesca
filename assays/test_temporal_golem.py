from __future__ import annotations

"""Tests for temporal-golem — worker, workflow, CLI.

All Temporal client calls are mocked; no live server needed.
"""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Ensure the temporal-golem package is importable ──────────────────

TG_DIR = str(Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem")
import sys

if TG_DIR not in sys.path:
    sys.path.insert(0, TG_DIR)

# ── Import modules under test ────────────────────────────────────────

from worker import GolemResult, TASK_QUEUE, run_golem_task
from workflow import (
    DEFAULT_CONCURRENCY,
    GOLEM_RETRY,
    PROVIDER_CONCURRENCY,
    GolemDispatchInput,
    GolemDispatchOutput,
    GolemDispatchWorkflow,
    GolemTaskSpec,
)
from cli import _parse_task_file


# ══════════════════════════════════════════════════════════════════════
# GolemResult tests
# ══════════════════════════════════════════════════════════════════════


class TestGolemResult:
    """Tests for the GolemResult data class."""

    def test_ok_when_exit_zero(self) -> None:
        r = GolemResult(provider="zhipu", task="t", exit_code=0, stdout="", stderr="")
        assert r.ok is True

    def test_not_ok_when_nonzero_exit(self) -> None:
        r = GolemResult(provider="zhipu", task="t", exit_code=1, stdout="", stderr="")
        assert r.ok is False

    def test_not_ok_when_timed_out(self) -> None:
        r = GolemResult(
            provider="zhipu", task="t", exit_code=0, stdout="", stderr="",
            timed_out=True,
        )
        assert r.ok is False

    def test_str_ok(self) -> None:
        r = GolemResult(provider="zhipu", task="do stuff", exit_code=0, stdout="", stderr="")
        s = str(r)
        assert "[OK]" in s
        assert "zhipu" in s

    def test_str_fail(self) -> None:
        r = GolemResult(provider="infini", task="bad", exit_code=2, stdout="", stderr="")
        s = str(r)
        assert "[FAIL]" in s

    def test_exit_code_default_on_none(self) -> None:
        """When proc.returncode is None (killed), we default to 1."""
        r = GolemResult(provider="zhipu", task="t", exit_code=1, stdout="", stderr="")
        assert r.exit_code == 1

    def test_fields_populated(self) -> None:
        r = GolemResult(
            provider="volcano", task="build", exit_code=0,
            stdout="ok output", stderr="",
        )
        assert r.provider == "volcano"
        assert r.task == "build"
        assert r.stdout == "ok output"


# ══════════════════════════════════════════════════════════════════════
# Activity tests (run_golem_task)
# ══════════════════════════════════════════════════════════════════════


class TestRunGolemTask:
    """Tests for the run_golem_task activity."""

    @pytest.fixture
    def mock_activity_context(self) -> MagicMock:
        """Patch activity.heartbeat so it doesn't require a Temporal context."""
        with patch("worker.activity.heartbeat"):
            yield

    @pytest.mark.asyncio
    async def test_successful_run(self, mock_activity_context: MagicMock) -> None:
        fake_proc = AsyncMock()
        fake_proc.returncode = 0
        fake_proc.communicate = AsyncMock(return_value=(b"done", b""))
        fake_proc.kill = MagicMock()

        with patch("worker.asyncio.create_subprocess_exec", return_value=fake_proc):
            result = await run_golem_task("zhipu", "test task")

        assert result.ok
        assert result.exit_code == 0
        assert result.stdout == "done"
        assert result.provider == "zhipu"
        assert result.task == "test task"

    @pytest.mark.asyncio
    async def test_failed_run(self, mock_activity_context: MagicMock) -> None:
        fake_proc = AsyncMock()
        fake_proc.returncode = 1
        fake_proc.communicate = AsyncMock(return_value=(b"", b"error!"))
        fake_proc.kill = MagicMock()

        with patch("worker.asyncio.create_subprocess_exec", return_value=fake_proc):
            result = await run_golem_task("infini", "failing task")

        assert not result.ok
        assert result.exit_code == 1
        assert "error!" in result.stderr

    @pytest.mark.asyncio
    async def test_timeout_kills_process(self, mock_activity_context: MagicMock) -> None:
        async def _hang_forever() -> tuple[bytes, bytes]:
            await asyncio.sleep(9999)
            return b"", b""

        fake_proc = AsyncMock()
        fake_proc.returncode = None
        fake_proc.communicate = _hang_forever
        fake_proc.kill = MagicMock()
        fake_proc.wait = AsyncMock()

        with patch("worker.asyncio.create_subprocess_exec", return_value=fake_proc):
            with patch("worker.asyncio.wait_for", side_effect=asyncio.TimeoutError):
                result = await run_golem_task("volcano", "hanging task")

        assert result.timed_out
        assert not result.ok
        fake_proc.kill.assert_called()

    @pytest.mark.asyncio
    async def test_sets_env_provider(self, mock_activity_context: MagicMock) -> None:
        fake_proc = AsyncMock()
        fake_proc.returncode = 0
        fake_proc.communicate = AsyncMock(return_value=(b"ok", b""))

        captured_env: dict = {}

        async def _capture_exec(*args: Any, **kwargs: Any) -> AsyncMock:
            captured_env.update(kwargs.get("env", {}))
            return fake_proc

        with patch("worker.asyncio.create_subprocess_exec", side_effect=_capture_exec):
            await run_golem_task("zhipu", "env test")

        assert captured_env.get("GOLEM_PROVIDER") == "zhipu"

    @pytest.mark.asyncio
    async def test_command_includes_provider(self, mock_activity_context: MagicMock) -> None:
        fake_proc = AsyncMock()
        fake_proc.returncode = 0
        fake_proc.communicate = AsyncMock(return_value=(b"ok", b""))

        captured_args: tuple = ()

        async def _capture_exec(*args: Any, **kwargs: Any) -> AsyncMock:
            nonlocal captured_args
            captured_args = args
            return fake_proc

        with patch("worker.asyncio.create_subprocess_exec", side_effect=_capture_exec):
            await run_golem_task("infini", "cmd test")

        assert "--provider" in captured_args
        idx = captured_args.index("--provider")
        assert captured_args[idx + 1] == "infini"


# ══════════════════════════════════════════════════════════════════════
# Workflow config tests
# ══════════════════════════════════════════════════════════════════════


class TestWorkflowConfig:
    """Tests for provider concurrency config and retry policy."""

    def test_zhipu_concurrency(self) -> None:
        assert PROVIDER_CONCURRENCY["zhipu"] == 8

    def test_infini_concurrency(self) -> None:
        assert PROVIDER_CONCURRENCY["infini"] == 8

    def test_volcano_concurrency(self) -> None:
        assert PROVIDER_CONCURRENCY["volcano"] == 16

    def test_default_concurrency(self) -> None:
        assert DEFAULT_CONCURRENCY == 4

    def test_retry_max_attempts(self) -> None:
        assert GOLEM_RETRY.maximum_attempts == 3

    def test_retry_initial_interval(self) -> None:
        assert GOLEM_RETRY.initial_interval == timedelta(seconds=10)

    def test_retry_backoff_coefficient(self) -> None:
        assert GOLEM_RETRY.backoff_coefficient == 2.0

    def test_retry_maximum_interval(self) -> None:
        assert GOLEM_RETRY.maximum_interval == timedelta(minutes=5)


# ══════════════════════════════════════════════════════════════════════
# GolemDispatchInput / Output tests
# ══════════════════════════════════════════════════════════════════════


class TestGolemDispatchInput:
    """Tests for GolemDispatchInput data class."""

    def test_default_empty_tasks(self) -> None:
        inp = GolemDispatchInput()
        assert inp.tasks == []

    def test_tasks_populated(self) -> None:
        specs = [
            GolemTaskSpec(provider="zhipu", task="a"),
            GolemTaskSpec(provider="infini", task="b"),
        ]
        inp = GolemDispatchInput(tasks=specs)
        assert len(inp.tasks) == 2
        assert inp.tasks[0].provider == "zhipu"
        assert inp.tasks[1].task == "b"


class TestGolemDispatchOutput:
    """Tests for GolemDispatchOutput data class."""

    def test_empty_output(self) -> None:
        out = GolemDispatchOutput()
        assert out.total == 0
        assert out.succeeded == 0
        assert out.failed == 0

    def test_output_str(self) -> None:
        results = [
            GolemResult(provider="zhipu", task="t1", exit_code=0, stdout="", stderr=""),
            GolemResult(provider="infini", task="t2", exit_code=1, stdout="", stderr=""),
        ]
        out = GolemDispatchOutput(results=results, total=2, succeeded=1, failed=1)
        s = str(out)
        assert "1/2 succeeded" in s
        assert "1 failed" in s
        assert "[OK]" in s
        assert "[FAIL]" in s

    def test_output_all_succeeded(self) -> None:
        results = [
            GolemResult(provider="zhipu", task="t1", exit_code=0, stdout="", stderr=""),
        ]
        out = GolemDispatchOutput(results=results, total=1, succeeded=1, failed=0)
        assert out.failed == 0

    def test_output_all_failed(self) -> None:
        results = [
            GolemResult(provider="zhipu", task="t1", exit_code=1, stdout="", stderr=""),
            GolemResult(provider="zhipu", task="t2", exit_code=2, stdout="", stderr=""),
        ]
        out = GolemDispatchOutput(results=results, total=2, succeeded=0, failed=2)
        assert out.succeeded == 0


# ══════════════════════════════════════════════════════════════════════
# CLI _parse_task_file tests
# ══════════════════════════════════════════════════════════════════════


class TestParseTaskFile:
    """Tests for CLI task file parsing."""

    def test_parse_provider_pipe_task(self, tmp_path: Path) -> None:
        f = tmp_path / "tasks.txt"
        f.write_text("zhipu|Write tests for foo.py\ninfini|Refactor bar.py\n")
        specs = _parse_task_file(str(f))
        assert len(specs) == 2
        assert specs[0].provider == "zhipu"
        assert specs[0].task == "Write tests for foo.py"
        assert specs[1].provider == "infini"

    def test_parse_bare_task_defaults_zhipu(self, tmp_path: Path) -> None:
        f = tmp_path / "tasks.txt"
        f.write_text("Write tests for foo.py\n")
        specs = _parse_task_file(str(f))
        assert len(specs) == 1
        assert specs[0].provider == "zhipu"
        assert specs[0].task == "Write tests for foo.py"

    def test_skip_empty_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "tasks.txt"
        f.write_text("zhipu|task1\n\n\ninfini|task2\n")
        specs = _parse_task_file(str(f))
        assert len(specs) == 2

    def test_skip_comments(self, tmp_path: Path) -> None:
        f = tmp_path / "tasks.txt"
        f.write_text("# comment\nzhipu|task1\n# another comment\n")
        specs = _parse_task_file(str(f))
        assert len(specs) == 1

    def test_strips_whitespace(self, tmp_path: Path) -> None:
        f = tmp_path / "tasks.txt"
        f.write_text("  zhipu | task with spaces  \n")
        specs = _parse_task_file(str(f))
        assert specs[0].provider == "zhipu"
        assert specs[0].task == "task with spaces"


# ══════════════════════════════════════════════════════════════════════
# CLI submit / status tests (Click runner)
# ══════════════════════════════════════════════════════════════════════


class TestCliSubmit:
    """Tests for the CLI submit command."""

    def test_submit_no_tasks_exits_1(self) -> None:
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["submit", "--provider", "zhipu"])
        assert result.exit_code != 0
        assert "No tasks" in result.output

    @patch("cli.Client.connect", new_callable=AsyncMock)
    def test_submit_single_task(self, mock_connect: AsyncMock) -> None:
        from click.testing import CliRunner
        from cli import cli

        mock_handle = MagicMock()
        mock_handle.id = "golem-zhipu-20260401-120000"
        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)
        mock_connect.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["submit", "--provider", "zhipu", "--task", "Write tests"],
        )
        assert result.exit_code == 0
        assert "Workflow started" in result.output
        mock_client.start_workflow.assert_called_once()

    @patch("cli.Client.connect", new_callable=AsyncMock)
    def test_submit_multiple_tasks(self, mock_connect: AsyncMock) -> None:
        from click.testing import CliRunner
        from cli import cli

        mock_handle = MagicMock()
        mock_handle.id = "golem-zhipu-20260401-120000"
        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)
        mock_connect.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "submit", "--provider", "zhipu",
                "--task", "task a",
                "--task", "task b",
            ],
        )
        assert result.exit_code == 0
        assert "Tasks: 2" in result.output

    @patch("cli.Client.connect", new_callable=AsyncMock)
    def test_submit_custom_workflow_id(self, mock_connect: AsyncMock) -> None:
        from click.testing import CliRunner
        from cli import cli

        mock_handle = MagicMock()
        mock_handle.id = "my-custom-id"
        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)
        mock_connect.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "submit", "--provider", "infini",
                "--task", "do thing",
                "--workflow-id", "my-custom-id",
            ],
        )
        assert result.exit_code == 0
        assert "my-custom-id" in result.output


class TestCliStatus:
    """Tests for the CLI status command."""

    @patch("cli.Client.connect", new_callable=AsyncMock)
    def test_status_running(self, mock_connect: AsyncMock) -> None:
        from click.testing import CliRunner
        from cli import cli

        mock_desc = MagicMock()
        mock_desc.id = "wf-123"
        mock_desc.status.name = "RUNNING"
        mock_desc.start_time = "2026-04-01T12:00:00"
        mock_desc.close_time = None

        mock_handle = AsyncMock()
        mock_handle.describe = AsyncMock(return_value=mock_desc)

        mock_client = AsyncMock()
        mock_client.get_workflow_handle.return_value = mock_handle
        mock_connect.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "wf-123"])
        assert result.exit_code == 0
        assert "RUNNING" in result.output
        assert "wf-123" in result.output

    @patch("cli.Client.connect", new_callable=AsyncMock)
    def test_status_completed_json(self, mock_connect: AsyncMock) -> None:
        from click.testing import CliRunner
        from cli import cli

        mock_desc = MagicMock()
        mock_desc.id = "wf-456"
        mock_desc.status.name = "COMPLETED"
        mock_desc.start_time = "2026-04-01T12:00:00"
        mock_desc.close_time = "2026-04-01T12:05:00"

        mock_output = GolemDispatchOutput(
            results=[
                GolemResult(provider="zhipu", task="t", exit_code=0, stdout="ok", stderr=""),
            ],
            total=1,
            succeeded=1,
            failed=0,
        )

        mock_handle = AsyncMock()
        mock_handle.describe = AsyncMock(return_value=mock_desc)
        mock_handle.result = AsyncMock(return_value=mock_output)

        mock_client = AsyncMock()
        mock_client.get_workflow_handle.return_value = mock_handle
        mock_connect.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "wf-456", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output.split("\n", 3)[-1])
        assert data["total"] == 1
        assert data["succeeded"] == 1


# ══════════════════════════════════════════════════════════════════════
# Task queue constant test
# ══════════════════════════════════════════════════════════════════════


class TestConstants:
    """Smoke tests for module-level constants."""

    def test_task_queue_name(self) -> None:
        assert TASK_QUEUE == "golem-tasks"

    def test_golem_bin_points_to_file(self) -> None:
        from worker import GOLEM_BIN
        assert GOLEM_BIN.name == "golem"
        assert GOLEM_BIN.parent.name == "effectors"


# ══════════════════════════════════════════════════════════════════════
# Worker entrypoint tests
# ══════════════════════════════════════════════════════════════════════


class TestWorkerEntrypoint:
    """Tests for the worker module entrypoint function."""

    @patch("worker.Client.connect", new_callable=AsyncMock)
    @patch("worker.Worker.__init__", return_value=None)
    @patch("worker.Worker.run", new_callable=AsyncMock)
    async def test_run_worker_connects(
        self,
        mock_run: AsyncMock,
        mock_init: MagicMock,
        mock_connect: AsyncMock,
    ) -> None:
        mock_client = AsyncMock()
        mock_connect.return_value = mock_client

        from worker import run_worker
        await run_worker("localhost:7233")
        mock_connect.assert_called_once_with("localhost:7233")
        mock_run.assert_called_once()
