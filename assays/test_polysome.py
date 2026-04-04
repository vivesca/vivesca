"""Tests for polysome: translocase activities, workflow logic, and CLI — all mocked."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup — add polysome to sys.path so imports work
# ---------------------------------------------------------------------------

_POLYSOME_DIR = Path(__file__).resolve().parent.parent / "effectors" / "polysome"
sys.path.insert(0, str(_POLYSOME_DIR))


# ============================================================================
# Worker activity tests
# ============================================================================


class TestTranslate:
    """Test the translate activity."""

    def test_imports_worker(self):
        """Worker module imports cleanly."""
        import translocase as worker

        assert hasattr(worker, "translate")
        assert hasattr(worker, "TASK_QUEUE")
        assert worker.TASK_QUEUE == "translation-queue"

    def test_provider_semaphores_defined(self):
        """Per-provider semaphores are initialised with correct limits."""
        import translocase as worker

        assert "zhipu" in worker.PROVIDER_LIMITS
        assert "volcano" in worker.PROVIDER_LIMITS
        assert worker.PROVIDER_LIMITS["zhipu"] == 8
        assert worker.PROVIDER_LIMITS["volcano"] == 16

    @pytest.mark.asyncio
    async def test_successful_translation_run(self):
        """translate activity returns success dict on exit 0."""
        import translocase as worker

        mock_proc = AsyncMock()
        mock_proc.returncode = None
        mock_proc.communicate = AsyncMock(return_value=(b"all tests passed", b""))
        mock_proc.wait = AsyncMock()
        mock_proc.kill = MagicMock()

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            patch.object(
                sys.modules.get("temporalio.activity", MagicMock()), "heartbeat", MagicMock()
            ),
        ):
            result = await worker.translate("Write tests for foo.py", "zhipu", 50)

        assert result["success"] is True
        assert result["exit_code"] == 0
        assert result["provider"] == "zhipu"
        assert "tests passed" in result["stdout"]

    def test_ribosome_script_path(self):
        """RIBOSOME_SCRIPT points to the ribosome effector."""
        import translocase as worker

        assert worker.RIBOSOME_SCRIPT.name == "ribosome"
        assert worker.RIBOSOME_SCRIPT.parent.name == "effectors"

    @pytest.mark.asyncio
    async def test_command_includes_provider_and_turns(self):
        """The subprocess command includes --provider and --max-turns."""
        import translocase as worker

        captured_cmd = None
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        mock_proc.communicate = AsyncMock(return_value=(b"ok", b""))

        async def _capture_cmd(*args, **kwargs):
            nonlocal captured_cmd
            captured_cmd = list(args)
            return mock_proc

        with (
            patch("asyncio.create_subprocess_exec", side_effect=_capture_cmd),
            patch.object(
                sys.modules.get("temporalio.activity", MagicMock()), "heartbeat", MagicMock()
            ),
        ):
            await worker.translate("task desc", "infini", 42)

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

    def test_workflow_decorator(self):
        """TranslationWorkflow has @workflow.defn decorator."""
        from workflow import TranslationWorkflow

        assert hasattr(TranslationWorkflow, "__temporal_workflow_definition")


class TestCli:
    """Test CLI commands with mocked Temporal client."""

    def test_cli_group_exists(self):
        """CLI main group loads."""
        from cli import main

        assert main.name == "main" or callable(main)

    def test_submit_no_tasks_exits(self):
        """submit with no tasks prints error and exits 1."""
        from cli import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ["submit"])
        assert result.exit_code == 1
        assert "no tasks" in result.output.lower() or "Error" in result.output

    def test_submit_single_task(self):
        """submit with one task starts a workflow."""
        from cli import main
        from click.testing import CliRunner

        mock_handle = MagicMock()
        mock_handle.id = "ribosome-zhipu-abcd1234"

        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        mock_gc = AsyncMock(return_value=mock_client)
        with patch("cli._get_client", mock_gc):
            runner = CliRunner()
            result = runner.invoke(main, ["submit", "-p", "zhipu", "Write tests for bar.py"])

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        assert output["tasks_submitted"] == 1
        assert "workflow_id" in output

    def test_submit_from_file(self):
        """submit --file reads tasks from a file."""
        import tempfile

        from cli import main
        from click.testing import CliRunner

        mock_handle = MagicMock()
        mock_handle.id = "ribosome-volcano-feed"

        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        mock_gc = AsyncMock(return_value=mock_client)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Task alpha\n# comment\nTask beta\n\nTask gamma\n")
            f.flush()

            with patch("cli._get_client", mock_gc):
                runner = CliRunner()
                result = runner.invoke(main, ["submit", "-p", "volcano", "-f", f.name])

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        assert output["tasks_submitted"] == 3

    def test_status_completed(self):
        """status shows COMPLETED workflow with result."""
        from cli import main
        from click.testing import CliRunner

        mock_desc = MagicMock()
        mock_desc.status.name = "COMPLETED"
        mock_desc.run_id = "run-abc"
        mock_desc.start_time = "2026-04-01T12:00:00"

        mock_handle = MagicMock()
        mock_handle.describe = AsyncMock(return_value=mock_desc)
        mock_handle.result = AsyncMock(return_value={"total": 1, "succeeded": 1, "failed": 0})

        mock_client = MagicMock()
        # get_workflow_handle is synchronous (returns handle directly)
        mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)

        mock_gc = AsyncMock(return_value=mock_client)
        with patch("cli._get_client", mock_gc):
            runner = CliRunner()
            result = runner.invoke(main, ["status", "ribosome-zhipu-abcd"])

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        assert output["status"] == "COMPLETED"

    def test_list_workflows(self):
        """list returns recent workflows."""
        from cli import main
        from click.testing import CliRunner

        mock_wf = MagicMock()
        mock_wf.id = "ribosome-1"
        mock_wf.status.name = "COMPLETED"
        mock_wf.start_time = "2026-04-01T10:00:00"

        async def _aiter(*a, **kw):
            yield mock_wf

        mock_client = AsyncMock()
        mock_client.list_workflows = _aiter

        mock_gc = AsyncMock(return_value=mock_client)
        with patch("cli._get_client", mock_gc):
            runner = CliRunner()
            result = runner.invoke(main, ["list", "-n", "5"])

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        assert len(output) >= 1
        assert output[0]["workflow_id"] == "ribosome-1"

    def test_submit_custom_workflow_id(self):
        """submit -w sets a custom workflow ID."""
        from cli import main
        from click.testing import CliRunner

        mock_handle = MagicMock()
        mock_handle.id = "my-custom-batch"

        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        mock_gc = AsyncMock(return_value=mock_client)
        with patch("cli._get_client", mock_gc):
            runner = CliRunner()
            result = runner.invoke(
                main, ["submit", "-p", "infini", "-w", "my-custom-batch", "Do stuff"]
            )

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        assert output["workflow_id"] == "my-custom-batch"

    def test_submit_multiple_tasks_args(self):
        """submit with multiple TASK arguments works."""
        from cli import main
        from click.testing import CliRunner

        mock_handle = MagicMock()
        mock_handle.id = "multi-batch"

        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        mock_gc = AsyncMock(return_value=mock_client)
        with patch("cli._get_client", mock_gc):
            runner = CliRunner()
            result = runner.invoke(main, ["submit", "-p", "zhipu", "Task A", "Task B", "Task C"])

        assert "no tasks" not in (result.output or "").lower()


# ============================================================================
# Docker / infra tests
# ============================================================================


class TestDockerCompose:
    """Verify docker-compose.yml is valid YAML with expected services."""

    def test_docker_compose_valid_yaml(self):
        """docker-compose.yml parses as valid YAML."""
        import yaml

        dc_path = _POLYSOME_DIR / "docker-compose.yml"
        with open(dc_path) as f:
            data = yaml.safe_load(f)
        assert "services" in data

    def test_docker_compose_services(self):
        """docker-compose.yml has all four required services."""
        import yaml

        dc_path = _POLYSOME_DIR / "docker-compose.yml"
        with open(dc_path) as f:
            data = yaml.safe_load(f)
        services = data["services"]
        assert "postgresql" in services
        assert "temporal-server" in services
        # Accept either temporal-ui or temporal-web (competing services may rename)
        ui_service = services.get("temporal-ui") or services.get("temporal-web")
        assert ui_service is not None, "Missing temporal-ui or temporal-web service"
        assert "temporal-admin-tools" in services

    def test_docker_compose_ports(self):
        """Services expose expected ports."""
        import yaml

        dc_path = _POLYSOME_DIR / "docker-compose.yml"
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

        dc_path = _POLYSOME_DIR / "docker-compose.yml"
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
        assert (_POLYSOME_DIR / "pyproject.toml").is_file()

    def test_worker_py_exists(self):
        assert (_POLYSOME_DIR / "worker.py").is_file()

    def test_workflow_py_exists(self):
        assert (_POLYSOME_DIR / "workflow.py").is_file()

    def test_cli_py_exists(self):
        assert (_POLYSOME_DIR / "cli.py").is_file()

    def test_docker_compose_exists(self):
        assert (_POLYSOME_DIR / "docker-compose.yml").is_file()

    def test_readme_exists(self):
        assert (_POLYSOME_DIR / "README.md").is_file()

    def test_start_sh_exists(self):
        assert (_POLYSOME_DIR / "start.sh").is_file()

    def test_pyproject_has_temporalio(self):
        content = (_POLYSOME_DIR / "pyproject.toml").read_text()
        assert "temporalio" in content

    def test_all_python_files_parse(self):
        """Every .py file in polysome parses as valid Python."""
        import ast

        for py in _POLYSOME_DIR.glob("*.py"):
            source = py.read_text()
            ast.parse(source)  # raises SyntaxError on failure


# ============================================================================
# Enhanced tests — heartbeat, concurrency, unknown provider, CLI flags
# ============================================================================


class TestConcurrentWorkflow:
    """Test that the workflow dispatches tasks concurrently."""

    def test_workflow_has_execute_one(self):
        """TranslationWorkflow has the _execute_one helper method."""
        from workflow import TranslationWorkflow

        assert hasattr(TranslationWorkflow, "_execute_one")

    def test_workflow_run_uses_asyncio(self):
        """Workflow imports asyncio for concurrent gather."""
        import workflow

        assert hasattr(workflow, "asyncio")


class TestCliFlags:
    """Additional CLI flag and edge-case tests."""

    def test_submit_max_turns_flag(self):
        """submit --max-turns passes through to task specs."""
        from cli import main
        from click.testing import CliRunner

        captured_specs = None

        async def _fake_start_workflow(*args, **kwargs):
            nonlocal captured_specs
            captured_specs = kwargs.get("args", args[1] if len(args) > 1 else None)
            mock_handle = MagicMock()
            mock_handle.id = "ribosome-zhipu-mt"
            return mock_handle

        mock_client = AsyncMock()
        mock_client.start_workflow = _fake_start_workflow

        mock_gc = AsyncMock(return_value=mock_client)
        with patch("cli._get_client", mock_gc):
            runner = CliRunner()
            result = runner.invoke(
                main, ["submit", "-p", "zhipu", "--max-turns", "25", "Do the thing"]
            )

        assert result.exit_code == 0, f"Output: {result.output}"
        # Verify max_turns was captured in the specs
        assert captured_specs is not None
        specs_list = captured_specs[0] if isinstance(captured_specs, list) else captured_specs
        assert specs_list[0]["max_turns"] == 25

    def test_submit_file_ignores_comments_and_blanks(self):
        """submit --file skips blank lines and # comments."""
        import tempfile

        from cli import main
        from click.testing import CliRunner

        captured_specs = None

        async def _fake_start_workflow(*args, **kwargs):
            nonlocal captured_specs
            captured_specs = kwargs.get("args", args[1] if len(args) > 1 else None)
            mock_handle = MagicMock()
            mock_handle.id = "ribosome-filter"
            return mock_handle

        mock_client = AsyncMock()
        mock_client.start_workflow = _fake_start_workflow

        mock_gc = AsyncMock(return_value=mock_client)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# This is a comment\n\nTask one\n# Another comment\nTask two\n")
            f.flush()

            with patch("cli._get_client", mock_gc):
                runner = CliRunner()
                result = runner.invoke(main, ["submit", "-p", "zhipu", "-f", f.name])

        assert result.exit_code == 0, f"Output: {result.output}"
        specs_list = captured_specs[0] if isinstance(captured_specs, list) else captured_specs
        assert len(specs_list) == 2
        assert specs_list[0]["task"] == "Task one"
        assert specs_list[1]["task"] == "Task two"

    def test_status_running_workflow(self):
        """status shows a RUNNING workflow without result."""
        from cli import main
        from click.testing import CliRunner

        mock_desc = MagicMock()
        mock_desc.status.name = "RUNNING"
        mock_desc.run_id = "run-running"
        mock_desc.start_time = "2026-04-01T14:00:00"

        mock_handle = MagicMock()
        mock_handle.describe = AsyncMock(return_value=mock_desc)

        mock_client = MagicMock()
        mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)

        mock_gc = AsyncMock(return_value=mock_client)
        with patch("cli._get_client", mock_gc):
            runner = CliRunner()
            result = runner.invoke(main, ["status", "ribosome-zhipu-running"])

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        assert output["status"] == "RUNNING"
        assert output["result"] is None


class TestReviewPostMortem:
    """Test no_commit_on_success and target_file_missing flags."""

    def test_no_commit_detected(self):
        """exit_code=0 with empty post_diff flags no_commit_on_success."""
        import translocase as worker

        result = asyncio.run(
            worker.chaperone(
                {
                    "task": "Build foo at metabolon/enzymes/foo.py",
                    "provider": "zhipu",
                    "exit_code": 0,
                    "stdout": "Done! All tests pass.",
                    "stderr": "",
                    "pre_diff": {"stat": "", "numstat": ""},
                    "post_diff": {"stat": "", "numstat": ""},
                }
            )
        )
        assert "no_commit_on_success" in result["flags"]
        assert not result["approved"]

    def test_no_commit_not_flagged_on_failure(self):
        """exit_code=1 with empty diff should NOT flag no_commit."""
        import translocase as worker

        result = asyncio.run(
            worker.chaperone(
                {
                    "task": "Build foo",
                    "provider": "zhipu",
                    "exit_code": 1,
                    "stdout": "Error",
                    "stderr": "SyntaxError",
                    "pre_diff": {"stat": "", "numstat": ""},
                    "post_diff": {"stat": "", "numstat": ""},
                }
            )
        )
        assert "no_commit_on_success" not in result["flags"]

    def test_target_file_missing_detected(self):
        """When prompt says 'at X.py' but diff doesn't include it, flag."""
        import translocase as worker

        result = asyncio.run(
            worker.chaperone(
                {
                    "task": "Build enzyme at metabolon/enzymes/ribosome_dispatch.py",
                    "provider": "zhipu",
                    "exit_code": 0,
                    "stdout": "Done!",
                    "stderr": "",
                    "pre_diff": {"stat": "", "numstat": ""},
                    "post_diff": {
                        "stat": " assays/test_something.py | 10 +\n 1 file changed\n",
                        "numstat": "10\t0\tassays/test_something.py",
                    },
                }
            )
        )
        assert any("target_file_missing" in f for f in result["flags"])

    def test_target_file_present_no_flag(self):
        """When target file IS in the diff, no flag."""
        import translocase as worker

        result = asyncio.run(
            worker.chaperone(
                {
                    "task": "Build enzyme at metabolon/enzymes/ribosome_dispatch.py",
                    "provider": "zhipu",
                    "exit_code": 0,
                    "stdout": "Done! All good.",
                    "stderr": "",
                    "pre_diff": {"stat": "", "numstat": ""},
                    "post_diff": {
                        "stat": " metabolon/enzymes/ribosome_dispatch.py | 80 +\n 1 file changed\n",
                        "numstat": "80\t0\tmetabolon/enzymes/ribosome_dispatch.py",
                    },
                }
            )
        )
        assert not any("target_file_missing" in f for f in result["flags"])
        assert "no_commit_on_success" not in result["flags"]
