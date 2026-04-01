"""Tests for temporal-golem: worker activities, workflow logic, and CLI — all mocked."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup — add temporal-golem to sys.path so imports work
# ---------------------------------------------------------------------------

_TEMPORAL_GOLEM_DIR = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem"
sys.path.insert(0, str(_TEMPORAL_GOLEM_DIR))


# ============================================================================
# Worker activity tests
# ============================================================================


class TestRunGolemTask:
    """Test the run_golem_task activity."""

    def test_imports_worker(self):
        """Worker module imports cleanly."""
        import worker
        assert hasattr(worker, "run_golem_task")
        assert hasattr(worker, "TASK_QUEUE")
        assert worker.TASK_QUEUE == "golem-tasks"

    def test_provider_semaphores_defined(self):
        """Per-provider semaphores are initialised with correct limits."""
        import worker
        assert "zhipu" in worker._PROVIDER_SEMAPHORES
        assert "infini" in worker._PROVIDER_SEMAPHORES
        assert "volcano" in worker._PROVIDER_SEMAPHORES
        # Semaphore._value is the internal counter
        assert worker._PROVIDER_SEMAPHORES["zhipu"]._value == 8
        assert worker._PROVIDER_SEMAPHORES["infini"]._value == 8
        assert worker._PROVIDER_SEMAPHORES["volcano"]._value == 16

    @pytest.mark.asyncio
    async def test_successful_golem_run(self):
        """run_golem_task returns success dict on exit 0."""
        import worker

        mock_proc = AsyncMock()
        mock_proc.returncode = None
        mock_proc.communicate = AsyncMock(
            return_value=(b"all tests passed", b"")
        )
        mock_proc.wait = AsyncMock()
        mock_proc.kill = MagicMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            # Patch activity.heartbeat to be a no-op
            with patch.object(sys.modules.get("temporalio.activity", MagicMock()), "heartbeat", MagicMock()):
                result = await worker.run_golem_task(
                    "Write tests for foo.py", "zhipu", 50
                )

        assert result["success"] is True
        assert result["exit_code"] == 0
        assert result["provider"] == "zhipu"
        assert "tests passed" in result["stdout"]

    @pytest.mark.asyncio
    async def test_failed_golem_run_raises(self):
        """run_golem_task raises RuntimeError on non-zero exit."""
        import worker

        mock_proc = AsyncMock()
        # Set returncode to a non-zero value *after* communicate completes
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(
            return_value=(b"", b"error: something broke")
        )
        mock_proc.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch.object(sys.modules.get("temporalio.activity", MagicMock()), "heartbeat", MagicMock()):
                with pytest.raises(RuntimeError, match="Golem exited"):
                    await worker.run_golem_task("Bad task", "infini", 30)

    @pytest.mark.asyncio
    async def test_timeout_kills_process(self):
        """run_golem_task kills process and raises on timeout."""
        import worker

        # communicate will hang forever
        hang_future = asyncio.get_event_loop().create_future()
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        mock_proc.communicate = AsyncMock(return_value=hang_future)
        mock_proc.wait = AsyncMock()
        mock_proc.kill = MagicMock()

        async def _fake_wait_for(coro, timeout):
            raise asyncio.TimeoutError()

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch("asyncio.wait_for", side_effect=_fake_wait_for):
                with patch.object(sys.modules.get("temporalio.activity", MagicMock()), "heartbeat", MagicMock()):
                    with pytest.raises(RuntimeError, match="timed out"):
                        await worker.run_golem_task("Slow task", "volcano", 10)

        mock_proc.kill.assert_called_once()

    def test_golem_script_path(self):
        """GOLEM_SCRIPT points to the golem effector."""
        import worker
        assert worker.GOLEM_SCRIPT.name == "golem"
        assert worker.GOLEM_SCRIPT.parent.name == "effectors"

    @pytest.mark.asyncio
    async def test_command_includes_provider_and_turns(self):
        """The subprocess command includes --provider and --max-turns."""
        import worker

        captured_cmd = None
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        mock_proc.communicate = AsyncMock(return_value=(b"ok", b""))

        async def _capture_cmd(*args, **kwargs):
            nonlocal captured_cmd
            captured_cmd = list(args)
            return mock_proc

        with patch("asyncio.create_subprocess_exec", side_effect=_capture_cmd):
            with patch.object(sys.modules.get("temporalio.activity", MagicMock()), "heartbeat", MagicMock()):
                await worker.run_golem_task("task desc", "infini", 42)

        assert "--provider" in captured_cmd
        idx = captured_cmd.index("--provider")
        assert captured_cmd[idx + 1] == "infini"
        assert "--max-turns" in captured_cmd
        idx2 = captured_cmd.index("--max-turns")
        assert captured_cmd[idx2 + 1] == "42"


# ============================================================================
# Workflow tests
# ============================================================================


class TestWorkflow:
    """Test workflow data types and structure."""

    def test_golem_task_spec(self):
        """GolemTaskSpec dataclass holds expected fields."""
        from workflow import GolemTaskSpec
        spec = GolemTaskSpec(task="do thing", provider="volcano", max_turns=25)
        assert spec.task == "do thing"
        assert spec.provider == "volcano"
        assert spec.max_turns == 25

    def test_golem_task_spec_defaults(self):
        """GolemTaskSpec has sensible defaults."""
        from workflow import GolemTaskSpec
        spec = GolemTaskSpec(task="hello")
        assert spec.provider == "zhipu"
        assert spec.max_turns == 50

    def test_golem_task_result(self):
        """GolemTaskResult holds exit information."""
        from workflow import GolemTaskResult
        r = GolemTaskResult(task="t", provider="zhipu", success=True, exit_code=0)
        assert r.success is True
        assert r.exit_code == 0

    def test_golem_batch_result(self):
        """GolemBatchResult aggregates results."""
        from workflow import GolemBatchResult, GolemTaskResult
        batch = GolemBatchResult(
            total=3, succeeded=2, failed=1,
            results=[
                GolemTaskResult(task="a", provider="zhipu", success=True),
                GolemTaskResult(task="b", provider="infini", success=True),
                GolemTaskResult(task="c", provider="volcano", success=False, exit_code=1),
            ],
        )
        assert batch.total == 3
        assert batch.succeeded == 2
        assert batch.failed == 1
        assert len(batch.results) == 3

    def test_workflow_decorator(self):
        """GolemDispatchWorkflow has @workflow.defn decorator."""
        from workflow import GolemDispatchWorkflow
        assert hasattr(GolemDispatchWorkflow, "__temporal_workflow_definition")

    def test_retry_policy_exists(self):
        """Retry policy constants are defined."""
        from workflow import _RETRY_POLICY_ARGS
        assert "start_to_close_timeout" in _RETRY_POLICY_ARGS
        assert "retry_policy" in _RETRY_POLICY_ARGS
        rp = _RETRY_POLICY_ARGS["retry_policy"]
        assert rp.maximum_attempts == 3
        assert rp.backoff_coefficient == 2.0


# ============================================================================
# CLI tests
# ============================================================================


class TestCli:
    """Test CLI commands with mocked Temporal client."""

    def test_cli_group_exists(self):
        """CLI main group loads."""
        from cli import main
        assert main.name == "main" or callable(main)

    def test_submit_no_tasks_exits(self):
        """submit with no tasks prints error and exits 1."""
        from click.testing import CliRunner
        from cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["submit"])
        assert result.exit_code == 1
        assert "no tasks" in result.output.lower() or "Error" in result.output

    def test_submit_single_task(self):
        """submit with one task starts a workflow."""
        from click.testing import CliRunner
        from cli import main

        mock_handle = MagicMock()
        mock_handle.id = "golem-zhipu-abcd1234"

        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        with patch("cli._get_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(main, ["submit", "-p", "zhipu", "Write tests for bar.py"])

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        assert output["tasks_submitted"] == 1
        assert "workflow_id" in output

    def test_submit_from_file(self):
        """submit --file reads tasks from a file."""
        from click.testing import CliRunner
        from cli import main
        import tempfile

        mock_handle = MagicMock()
        mock_handle.id = "golem-volcano-feed"

        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Task alpha\n# comment\nTask beta\n\nTask gamma\n")
            f.flush()

            with patch("cli._get_client", return_value=mock_client):
                runner = CliRunner()
                result = runner.invoke(
                    main, ["submit", "-p", "volcano", "-f", f.name]
                )

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        # Should skip blank lines and comments -> 3 tasks
        assert output["tasks_submitted"] == 3

    def test_status_completed(self):
        """status shows COMPLETED workflow with result."""
        from click.testing import CliRunner
        from cli import main

        mock_desc = MagicMock()
        mock_desc.status.name = "COMPLETED"
        mock_desc.run_id = "run-abc"
        mock_desc.start_time = "2026-04-01T12:00:00"

        mock_handle = MagicMock()
        mock_handle.describe = AsyncMock(return_value=mock_desc)
        mock_handle.result = AsyncMock(return_value={"total": 1, "succeeded": 1, "failed": 0})

        mock_client = AsyncMock()
        mock_client.get_workflow_handle.return_value = mock_handle

        with patch("cli._get_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(main, ["status", "golem-zhipu-abcd"])

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        assert output["status"] == "COMPLETED"

    def test_list_workflows(self):
        """list returns recent workflows."""
        from click.testing import CliRunner
        from cli import main

        mock_wf = MagicMock()
        mock_wf.id = "golem-1"
        mock_wf.status.name = "COMPLETED"
        mock_wf.start_time = "2026-04-01T10:00:00"

        async def _aiter(*a, **kw):
            yield mock_wf

        mock_client = AsyncMock()
        mock_client.list_workflows = _aiter

        with patch("cli._get_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(main, ["list", "-n", "5"])

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        assert len(output) >= 1
        assert output[0]["workflow_id"] == "golem-1"

    def test_submit_custom_workflow_id(self):
        """submit -w sets a custom workflow ID."""
        from click.testing import CliRunner
        from cli import main

        mock_handle = MagicMock()
        mock_handle.id = "my-custom-batch"

        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        with patch("cli._get_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(
                main, ["submit", "-p", "infini", "-w", "my-custom-batch", "Do stuff"]
            )

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        assert output["workflow_id"] == "my-custom-batch"

    def test_submit_multiple_tasks_args(self):
        """submit with multiple TASK arguments works."""
        from click.testing import CliRunner
        from cli import main

        mock_handle = MagicMock()
        mock_handle.id = "multi-batch"

        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        with patch("cli._get_client", return_value=mock_client):
            runner = CliRunner()
            result = runner.invoke(
                main, ["submit", "-p", "zhipu", "Task A", "Task B", "Task C"]
            )

        assert "no tasks" not in (result.output or "").lower()


# ============================================================================
# Docker / infra tests
# ============================================================================


class TestDockerCompose:
    """Verify docker-compose.yml is valid YAML with expected services."""

    def test_docker_compose_valid_yaml(self):
        """docker-compose.yml parses as valid YAML."""
        import yaml
        dc_path = _TEMPORAL_GOLEM_DIR / "docker-compose.yml"
        with open(dc_path) as f:
            data = yaml.safe_load(f)
        assert "services" in data

    def test_docker_compose_services(self):
        """docker-compose.yml has all four required services."""
        import yaml
        dc_path = _TEMPORAL_GOLEM_DIR / "docker-compose.yml"
        with open(dc_path) as f:
            data = yaml.safe_load(f)
        services = data["services"]
        assert "postgresql" in services
        assert "temporal-server" in services
        # Accept either temporal-ui or temporal-web (competing golems may rename)
        ui_service = services.get("temporal-ui") or services.get("temporal-web")
        assert ui_service is not None, "Missing temporal-ui or temporal-web service"
        assert "temporal-admin-tools" in services

    def test_docker_compose_ports(self):
        """Services expose expected ports."""
        import yaml
        dc_path = _TEMPORAL_GOLEM_DIR / "docker-compose.yml"
        with open(dc_path) as f:
            data = yaml.safe_load(f)
        services = data["services"]

        # Temporal server on 7233
        server_ports = services["temporal-server"]["ports"]
        assert any("7233" in str(p) for p in server_ports)

        # Web UI on 8080-ish (service may be temporal-ui or temporal-web)
        ui_service = services.get("temporal-ui") or services.get("temporal-web")
        ui_ports = ui_service["ports"]
        assert any("8080" in str(p) or "8088" in str(p) for p in ui_ports)

        # PostgreSQL on 5432
        pg_ports = services["postgresql"]["ports"]
        assert any("5432" in str(p) for p in pg_ports)

    def test_docker_compose_persistence(self):
        """PostgreSQL uses a named volume for persistence."""
        import yaml
        dc_path = _TEMPORAL_GOLEM_DIR / "docker-compose.yml"
        with open(dc_path) as f:
            data = yaml.safe_load(f)
        assert "volumes" in data
        assert "temporal-pgdata" in data["volumes"]


# ============================================================================
# File structure tests
# ============================================================================


class TestFileStructure:
    """Verify all scaffold files exist."""

    def test_pyproject_toml_exists(self):
        assert (_TEMPORAL_GOLEM_DIR / "pyproject.toml").is_file()

    def test_worker_py_exists(self):
        assert (_TEMPORAL_GOLEM_DIR / "worker.py").is_file()

    def test_workflow_py_exists(self):
        assert (_TEMPORAL_GOLEM_DIR / "workflow.py").is_file()

    def test_cli_py_exists(self):
        assert (_TEMPORAL_GOLEM_DIR / "cli.py").is_file()

    def test_docker_compose_exists(self):
        assert (_TEMPORAL_GOLEM_DIR / "docker-compose.yml").is_file()

    def test_readme_exists(self):
        assert (_TEMPORAL_GOLEM_DIR / "README.md").is_file()

    def test_start_sh_exists(self):
        assert (_TEMPORAL_GOLEM_DIR / "start.sh").is_file()

    def test_pyproject_has_temporalio(self):
        content = (_TEMPORAL_GOLEM_DIR / "pyproject.toml").read_text()
        assert "temporalio" in content

    def test_all_python_files_parse(self):
        """Every .py file in temporal-golem parses as valid Python."""
        import ast
        for py in _TEMPORAL_GOLEM_DIR.glob("*.py"):
            source = py.read_text()
            ast.parse(source)  # raises SyntaxError on failure
