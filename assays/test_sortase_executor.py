"""Tests for sortase executor."""
from __future__ import annotations

from unittest.mock import patch

from metabolon.sortase.executor import (
    ExecutionAttempt,
    TaskExecutionResult,
    _clean_env,
    _compute_adaptive_timeout,
    _prepend_coaching,
    _tool_chain,
    classify_failure,
    estimate_cost,
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


def test_estimate_cost_flat_rate_crush():
    assert estimate_cost("crush", "prompt", "output") == "$0.00 (flat-rate)"


def test_estimate_cost_gemini():
    """Gemini pricing: input $1.25/M, output $10.00/M tokens."""
    prompt = "a" * 4000   # ~1000 input tokens
    output = "b" * 4000   # ~1000 output tokens
    cost = estimate_cost("gemini", prompt, output)
    # input: 1000 * 1.25 / 1e6 = $0.00125
    # output: 1000 * 10.0 / 1e6 = $0.01000
    # total: $0.01125 → rounds to $0.0112 (banker's rounding)
    assert cost == "$0.0112"


def test_estimate_cost_gemini_small():
    """Very short prompt and output still produce a numeric estimate."""
    cost = estimate_cost("gemini", "hi", "ok")
    assert cost.startswith("$")
    assert "(flat-rate)" not in cost
    assert "(unknown" not in cost


def test_estimate_cost_codex():
    """Codex free tier — zero cost."""
    cost = estimate_cost("codex", "prompt" * 500, "output" * 500)
    assert cost == "$0.0000"


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
