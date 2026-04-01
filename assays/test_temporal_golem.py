from __future__ import annotations

"""Tests for temporal-golem: activity logic, workflow dispatch, CLI, retry config.

All Temporal client interactions are mocked — no live server required.
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add temporal-golem dir to import path so worker/workflow/cli resolve.
_TEMPORAL_GOLEM_DIR = str(
    Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem"
)
sys.path.insert(0, _TEMPORAL_GOLEM_DIR)

from worker import GolemResult, TASK_QUEUE, run_golem_task
from workflow import (
    DEFAULT_CONCURRENCY,
    GOLEM_RETRY,
    PROVIDER_CONCURRENCY,
    GolemDispatchInput,
    GolemDispatchOutput,
    GolemTaskSpec,
)
from cli import _parse_task_file

# ── GolemResult ───────────────────────────────────────────────────────


class TestGolemResult:
    def test_ok_success(self):
        r = GolemResult(provider="zhipu", task="do stuff", exit_code=0, stdout="ok", stderr="")
        assert r.ok is True
        assert r.timed_out is False

    def test_ok_failure_nonzero(self):
        r = GolemResult(provider="zhipu", task="fail", exit_code=1, stdout="", stderr="err")
        assert r.ok is False

    def test_ok_timeout(self):
        r = GolemResult(provider="zhipu", task="slow", exit_code=0, stdout="", stderr="", timed_out=True)
        assert r.ok is False

    def test_str_success(self):
        r = GolemResult(provider="infini", task="hello", exit_code=0, stdout="", stderr="")
        s = str(r)
        assert "[OK]" in s
        assert "infini" in s

    def test_str_failure(self):
        r = GolemResult(provider="volcano", task="boom", exit_code=2, stdout="", stderr="err")
        s = str(r)
        assert "[FAIL]" in s
        assert "volcano" in s

    def test_exit_code_default_on_none(self):
        """exit_code is 0 but proc returned None — .ok checks both."""
        r = GolemResult(provider="zhipu", task="x", exit_code=0, stdout="", stderr="")
        assert r.ok is True


# ── GolemDispatchOutput ──────────────────────────────────────────────


class TestGolemDispatchOutput:
    def test_str_format(self):
        results = [
            GolemResult(provider="zhipu", task="t1", exit_code=0, stdout="", stderr=""),
            GolemResult(provider="infini", task="t2", exit_code=1, stdout="", stderr="err"),
        ]
        out = GolemDispatchOutput(results=results, total=2, succeeded=1, failed=1)
        s = str(out)
        assert "1/2 succeeded" in s
        assert "1 failed" in s
        assert "[OK]" in s
        assert "[FAIL]" in s

    def test_empty_results(self):
        out = GolemDispatchOutput()
        assert out.total == 0
        assert out.succeeded == 0
        assert out.failed == 0
        assert "0/0" in str(out)


# ── Config constants ─────────────────────────────────────────────────


class TestConfig:
    def test_provider_concurrency(self):
        assert PROVIDER_CONCURRENCY["zhipu"] == 8
        assert PROVIDER_CONCURRENCY["infini"] == 8
        assert PROVIDER_CONCURRENCY["volcano"] == 16

    def test_default_concurrency(self):
        assert DEFAULT_CONCURRENCY == 4

    def test_task_queue_name(self):
        assert TASK_QUEUE == "golem-tasks"

    def test_retry_policy_attempts(self):
        assert GOLEM_RETRY.maximum_attempts == 3

    def test_retry_policy_backoff(self):
        assert GOLEM_RETRY.backoff_coefficient == 2.0

    def test_retry_policy_initial_interval(self):
        assert GOLEM_RETRY.initial_interval.total_seconds() == 10

    def test_retry_policy_max_interval(self):
        assert GOLEM_RETRY.maximum_interval.total_seconds() == 300  # 5 min

    def test_retry_non_retryable_types(self):
        assert "temporalio.exceptions.ActivityError" in GOLEM_RETRY.non_retryable_error_types


# ── Task file parsing ────────────────────────────────────────────────


class TestParseTaskFile:
    def test_pipe_separated(self, tmp_path):
        f = tmp_path / "tasks.txt"
        f.write_text("zhipu|Write tests\ninfini|Refactor code\n")
        specs = _parse_task_file(str(f))
        assert len(specs) == 2
        assert specs[0].provider == "zhipu"
        assert specs[0].task == "Write tests"
        assert specs[1].provider == "infini"

    def test_no_pipe_defaults_to_zhipu(self, tmp_path):
        f = tmp_path / "tasks.txt"
        f.write_text("Do something\n")
        specs = _parse_task_file(str(f))
        assert len(specs) == 1
        assert specs[0].provider == "zhipu"
        assert specs[0].task == "Do something"

    def test_empty_lines_skipped(self, tmp_path):
        f = tmp_path / "tasks.txt"
        f.write_text("\n\nzhipu|Task\n\n")
        specs = _parse_task_file(str(f))
        assert len(specs) == 1

    def test_comments_skipped(self, tmp_path):
        f = tmp_path / "tasks.txt"
        f.write_text("# comment\nzhipu|Real task\n")
        specs = _parse_task_file(str(f))
        assert len(specs) == 1
        assert specs[0].task == "Real task"

    def test_empty_file(self, tmp_path):
        f = tmp_path / "tasks.txt"
        f.write_text("")
        specs = _parse_task_file(str(f))
        assert specs == []


# ── Activity (run_golem_task) ────────────────────────────────────────


class TestRunGolemTask:
    @pytest.fixture()
    def _mock_subprocess(self):
        """Mock asyncio.create_subprocess_exec to return a fake process."""
        proc = MagicMock()
        proc.returncode = 0
        proc.communicate = AsyncMock(return_value=(b"output", b""))
        proc.wait = AsyncMock()
        proc.kill = MagicMock()
        with patch("asyncio.create_subprocess_exec", return_value=proc) as mock_exec:
            yield mock_exec, proc

    @pytest.fixture()
    def _mock_heartbeat(self):
        with patch("worker.activity.heartbeat"):
            yield

    @pytest.mark.asyncio
    async def test_successful_run(self, _mock_subprocess, _mock_heartbeat):
        mock_exec, proc = _mock_subprocess
        result = await run_golem_task("zhipu", "write tests")
        assert result.ok is True
        assert result.exit_code == 0
        assert result.stdout == "output"
        assert result.provider == "zhipu"
        assert result.task == "write tests"

    @pytest.mark.asyncio
    async def test_failure_nonzero_exit(self, _mock_subprocess, _mock_heartbeat):
        mock_exec, proc = _mock_subprocess
        proc.returncode = 1
        proc.communicate = AsyncMock(return_value=(b"", b"error message"))
        result = await run_golem_task("infini", "failing task")
        assert result.ok is False
        assert result.exit_code == 1
        assert result.stderr == "error message"

    @pytest.mark.asyncio
    async def test_timeout(self, _mock_subprocess, _mock_heartbeat):
        mock_exec, proc = _mock_subprocess
        # communicate raises TimeoutError
        proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError)
        result = await run_golem_task("volcano", "slow task")
        assert result.ok is False
        assert result.timed_out is True
        proc.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_includes_provider(self, _mock_subprocess, _mock_heartbeat):
        mock_exec, _ = _mock_subprocess
        await run_golem_task("zhipu", "check cmd")
        cmd = mock_exec.call_args[0]
        assert "--provider" in cmd
        idx = cmd.index("--provider")
        assert cmd[idx + 1] == "zhipu"

    @pytest.mark.asyncio
    async def test_cwd_is_germline_root(self, _mock_subprocess, _mock_heartbeat):
        mock_exec, _ = _mock_subprocess
        await run_golem_task("zhipu", "check cwd")
        kwargs = mock_exec.call_args[1]
        cwd = kwargs.get("cwd", "")
        assert "germline" in cwd

    @pytest.mark.asyncio
    async def test_env_includes_provider(self, _mock_subprocess, _mock_heartbeat):
        mock_exec, _ = _mock_subprocess
        await run_golem_task("infini", "env check")
        kwargs = mock_exec.call_args[1]
        env = kwargs.get("env", {})
        assert env.get("GOLEM_PROVIDER") == "infini"


# ── CLI submit ───────────────────────────────────────────────────────


class TestCliSubmit:
    @pytest.fixture()
    def _mock_client(self):
        """Mock Temporal client to avoid needing a live server."""
        handle = MagicMock()
        handle.id = "golem-zhipu-20260401-120000"

        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=handle)

        with patch("cli._connect", return_value=mock_client):
            yield mock_client, handle

    def test_submit_single_task(self, _mock_client):
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["submit", "--provider", "zhipu", "--task", "hello"])
        assert result.exit_code == 0
        assert "Workflow started" in result.output
        mock_client, handle = _mock_client
        mock_client.start_workflow.assert_called_once()
        call_args = mock_client.start_workflow.call_args
        input_data = call_args[0][1]  # second positional arg
        assert len(input_data.tasks) == 1
        assert input_data.tasks[0].provider == "zhipu"
        assert input_data.tasks[0].task == "hello"

    def test_submit_multiple_tasks(self, _mock_client):
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            "submit", "--provider", "infini",
            "--task", "task one", "--task", "task two",
        ])
        assert result.exit_code == 0
        mock_client, _ = _mock_client
        input_data = mock_client.start_workflow.call_args[0][1]
        assert len(input_data.tasks) == 2

    def test_submit_with_file(self, _mock_client, tmp_path):
        from click.testing import CliRunner
        from cli import cli

        task_file = tmp_path / "tasks.txt"
        task_file.write_text("zhipu|file task\n")
        runner = CliRunner()
        result = runner.invoke(cli, [
            "submit", "--provider", "zhipu",
            "--file", str(task_file),
        ])
        assert result.exit_code == 0
        mock_client, _ = _mock_client
        input_data = mock_client.start_workflow.call_args[0][1]
        assert any(t.task == "file task" for t in input_data.tasks)

    def test_submit_no_tasks_exits_1(self):
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["submit", "--provider", "zhipu"])
        assert result.exit_code != 0

    def test_submit_custom_workflow_id(self, _mock_client):
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            "submit", "--provider", "zhipu", "--task", "x",
            "--workflow-id", "my-custom-id",
        ])
        assert result.exit_code == 0
        mock_client, _ = _mock_client
        call_kwargs = mock_client.start_workflow.call_args[1]
        assert call_kwargs["id"] == "my-custom-id"


# ── CLI status ───────────────────────────────────────────────────────


class TestCliStatus:
    @pytest.fixture()
    def _mock_status_client(self):
        handle = MagicMock()
        desc = MagicMock()
        desc.id = "golem-test-123"
        desc.status.name = "COMPLETED"
        desc.start_time = "2026-04-01T12:00:00Z"
        desc.close_time = "2026-04-01T12:05:00Z"
        handle.describe = AsyncMock(return_value=desc)
        handle.result = AsyncMock(return_value=GolemDispatchOutput(
            results=[
                GolemResult(provider="zhipu", task="t1", exit_code=0, stdout="", stderr=""),
            ],
            total=1, succeeded=1, failed=0,
        ))

        mock_client = AsyncMock()
        mock_client.get_workflow_handle = MagicMock(return_value=handle)

        with patch("cli._connect", return_value=mock_client):
            yield mock_client, handle, desc

    def test_status_completed(self, _mock_status_client):
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "golem-test-123"])
        assert result.exit_code == 0
        assert "COMPLETED" in result.output
        assert "1/1 succeeded" in result.output

    def test_status_json_output(self, _mock_status_client):
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "golem-test-123", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output.split("\n", 3)[-1])  # skip header lines
        assert data["total"] == 1
        assert data["succeeded"] == 1
        assert data["failed"] == 0

    def test_status_running(self):
        handle = MagicMock()
        desc = MagicMock()
        desc.id = "golem-running"
        desc.status.name = "RUNNING"
        desc.start_time = "2026-04-01T12:00:00Z"
        desc.close_time = None
        handle.describe = AsyncMock(return_value=desc)

        mock_client = AsyncMock()
        mock_client.get_workflow_handle = MagicMock(return_value=handle)

        from click.testing import CliRunner
        from cli import cli

        with patch("cli._connect", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(cli, ["status", "golem-running"])
        assert result.exit_code == 0
        assert "RUNNING" in result.output


# ── Docker compose file exists and is valid ──────────────────────────


class TestDockerCompose:
    def test_compose_file_exists(self):
        compose = (
            Path(__file__).resolve().parent.parent
            / "effectors" / "temporal-golem" / "docker-compose.yml"
        )
        assert compose.is_file()

    def test_compose_has_required_services(self):
        import yaml

        compose = (
            Path(__file__).resolve().parent.parent
            / "effectors" / "temporal-golem" / "docker-compose.yml"
        )
        data = yaml.safe_load(compose.read_text())
        services = data.get("services", {})
        assert "postgresql" in services
        assert "temporal-server" in services
        assert "temporal-web" in services

    def test_compose_ports(self):
        import yaml

        compose = (
            Path(__file__).resolve().parent.parent
            / "effectors" / "temporal-golem" / "docker-compose.yml"
        )
        data = yaml.safe_load(compose.read_text())
        server_ports = data["services"]["temporal-server"]["ports"]
        web_ports = data["services"]["temporal-web"]["ports"]
        # Check that grpc and web ports are mapped
        assert any("7233" in p for p in server_ports)
        assert any("8080" in p for p in web_ports)


# ── GolemTaskSpec ────────────────────────────────────────────────────


class TestGolemTaskSpec:
    def test_fields(self):
        spec = GolemTaskSpec(provider="zhipu", task="hello")
        assert spec.provider == "zhipu"
        assert spec.task == "hello"

    def test_equality(self):
        a = GolemTaskSpec(provider="zhipu", task="hello")
        b = GolemTaskSpec(provider="zhipu", task="hello")
        assert a == b

    def test_inequality(self):
        a = GolemTaskSpec(provider="zhipu", task="hello")
        b = GolemTaskSpec(provider="infini", task="hello")
        assert a != b


# ── GolemDispatchInput ───────────────────────────────────────────────


class TestGolemDispatchInput:
    def test_default_empty(self):
        inp = GolemDispatchInput()
        assert inp.tasks == []

    def test_with_tasks(self):
        tasks = [GolemTaskSpec(provider="zhipu", task="t1")]
        inp = GolemDispatchInput(tasks=tasks)
        assert len(inp.tasks) == 1


# ── File layout verification ─────────────────────────────────────────


class TestFileLayout:
    BASE = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem"

    def test_worker_exists(self):
        assert (self.BASE / "worker.py").is_file()

    def test_workflow_exists(self):
        assert (self.BASE / "workflow.py").is_file()

    def test_cli_exists(self):
        assert (self.BASE / "cli.py").is_file()

    def test_readme_exists(self):
        assert (self.BASE / "README.md").is_file()

    def test_pyproject_exists(self):
        assert (self.BASE / "pyproject.toml").is_file()

    def test_docker_compose_exists(self):
        assert (self.BASE / "docker-compose.yml").is_file()

    def test_start_sh_exists(self):
        assert (self.BASE / "start.sh").is_file()

    def test_dynamic_config_exists(self):
        assert (self.BASE / "config" / "dynamicconfig" / "development-sql.yaml").is_file()

    def test_pyproject_has_temporalio(self):
        content = (self.BASE / "pyproject.toml").read_text()
        assert "temporalio" in content
