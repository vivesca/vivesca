"""Tests for sortase executor."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pathlib import Path

from metabolon.sortase.executor import (
    ExecutionAttempt,
    FallbackStep,
    TaskExecutionResult,
    _clean_env,
    _compute_adaptive_timeout,
    _prepend_coaching,
    _tool_chain,
    classify_failure,
    estimate_cost,
    summarize_cost_estimates,
)


def test_prepend_coaching_skips_gemini():
    """Coaching notes should NOT be prepended for gemini."""
    result = _prepend_coaching("do something", "gemini")
    assert result == "do something"


def test_prepend_coaching_applies_to_droid(tmp_path):
    """Coaching notes should be prepended for droid."""
    notes = tmp_path / "coaching.md"
    notes.write_text("---\nname: test\n---\n\n## Notes\nDon't hallucinate imports.")
    with patch("metabolon.sortase.executor.COACHING_NOTES", notes):
        result = _prepend_coaching("do something", "droid")
    assert "Don't hallucinate imports" in result
    assert "do something" in result


def test_prepend_coaching_strips_frontmatter(tmp_path):
    """YAML frontmatter should be stripped from coaching notes."""
    notes = tmp_path / "coaching.md"
    notes.write_text("---\nname: test\ntype: feedback\n---\n\nActual content here.")
    with patch("metabolon.sortase.executor.COACHING_NOTES", notes):
        result = _prepend_coaching("task", "goose")
    assert "name: test" not in result
    assert "Actual content here" in result


def test_tool_chain_starts_with_initial():
    chain = _tool_chain("droid")
    assert chain[0] == "droid"
    assert "gemini" in chain
    assert len(chain) == len(set(chain))  # no duplicates


def test_tool_chain_deduplicates():
    chain = _tool_chain("gemini")
    assert chain[0] == "gemini"
    assert chain.count("gemini") == 1


def test_classify_failure_success():
    assert classify_failure(0, "all good") is None


def test_classify_failure_quota():
    assert classify_failure(1, "Error 429 too many requests") == "quota"


def test_classify_failure_auth():
    assert classify_failure(1, "身份验证失败") == "auth"


def test_classify_failure_sandbox():
    assert classify_failure(1, "Operation not permitted") == "sandbox"


def test_classify_failure_generic():
    assert classify_failure(1, "something went wrong") == "process-error"


def test_clean_env_removes_claudecode():
    import os
    with patch.dict(os.environ, {"CLAUDECODE": "1", "PATH": "/usr/bin"}):
        env = _clean_env("gemini")
    assert "CLAUDECODE" not in env


def test_clean_env_goose_passes_through():
    """Translocon handles env vars internally — sortase passes through for goose and droid."""
    import os
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "gk", "GEMINI_API_KEY": "gem"}):
        env = _clean_env("goose")
    assert "GOOGLE_API_KEY" in env


def test_goose_tool_command_uses_translocon():
    from pathlib import Path
    from metabolon.sortase.executor import TOOL_COMMANDS
    cmd = TOOL_COMMANDS["goose"](Path("/tmp/test"), "do something")
    assert cmd[0] == "translocon"
    assert "--backend" in cmd
    assert "goose" in cmd
    assert "--build" in cmd


def test_droid_tool_command_uses_translocon():
    from pathlib import Path
    from metabolon.sortase.executor import TOOL_COMMANDS
    cmd = TOOL_COMMANDS["droid"](Path("/tmp/test"), "do something")
    assert cmd[0] == "translocon"
    assert "--backend" in cmd
    assert "droid" in cmd


def test_clean_env_cc_glm_sets_zhipu():
    import os
    with patch.dict(os.environ, {"ZHIPU_API_KEY": "test-key"}):
        env = _clean_env("cc-glm")
    assert env["ANTHROPIC_API_KEY"] == "test-key"
    assert "bigmodel.cn" in env["ANTHROPIC_BASE_URL"]


def test_execution_attempt_dataclass():
    a = ExecutionAttempt(tool="droid", exit_code=0, duration_s=1.5, output="ok")
    assert a.failure_reason is None
    assert a.duration_s == 1.5


def test_task_execution_result_dataclass():
    r = TaskExecutionResult(
        task_name="test", tool="droid", prompt_file=None, success=True
    )
    assert r.fallbacks == []
    assert r.output == ""


# ── cost estimation ──────────────────────────────────────────


def test_estimate_cost_flat_rate_goose():
    assert estimate_cost("goose", "some prompt", "some output") == "$0.00 (flat-rate)"


def test_estimate_cost_flat_rate_droid():
    assert estimate_cost("droid", "prompt" * 100, "output" * 100) == "$0.00 (flat-rate)"


def test_estimate_cost_flat_rate_cc_glm():
    assert estimate_cost("cc-glm", "prompt", "output") == "$0.00 (flat-rate)"


def test_estimate_cost_crush_unknown_pricing():
    assert estimate_cost("crush", "prompt", "output") == "$0.00 (unknown pricing)"


def test_estimate_cost_gemini():
    """Gemini 3 Pro pricing: input $2.00/M, output $12.00/M tokens."""
    prompt = "a" * 4000   # ~1000 input tokens
    output = "b" * 4000   # ~1000 output tokens
    cost = estimate_cost("gemini", prompt, output)
    # input: 1000 * 2.0 / 1e6 = $0.00200
    # output: 1000 * 12.0 / 1e6 = $0.01200
    # total: $0.01400
    assert cost == "$0.0140"


def test_estimate_cost_gemini_small():
    """Very short prompt and output still produce a numeric estimate."""
    cost = estimate_cost("gemini", "hi", "ok")
    assert cost.startswith("$")
    assert "(flat-rate)" not in cost
    assert "(unknown" not in cost


def test_estimate_cost_codex():
    """GPT-5.3-Codex pricing: input $1.75/M, output $14.00/M tokens."""
    cost = estimate_cost("codex", "prompt" * 500, "output" * 500)
    assert cost == "$0.0118"


def test_estimate_cost_unknown_tool():
    """Unknown tool gets unknown-pricing marker."""
    cost = estimate_cost("nonexistent-tool", "prompt", "output")
    assert cost == "$0.00 (unknown pricing)"


def test_execution_attempt_has_cost_estimate():
    a = ExecutionAttempt(tool="goose", exit_code=0, duration_s=1.0, output="ok")
    assert a.cost_estimate == ""


def test_execution_attempt_custom_cost_estimate():
    a = ExecutionAttempt(
        tool="gemini", exit_code=0, duration_s=2.0, output="ok",
        cost_estimate="$0.0113",
    )
    assert a.cost_estimate == "$0.0113"


def test_task_execution_result_has_cost_estimate():
    r = TaskExecutionResult(
        task_name="test", tool="droid", prompt_file=None, success=True,
        cost_estimate="$0.00 (flat-rate)",
    )
    assert r.cost_estimate == "$0.00 (flat-rate)"


def test_task_execution_result_default_cost_estimate():
    r = TaskExecutionResult(
        task_name="test", tool="droid", prompt_file=None, success=True,
    )
    assert r.cost_estimate == ""


def test_summarize_cost_estimates_flat_rate_only():
    summary = summarize_cost_estimates(["$0.00 (flat-rate)", "$0.00 (flat-rate)"])
    assert summary == "$0.00 (flat-rate)"


def test_summarize_cost_estimates_billable_and_flat_rate():
    summary = summarize_cost_estimates(["$0.0140", "$0.0158", "$0.00 (flat-rate)"])
    assert summary == "$0.0298 (+ flat-rate backends)"


def test_summarize_cost_estimates_unknown_only():
    summary = summarize_cost_estimates(["$0.00 (unknown pricing)"])
    assert summary == "N/A (unknown pricing)"


def test_summarize_cost_estimates_billable_and_unknown():
    summary = summarize_cost_estimates(["$0.0140", "$0.00 (unknown pricing)"])
    assert summary == "$0.0140 (+ unknown-priced backends)"


# ── adaptive timeout ──────────────────────────────────────────


def test_adaptive_timeout_read_heavy_doubles():
    """Spec mentioning 'read' should double the timeout."""
    assert _compute_adaptive_timeout("Read the file config.yaml and summarize it", 600) == 1200


def test_adaptive_timeout_source_reference_doubles():
    """Spec referencing source files should double the timeout."""
    assert _compute_adaptive_timeout("Analyze src/main.py for bugs", 600) == 1200


def test_adaptive_timeout_file_path_doubles():
    """Spec containing a file path reference should double the timeout."""
    assert _compute_adaptive_timeout("Look at the code in lib/parser.py and fix the bug", 600) == 1200


def test_adaptive_timeout_exact_one_halves():
    """Spec saying 'EXACTLY 1 tool call' should halve the timeout."""
    assert _compute_adaptive_timeout("Run this bash command EXACTLY 1 tool call", 600) == 300


def test_adaptive_timeout_exactly_one_case_insensitive():
    """'exactly 1 tool call' is case-insensitive."""
    assert _compute_adaptive_timeout("Do X exactly 1 tool call", 600) == 300


def test_adaptive_timeout_no_adjustment():
    """Spec with no read/file/exactly-1 signals returns base timeout unchanged."""
    assert _compute_adaptive_timeout("Refactor the authentication module", 600) == 600


def test_adaptive_timeout_read_takes_priority_over_exact_one():
    """Both read-heavy and exactly-1 present: read doubles (takes precedence)."""
    spec = "Read config.yaml and respond with EXACTLY 1 tool call"
    assert _compute_adaptive_timeout(spec, 600) == 1200


def test_adaptive_timeout_custom_base():
    """Works with non-default base timeouts."""
    assert _compute_adaptive_timeout("Read foo.py", 300) == 600
    assert _compute_adaptive_timeout("EXACTLY 1 tool call to do X", 400) == 200


# ── fallback_chain ──────────────────────────────────────────


def test_fallback_step_to_dict_succeeded():
    """Successful step: no failure_reason key."""
    step = FallbackStep(tool="goose", succeeded=True)
    assert step.to_dict() == {"tool": "goose", "succeeded": True}


def test_fallback_step_to_dict_failed():
    """Failed step: includes failure_reason."""
    step = FallbackStep(tool="goose", succeeded=False, failure_reason="quota")
    d = step.to_dict()
    assert d == {"tool": "goose", "succeeded": False, "failure_reason": "quota"}


def test_fallback_step_to_dict_failed_no_reason():
    """Failed step without explicit reason: failure_reason is None, so omitted."""
    step = FallbackStep(tool="codex", succeeded=False, failure_reason=None)
    assert step.to_dict() == {"tool": "codex", "succeeded": False}


def test_task_execution_result_default_fallback_chain():
    """Default fallback_chain is empty list."""
    result = TaskExecutionResult(
        task_name="test", tool="droid", prompt_file=None, success=True,
    )
    assert result.fallback_chain == []


def test_task_execution_result_with_fallback_chain():
    """fallback_chain populated with multiple steps."""
    chain = [
        FallbackStep(tool="goose", succeeded=False, failure_reason="quota"),
        FallbackStep(tool="droid", succeeded=False, failure_reason="process-error"),
        FallbackStep(tool="gemini", succeeded=True),
    ]
    result = TaskExecutionResult(
        task_name="task-1", tool="gemini", prompt_file=None,
        success=True, fallback_chain=chain,
        fallbacks=["droid", "gemini"],
    )
    assert len(result.fallback_chain) == 3
    assert result.fallback_chain[0].tool == "goose"
    assert result.fallback_chain[0].succeeded is False
    assert result.fallback_chain[1].failure_reason == "process-error"
    assert result.fallback_chain[2].succeeded is True
    assert result.fallback_chain[2].failure_reason is None


@pytest.mark.asyncio
async def test_execute_task_populates_fallback_chain_on_success():
    """When first backend succeeds, chain has one successful step."""
    from metabolon.sortase.decompose import TaskSpec
    from metabolon.sortase.executor import execute_task

    task = TaskSpec(name="t1", description="d", spec="do work", files=[], signal="default", prerequisite=None, temp_file=None)
    attempt = ExecutionAttempt(tool="goose", exit_code=0, duration_s=1.0, output="ok")

    with patch("metabolon.sortase.executor._run_command", new_callable=AsyncMock, return_value=attempt), \
         patch("metabolon.sortase.executor.register_running"), \
         patch("metabolon.sortase.executor.unregister_running"), \
         patch("metabolon.sortase.executor._emit_completion_signal"), \
         patch("metabolon.sortase.executor._analyze_for_coaching"):
        result = await execute_task(task, Path("/tmp/test"), "goose")

    assert result.success is True
    assert len(result.fallback_chain) == 1
    assert result.fallback_chain[0] == FallbackStep(tool="goose", succeeded=True, failure_reason=None)
    assert result.fallbacks == []


@pytest.mark.asyncio
async def test_execute_task_populates_fallback_chain_on_fallback():
    """When first backend fails and second succeeds, chain records both."""
    from metabolon.sortase.decompose import TaskSpec
    from metabolon.sortase.executor import execute_task

    task = TaskSpec(name="t2", description="d", spec="do work", files=[], signal="default", prerequisite=None, temp_file=None)
    fail_attempt = ExecutionAttempt(tool="goose", exit_code=1, duration_s=2.0, output="429 error", failure_reason="quota")
    ok_attempt = ExecutionAttempt(tool="droid", exit_code=0, duration_s=3.0, output="done")

    with patch("metabolon.sortase.executor._run_command", new_callable=AsyncMock, side_effect=[fail_attempt, ok_attempt]), \
         patch("metabolon.sortase.executor.register_running"), \
         patch("metabolon.sortase.executor.unregister_running"), \
         patch("metabolon.sortase.executor._emit_completion_signal"), \
         patch("metabolon.sortase.executor._analyze_for_coaching"):
        result = await execute_task(task, Path("/tmp/test"), "goose")

    assert result.success is True
    assert result.tool == "droid"
    assert result.fallbacks == ["droid"]
    assert len(result.fallback_chain) == 2
    assert result.fallback_chain[0] == FallbackStep(tool="goose", succeeded=False, failure_reason="quota")
    assert result.fallback_chain[1] == FallbackStep(tool="droid", succeeded=True, failure_reason=None)


@pytest.mark.asyncio
async def test_execute_task_fallback_chain_all_fail():
    """When all backends fail, chain records every attempt with reasons."""
    from metabolon.sortase.decompose import TaskSpec
    from metabolon.sortase.executor import execute_task, FALLBACK_ORDER

    task = TaskSpec(name="t3", description="d", spec="do work", files=[], signal="default", prerequisite=None, temp_file=None)
    fail1 = ExecutionAttempt(tool="goose", exit_code=1, duration_s=1.0, output="429", failure_reason="quota")
    fail2 = ExecutionAttempt(tool="droid", exit_code=1, duration_s=1.0, output="segfault", failure_reason="process-error")
    fail3 = ExecutionAttempt(tool="gemini", exit_code=1, duration_s=1.0, output="auth fail", failure_reason="auth")
    fail4 = ExecutionAttempt(tool="codex", exit_code=1, duration_s=1.0, output="err", failure_reason="process-error")

    with patch("metabolon.sortase.executor._run_command", new_callable=AsyncMock, side_effect=[fail1, fail2, fail3, fail4]), \
         patch("metabolon.sortase.executor.register_running"), \
         patch("metabolon.sortase.executor.unregister_running"), \
         patch("metabolon.sortase.executor._emit_completion_signal"), \
         patch("metabolon.sortase.executor._analyze_for_coaching"):
        result = await execute_task(task, Path("/tmp/test"), "goose")

    assert result.success is False
    assert len(result.fallback_chain) == 4
    assert result.fallback_chain[0].tool == "goose"
    assert result.fallback_chain[0].failure_reason == "quota"
    assert result.fallback_chain[2].tool == "gemini"
    assert result.fallback_chain[2].failure_reason == "auth"
