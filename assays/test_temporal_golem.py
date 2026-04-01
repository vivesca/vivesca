from __future__ import annotations

"""Tests for temporal-golem — Temporal.io golem orchestrator scaffold.

All tests mock the Temporal client/server; no live Temporal instance needed.
Tests cover: models, activity logic, workflow dispatch, CLI, retry policy.
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add temporal-golem dir to sys.path so bare imports resolve
_TG_DIR = str(Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem")
if _TG_DIR not in sys.path:
    sys.path.insert(0, _TG_DIR)

from models import (
    GolemDispatchInput,
    GolemDispatchOutput,
    GolemResult,
    GolemTaskSpec,
)


# ═══════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════


class TestGolemResult:
    """GolemResult data model tests."""

    def test_ok_true_when_exit_zero(self):
        r = GolemResult(provider="zhipu", task="t", exit_code=0, stdout="", stderr="")
        assert r.ok is True

    def test_ok_false_when_nonzero_exit(self):
        r = GolemResult(provider="zhipu", task="t", exit_code=1, stdout="", stderr="")
        assert r.ok is False

    def test_ok_false_when_timed_out(self):
        r = GolemResult(provider="zhipu", task="t", exit_code=0, stdout="", stderr="", timed_out=True)
        assert r.ok is False

    def test_str_ok(self):
        r = GolemResult(provider="zhipu", task="do stuff", exit_code=0, stdout="", stderr="")
        assert "[OK]" in str(r)
        assert "zhipu" in str(r)

    def test_str_fail(self):
        r = GolemResult(provider="infini", task="fail", exit_code=1, stdout="", stderr="")
        assert "[FAIL]" in str(r)

    def test_defaults(self):
        r = GolemResult(provider="x", task="y", exit_code=0, stdout="", stderr="")
        assert r.timed_out is False


class TestGolemTaskSpec:
    """GolemTaskSpec data model tests."""

    def test_fields(self):
        s = GolemTaskSpec(provider="volcano", task="refactor")
        assert s.provider == "volcano"
        assert s.task == "refactor"


class TestGolemDispatchInput:
    """GolemDispatchInput data model tests."""

    def test_default_empty(self):
        inp = GolemDispatchInput()
        assert inp.tasks == []

    def test_with_tasks(self):
        specs = [GolemTaskSpec(provider="zhipu", task="a")]
        inp = GolemDispatchInput(tasks=specs)
        assert len(inp.tasks) == 1


class TestGolemDispatchOutput:
    """GolemDispatchOutput data model tests."""

    def test_str_output(self):
        results = [
            GolemResult(provider="zhipu", task="a", exit_code=0, stdout="", stderr=""),
            GolemResult(provider="infini", task="b", exit_code=1, stdout="", stderr=""),
        ]
        out = GolemDispatchOutput(results=results, total=2, succeeded=1, failed=1)
        s = str(out)
        assert "1/2 succeeded" in s
        assert "1 failed" in s
        assert "[OK]" in s
        assert "[FAIL]" in s

    def test_defaults(self):
        out = GolemDispatchOutput()
        assert out.total == 0
        assert out.succeeded == 0
        assert out.failed == 0
        assert out.results == []


# ═══════════════════════════════════════════════════════════════════════
# Activity logic (run_golem_task)
# ═══════════════════════════════════════════════════════════════════════


class TestRunGolemTaskActivity:
    """Tests for the run_golem_task activity function."""

    @pytest.fixture
    def _patch_subprocess(self):
        """Patch asyncio.create_subprocess_exec to avoid real process spawn."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = None
            proc.communicate = AsyncMock(return_value=(b"output", b"err"))
            proc.kill = MagicMock()
            proc.wait = AsyncMock()
            mock_exec.return_value = proc
            yield mock_exec, proc

    @pytest.fixture
    def _patch_heartbeat(self):
        """Patch activity.heartbeat to avoid Temporal dependency."""
        with patch("worker.activity.heartbeat") as mock_hb:
            yield mock_hb

    @pytest.mark.asyncio
    async def test_successful_run(self, _patch_subprocess, _patch_heartbeat):
        from worker import run_golem_task

        mock_exec, proc = _patch_subprocess
        # Simulate process finishing
        async def fake_communicate(**kwargs):
            proc.returncode = 0
            return (b"all good", b"")
        proc.communicate = fake_communicate

        result = await run_golem_task("zhipu", "write tests")
        assert result.ok is True
        assert result.exit_code == 0
        assert result.stdout == "all good"
        assert result.timed_out is False

    @pytest.mark.asyncio
    async def test_failed_run(self, _patch_subprocess, _patch_heartbeat):
        from worker import run_golem_task

        mock_exec, proc = _patch_subprocess

        async def fake_communicate(**kwargs):
            proc.returncode = 1
            return (b"", b"error msg")
        proc.communicate = fake_communicate

        result = await run_golem_task("infini", "bad task")
        assert result.ok is False
        assert result.exit_code == 1
        assert result.stderr == "error msg"

    @pytest.mark.asyncio
    async def test_timeout(self, _patch_heartbeat):
        from worker import run_golem_task

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = MagicMock()
            proc.returncode = None
            proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
            proc.kill = MagicMock()
            proc.wait = AsyncMock()
            mock_exec.return_value = proc

            result = await run_golem_task("zhipu", "slow task")
            assert result.ok is False
            assert result.timed_out is True
            assert result.exit_code == -1
            proc.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_subprocess_exception(self, _patch_heartbeat):
        from worker import run_golem_task

        with patch("asyncio.create_subprocess_exec", side_effect=OSError("no bash")):
            result = await run_golem_task("zhipu", "broken")
            assert result.ok is False
            assert result.exit_code == -1
            assert "no bash" in result.stderr

    @pytest.mark.asyncio
    async def test_heartbeat_during_execution(self, _patch_subprocess, _patch_heartbeat):
        from worker import run_golem_task

        mock_exec, proc = _patch_subprocess
        mock_hb = _patch_heartbeat

        # Make communicate take some "time" (we just resolve it)
        async def fake_communicate(**kwargs):
            proc.returncode = 0
            return (b"ok", b"")
        proc.communicate = fake_communicate

        await run_golem_task("zhipu", "heartbeat test")
        # At least one heartbeat should have been scheduled
        # (the task may or may not have fired depending on event loop timing)


# ═══════════════════════════════════════════════════════════════════════
# Workflow configuration
# ═══════════════════════════════════════════════════════════════════════


class TestWorkflowConfig:
    """Tests for workflow configuration constants."""

    def test_provider_concurrency_limits(self):
        from workflow import PROVIDER_CONCURRENCY

        assert PROVIDER_CONCURRENCY["zhipu"] == 8
        assert PROVIDER_CONCURRENCY["infini"] == 8
        assert PROVIDER_CONCURRENCY["volcano"] == 16

    def test_default_concurrency(self):
        from workflow import DEFAULT_CONCURRENCY

        assert DEFAULT_CONCURRENCY == 4

    def test_retry_policy(self):
        from workflow import GOLEM_RETRY

        assert GOLEM_RETRY.maximum_attempts == 3
        assert GOLEM_RETRY.backoff_coefficient == 2.0

    def test_retry_policy_initial_interval(self):
        from workflow import GOLEM_RETRY
        from datetime import timedelta

        assert GOLEM_RETRY.initial_interval == timedelta(seconds=10)

    def test_retry_policy_max_interval(self):
        from workflow import GOLEM_RETRY
        from datetime import timedelta

        assert GOLEM_RETRY.maximum_interval == timedelta(seconds=300)


# ═══════════════════════════════════════════════════════════════════════
# Worker configuration
# ═══════════════════════════════════════════════════════════════════════


class TestWorkerConfig:
    """Tests for worker configuration."""

    def test_task_queue_name(self):
        from worker import TASK_QUEUE

        assert TASK_QUEUE == "golem-tasks"

    def test_activity_timeout(self):
        from worker import ACTIVITY_TIMEOUT
        from datetime import timedelta

        assert ACTIVITY_TIMEOUT == timedelta(minutes=30)

    def test_heartbeat_interval(self):
        from worker import HEARTBEAT_INTERVAL_SECONDS

        assert HEARTBEAT_INTERVAL_SECONDS == 30


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════


class TestCLI:
    """Tests for the temporal-golem CLI."""

    def test_submit_requires_provider(self):
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["submit"])
        assert result.exit_code != 0
        assert "provider" in result.output.lower() or "missing" in result.output.lower()

    def test_submit_no_tasks_error(self):
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["submit", "--provider", "zhipu"])
        assert result.exit_code != 0
        assert "no tasks" in result.output.lower()

    @patch("cli.Client.connect", new_callable=AsyncMock)
    def test_submit_single_task(self, mock_connect):
        from click.testing import CliRunner
        from cli import cli

        mock_client = MagicMock()
        mock_handle = MagicMock()
        mock_handle.id = "golem-zhipu-20260401-120000"
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)
        mock_connect.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, [
            "submit", "--provider", "zhipu", "--task", "write tests",
        ])
        assert result.exit_code == 0
        assert "Workflow started" in result.output
        mock_client.start_workflow.assert_called_once()

    @patch("cli.Client.connect", new_callable=AsyncMock)
    def test_submit_multiple_tasks(self, mock_connect):
        from click.testing import CliRunner
        from cli import cli

        mock_client = MagicMock()
        mock_handle = MagicMock()
        mock_handle.id = "golem-infini-test"
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)
        mock_connect.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, [
            "submit", "--provider", "infini",
            "--task", "task A",
            "--task", "task B",
        ])
        assert result.exit_code == 0
        # Verify the input had 2 tasks
        call_args = mock_client.start_workflow.call_args
        inp = call_args[0][1]  # second positional arg is the input
        assert len(inp.tasks) == 2

    @patch("cli.Client.connect", new_callable=AsyncMock)
    def test_submit_custom_workflow_id(self, mock_connect):
        from click.testing import CliRunner
        from cli import cli

        mock_client = MagicMock()
        mock_handle = MagicMock()
        mock_handle.id = "my-custom-id"
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)
        mock_connect.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, [
            "submit", "--provider", "zhipu",
            "--task", "test",
            "--workflow-id", "my-custom-id",
        ])
        assert result.exit_code == 0
        call_kwargs = mock_client.start_workflow.call_args
        assert call_kwargs.kwargs.get("id") == "my-custom-id" or "my-custom-id" in str(call_kwargs)

    @patch("cli.Client.connect", new_callable=AsyncMock)
    def test_status_running(self, mock_connect):
        from click.testing import CliRunner
        from cli import cli

        mock_client = MagicMock()
        mock_desc = MagicMock()
        mock_desc.id = "wf-123"
        mock_desc.status.name = "RUNNING"
        mock_desc.start_time = "2026-04-01T12:00:00"
        mock_desc.close_time = None
        mock_handle = MagicMock()
        mock_handle.describe = AsyncMock(return_value=mock_desc)
        mock_client.get_workflow_handle.return_value = mock_handle
        mock_connect.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "wf-123"])
        assert result.exit_code == 0
        assert "RUNNING" in result.output
        assert "wf-123" in result.output

    @patch("cli.Client.connect", new_callable=AsyncMock)
    def test_status_completed_json(self, mock_connect):
        from click.testing import CliRunner
        from cli import cli

        mock_client = MagicMock()
        mock_desc = MagicMock()
        mock_desc.id = "wf-456"
        mock_desc.status.name = "COMPLETED"
        mock_desc.start_time = "2026-04-01T12:00:00"
        mock_desc.close_time = "2026-04-01T12:05:00"

        output = GolemDispatchOutput(
            results=[
                GolemResult(provider="zhipu", task="t1", exit_code=0, stdout="", stderr=""),
            ],
            total=1,
            succeeded=1,
            failed=0,
        )
        mock_handle = MagicMock()
        mock_handle.describe = AsyncMock(return_value=mock_desc)
        mock_handle.result = AsyncMock(return_value=output)
        mock_client.get_workflow_handle.return_value = mock_handle
        mock_connect.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "wf-456", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output.split("\n", 3)[-1])
        assert data["total"] == 1
        assert data["succeeded"] == 1


class TestParseTaskFile:
    """Tests for CLI _parse_task_file helper."""

    def test_pipe_separated(self, tmp_path):
        from cli import _parse_task_file

        f = tmp_path / "tasks.txt"
        f.write_text("zhipu|write tests\ninfini|refactor code\n")
        specs = _parse_task_file(str(f))
        assert len(specs) == 2
        assert specs[0].provider == "zhipu"
        assert specs[0].task == "write tests"
        assert specs[1].provider == "infini"

    def test_default_provider(self, tmp_path):
        from cli import _parse_task_file

        f = tmp_path / "tasks.txt"
        f.write_text("bare task line\n")
        specs = _parse_task_file(str(f))
        assert len(specs) == 1
        assert specs[0].provider == "zhipu"

    def test_skip_comments_and_blanks(self, tmp_path):
        from cli import _parse_task_file

        f = tmp_path / "tasks.txt"
        f.write_text("# comment\n\n  \nzhipu|real task\n")
        specs = _parse_task_file(str(f))
        assert len(specs) == 1

    def test_empty_file(self, tmp_path):
        from cli import _parse_task_file

        f = tmp_path / "tasks.txt"
        f.write_text("")
        specs = _parse_task_file(str(f))
        assert specs == []


# ═══════════════════════════════════════════════════════════════════════
# Docker Compose config validation
# ═══════════════════════════════════════════════════════════════════════


class TestDockerCompose:
    """Tests for docker-compose.yml validity."""

    def test_compose_file_exists(self):
        dc = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem" / "docker-compose.yml"
        assert dc.exists()

    def test_compose_has_required_services(self):
        dc = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem" / "docker-compose.yml"
        content = dc.read_text()
        for service in ("postgresql", "temporal-server", "temporal-web"):
            assert service in content, f"Missing service: {service}"

    def test_compose_has_persistence(self):
        dc = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem" / "docker-compose.yml"
        content = dc.read_text()
        assert "pgdata" in content

    def test_compose_default_ports(self):
        dc = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem" / "docker-compose.yml"
        content = dc.read_text()
        assert "7233" in content  # gRPC
        assert "8080" in content  # Web UI
        assert "5432" in content  # PostgreSQL


# ═══════════════════════════════════════════════════════════════════════
# Pyproject config
# ═══════════════════════════════════════════════════════════════════════


class TestPyprojectConfig:
    """Tests for pyproject.toml dependencies."""

    def test_pyproject_exists(self):
        pp = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem" / "pyproject.toml"
        assert pp.exists()

    def test_temporalio_dependency(self):
        pp = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem" / "pyproject.toml"
        content = pp.read_text()
        assert "temporalio" in content

    def test_click_dependency(self):
        pp = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem" / "pyproject.toml"
        content = pp.read_text()
        assert "click" in content


# ═══════════════════════════════════════════════════════════════════════
# README
# ═══════════════════════════════════════════════════════════════════════


class TestReadme:
    """Tests for README.md documentation."""

    def test_readme_exists(self):
        readme = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem" / "README.md"
        assert readme.exists()

    def test_readme_documents_concurrency(self):
        readme = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem" / "README.md"
        content = readme.read_text()
        assert "zhipu" in content
        assert "infini" in content
        assert "volcano" in content

    def test_readme_documents_ports(self):
        readme = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem" / "README.md"
        content = readme.read_text()
        assert "7233" in content
        assert "8080" in content
