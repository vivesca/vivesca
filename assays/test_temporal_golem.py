"""Tests for temporal-golem: worker activities, workflow logic, and CLI — all mocked."""
from __future__ import annotations

import asyncio
import json
import sys
import time
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
        from click.testing import CliRunner
        from cli import main
        import tempfile

        mock_handle = MagicMock()
        mock_handle.id = "golem-volcano-feed"

        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        mock_gc = AsyncMock(return_value=mock_client)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Task alpha\n# comment\nTask beta\n\nTask gamma\n")
            f.flush()

            with patch("cli._get_client", mock_gc):
                runner = CliRunner()
                result = runner.invoke(
                    main, ["submit", "-p", "volcano", "-f", f.name]
                )

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
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

        mock_client = MagicMock()
        # get_workflow_handle is synchronous (returns handle directly)
        mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)

        mock_gc = AsyncMock(return_value=mock_client)
        with patch("cli._get_client", mock_gc):
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

        mock_gc = AsyncMock(return_value=mock_client)
        with patch("cli._get_client", mock_gc):
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
        from click.testing import CliRunner
        from cli import main

        mock_handle = MagicMock()
        mock_handle.id = "multi-batch"

        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        mock_gc = AsyncMock(return_value=mock_client)
        with patch("cli._get_client", mock_gc):
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


# ============================================================================
# Enhanced tests — heartbeat, concurrency, unknown provider, CLI flags
# ============================================================================


class TestHeartbeatLoop:
    """Test the periodic heartbeat background task."""

    def test_heartbeat_loop_function_exists(self):
        """worker exposes _heartbeat_loop."""
        import worker
        assert hasattr(worker, "_heartbeat_loop")
        assert callable(worker._heartbeat_loop)

    @pytest.mark.asyncio
    async def test_heartbeat_loop_emits_heartbeats(self):
        """_heartbeat_loop calls activity.heartbeat at least once."""
        import worker

        heartbeat_calls: list[str] = []

        with patch.object(sys.modules.get("temporalio.activity", MagicMock()), "heartbeat", side_effect=lambda m: heartbeat_calls.append(m)):
            stop = await worker._heartbeat_loop("test-task", interval=0.05)
            # Wait long enough for at least one heartbeat tick
            await asyncio.sleep(0.15)
            stop.set()
            await stop.task  # type: ignore[attr-defined]

        assert len(heartbeat_calls) >= 1
        assert "running" in heartbeat_calls[0]

    @pytest.mark.asyncio
    async def test_heartbeat_loop_stops_cleanly(self):
        """_heartbeat_loop terminates when stop event is set."""
        import worker

        with patch.object(sys.modules.get("temporalio.activity", MagicMock()), "heartbeat", MagicMock()):
            stop = await worker._heartbeat_loop("test-task", interval=0.1)
            stop.set()
            await stop.task  # type: ignore[attr-defined]
            # Task completed without error


class TestUnknownProvider:
    """Test that unknown providers are rejected."""

    @pytest.mark.asyncio
    async def test_unknown_provider_raises(self):
        """run_golem_task rejects an unknown provider."""
        import worker

        with pytest.raises(ValueError, match="Unknown provider"):
            await worker.run_golem_task("some task", "nonexistent", 10)


class TestConcurrentWorkflow:
    """Test that the workflow dispatches tasks concurrently."""

    def test_workflow_has_execute_one(self):
        """GolemDispatchWorkflow has the _execute_one helper method."""
        from workflow import GolemDispatchWorkflow
        assert hasattr(GolemDispatchWorkflow, "_execute_one")

    def test_workflow_run_uses_asyncio(self):
        """Workflow imports asyncio for concurrent gather."""
        import workflow
        assert hasattr(workflow, "asyncio")


class TestCliFlags:
    """Additional CLI flag and edge-case tests."""

    def test_submit_max_turns_flag(self):
        """submit --max-turns passes through to task specs."""
        from click.testing import CliRunner
        from cli import main

        captured_specs = None

        async def _fake_start_workflow(*args, **kwargs):
            nonlocal captured_specs
            captured_specs = kwargs.get("args", args[1] if len(args) > 1 else None)
            mock_handle = MagicMock()
            mock_handle.id = "golem-zhipu-mt"
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
        from click.testing import CliRunner
        from cli import main
        import tempfile

        captured_specs = None

        async def _fake_start_workflow(*args, **kwargs):
            nonlocal captured_specs
            captured_specs = kwargs.get("args", args[1] if len(args) > 1 else None)
            mock_handle = MagicMock()
            mock_handle.id = "golem-filter"
            return mock_handle

        mock_client = AsyncMock()
        mock_client.start_workflow = _fake_start_workflow

        mock_gc = AsyncMock(return_value=mock_client)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# This is a comment\n\nTask one\n# Another comment\nTask two\n")
            f.flush()

            with patch("cli._get_client", mock_gc):
                runner = CliRunner()
                result = runner.invoke(
                    main, ["submit", "-p", "zhipu", "-f", f.name]
                )

        assert result.exit_code == 0, f"Output: {result.output}"
        specs_list = captured_specs[0] if isinstance(captured_specs, list) else captured_specs
        assert len(specs_list) == 2
        assert specs_list[0]["task"] == "Task one"
        assert specs_list[1]["task"] == "Task two"

    def test_status_running_workflow(self):
        """status shows a RUNNING workflow without result."""
        from click.testing import CliRunner
        from cli import main

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
            result = runner.invoke(main, ["status", "golem-zhipu-running"])

        assert result.exit_code == 0, f"Output: {result.output}"
        output = json.loads(result.output)
        assert output["status"] == "RUNNING"
        assert output["result"] is None


class TestModelsModule:
    """Test the shared models module."""

    def test_golem_result_ok(self):
        """GolemResult.ok is True for exit 0 and no timeout."""
        from models import GolemResult
        r = GolemResult(provider="zhipu", task="t", exit_code=0, stdout="ok", stderr="")
        assert r.ok is True

    def test_golem_result_fail(self):
        """GolemResult.ok is False for non-zero exit."""
        from models import GolemResult
        r = GolemResult(provider="zhipu", task="t", exit_code=1, stdout="", stderr="err")
        assert r.ok is False

    def test_golem_result_timeout(self):
        """GolemResult.ok is False when timed_out is True."""
        from models import GolemResult
        r = GolemResult(provider="zhipu", task="t", exit_code=0, stdout="", stderr="", timed_out=True)
        assert r.ok is False

    def test_golem_result_str(self):
        """GolemResult __str__ shows status and provider."""
        from models import GolemResult
        r = GolemResult(provider="volcano", task="do thing", exit_code=0, stdout="ok", stderr="")
        s = str(r)
        assert "OK" in s
        assert "volcano" in s

    def test_golem_dispatch_output_str(self):
        """GolemDispatchOutput __str__ summarises results."""
        from models import GolemResult, GolemDispatchOutput
        out = GolemDispatchOutput(
            total=2,
            succeeded=1,
            failed=1,
            results=[
                GolemResult(provider="zhipu", task="a", exit_code=0, stdout="", stderr=""),
                GolemResult(provider="infini", task="b", exit_code=1, stdout="", stderr="err"),
            ],
        )
        s = str(out)
        assert "1/2 succeeded" in s
        assert "FAIL" in s

    def test_golem_dispatch_input(self):
        """GolemDispatchInput holds a list of specs."""
        from models import GolemTaskSpec, GolemDispatchInput
        inp = GolemDispatchInput(tasks=[GolemTaskSpec(provider="zhipu", task="hello")])
        assert len(inp.tasks) == 1
        assert inp.tasks[0].provider == "zhipu"


# ============================================================================
# Dispatch module tests — queue parsing, cooldown, throttle, concurrency
# ============================================================================


class TestDispatchQueueLock:
    """Test QueueLock context manager from dispatch module."""

    def test_queue_lock_acquires_and_releases(self):
        """QueueLock can be used as a context manager without error."""
        import dispatch
        with dispatch.QueueLock():
            pass  # should not raise

    def test_queue_lock_path_matches_daemon(self):
        """QueueLock uses the same lock file as golem-daemon."""
        import dispatch
        assert "golem-queue.lock" in str(dispatch.QueueLock._lock_path)


class TestDispatchTaskId:
    """Test task ID generation and parsing."""

    def test_generate_task_id_format(self):
        """Generated task IDs match t-XXXXXX format."""
        import dispatch
        tid = dispatch._generate_task_id()
        assert tid.startswith("t-")
        assert len(tid) == 8  # "t-" + 6 hex chars
        import re
        assert re.match(r"^t-[0-9a-f]{6}$", tid)

    def test_generate_task_id_unique(self):
        """Successive calls produce different IDs."""
        import dispatch
        ids = {dispatch._generate_task_id() for _ in range(20)}
        assert len(ids) == 20

    def test_task_id_re_extracts_hex(self):
        """TASK_ID_RE extracts 6-char hex from bracket notation."""
        import dispatch
        m = dispatch.TASK_ID_RE.search("golem [t-abc123] --provider zhipu")
        assert m is not None
        assert m.group(1) == "abc123"


class TestDispatchParseQueue:
    """Test parse_queue with temp queue files."""

    def _write_queue(self, content: str, tmp_path: Path) -> Path:
        qf = tmp_path / "golem-queue.md"
        qf.write_text(content)
        return qf

    def test_parse_empty_queue(self, tmp_path):
        """parse_queue returns [] for empty queue."""
        import dispatch
        qf = self._write_queue("", tmp_path)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            result = dispatch.parse_queue()
        assert result == []

    def test_parse_single_pending(self, tmp_path):
        """parse_queue finds a single pending task."""
        import dispatch
        qf = self._write_queue('- [ ] `golem --provider zhipu "Do stuff"`\n', tmp_path)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            result = dispatch.parse_queue()
        assert len(result) == 1
        line_num, prompt, provider, task_id, max_turns = result[0]
        assert provider == "zhipu"
        assert "Do stuff" in prompt
        assert task_id.startswith("t-")

    def test_parse_generates_task_ids(self, tmp_path):
        """parse_queue generates t-xxxxxx IDs for tasks without them."""
        import dispatch
        qf = self._write_queue('- [ ] `golem --provider zhipu "Task"`\n', tmp_path)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            result = dispatch.parse_queue()
        assert len(result) == 1
        task_id = result[0][3]
        assert task_id.startswith("t-")
        # Verify ID was written back to file
        content = qf.read_text()
        assert f"[{task_id}]" in content

    def test_parse_preserves_existing_task_id(self, tmp_path):
        """parse_queue keeps existing task IDs."""
        import dispatch
        qf = self._write_queue('- [ ] `golem [t-dead42] --provider zhipu "Task"`\n', tmp_path)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            result = dispatch.parse_queue()
        assert len(result) == 1
        assert result[0][3] == "t-dead42"

    def test_parse_high_priority_first(self, tmp_path):
        """High-priority [!!] tasks sort before normal [ ]."""
        import dispatch
        content = (
            '- [ ] `golem --provider zhipu "Normal"`\n'
            '- [!!] `golem --provider zhipu "Urgent"`\n'
        )
        qf = self._write_queue(content, tmp_path)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            result = dispatch.parse_queue()
        assert len(result) == 2
        # Urgent should be first
        assert "Urgent" in result[0][1]
        assert "Normal" in result[1][1]

    def test_parse_skips_completed(self, tmp_path):
        """Completed [x] tasks are ignored."""
        import dispatch
        content = '- [x] `golem [t-aaa111] --provider zhipu "Done"`\n'
        qf = self._write_queue(content, tmp_path)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            result = dispatch.parse_queue()
        assert result == []

    def test_parse_extracts_max_turns(self, tmp_path):
        """parse_queue extracts --max-turns value."""
        import dispatch
        content = '- [ ] `golem --provider zhipu --max-turns 42 "Task"`\n'
        qf = self._write_queue(content, tmp_path)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            result = dispatch.parse_queue()
        assert result[0][4] == 42

    def test_parse_default_max_turns(self, tmp_path):
        """parse_queue defaults max_turns to 50."""
        import dispatch
        content = '- [ ] `golem --provider zhipu "Task"`\n'
        qf = self._write_queue(content, tmp_path)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            result = dispatch.parse_queue()
        assert result[0][4] == 50


class TestDispatchMarkDone:
    """Test mark_done with temp queue files."""

    def test_mark_done_normal(self, tmp_path):
        """mark_done changes [ ] to [x]."""
        import dispatch
        content = '- [ ] `golem [t-abc123] --provider zhipu "Task"`\n'
        qf = tmp_path / "golem-queue.md"
        qf.write_text(content)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            dispatch.mark_done(0, task_id="t-abc123")
        assert "[x]" in qf.read_text()

    def test_mark_done_high_priority(self, tmp_path):
        """mark_done changes [!!] to [x]."""
        import dispatch
        content = '- [!!] `golem [t-def456] --provider zhipu "Task"`\n'
        qf = tmp_path / "golem-queue.md"
        qf.write_text(content)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            dispatch.mark_done(0, task_id="t-def456")
        assert "[x]" in qf.read_text()
        assert "[!!]" not in qf.read_text()


class TestDispatchMarkFailed:
    """Test mark_failed with temp queue files."""

    def test_mark_failed_retries_once(self, tmp_path):
        """mark_failed adds (retry) tag on first failure."""
        import dispatch
        content = '- [ ] `golem [t-fail00] --provider zhipu "Task"`\n'
        qf = tmp_path / "golem-queue.md"
        qf.write_text(content)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            result = dispatch.mark_failed(0, task_id="t-fail00")
        assert result["retried"] is True
        assert "(retry)" in qf.read_text()

    def test_mark_failed_permanent_after_retry(self, tmp_path):
        """mark_failed marks [!] permanently on second failure."""
        import dispatch
        content = '- [ ] `golem [t-fail01] --provider zhipu "Task (retry)"`\n'
        qf = tmp_path / "golem-queue.md"
        qf.write_text(content)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            result = dispatch.mark_failed(0, task_id="t-fail01")
        assert result["retried"] is False
        assert "[!]" in qf.read_text()

    def test_mark_failed_detects_rate_limit(self, tmp_path):
        """mark_failed sets rate_limited=True when reason contains 429."""
        import dispatch
        content = '- [ ] `golem [t-rl0000] --provider zhipu "Task"`\n'
        qf = tmp_path / "golem-queue.md"
        qf.write_text(content)
        with patch.object(dispatch, "QUEUE_FILE", qf):
            result = dispatch.mark_failed(0, task_id="t-rl0000", reason="HTTP 429 rate limit exceeded")
        assert result["rate_limited"] is True


class TestDispatchCooldown:
    """Test cooldown tracking functions."""

    def test_set_and_check_cooldown(self):
        """_set_cooldown and _is_on_cooldown work together."""
        import dispatch
        dispatch._provider_cooldown_until.clear()
        dispatch._set_cooldown("zhipu", 3600)
        assert dispatch._is_on_cooldown("zhipu")

    def test_cooldown_expires(self):
        """Cooldown expires when time has passed."""
        import dispatch
        dispatch._provider_cooldown_until.clear()
        # Set cooldown in the past
        dispatch._provider_cooldown_until["infini"] = time.time() - 1
        assert not dispatch._is_on_cooldown("infini")

    def test_cooldown_only_extends(self):
        """_set_cooldown only extends, never shortens cooldown."""
        import dispatch
        dispatch._provider_cooldown_until.clear()
        far_future = time.time() + 10000
        dispatch._provider_cooldown_until["volcano"] = far_future
        dispatch._set_cooldown("volcano", 10)  # try to shorten
        assert dispatch._provider_cooldown_until["volcano"] == far_future


class TestDispatchThrottle:
    """Test adaptive throttle functions."""

    def test_throttle_reduces_limit(self):
        """_throttle_provider reduces effective concurrency."""
        import dispatch
        dispatch._provider_throttle.clear()
        base = dispatch.PROVIDER_LIMITS["zhipu"]
        dispatch._throttle_provider("zhipu")
        assert dispatch.get_provider_limit("zhipu") == base - 1

    def test_unthrottle_restores_limit(self):
        """_unthrottle_provider restores concurrency."""
        import dispatch
        dispatch._provider_throttle.clear()
        dispatch._provider_throttle["zhipu"] = 2
        dispatch._unthrottle_provider("zhipu")
        assert dispatch.get_provider_limit("zhipu") == dispatch.PROVIDER_LIMITS["zhipu"] - 1

    def test_throttle_minimum_one(self):
        """Concurrency never drops below 1."""
        import dispatch
        dispatch._provider_throttle.clear()
        dispatch._provider_throttle["infini"] = dispatch.PROVIDER_LIMITS["infini"] - 1
        dispatch._throttle_provider("infini")
        assert dispatch.get_provider_limit("infini") >= 1

    def test_unthrottle_wont_go_negative(self):
        """Unthrottling at 0 stays at 0."""
        import dispatch
        dispatch._provider_throttle.clear()
        dispatch._unthrottle_provider("zhipu")
        assert dispatch._provider_throttle.get("zhipu", 0) == 0


class TestDispatchCandidates:
    """Test _dispatch_candidates fallback chain."""

    def test_candidates_includes_fallback_first(self):
        """Fallback candidates come first, then remaining providers."""
        import dispatch
        candidates = dispatch._dispatch_candidates("codex")
        assert candidates[0] == "gemini"
        assert candidates[1] == "zhipu"
        # All providers should be present except codex itself
        assert "codex" not in candidates
        assert len(candidates) == len(dispatch.PROVIDER_LIMITS) - 1

    def test_candidates_no_duplicates(self):
        """_dispatch_candidates never returns duplicates."""
        import dispatch
        for prov in dispatch.PROVIDER_LIMITS:
            candidates = dispatch._dispatch_candidates(prov)
            assert len(candidates) == len(set(candidates))


class TestDispatchPickProvider:
    """Test _pick_dispatch_provider fallback logic."""

    def test_prefers_primary_when_available(self):
        """Returns primary provider when not on cooldown."""
        import dispatch
        dispatch._provider_cooldown_until.clear()
        dispatch._provider_running.clear()
        assert dispatch._pick_dispatch_provider("zhipu") == "zhipu"

    def test_falls_back_on_cooldown(self):
        """Falls back when primary is on cooldown."""
        import dispatch
        dispatch._provider_cooldown_until.clear()
        dispatch._provider_running.clear()
        dispatch._set_cooldown("zhipu", 3600)
        result = dispatch._pick_dispatch_provider("zhipu")
        assert result is not None
        assert result != "zhipu"

    def test_returns_none_all_on_cooldown(self):
        """Returns None when all providers are on cooldown."""
        import dispatch
        dispatch._provider_cooldown_until.clear()
        dispatch._provider_running.clear()
        for prov in dispatch.PROVIDER_LIMITS:
            dispatch._set_cooldown(prov, 3600)
        assert dispatch._pick_dispatch_provider("zhipu") is None


class TestDispatchFindTaskLine:
    """Test _find_task_line resilience."""

    def test_fast_path_correct_line(self):
        """Returns line_num when it still matches."""
        import dispatch
        lines = [
            "- [ ] `golem [t-abc123] --provider zhipu \"Task\"`",
            "- [ ] `golem [t-def456] --provider zhipu \"Other\"`",
        ]
        assert dispatch._find_task_line(lines, 0, "t-abc123") == 0
        assert dispatch._find_task_line(lines, 1, "t-def456") == 1

    def test_slow_path_scan_by_id(self):
        """Scans by task_id when line_num is wrong."""
        import dispatch
        lines = [
            "# header",
            "- [ ] `golem [t-abc123] --provider zhipu \"Task\"`",
        ]
        assert dispatch._find_task_line(lines, 0, "t-abc123") == 1

    def test_returns_minus_one_not_found(self):
        """Returns -1 when task can't be found."""
        import dispatch
        lines = ["- [x] completed task"]
        assert dispatch._find_task_line(lines, 0, "t-noexist") == -1


class TestDispatchRateLimit:
    """Test rate-limit detection functions."""

    def test_is_rate_limited_429(self):
        """Detects HTTP 429."""
        import dispatch
        assert dispatch.is_rate_limited("HTTP 429 Too Many Requests")

    def test_is_rate_limited_quota(self):
        """Detects quota exceeded."""
        import dispatch
        assert dispatch.is_rate_limited("AccountQuotaExceeded for user")

    def test_not_rate_limited_normal(self):
        """Normal errors are not rate-limited."""
        import dispatch
        assert not dispatch.is_rate_limited("file not found")

    def test_parse_rate_limit_window_duration(self):
        """Parses '5-hour' duration."""
        import dispatch
        assert dispatch.parse_rate_limit_window("rate limit: 5-hour window") == 5 * 3600

    def test_parse_rate_limit_window_minutes(self):
        """Parses '30-minute' duration."""
        import dispatch
        assert dispatch.parse_rate_limit_window("retry after 30-minute cooldown") == 30 * 60

    def test_parse_rate_limit_window_gemini(self):
        """Parses Gemini 'quota will reset after NmNs' format."""
        import dispatch
        assert dispatch.parse_rate_limit_window("quota will reset after 18m38s") == 18 * 60 + 38

    def test_parse_rate_limit_window_none(self):
        """Returns None for non-matching text."""
        import dispatch
        assert dispatch.parse_rate_limit_window("something went wrong") is None


class TestDispatchSwapProvider:
    """Test _swap_provider command rewriting."""

    def test_swap_provider_in_command(self):
        """Swaps --provider in a golem command string."""
        import dispatch
        cmd = 'golem [t-abc123] --provider zhipu --max-turns 25 "Do stuff"'
        result = dispatch._swap_provider(cmd, "zhipu", "codex")
        assert "--provider codex" in result
        assert "--provider zhipu" not in result

    def test_swap_preserves_rest(self):
        """Swapping provider preserves the rest of the command."""
        import dispatch
        cmd = 'golem --provider zhipu --max-turns 25 "Do stuff"'
        result = dispatch._swap_provider(cmd, "zhipu", "gemini")
        assert "--max-turns 25" in result
        assert "Do stuff" in result
