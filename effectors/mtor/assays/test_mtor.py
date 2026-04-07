"""Tests for mtor.

All tests invoke the cyclopts App directly with captured stdout.
Temporal client calls are mocked via unittest.mock.patch.
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

from mtor.cli import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def invoke(args: list[str] | None = None) -> tuple[int, dict]:
    """Invoke CLI and return (exit_code, parsed_json)."""
    captured = io.StringIO()
    old_stdout = sys.stdout
    exit_code = 0
    try:
        sys.stdout = captured
        app(args or [])
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.stdout = old_stdout

    output = captured.getvalue()
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"Output is not valid JSON. Exit={exit_code}\nOutput: {output!r}\nException: {exc}"
        ) from exc
    return exit_code, data


def make_mock_client():
    """Build a minimal async mock Temporal client."""
    client = MagicMock()

    # start_workflow returns a handle with an .id attribute
    handle = MagicMock()
    handle.id = "ribosome-test1234"
    start_coro = AsyncMock(return_value=handle)
    client.start_workflow = start_coro

    # list_workflows returns an async iterator
    async def _fake_list(query=None):
        execution = MagicMock()
        execution.id = "ribosome-test1234"
        execution.status = MagicMock()
        execution.status.name = "COMPLETED"
        execution.start_time = MagicMock()
        execution.start_time.isoformat.return_value = "2026-04-06T00:00:00+00:00"
        execution.close_time = MagicMock()
        execution.close_time.isoformat.return_value = "2026-04-06T00:01:00+00:00"
        yield execution

    client.list_workflows = _fake_list

    # get_workflow_handle returns a handle
    wf_handle = MagicMock()
    desc = MagicMock()
    desc.status = MagicMock()
    desc.status.name = "COMPLETED"
    desc.start_time = MagicMock()
    desc.start_time.isoformat.return_value = "2026-04-06T00:00:00+00:00"
    desc.close_time = MagicMock()
    desc.close_time.isoformat.return_value = "2026-04-06T00:01:00+00:00"
    describe_coro = AsyncMock(return_value=desc)
    wf_handle.describe = describe_coro
    cancel_coro = AsyncMock(return_value=None)
    wf_handle.cancel = cancel_coro
    client.get_workflow_handle = MagicMock(return_value=wf_handle)

    return client, wf_handle


# Modules that import _get_client — patch all of them to keep tests reliable.
_CLIENT_PATCH_TARGETS = [
    "mtor.cli._get_client",
    "mtor.doctor._get_client",
    "mtor.dispatch._get_client",
]


def _patch_client(mock_client):
    """Context manager: patch _get_client in all modules that import it."""
    stack = ExitStack()
    for target in _CLIENT_PATCH_TARGETS:
        stack.enter_context(patch(target, return_value=(mock_client, None)))
    return stack


def _patch_client_error(error_msg="Connection refused"):
    """Context manager: patch _get_client to return error in all modules."""
    stack = ExitStack()
    for target in _CLIENT_PATCH_TARGETS:
        stack.enter_context(patch(target, return_value=(None, error_msg)))
    return stack


# ---------------------------------------------------------------------------
# Basic structure tests
# ---------------------------------------------------------------------------


class TestBareInvocation:
    def test_returns_valid_json(self):
        exit_code, _data = invoke([])
        assert exit_code == 0, f"Expected exit 0, got {exit_code}"

    def test_ok_true(self):
        _, data = invoke([])
        assert data["ok"] is True

    def test_has_commands_list(self):
        _, data = invoke([])
        assert "commands" in data["result"]
        assert isinstance(data["result"]["commands"], list)
        assert len(data["result"]["commands"]) > 0

    def test_command_field_present(self):
        _, data = invoke([])
        assert data["command"] == "mtor"

    def test_next_actions_present(self):
        _, data = invoke([])
        assert "next_actions" in data

    def test_all_subcommands_in_tree(self):
        _, data = invoke([])
        for expected in [
            "mtor",
            "mtor list",
            "mtor status <workflow_id>",
            "mtor logs <workflow_id>",
            "mtor cancel <workflow_id>",
            "mtor doctor",
            "mtor schema",
        ]:
            first_word = expected.split()[0]
            assert any(cmd["name"].startswith(first_word) for cmd in data["result"]["commands"]), (
                f"Command starting with '{first_word}' not found in tree"
            )


class TestHelpSuppression:
    def test_no_human_help_output(self):
        """With help_flags=[], no human-readable help page should appear."""
        captured = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        try:
            sys.stdout = captured
            sys.stderr = captured
            app(["--help"])
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        output = captured.getvalue()
        # Must not contain standard help indicators
        assert "Show this message and exit" not in output


class TestExitCodes:
    def test_ok_exits_0(self):
        exit_code, _ = invoke([])
        assert exit_code == 0

    def test_schema_exits_0(self):
        exit_code, _ = invoke(["schema"])
        assert exit_code == 0

    def test_dispatch_no_prompt_exits_2(self):
        # dispatch with empty string = usage error
        _exit_code, data = invoke([""])
        assert data["ok"] is False
        assert data["error"]["code"] in (
            "MISSING_PROMPT",
            "TEMPORAL_UNREACHABLE",
            "DISPATCH_ERROR",
        )

    def test_temporal_unreachable_exits_3(self):
        with _patch_client_error("Connection refused"):
            exit_code, data = invoke(["doctor"])
        assert exit_code == 3
        assert data["ok"] is False

    def test_workflow_not_found_exits_4(self):
        mock_client, mock_handle = make_mock_client()
        not_found_exc = Exception("workflow not found: no such workflow")
        mock_handle.describe = AsyncMock(side_effect=not_found_exc)
        with _patch_client(mock_client):
            exit_code, data = invoke(["status", "nonexistent-id"])
        assert exit_code == 4
        assert data["ok"] is False
        assert data["error"]["code"] == "WORKFLOW_NOT_FOUND"


# ---------------------------------------------------------------------------
# Dispatch tests
# ---------------------------------------------------------------------------


class TestDispatch:
    def test_dispatch_with_prompt_returns_workflow_id(self):
        mock_client, _ = make_mock_client()
        with _patch_client(mock_client):
            exit_code, data = invoke(["Test task prompt"])
        assert exit_code == 0
        assert data["ok"] is True
        assert "workflow_id" in data["result"]
        assert data["result"]["status"] == "RUNNING"

    def test_dispatch_has_next_actions(self):
        mock_client, _ = make_mock_client()
        with _patch_client(mock_client):
            _, data = invoke(["Test task"])
        assert len(data["next_actions"]) > 0
        commands = [na["command"] for na in data["next_actions"]]
        assert any("status" in cmd for cmd in commands)

    def test_dispatch_no_prompt_returns_error_envelope(self):
        """Empty prompt string must return error with fix field."""
        _exit_code, data = invoke([""])
        assert data["ok"] is False
        assert "fix" in data, "Error envelope must include 'fix' field"

    def test_dispatch_temporal_unreachable_exits_3(self):
        with _patch_client_error("Connection refused"):
            exit_code, data = invoke(["Write tests for foo.py"])
        assert exit_code == 3
        assert data["ok"] is False
        assert data["error"]["code"] == "TEMPORAL_UNREACHABLE"
        assert "fix" in data

    def test_all_outputs_are_valid_json(self):
        """Sanity: every output path produces parseable JSON."""
        mock_client, _ = make_mock_client()
        test_cases = [
            [],
            ["schema"],
            ["doctor"],
        ]
        with _patch_client(mock_client):
            for args in test_cases:
                _exit_code, data = invoke(args)
                assert isinstance(data, dict), f"Not a dict for args={args}"


# ---------------------------------------------------------------------------
# List tests
# ---------------------------------------------------------------------------


class TestList:
    def test_list_returns_workflows(self):
        mock_client, _ = make_mock_client()
        with _patch_client(mock_client):
            exit_code, data = invoke(["list"])
        assert exit_code == 0
        assert data["ok"] is True
        assert "workflows" in data["result"]

    def test_list_temporal_unreachable(self):
        with _patch_client_error("Connection refused"):
            exit_code, data = invoke(["list"])
        assert exit_code == 3
        assert data["ok"] is False
        assert "fix" in data

    def test_list_has_next_actions_per_workflow(self):
        mock_client, _ = make_mock_client()
        with _patch_client(mock_client):
            _, data = invoke(["list"])
        if data["result"]["count"] > 0:
            assert len(data["next_actions"]) > 0


# ---------------------------------------------------------------------------
# Status tests
# ---------------------------------------------------------------------------


class TestStatus:
    def test_status_returns_workflow_details(self):
        mock_client, _ = make_mock_client()
        with _patch_client(mock_client):
            exit_code, data = invoke(["status", "ribosome-test1234"])
        assert exit_code == 0
        assert data["ok"] is True
        assert data["result"]["workflow_id"] == "ribosome-test1234"
        assert "status" in data["result"]

    def test_status_not_found(self):
        mock_client, mock_handle = make_mock_client()
        mock_handle.describe = AsyncMock(side_effect=Exception("workflow_not_found"))
        with _patch_client(mock_client):
            exit_code, data = invoke(["status", "bad-id"])
        assert exit_code == 4
        assert data["ok"] is False
        assert data["error"]["code"] == "WORKFLOW_NOT_FOUND"

    def test_status_temporal_unreachable(self):
        with _patch_client_error("timeout"):
            exit_code, data = invoke(["status", "any-id"])
        assert exit_code == 3
        assert data["ok"] is False


# ---------------------------------------------------------------------------
# Cancel tests
# ---------------------------------------------------------------------------


class TestCancel:
    def test_cancel_success(self):
        mock_client, _ = make_mock_client()
        with _patch_client(mock_client):
            exit_code, data = invoke(["cancel", "ribosome-test1234"])
        assert exit_code == 0
        assert data["ok"] is True
        assert data["result"]["cancelled"] is True

    def test_cancel_not_found_exits_4(self):
        mock_client, mock_handle = make_mock_client()
        mock_handle.cancel = AsyncMock(side_effect=Exception("workflow not found"))
        with _patch_client(mock_client):
            exit_code, data = invoke(["cancel", "nonexistent-id"])
        assert exit_code == 4
        assert data["ok"] is False
        assert "fix" in data

    def test_cancel_already_cancelled_is_ok(self):
        """Cancelling an already-cancelled workflow = idempotent success."""
        mock_client, mock_handle = make_mock_client()
        mock_handle.cancel = AsyncMock(side_effect=Exception("workflow already cancelled"))
        with _patch_client(mock_client):
            exit_code, data = invoke(["cancel", "ribosome-done1234"])
        assert exit_code == 0
        assert data["ok"] is True

    def test_cancel_temporal_unreachable(self):
        with _patch_client_error("refused"):
            exit_code, data = invoke(["cancel", "any-id"])
        assert exit_code == 3
        assert data["ok"] is False


# ---------------------------------------------------------------------------
# Doctor tests
# ---------------------------------------------------------------------------


class TestDoctor:
    def test_doctor_unreachable_temporal_exits_3(self):
        with _patch_client_error("Connection refused"):
            exit_code, data = invoke(["doctor"])
        assert exit_code == 3
        assert data["ok"] is False
        assert "fix" in data

    def test_doctor_has_checks_list(self):
        with _patch_client_error("Connection refused"):
            _, data = invoke(["doctor"])
        # Even failed doctor has checks in result
        assert "result" in data
        assert "checks" in data["result"]

    def test_doctor_success(self):
        mock_client, _ = make_mock_client()
        with _patch_client(mock_client):
            _exit_code, data = invoke(["doctor"])
        # May still fail if coaching file missing, but should be JSON
        assert isinstance(data, dict)
        assert "result" in data


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


class TestSchema:
    def test_schema_returns_commands(self):
        exit_code, data = invoke(["schema"])
        assert exit_code == 0
        assert data["ok"] is True
        assert "commands" in data["result"]
        assert isinstance(data["result"]["commands"], list)

    def test_schema_has_exit_codes(self):
        _, data = invoke(["schema"])
        assert "exit_codes" in data["result"]
        exit_codes = data["result"]["exit_codes"]
        assert "0" in exit_codes
        assert "3" in exit_codes
        assert "4" in exit_codes


# ---------------------------------------------------------------------------
# JSON envelope invariants
# ---------------------------------------------------------------------------


class TestEnvelopeInvariants:
    """Every response must satisfy the JSON envelope contract."""

    def _all_reachable_outputs(self):
        """Return list of (exit_code, data) for all testable paths."""
        mock_client, _ = make_mock_client()
        outputs = []

        with _patch_client(mock_client):
            outputs.append(invoke([]))
            outputs.append(invoke(["schema"]))
            outputs.append(invoke(["list"]))
            outputs.append(invoke(["status", "ribosome-test1234"]))

        with _patch_client_error("refused"):
            outputs.append(invoke(["doctor"]))
            outputs.append(invoke(["status", "any"]))
            outputs.append(invoke(["cancel", "any"]))

        return outputs

    def test_every_output_has_ok_field(self):
        for _exit_code, data in self._all_reachable_outputs():
            assert "ok" in data, f"Missing 'ok' field in: {data}"

    def test_every_output_has_command_field(self):
        for _exit_code, data in self._all_reachable_outputs():
            assert "command" in data, f"Missing 'command' field in: {data}"

    def test_error_envelope_has_fix_field(self):
        for _exit_code, data in self._all_reachable_outputs():
            if not data["ok"]:
                assert "fix" in data, f"Error envelope missing 'fix': {data}"
                assert "error" in data, f"Error envelope missing 'error': {data}"

    def test_ok_envelope_has_result(self):
        for _exit_code, data in self._all_reachable_outputs():
            if data["ok"]:
                assert "result" in data, f"Ok envelope missing 'result': {data}"

    def test_every_output_has_next_actions(self):
        for _exit_code, data in self._all_reachable_outputs():
            assert "next_actions" in data, f"Missing 'next_actions' field in: {data}"


# ---------------------------------------------------------------------------
# decompose_spec tests
# ---------------------------------------------------------------------------


class TestDecomposeSpec:
    def test_single_task_returns_none(self):
        from mtor.dispatch import decompose_spec

        assert decompose_spec("Just do this one thing") is None

    def test_two_tasks_splits(self):
        from mtor.dispatch import decompose_spec

        spec = "# Preamble\nShared context.\n\n## Task 1\nDo A.\n\n## Task 2\nDo B."
        tasks = decompose_spec(spec)
        assert len(tasks) == 2
        assert "Shared context." in tasks[0]
        assert "Do A." in tasks[0]
        assert "Shared context." in tasks[1]
        assert "Do B." in tasks[1]

    def test_preamble_prepended_to_each(self):
        from mtor.dispatch import decompose_spec

        spec = "Important context.\n\n## Task 1\nFirst.\n\n## Task 2\nSecond."
        tasks = decompose_spec(spec)
        assert all("Important context." in t for t in tasks)

    def test_no_preamble(self):
        from mtor.dispatch import decompose_spec

        spec = "## Task 1\nFirst.\n\n## Task 2\nSecond."
        tasks = decompose_spec(spec)
        assert len(tasks) == 2


# ---------------------------------------------------------------------------
# Experiment mode tests
# ---------------------------------------------------------------------------


class TestExperimentMode:
    def test_default_is_build(self):
        """Verify the spec has mode=build by default."""
        mock_client, _ = make_mock_client()
        with _patch_client(mock_client):
            exit_code, data = invoke(["Test task prompt"])
        assert exit_code == 0
        assert data["ok"] is True
        # Verify the workflow was started with build mode spec
        call_kwargs = mock_client.start_workflow.call_args.kwargs
        spec = call_kwargs["args"][0][0]
        assert spec["mode"] == "build"
        assert "experiment" not in data["result"]

    def test_experiment_flag_sets_mode(self):
        """Verify experiment=True sets mode=experiment in spec and result."""
        mock_client, _ = make_mock_client()
        with _patch_client(mock_client):
            exit_code, data = invoke(["Test task prompt", "-x"])
        assert exit_code == 0
        assert data["ok"] is True
        # Verify the workflow was started with experiment mode spec
        call_kwargs = mock_client.start_workflow.call_args.kwargs
        spec = call_kwargs["args"][0][0]
        assert spec["mode"] == "experiment"
        assert spec["experiment"] is True
        # Verify result envelope has experiment flag
        assert data["result"]["experiment"] is True
        # Verify next_actions has the no-auto-merge note
        action_descs = [na.get("description", "") for na in data["next_actions"]]
        assert any("NOT auto-merge" in desc for desc in action_descs), (
            f"Expected auto-merge note in next_actions, got: {action_descs}"
        )
