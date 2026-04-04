from __future__ import annotations

"""Tests for metabolon.sortase.executor module."""


import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from metabolon.sortase.decompose import TaskSpec
from metabolon.sortase.executor import (
    FALLBACK_ORDER,
    ExecutionAttempt,
    FallbackStep,
    TaskExecutionResult,
    _clean_env,
    _compute_adaptive_timeout,
    _legacy_tombstone,
    _read_status_entries,
    _status_path,
    _tool_chain,
    _validate_backend,
    _write_status_entries,
    classify_failure,
    estimate_cost,
    execute_task,
    execute_tasks,
    register_running,
    summarize_cost_estimates,
    unregister_running,
)


class TestComputeAdaptiveTimeout:
    """Tests for _compute_adaptive_timeout function."""

    def test_base_timeout_returned_for_simple_spec(self):
        """Simple specs without special patterns return base timeout."""
        spec = "Create a simple function"
        assert _compute_adaptive_timeout(spec, 100) == 100

    def test_read_pattern_doubles_timeout(self):
        """Specs mentioning 'read' get doubled timeout."""
        spec = "Read the configuration file and process it"
        assert _compute_adaptive_timeout(spec, 100) == 200

    def test_source_file_pattern_doubles_timeout(self):
        """Specs referencing source files get doubled timeout."""
        spec = "Process config.yaml and output results"
        assert _compute_adaptive_timeout(spec, 100) == 200

    def test_exactly_one_tool_call_halves_timeout(self):
        """Specs with 'exactly 1 tool call' get halved timeout."""
        spec = "Make exactly 1 tool call to fetch data"
        assert _compute_adaptive_timeout(spec, 100) == 50

    def test_read_takes_priority_over_exact_one(self):
        """Read-heavy pattern takes priority over exact-one pattern."""
        spec = "Read the file and make exactly 1 tool call"
        assert _compute_adaptive_timeout(spec, 100) == 200

    def test_case_insensitive_read_pattern(self):
        """Read pattern matching is case insensitive."""
        spec = "READ the file"
        assert _compute_adaptive_timeout(spec, 100) == 200


class TestClassifyFailure:
    """Tests for classify_failure function."""

    def test_exit_code_zero_returns_none(self):
        """Exit code 0 returns None (no failure)."""
        assert classify_failure(0, "any output") is None

    def test_quota_429_detected(self):
        """429 status code detected as quota failure."""
        assert classify_failure(1, "Error: 429 Too Many Requests") == "quota"

    def test_quota_keyword_detected(self):
        """Quota keyword detected."""
        assert classify_failure(1, "quota exceeded") == "quota"

    def test_auth_chinese_detected(self):
        """Chinese authentication error detected."""
        assert classify_failure(1, "身份验证失败") == "auth"

    def test_sandbox_detected(self):
        """Sandbox permission error detected."""
        assert classify_failure(1, "operation not permitted") == "sandbox"

    def test_generic_process_error(self):
        """Generic errors classified as process-error."""
        assert classify_failure(1, "something went wrong") == "process-error"

    def test_case_insensitive_matching(self):
        """Pattern matching is case insensitive."""
        assert classify_failure(1, "QUOTA EXCEEDED") == "quota"
        assert classify_failure(1, "OPERATION NOT PERMITTED") == "sandbox"


class TestEstimateCost:
    """Tests for estimate_cost function."""

    def test_flat_rate_tools_return_zero(self):
        """Flat-rate tools return $0.00 (flat-rate)."""
        for tool in ["goose", "droid", "golem"]:
            result = estimate_cost(tool, "prompt" * 100, "output" * 100)
            assert result == "$0.00 (flat-rate)"

    def test_gemini_cost_estimation(self):
        """Gemini cost estimation based on token approximation."""
        prompt = "x" * 4000  # ~1000 tokens
        output = "y" * 400  # ~100 tokens
        result = estimate_cost("gemini", prompt, output)
        assert result.startswith("$")
        # 1000 input tokens * $2/M = $0.002
        # 100 output tokens * $12/M = $0.0012
        # Total ≈ $0.0032

    def test_codex_cost_estimation(self):
        """Codex cost estimation based on token approximation."""
        prompt = "x" * 4000
        output = "y" * 400
        result = estimate_cost("codex", prompt, output)
        assert result.startswith("$")

    def test_unknown_tool_returns_zero(self):
        """Unknown tools return $0.00 (unknown pricing)."""
        result = estimate_cost("unknown_tool", "prompt", "output")
        assert result == "$0.00 (unknown pricing)"


class TestSummarizeCostEstimates:
    """Tests for summarize_cost_estimates function."""

    def test_empty_list_returns_na(self):
        """Empty list returns N/A."""
        assert summarize_cost_estimates([]) == "N/A"

    def test_all_flat_rate(self):
        """All flat-rate costs return flat-rate summary."""
        result = summarize_cost_estimates(["$0.00 (flat-rate)", "$0.00 (flat-rate)"])
        assert result == "$0.00 (flat-rate)"

    def test_mixed_costs(self):
        """Mixed costs are summed with notes."""
        result = summarize_cost_estimates(
            [
                "$0.0050",
                "$0.00 (flat-rate)",
            ]
        )
        assert "$0.0050" in result
        assert "flat-rate" in result

    def test_multiple_dollar_amounts_summed(self):
        """Multiple dollar amounts are summed correctly."""
        result = summarize_cost_estimates(["$0.0100", "$0.0200", "$0.0050"])
        assert result == "$0.0350"

    def test_unknown_pricing_noted(self):
        """Unknown pricing is noted in summary."""
        result = summarize_cost_estimates(["$0.00 (unknown pricing)"])
        assert "unknown pricing" in result


class TestToolChain:
    """Tests for _tool_chain function."""

    def test_initial_tool_first(self):
        """Initial tool is first in chain."""
        chain = _tool_chain("gemini")
        assert chain[0] == "gemini"

    def test_all_tools_included(self):
        """All fallback tools are included (initial tool + fallbacks, no duplicates)."""
        chain = _tool_chain("gemini")
        # The chain contains the initial tool plus all other fallback tools not already included
        # Since gemini is in FALLBACK_ORDER, the result is unique tools
        assert len(chain) == len(set(FALLBACK_ORDER) | {"gemini"})

    def test_no_duplicates(self):
        """No duplicates in tool chain."""
        chain = _tool_chain("gemini")
        assert len(chain) == len(set(chain))

    def test_fallback_order_preserved(self):
        """Fallback order is preserved after initial tool."""
        chain = _tool_chain("codex")
        # codex should be first
        assert chain[0] == "codex"
        # goose, droid, gemini should follow in FALLBACK_ORDER
        for tool in FALLBACK_ORDER:
            if tool != "codex":
                assert tool in chain


class TestCleanEnv:
    """Tests for _clean_env function."""

    def test_removes_claudecode(self):
        """CLAUDECODE environment variable is removed."""
        with patch.dict(os.environ, {"CLAUDECODE": "test"}, clear=False):
            env = _clean_env("gemini")
            assert "CLAUDECODE" not in env

    def test_golem_sets_anthropic_vars(self):
        """Golem tool sets Anthropic environment variables."""
        with patch.dict(os.environ, {"ZHIPU_API_KEY": "test-key"}, clear=False):
            env = _clean_env("golem")
            assert env.get("ANTHROPIC_AUTH_TOKEN") == "test-key"
            assert env.get("ANTHROPIC_BASE_URL") == "https://open.bigmodel.cn/api/anthropic"


class TestFallbackStep:
    """Tests for FallbackStep dataclass."""

    def test_to_dict_basic(self):
        """Basic to_dict conversion."""
        step = FallbackStep(tool="gemini", succeeded=True)
        result = step.to_dict()
        assert result == {"tool": "gemini", "succeeded": True}

    def test_to_dict_with_failure_reason(self):
        """to_dict includes failure_reason when present."""
        step = FallbackStep(tool="gemini", succeeded=False, failure_reason="quota")
        result = step.to_dict()
        assert result == {
            "tool": "gemini",
            "succeeded": False,
            "failure_reason": "quota",
        }


class TestExecutionAttempt:
    """Tests for ExecutionAttempt dataclass."""

    def test_frozen_dataclass(self):
        """ExecutionAttempt is immutable."""
        attempt = ExecutionAttempt(
            tool="gemini",
            exit_code=0,
            duration_s=1.5,
            output="success",
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            attempt.exit_code = 1


class TestTaskExecutionResult:
    """Tests for TaskExecutionResult dataclass."""

    def test_default_values(self):
        """Default values for optional fields."""
        result = TaskExecutionResult(
            task_name="test",
            tool="gemini",
            prompt_file=None,
            success=True,
        )
        assert result.attempts == []
        assert result.output == ""
        assert result.fallbacks == []
        assert result.fallback_chain == []
        assert result.cost_estimate == ""


class TestStatusManagement:
    """Tests for status file management functions."""

    def test_legacy_tombstone_format(self):
        """Legacy tombstone format is correct."""
        assert _legacy_tombstone("my-task") == "__removed__:my-task"

    def test_status_path_default(self):
        """Default status path is correct."""
        with patch.dict(os.environ, {}, clear=True):
            path = _status_path()
            assert "sortase" in str(path)
            assert path.name == "status.json"

    def test_status_path_override(self):
        """Status path can be overridden via environment."""
        with patch.dict(os.environ, {"OPIFEX_STATUS_PATH": "/custom/status.json"}, clear=False):
            path = _status_path()
            assert str(path) == "/custom/status.json"

    def test_read_write_status_entries(self, tmp_path):
        """Read and write status entries round-trip."""
        status_file = tmp_path / "status.json"
        entries = [
            {"task_name": "task1", "tool": "gemini"},
            {"task_name": "task2", "tool": "codex"},
        ]

        with patch("metabolon.sortase.executor._status_path", return_value=status_file):
            _write_status_entries(entries)
            result = _read_status_entries()

        assert result == entries

    def test_read_status_missing_file(self, tmp_path):
        """Reading missing status file returns empty list."""
        status_file = tmp_path / "missing.json"

        with patch("metabolon.sortase.executor._status_path", return_value=status_file):
            result = _read_status_entries()

        assert result == []

    def test_read_status_invalid_json(self, tmp_path):
        """Reading invalid JSON returns empty list."""
        status_file = tmp_path / "invalid.json"
        status_file.write_text("not valid json")

        with patch("metabolon.sortase.executor._status_path", return_value=status_file):
            result = _read_status_entries()

        assert result == []

    def test_register_unregister_running(self, tmp_path):
        """Register and unregister running tasks."""
        status_file = tmp_path / "status.json"

        with patch("metabolon.sortase.executor._status_path", return_value=status_file):
            register_running("task1", "gemini", Path("/project"))
            entries = _read_status_entries()
            assert len(entries) == 1
            assert entries[0]["task_name"] == "task1"
            assert entries[0]["tool"] == "gemini"

            unregister_running("task1", Path("/project"))
            entries = _read_status_entries()
            assert len(entries) == 0


class TestValidateBackend:
    """Tests for _validate_backend function."""

    def test_valid_backend_passes(self):
        """Valid backend passes validation."""
        with patch("shutil.which", return_value="/usr/bin/gemini"):
            # Should not raise
            _validate_backend("gemini", Path("/project"), "prompt")

    def test_invalid_backend_raises_key_error(self):
        """Invalid backend raises KeyError (tool not in TOOL_COMMANDS)."""
        with pytest.raises(KeyError):
            _validate_backend("invalid_tool", Path("/project"), "prompt")

    def test_missing_binary_raises_filenotfound(self):
        """Missing binary raises FileNotFoundError."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(FileNotFoundError) as exc_info:
                _validate_backend("gemini", Path("/project"), "prompt")
            assert "gemini" in str(exc_info.value)


class TestExecuteTask:
    """Tests for execute_task async function."""

    @pytest.mark.asyncio
    async def test_execute_task_success(self, tmp_path):
        """Successful task execution returns correct result."""
        task = TaskSpec(
            name="test-task",
            description="Test task",
            spec="Do something",
            files=[],
        )

        mock_attempt = ExecutionAttempt(
            tool="gemini",
            exit_code=0,
            duration_s=1.0,
            output="Success",
            failure_reason=None,
            cost_estimate="$0.001",
        )

        status_file = tmp_path / "status.json"

        with patch("metabolon.sortase.executor._status_path", return_value=status_file):
            with patch(
                "metabolon.sortase.executor._run_command",
                new_callable=AsyncMock,
                return_value=mock_attempt,
            ):
                with patch("metabolon.sortase.executor._validate_backend"):
                    result = await execute_task(
                        task,
                        tmp_path,
                        "gemini",
                        timeout_sec=60,
                    )

        assert result.success is True
        assert result.task_name == "test-task"
        assert result.tool == "gemini"

    @pytest.mark.asyncio
    async def test_execute_task_with_fallback(self, tmp_path):
        """Task execution with fallback to second tool."""
        task = TaskSpec(
            name="test-task",
            description="Test task",
            spec="Do something",
            files=[],
        )

        # Use "process-error" instead of "quota" to avoid the quota retry logic
        fail_attempt = ExecutionAttempt(
            tool="gemini",
            exit_code=1,
            duration_s=1.0,
            output="Failed",
            failure_reason="process-error",
            cost_estimate="$0.00",
        )

        success_attempt = ExecutionAttempt(
            tool="goose",
            exit_code=0,
            duration_s=2.0,
            output="Success",
            failure_reason=None,
            cost_estimate="$0.00 (flat-rate)",
        )

        status_file = tmp_path / "status.json"

        with patch("metabolon.sortase.executor._status_path", return_value=status_file):
            with patch(
                "metabolon.sortase.executor._run_command",
                new_callable=AsyncMock,
                side_effect=[fail_attempt, success_attempt],
            ):
                with patch("metabolon.sortase.executor._validate_backend"):
                    result = await execute_task(
                        task,
                        tmp_path,
                        "gemini",
                        timeout_sec=60,
                    )

        assert result.success is True
        assert result.tool == "goose"
        assert "goose" in result.fallbacks


class TestExecuteTasks:
    """Tests for execute_tasks async function."""

    @pytest.mark.asyncio
    async def test_execute_tasks_serial(self, tmp_path):
        """Serial execution processes tasks one at a time."""
        tasks = [
            TaskSpec(name="task1", description="Task 1", spec="Do 1", files=[]),
            TaskSpec(name="task2", description="Task 2", spec="Do 2", files=[]),
        ]

        mock_attempt = ExecutionAttempt(
            tool="gemini",
            exit_code=0,
            duration_s=1.0,
            output="Success",
            failure_reason=None,
            cost_estimate="$0.001",
        )

        tool_by_task = {"task1": "gemini", "task2": "gemini"}
        status_file = tmp_path / "status.json"

        with patch("metabolon.sortase.executor._status_path", return_value=status_file):
            with patch(
                "metabolon.sortase.executor._run_command",
                new_callable=AsyncMock,
                return_value=mock_attempt,
            ):
                with patch("metabolon.sortase.executor._validate_backend"):
                    results = await execute_tasks(
                        tasks,
                        tmp_path,
                        tool_by_task,
                        serial=True,
                        timeout_sec=60,
                    )

        assert len(results) == 2
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_execute_tasks_parallel(self, tmp_path):
        """Parallel execution processes tasks concurrently."""
        tasks = [
            TaskSpec(name="task1", description="Task 1", spec="Do 1", files=[]),
            TaskSpec(name="task2", description="Task 2", spec="Do 2", files=[]),
        ]

        mock_attempt = ExecutionAttempt(
            tool="gemini",
            exit_code=0,
            duration_s=1.0,
            output="Success",
            failure_reason=None,
            cost_estimate="$0.001",
        )

        tool_by_task = {"task1": "gemini", "task2": "gemini"}
        status_file = tmp_path / "status.json"

        with patch("metabolon.sortase.executor._status_path", return_value=status_file):
            with patch(
                "metabolon.sortase.executor._run_command",
                new_callable=AsyncMock,
                return_value=mock_attempt,
            ):
                with patch("metabolon.sortase.executor._validate_backend"):
                    with patch("metabolon.sortase.executor._is_git_repo", return_value=False):
                        results = await execute_tasks(
                            tasks,
                            tmp_path,
                            tool_by_task,
                            serial=False,
                            timeout_sec=60,
                        )

        assert len(results) == 2
        assert all(r.success for r in results)
