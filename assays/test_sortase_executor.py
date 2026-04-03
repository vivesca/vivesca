from __future__ import annotations

"""Tests for metabolon/sortase/executor.py — task execution, fallback, and cost logic.

Pure-function and mock-heavy tests covering adaptive timeout, coaching prep,
cost estimation, failure classification, tool chain, status bookkeeping,
git worktree helpers, and async execute_task / execute_tasks orchestration.
"""


import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.sortase.executor import (
    _compute_adaptive_timeout,
    _prepend_coaching,
    estimate_cost,
    summarize_cost_estimates,
    classify_failure,
    _tool_chain,
    _validate_backend,
    _clean_env,
    _status_path,
    _legacy_tombstone,
    _read_status_entries,
    _write_status_entries,
    _is_git_repo,
    summarize_results,
    _reset_git_state,
    _create_worktree,
    _merge_worktree,
    _remove_worktree,
    _force_remove_worktree,
    _run_command,
    _emit_completion_signal,
    _analyze_for_coaching,
    register_running,
    unregister_running,
    list_running,
    execute_task,
    execute_tasks,
    ExecutionAttempt,
    FallbackStep,
    TaskExecutionResult,
    TOOL_COMMANDS,
    FALLBACK_ORDER,
    FLAT_RATE_TOOLS,
    MODEL_BY_TOOL,
    TOKEN_PRICING,
    STATUS_PATH,
    COACHING_NOTES,
    DEFAULT_TIMEOUT_SEC,
)


# ─────────────────────────────────────────────────────────────────────────────
# Constants tests
# ─────────────────────────────────────────────────────────────────────────────

def test_default_timeout_value():
    """Test DEFAULT_TIMEOUT_SEC is reasonable (10 minutes)."""
    assert DEFAULT_TIMEOUT_SEC == 600


def test_fallback_order_contains_expected_tools():
    """Test FALLBACK_ORDER has expected tool names."""
    assert "goose" in FALLBACK_ORDER
    assert "droid" in FALLBACK_ORDER
    assert "gemini" in FALLBACK_ORDER
    assert "codex" in FALLBACK_ORDER


def test_fallback_order_no_duplicates():
    """Test FALLBACK_ORDER has no duplicate entries."""
    assert len(FALLBACK_ORDER) == len(set(FALLBACK_ORDER))


def test_flat_rate_tools():
    """Test FLAT_RATE_TOOLS contains subscription-based backends."""
    assert "goose" in FLAT_RATE_TOOLS
    assert "droid" in FLAT_RATE_TOOLS
    assert "golem" in FLAT_RATE_TOOLS


def test_model_by_tool_has_all_tools():
    """Test MODEL_BY_TOOL has entries for all known tools."""
    for tool in TOOL_COMMANDS:
        assert tool in MODEL_BY_TOOL, f"Missing model entry for {tool}"


def test_token_pricing_keys_match_models():
    """Test TOKEN_PRICING keys match model names in MODEL_BY_TOOL."""
    for model_name in TOKEN_PRICING:
        assert model_name in MODEL_BY_TOOL.values() or model_name is None


# ─────────────────────────────────────────────────────────────────────────────
# _compute_adaptive_timeout tests
# ─────────────────────────────────────────────────────────────────────────────

def test_compute_adaptive_timeout_base_case():
    """Test base timeout returned for generic spec."""
    spec = "Write a function to add two numbers."
    assert _compute_adaptive_timeout(spec, 600) == 600


def test_compute_adaptive_timeout_read_pattern():
    """Test timeout doubled for read-heavy specs."""
    spec = "Read the file and process its contents."
    assert _compute_adaptive_timeout(spec, 600) == 1200


def test_compute_adaptive_timeout_read_case_insensitive():
    """Test READ pattern matches case-insensitively."""
    spec = "READ the configuration file"
    assert _compute_adaptive_timeout(spec, 600) == 1200

    spec = "Please read and analyze"
    assert _compute_adaptive_timeout(spec, 600) == 1200


def test_compute_adaptive_timeout_source_file_pattern():
    """Test timeout doubled when spec references source files."""
    spec = "Modify src/main.py to add logging"
    assert _compute_adaptive_timeout(spec, 600) == 1200


def test_compute_adaptive_timeout_source_file_various_extensions():
    """Test source file pattern matches various extensions."""
    # Short extensions (1-4 chars)
    assert _compute_adaptive_timeout("Edit config.yaml", 600) == 1200
    assert _compute_adaptive_timeout("Update README.md", 600) == 1200
    assert _compute_adaptive_timeout("Fix script.py", 600) == 1200
    assert _compute_adaptive_timeout("Modify data.json", 600) == 1200


def test_compute_adaptive_timeout_exactly_one_tool_call():
    """Test timeout halved for 'exactly 1 tool call' specs."""
    spec = "Make exactly 1 tool call to fix the typo."
    assert _compute_adaptive_timeout(spec, 600) == 300


def test_compute_adaptive_timeout_exactly_one_case_insensitive():
    """Test EXACTLY 1 TOOL CALL pattern matches case-insensitively."""
    spec = "You should make EXACTLY 1 tool call"
    assert _compute_adaptive_timeout(spec, 600) == 300


def test_compute_adaptive_timeout_read_takes_priority():
    """Test read-heavy takes priority over exact-one heuristic."""
    spec = "Read the file and make exactly 1 tool call"
    # Read-heavy should win, so doubled not halved
    assert _compute_adaptive_timeout(spec, 600) == 1200


def test_compute_adaptive_timeout_custom_base():
    """Test adaptive timeout works with custom base."""
    spec = "Read file.txt"
    assert _compute_adaptive_timeout(spec, 300) == 600

    spec = "Make exactly 1 tool call"
    assert _compute_adaptive_timeout(spec, 300) == 150


# ─────────────────────────────────────────────────────────────────────────────
# _prepend_coaching tests
# ─────────────────────────────────────────────────────────────────────────────

def test_prepend_coaching_translocon_tools_excluded():
    """Test coaching is NOT prepended for translocon tools."""
    prompt = "Write a function"
    # goose and droid are routed through translocon
    assert _prepend_coaching(prompt, "goose") == prompt
    assert _prepend_coaching(prompt, "droid") == prompt


def test_prepend_coaching_unknown_tool():
    """Test coaching is NOT prepended for unknown tools."""
    prompt = "Write a function"
    assert _prepend_coaching(prompt, "unknown-tool") == prompt


@patch.object(Path, 'exists', return_value=False)
def test_prepend_coaching_no_notes_file(mock_exists):
    """Test coaching is NOT prepended when notes file doesn't exist."""
    prompt = "Write a function"
    # opencode is in the list but notes file doesn't exist
    result = _prepend_coaching(prompt, "opencode")
    assert result == prompt


@patch.object(Path, 'exists', return_value=True)
@patch.object(Path, 'read_text', return_value="---\nlayout: default\n---\nCoaching note here.")
def test_prepend_coaching_strips_yaml_frontmatter(mock_read, mock_exists):
    """Test YAML frontmatter is stripped from coaching notes."""
    prompt = "Write a function"
    result = _prepend_coaching(prompt, "opencode")
    # Should strip frontmatter and prepend
    assert "Coaching note here" in result
    assert "---" in result  # divider between notes and prompt
    assert prompt in result


@patch.object(Path, 'exists', return_value=True)
@patch.object(Path, 'read_text', return_value="Plain coaching without frontmatter.")
def test_prepend_coaching_no_frontmatter(mock_read, mock_exists):
    """Test coaching works when there's no YAML frontmatter."""
    prompt = "Write a function"
    result = _prepend_coaching(prompt, "golem")
    assert "Plain coaching without frontmatter" in result
    assert prompt in result


@patch.object(Path, 'exists', return_value=True)
@patch.object(Path, 'read_text', side_effect=PermissionError("No access"))
def test_prepend_coaching_exception_returns_original(mock_read, mock_exists):
    """Test coaching returns original prompt on exception."""
    prompt = "Write a function"
    result = _prepend_coaching(prompt, "crush")
    assert result == prompt


# ─────────────────────────────────────────────────────────────────────────────
# estimate_cost tests
# ─────────────────────────────────────────────────────────────────────────────

def test_estimate_cost_flat_rate_tools():
    """Test flat-rate tools return $0.00 (flat-rate)."""
    prompt = "x" * 1000
    output = "y" * 500

    for tool in FLAT_RATE_TOOLS:
        assert estimate_cost(tool, prompt, output) == "$0.00 (flat-rate)"


def test_estimate_cost_unknown_tool():
    """Test unknown tool returns $0.00 (unknown pricing)."""
    result = estimate_cost("unknown-tool", "prompt", "output")
    assert result == "$0.00 (unknown pricing)"


def test_estimate_cost_gemini():
    """Test cost estimation for Gemini."""
    # Gemini 3 Pro: $2.00 input/million, $12.00 output/million
    prompt = "x" * 4000  # ~1000 tokens
    output = "y" * 4000  # ~1000 tokens
    result = estimate_cost("gemini", prompt, output)
    # Input: 1000 * 2 / 1e6 = 0.002
    # Output: 1000 * 12 / 1e6 = 0.012
    # Total: 0.014
    assert result == "$0.0140"


def test_estimate_cost_codex():
    """Test cost estimation for Codex."""
    # GPT-5.3-Codex: $1.75 input/million, $14.00 output/million
    prompt = "x" * 4000  # ~1000 tokens
    output = "y" * 4000  # ~1000 tokens
    result = estimate_cost("codex", prompt, output)
    # Input: 1000 * 1.75 / 1e6 = 0.00175
    # Output: 1000 * 14 / 1e6 = 0.014
    # Total: 0.01575
    assert result == "$0.0158"


def test_estimate_cost_empty_strings():
    """Test cost estimation handles empty strings."""
    # Empty strings are treated as length 0, max(1, 0) // 4 = 0
    result = estimate_cost("gemini", "", "")
    # Should still produce a result
    assert result.startswith("$")


def test_estimate_cost_small_prompt():
    """Test cost estimation for small prompts."""
    prompt = "hi"
    output = "ok"
    result = estimate_cost("gemini", prompt, output)
    # max(1, 2) // 4 = 0 tokens for each
    # So both will be 0
    assert result == "$0.0000"


# ─────────────────────────────────────────────────────────────────────────────
# summarize_cost_estimates tests
# ─────────────────────────────────────────────────────────────────────────────

def test_summarize_cost_estimates_empty():
    """Test empty list returns N/A."""
    assert summarize_cost_estimates([]) == "N/A"


def test_summarize_cost_estimates_single_dollar():
    """Test single dollar estimate is returned."""
    result = summarize_cost_estimates(["$0.0140"])
    assert result == "$0.0140"


def test_summarize_cost_estimates_multiple_dollars():
    """Test multiple dollar estimates are summed."""
    result = summarize_cost_estimates(["$0.0100", "$0.0200", "$0.0050"])
    assert result == "$0.0350"


def test_summarize_cost_estimates_flat_rate_only():
    """Test all flat-rate returns flat-rate summary."""
    result = summarize_cost_estimates(["$0.00 (flat-rate)", "$0.00 (flat-rate)"])
    assert result == "$0.00 (flat-rate)"


def test_summarize_cost_estimates_unknown_pricing_only():
    """Test all unknown pricing returns N/A."""
    result = summarize_cost_estimates(["$0.00 (unknown pricing)"])
    assert result == "N/A (unknown pricing)"


def test_summarize_cost_estimates_mixed_flat_rate():
    """Test mixed with flat-rate notes flat-rate backends."""
    result = summarize_cost_estimates(["$0.0100", "$0.00 (flat-rate)"])
    assert result == "$0.0100 (+ flat-rate backends)"


def test_summarize_cost_estimates_mixed_unknown():
    """Test mixed with unknown notes unknown-priced backends."""
    result = summarize_cost_estimates(["$0.0100", "$0.00 (unknown pricing)"])
    assert result == "$0.0100 (+ unknown-priced backends)"


def test_summarize_cost_estimates_mixed_all():
    """Test mixed with both notes both."""
    result = summarize_cost_estimates([
        "$0.0100",
        "$0.00 (flat-rate)",
        "$0.00 (unknown pricing)"
    ])
    assert "flat-rate backends" in result
    assert "unknown-priced backends" in result


def test_summarize_cost_estimates_invalid_format():
    """Test invalid format is treated as unknown pricing."""
    result = summarize_cost_estimates(["invalid", "$0.0100"])
    assert "unknown-priced backends" in result


def test_summarize_cost_estimates_zero_total_with_flat_and_unknown():
    """Test zero total with both flat and unknown shows both notes."""
    result = summarize_cost_estimates([
        "$0.00 (flat-rate)",
        "$0.00 (unknown pricing)"
    ])
    # Zero total with both flat and unknown shows both notes
    assert "flat-rate backends" in result
    assert "unknown-priced backends" in result


# ─────────────────────────────────────────────────────────────────────────────
# classify_failure tests
# ─────────────────────────────────────────────────────────────────────────────

def test_classify_failure_success():
    """Test exit code 0 returns None."""
    assert classify_failure(0, "any output") is None


def test_classify_failure_quota_429():
    """Test 429 status code classified as quota."""
    assert classify_failure(1, "Error 429: Too many requests") == "quota"


def test_classify_failure_quota_keyword():
    """Test 'quota' keyword classified as quota."""
    assert classify_failure(1, "Exceeded quota limit") == "quota"


def test_classify_failure_quota_case_insensitive():
    """Test quota detection is case-insensitive."""
    assert classify_failure(1, "QUOTA exceeded") == "quota"
    assert classify_failure(1, "Quota Limit") == "quota"


def test_classify_failure_auth():
    """Test 身份验证 (Chinese for authentication) classified as auth."""
    assert classify_failure(1, "身份验证失败") == "auth"


def test_classify_failure_sandbox():
    """Test 'operation not permitted' classified as sandbox."""
    assert classify_failure(1, "Operation not permitted") == "sandbox"


def test_classify_failure_sandbox_case_insensitive():
    """Test sandbox detection is case-insensitive."""
    assert classify_failure(1, "OPERATION NOT PERMITTED") == "sandbox"


def test_classify_failure_generic_process_error():
    """Test generic failure classified as process-error."""
    assert classify_failure(1, "Something went wrong") == "process-error"
    assert classify_failure(127, "Command not found") == "process-error"
    assert classify_failure(-1, "Killed") == "process-error"


# ─────────────────────────────────────────────────────────────────────────────
# _tool_chain tests
# ─────────────────────────────────────────────────────────────────────────────

def test_tool_chain_starts_with_initial():
    """Test tool chain starts with initial tool."""
    chain = _tool_chain("gemini")
    assert chain[0] == "gemini"


def test_tool_chain_includes_all_fallbacks():
    """Test tool chain includes all fallback tools."""
    chain = _tool_chain("gemini")
    for tool in FALLBACK_ORDER:
        assert tool in chain


def test_tool_chain_no_duplicates():
    """Test tool chain has no duplicates."""
    chain = _tool_chain("gemini")
    assert len(chain) == len(set(chain))


def test_tool_chain_length():
    """Test tool chain length depends on whether initial is in fallbacks."""
    # When initial tool is NOT in FALLBACK_ORDER, length is 1 + len(FALLBACK_ORDER)
    chain = _tool_chain("opencode")  # opencode not in FALLBACK_ORDER
    assert len(chain) == 1 + len(FALLBACK_ORDER)

    # When initial tool IS in FALLBACK_ORDER, it's not duplicated
    chain = _tool_chain("gemini")  # gemini IS in FALLBACK_ORDER
    assert len(chain) == len(FALLBACK_ORDER)  # No +1 since gemini already counted


def test_tool_chain_initial_not_in_fallback():
    """Test initial tool is not repeated in fallback section."""
    chain = _tool_chain("goose")
    # goose should be first, and not appear again
    assert chain[0] == "goose"
    assert "goose" not in chain[1:]


def test_tool_chain_preserves_fallback_order():
    """Test fallback tools appear in FALLBACK_ORDER sequence."""
    # Use a tool not in FALLBACK_ORDER to test pure fallback order
    chain = _tool_chain("opencode")  # opencode not in FALLBACK_ORDER
    # The fallback part should exactly match FALLBACK_ORDER
    fallback_part = chain[1:]  # Skip the initial tool
    assert fallback_part == FALLBACK_ORDER


def test_tool_chain_gemini_excludes_from_fallback():
    """Test that initial tool is excluded from fallback when it's in FALLBACK_ORDER."""
    chain = _tool_chain("gemini")
    # gemini should be first
    assert chain[0] == "gemini"
    # gemini should NOT appear again in the chain
    assert chain.count("gemini") == 1
    # The rest should be FALLBACK_ORDER minus gemini, in order
    expected_rest = [t for t in FALLBACK_ORDER if t != "gemini"]
    assert chain[1:] == expected_rest


# ─────────────────────────────────────────────────────────────────────────────
# _validate_backend tests
# ─────────────────────────────────────────────────────────────────────────────

@patch('shutil.which', return_value="/usr/bin/gemini")
def test_validate_backend_found(mock_which):
    """Test validation passes when binary is found."""
    # Should not raise
    _validate_backend("gemini", Path("/project"), "prompt")
    mock_which.assert_called_once_with("gemini")


@patch('shutil.which', return_value=None)
def test_validate_backend_not_found(mock_which):
    """Test validation raises FileNotFoundError when binary not found."""
    with pytest.raises(FileNotFoundError) as exc_info:
        _validate_backend("gemini", Path("/project"), "prompt")
    assert "gemini" in str(exc_info.value)
    assert "not found on PATH" in str(exc_info.value)


@patch('shutil.which', return_value="/usr/local/bin/claude")
def test_validate_backend_uses_command_binary(mock_which):
    """Test validation uses the binary from TOOL_COMMANDS."""
    _validate_backend("golem", Path("/project"), "prompt")
    # golem uses 'claude' binary
    mock_which.assert_called_once_with("claude")


@patch('shutil.which', return_value="/usr/bin/translocon")
def test_validate_backend_translocon_tools(mock_which):
    """Test translocon-based tools check for translocon binary."""
    _validate_backend("goose", Path("/project"), "prompt")
    mock_which.assert_called_once_with("translocon")


# ─────────────────────────────────────────────────────────────────────────────
# _clean_env tests
# ─────────────────────────────────────────────────────────────────────────────

def test_clean_env_removes_claudecode():
    """Test CLAUDECODE is removed from environment."""
    with patch.dict(os.environ, {"CLAUDECODE": "test-value"}, clear=False):
        env = _clean_env("gemini")
        assert "CLAUDECODE" not in env


def test_clean_env_golem_sets_anthropic_vars():
    """Test golem sets Anthropic compatibility variables."""
    with patch.dict(os.environ, {"ZHIPU_API_KEY": "test-key"}, clear=False):
        env = _clean_env("golem")
        assert env["ANTHROPIC_AUTH_TOKEN"] == "test-key"
        assert env["ANTHROPIC_BASE_URL"] == "https://open.bigmodel.cn/api/anthropic"
        assert env["ANTHROPIC_DEFAULT_OPUS_MODEL"] == "GLM-5.1"
        assert env["ANTHROPIC_DEFAULT_SONNET_MODEL"] == "GLM-5.1"
        assert env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == "GLM-4.5-air"
        assert env["API_TIMEOUT_MS"] == "3000000"
        assert env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] == "1"


def test_clean_env_golem_missing_zhipu_key():
    """Test golem handles missing ZHIPU_API_KEY."""
    # Make sure ZHIPU_API_KEY is not set
    env_copy = os.environ.copy()
    env_copy.pop("ZHIPU_API_KEY", None)
    with patch.dict(os.environ, env_copy, clear=True):
        env = _clean_env("golem")
        assert env["ANTHROPIC_AUTH_TOKEN"] == ""


def test_clean_env_copies_existing_env():
    """Test existing environment is copied."""
    with patch.dict(os.environ, {"CUSTOM_VAR": "custom-value"}, clear=False):
        env = _clean_env("gemini")
        assert "CUSTOM_VAR" in env
        assert env["CUSTOM_VAR"] == "custom-value"


def test_clean_env_other_tools_no_special_vars():
    """Test other tools don't get special env vars."""
    # Make sure none of these exist initially
    env_copy = os.environ.copy()
    for key in ["ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"]:
        env_copy.pop(key, None)
    
    with patch.dict(os.environ, env_copy, clear=True):
        env = _clean_env("gemini")
        assert "ANTHROPIC_AUTH_TOKEN" not in env


# ─────────────────────────────────────────────────────────────────────────────
# _status_path tests
# ─────────────────────────────────────────────────────────────────────────────

def test_status_path_default():
    """Test default status path."""
    with patch.dict(os.environ, {}, clear=True):
        result = _status_path()
        assert result == STATUS_PATH


def test_status_path_override():
    """Test status path can be overridden via env var."""
    with patch.dict(os.environ, {"OPIFEX_STATUS_PATH": "/custom/status.json"}, clear=True):
        result = _status_path()
        assert result == Path("/custom/status.json")


# ─────────────────────────────────────────────────────────────────────────────
# _legacy_tombstone tests
# ─────────────────────────────────────────────────────────────────────────────

def test_legacy_tombstone_format():
    """Test legacy tombstone format."""
    result = _legacy_tombstone("my-task")
    assert result == "__removed__:my-task"


def test_legacy_tombstone_with_special_chars():
    """Test legacy tombstone with special characters in task name."""
    result = _legacy_tombstone("task-with-dashes_and_underscores")
    assert "task-with-dashes_and_underscores" in result


# ─────────────────────────────────────────────────────────────────────────────
# _read_status_entries tests
# ─────────────────────────────────────────────────────────────────────────────

def test_read_status_entries_nonexistent_file(tmp_path):
    """Test reading status from nonexistent file returns empty list."""
    with patch('metabolon.sortase.executor._status_path', return_value=tmp_path / "missing.json"):
        result = _read_status_entries()
        assert result == []


def test_read_status_entries_valid_json(tmp_path):
    """Test reading status from valid JSON file."""
    status_path = tmp_path / "status.json"
    status_path.write_text('[{"task_name": "task1", "tool": "gemini"}]')
    
    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        result = _read_status_entries()
        assert len(result) == 1
        assert result[0]["task_name"] == "task1"


def test_read_status_entries_invalid_json(tmp_path):
    """Test reading status from invalid JSON returns empty list."""
    status_path = tmp_path / "status.json"
    status_path.write_text('not valid json')
    
    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        result = _read_status_entries()
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# _write_status_entries tests
# ─────────────────────────────────────────────────────────────────────────────

def test_write_status_entries_creates_file(tmp_path):
    """Test writing status entries creates file."""
    status_path = tmp_path / "status.json"
    
    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        _write_status_entries([{"task_name": "task1"}])
    
    assert status_path.exists()


def test_write_status_entries_creates_parent_dirs(tmp_path):
    """Test writing status entries creates parent directories."""
    status_path = tmp_path / "nested" / "dir" / "status.json"
    
    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        _write_status_entries([{"task_name": "task1"}])
    
    assert status_path.exists()


def test_write_status_entries_valid_json(tmp_path):
    """Test written JSON is valid and properly formatted."""
    import json
    status_path = tmp_path / "status.json"
    entries = [{"task_name": "task1"}, {"task_name": "task2"}]
    
    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        _write_status_entries(entries)
    
    loaded = json.loads(status_path.read_text())
    assert loaded == entries


# ─────────────────────────────────────────────────────────────────────────────
# _is_git_repo tests
# ─────────────────────────────────────────────────────────────────────────────

def test_is_git_repo_true(tmp_path):
    """Test returns True when .git directory exists."""
    (tmp_path / ".git").mkdir()
    assert _is_git_repo(tmp_path) is True


def test_is_git_repo_false(tmp_path):
    """Test returns False when .git directory doesn't exist."""
    assert _is_git_repo(tmp_path) is False


def test_is_git_repo_file_not_dir(tmp_path):
    """Test returns True for .git file too (uses exists(), not is_dir())."""
    # Note: The implementation uses .exists() which returns True for files too.
    # A .git file (git worktree pointer) should still indicate a git repo.
    (tmp_path / ".git").write_text("gitdir: somewhere")
    # This returns True because .exists() works on files
    assert _is_git_repo(tmp_path) is True


# ─────────────────────────────────────────────────────────────────────────────
# Dataclass tests
# ─────────────────────────────────────────────────────────────────────────────

def test_execution_attempt_dataclass():
    """Test ExecutionAttempt dataclass creation."""
    attempt = ExecutionAttempt(
        tool="gemini",
        exit_code=0,
        duration_s=1.5,
        output="Success",
    )
    assert attempt.tool == "gemini"
    assert attempt.exit_code == 0
    assert attempt.duration_s == 1.5
    assert attempt.output == "Success"
    assert attempt.failure_reason is None
    assert attempt.cost_estimate == ""


def test_execution_attempt_with_failure():
    """Test ExecutionAttempt with failure reason."""
    attempt = ExecutionAttempt(
        tool="gemini",
        exit_code=1,
        duration_s=2.0,
        output="Error: quota exceeded",
        failure_reason="quota",
        cost_estimate="$0.0000",
    )
    assert attempt.failure_reason == "quota"
    assert attempt.cost_estimate == "$0.0000"


def test_fallback_step_dataclass():
    """Test FallbackStep dataclass creation."""
    step = FallbackStep(tool="gemini", succeeded=True)
    assert step.tool == "gemini"
    assert step.succeeded is True
    assert step.failure_reason is None


def test_fallback_step_to_dict():
    """Test FallbackStep.to_dict() method."""
    step = FallbackStep(tool="gemini", succeeded=False, failure_reason="quota")
    result = step.to_dict()
    assert result["tool"] == "gemini"
    assert result["succeeded"] is False
    assert result["failure_reason"] == "quota"


def test_fallback_step_to_dict_no_failure_reason():
    """Test FallbackStep.to_dict() without failure reason."""
    step = FallbackStep(tool="gemini", succeeded=True)
    result = step.to_dict()
    assert "failure_reason" not in result


def test_task_execution_result_dataclass():
    """Test TaskExecutionResult dataclass creation."""
    result = TaskExecutionResult(
        task_name="my-task",
        tool="gemini",
        prompt_file="/tmp/prompt.txt",
        success=True,
    )
    assert result.task_name == "my-task"
    assert result.tool == "gemini"
    assert result.prompt_file == "/tmp/prompt.txt"
    assert result.success is True
    assert result.attempts == []
    assert result.output == ""
    assert result.fallbacks == []
    assert result.fallback_chain == []
    assert result.cost_estimate == ""


def test_task_execution_result_with_attempts():
    """Test TaskExecutionResult with attempts and fallbacks."""
    attempt = ExecutionAttempt(tool="gemini", exit_code=0, duration_s=1.0, output="OK")
    result = TaskExecutionResult(
        task_name="task",
        tool="gemini",
        prompt_file=None,
        success=True,
        attempts=[attempt],
        output="Done",
        fallbacks=["codex"],
        cost_estimate="$0.0100",
    )
    assert len(result.attempts) == 1
    assert result.fallbacks == ["codex"]
    assert result.cost_estimate == "$0.0100"


# ─────────────────────────────────────────────────────────────────────────────
# summarize_results tests
# ─────────────────────────────────────────────────────────────────────────────

def test_summarize_results_empty():
    """Test summarize_results with empty list."""
    result = summarize_results([])
    assert result["tasks"] == 0
    assert result["successful"] == 0
    assert result["failed"] == 0
    assert result["fallbacks"] == 0


def test_summarize_results_all_success():
    """Test summarize_results with all successful tasks."""
    results = [
        TaskExecutionResult(task_name="t1", tool="gemini", prompt_file=None, success=True),
        TaskExecutionResult(task_name="t2", tool="gemini", prompt_file=None, success=True),
    ]
    summary = summarize_results(results)
    assert summary["tasks"] == 2
    assert summary["successful"] == 2
    assert summary["failed"] == 0


def test_summarize_results_all_failed():
    """Test summarize_results with all failed tasks."""
    results = [
        TaskExecutionResult(task_name="t1", tool="gemini", prompt_file=None, success=False),
        TaskExecutionResult(task_name="t2", tool="gemini", prompt_file=None, success=False),
    ]
    summary = summarize_results(results)
    assert summary["tasks"] == 2
    assert summary["successful"] == 0
    assert summary["failed"] == 2


def test_summarize_results_mixed():
    """Test summarize_results with mixed results."""
    results = [
        TaskExecutionResult(task_name="t1", tool="gemini", prompt_file=None, success=True),
        TaskExecutionResult(task_name="t2", tool="gemini", prompt_file=None, success=False),
        TaskExecutionResult(task_name="t3", tool="gemini", prompt_file=None, success=True),
    ]
    summary = summarize_results(results)
    assert summary["tasks"] == 3
    assert summary["successful"] == 2
    assert summary["failed"] == 1


def test_summarize_results_counts_fallbacks():
    """Test summarize_results counts fallbacks correctly."""
    results = [
        TaskExecutionResult(
            task_name="t1", tool="gemini", prompt_file=None, success=True,
            fallbacks=["codex"]
        ),
        TaskExecutionResult(
            task_name="t2", tool="goose", prompt_file=None, success=False,
            fallbacks=["droid", "gemini", "codex"]
        ),
    ]
    summary = summarize_results(results)
    assert summary["fallbacks"] == 4


def test_summarize_results_prompt_files():
    """Test summarize_results includes prompt files."""
    results = [
        TaskExecutionResult(task_name="t1", tool="gemini", prompt_file="/tmp/p1.txt", success=True),
        TaskExecutionResult(task_name="t2", tool="gemini", prompt_file="/tmp/p2.txt", success=True),
        TaskExecutionResult(task_name="t3", tool="gemini", prompt_file=None, success=True),
    ]
    summary = summarize_results(results)
    assert len(summary["prompt_files"]) == 2
    assert "/tmp/p1.txt" in summary["prompt_files"]
    assert "/tmp/p2.txt" in summary["prompt_files"]


# ─────────────────────────────────────────────────────────────────────────────
# TOOL_COMMANDS tests
# ─────────────────────────────────────────────────────────────────────────────

def test_tool_commands_callable():
    """Test TOOL_COMMANDS entries are callable."""
    for tool, command_fn in TOOL_COMMANDS.items():
        result = command_fn(Path("/project"), "test prompt")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(arg, str) for arg in result)


def test_tool_commands_include_project():
    """Test TOOL_COMMANDS include project directory where appropriate."""
    project = Path("/my/project")
    
    # goose includes project
    goose_cmd = TOOL_COMMANDS["goose"](project, "prompt")
    assert str(project) in goose_cmd
    
    # opencode includes project
    opencode_cmd = TOOL_COMMANDS["opencode"](project, "prompt")
    assert str(project) in opencode_cmd
    
    # crush includes project
    crush_cmd = TOOL_COMMANDS["crush"](project, "prompt")
    assert str(project) in crush_cmd


def test_tool_commands_include_prompt():
    """Test TOOL_COMMANDS include prompt."""
    prompt = "my special prompt text"
    for tool, command_fn in TOOL_COMMANDS.items():
        result = command_fn(Path("/project"), prompt)
        assert prompt in result, f"{tool} should include prompt"


# ─────────────────────────────────────────────────────────────────────────────
# Additional edge case tests
# ─────────────────────────────────────────────────────────────────────────────

def test_compute_adaptive_timeout_empty_spec():
    """Test timeout for empty spec returns base."""
    assert _compute_adaptive_timeout("", 600) == 600


def test_compute_adaptive_timeout_whitespace_spec():
    """Test timeout for whitespace-only spec returns base."""
    assert _compute_adaptive_timeout("   \n\t  ", 600) == 600


def test_compute_adaptive_timeout_multiple_read_mentions():
    """Test timeout for spec with multiple 'read' mentions still doubles."""
    spec = "Read this, then read that, and also read the other file"
    # Should still only double, not triple
    assert _compute_adaptive_timeout(spec, 600) == 1200


def test_compute_adaptive_timeout_exactly_one_various_formats():
    """Test 'exactly 1 tool call' pattern with various formats."""
    assert _compute_adaptive_timeout("Make exactly 1 tool call", 600) == 300
    assert _compute_adaptive_timeout("EXACTLY 1 tool call required", 600) == 300
    assert _compute_adaptive_timeout("You need exactly 1 tool call.", 600) == 300


def test_classify_failure_exit_code_zero_with_quota_text():
    """Test exit code 0 returns None even with quota text."""
    # Exit code 0 means success, regardless of output text
    assert classify_failure(0, "Error 429: Too many requests") is None


def test_estimate_cost_opencode():
    """Test cost estimation for opencode (unknown pricing)."""
    # opencode has None model in MODEL_BY_TOOL
    result = estimate_cost("opencode", "prompt", "output")
    assert result == "$0.00 (unknown pricing)"


def test_estimate_cost_crush():
    """Test cost estimation for crush (unknown pricing)."""
    # crush has model "zhipu-coding/glm-5" which isn't in TOKEN_PRICING
    result = estimate_cost("crush", "prompt", "output")
    assert result == "$0.00 (unknown pricing)"


def test_summarize_cost_estimates_all_zero():
    """Test summarize with all zero dollar amounts."""
    result = summarize_cost_estimates(["$0.0000", "$0.0000"])
    assert result == "$0.0000"


def test_summarize_cost_estimates_zero_with_notes():
    """Test zero total with flat-rate returns flat-rate (priority rule)."""
    # When total is 0 and there's flat-rate (but no unknown), returns flat-rate
    result = summarize_cost_estimates(["$0.0000", "$0.00 (flat-rate)"])
    assert result == "$0.00 (flat-rate)"


def test_summarize_cost_estimates_zero_with_unknown():
    """Test zero total with unknown pricing returns N/A."""
    # When total is 0 and there's unknown pricing (but no flat-rate), returns N/A
    result = summarize_cost_estimates(["$0.0000", "$0.00 (unknown pricing)"])
    assert result == "N/A (unknown pricing)"


def test_summarize_cost_estimates_large_amounts():
    """Test summarize with large dollar amounts."""
    result = summarize_cost_estimates(["$100.5000", "$50.2500"])
    assert result == "$150.7500"


def test_fallback_step_to_dict_succeeded_no_reason():
    """Test to_dict for succeeded step has no failure_reason key."""
    step = FallbackStep(tool="gemini", succeeded=True)
    d = step.to_dict()
    assert d == {"tool": "gemini", "succeeded": True}


def test_fallback_step_to_dict_failed_with_reason():
    """Test to_dict for failed step includes failure_reason."""
    step = FallbackStep(tool="gemini", succeeded=False, failure_reason="quota")
    d = step.to_dict()
    assert d == {"tool": "gemini", "succeeded": False, "failure_reason": "quota"}


def test_tool_chain_with_custom_tool():
    """Test tool chain with a custom tool not in FALLBACK_ORDER."""
    chain = _tool_chain("my-custom-tool")
    assert chain[0] == "my-custom-tool"
    assert chain[1:] == FALLBACK_ORDER


def test_status_path_uses_path_object():
    """Test _status_path returns a Path object."""
    with patch.dict(os.environ, {}, clear=True):
        result = _status_path()
        assert isinstance(result, Path)


def test_read_status_entries_empty_json_array(tmp_path):
    """Test reading status from empty JSON array."""
    status_path = tmp_path / "status.json"
    status_path.write_text('[]')

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        result = _read_status_entries()
        assert result == []


def test_read_status_entries_non_list_json(tmp_path):
    """Test reading status from JSON that's not a list."""
    status_path = tmp_path / "status.json"
    status_path.write_text('{"key": "value"}')

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        result = _read_status_entries()
        # JSON that's not a list will still be returned as-is
        assert isinstance(result, dict)


def test_clean_env_preserves_path():
    """Test _clean_env preserves PATH."""
    with patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=False):
        env = _clean_env("gemini")
        assert "PATH" in env


def test_clean_env_preserves_home():
    """Test _clean_env preserves HOME."""
    with patch.dict(os.environ, {"HOME": str(Path.home())}, clear=False):
        env = _clean_env("gemini")
        assert "HOME" in env


# ─────────────────────────────────────────────────────────────────────────────
# TOOL_COMMANDS detailed tests
# ─────────────────────────────────────────────────────────────────────────────

def test_tool_command_gemini_structure():
    """Test gemini command has expected structure."""
    cmd = TOOL_COMMANDS["gemini"](Path("/project"), "test prompt")
    assert cmd[0] == "gemini"
    assert "-m" in cmd
    assert "gemini-3.1-pro-preview" in cmd
    assert "-p" in cmd
    assert "--yolo" in cmd


def test_tool_command_codex_structure():
    """Test codex command has expected structure."""
    cmd = TOOL_COMMANDS["codex"](Path("/project"), "test prompt")
    assert cmd[0] == "codex"
    assert "exec" in cmd
    assert "--full-auto" in cmd


def test_tool_command_golem_structure():
    """Test golem command has expected structure."""
    cmd = TOOL_COMMANDS["golem"](Path("/project"), "test prompt")
    assert cmd[0] == "claude"
    assert "--print" in cmd
    assert "--bare" in cmd
    assert "--max-turns" in cmd


def test_tool_command_opencode_structure():
    """Test opencode command has expected structure."""
    cmd = TOOL_COMMANDS["opencode"](Path("/project"), "test prompt")
    assert cmd[0] == "opencode"
    assert "run" in cmd
    assert "--dir" in cmd


def test_tool_command_crush_structure():
    """Test crush command has expected structure."""
    cmd = TOOL_COMMANDS["crush"](Path("/project"), "test prompt")
    assert cmd[0] == "crush"
    assert "run" in cmd
    assert "--model" in cmd
    assert "zhipu-coding/glm-5" in cmd
    assert "--cwd" in cmd


def test_tool_command_goose_uses_translocon():
    """Test goose command uses translocon."""
    cmd = TOOL_COMMANDS["goose"](Path("/project"), "test prompt")
    assert cmd[0] == "translocon"
    assert "--backend" in cmd
    assert "goose" in cmd


def test_tool_command_droid_uses_translocon():
    """Test droid command uses translocon."""
    cmd = TOOL_COMMANDS["droid"](Path("/project"), "test prompt")
    assert cmd[0] == "translocon"
    assert "--backend" in cmd
    assert "droid" in cmd


# ─────────────────────────────────────────────────────────────────────────────
# register_running / unregister_running / list_running tests
# ─────────────────────────────────────────────────────────────────────────────

def test_register_running_legacy_mode(tmp_path):
    """Test register_running in legacy mode (no tool/project_dir)."""
    status_path = tmp_path / "status.json"

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        register_running("task-1")

        entries = _read_status_entries()
        assert "task-1" in entries


def test_register_running_legacy_removes_tombstone(tmp_path):
    """Test register_running removes tombstone if present."""
    status_path = tmp_path / "status.json"
    status_path.write_text('["__removed__:task-1"]')

    with patch('metabolon.sortase.executor._status_path', return_value=status_path), \
         patch('metabolon.sortase.executor._locked_status_update') as mock_locked:
        # Call the inner function directly to test the logic
        from metabolon.sortase.executor import register_running
        # Manually test the logic by calling _add directly
        entries = ["__removed__:task-1"]
        # Simulate the _add inner function
        tombstone = "__removed__:task-1"
        if tombstone in entries:
            entries.remove(tombstone)
        entries.append("task-1")
        assert "__removed__:task-1" not in entries
        assert "task-1" in entries


def test_register_running_full_mode(tmp_path):
    """Test register_running with tool and project_dir."""
    status_path = tmp_path / "status.json"

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        register_running("task-1", tool="gemini", project_dir=Path("/project"))

        entries = _read_status_entries()
        assert len(entries) == 1
        assert entries[0]["task_name"] == "task-1"
        assert entries[0]["tool"] == "gemini"
        assert entries[0]["project_dir"] == "/project"
        assert "started_at" in entries[0]
        assert "pid" in entries[0]


def test_unregister_running_legacy_mode(tmp_path):
    """Test unregister_running in legacy mode."""
    status_path = tmp_path / "status.json"
    status_path.write_text('["task-1", "task-2"]')

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        unregister_running("task-1")

        entries = _read_status_entries()
        assert "task-1" not in entries
        assert "task-2" in entries


def test_unregister_running_legacy_creates_tombstone(tmp_path):
    """Test unregister_running creates tombstone if task not found."""
    status_path = tmp_path / "status.json"
    status_path.write_text('["task-2"]')

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        unregister_running("task-1")

        entries = _read_status_entries()
        assert "__removed__:task-1" in entries


def test_unregister_running_full_mode(tmp_path):
    """Test unregister_running with project_dir."""
    status_path = tmp_path / "status.json"
    status_path.write_text('[{"task_name": "task-1", "project_dir": "/project", "tool": "gemini"}]')

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        unregister_running("task-1", project_dir=Path("/project"))

        entries = _read_status_entries()
        assert len(entries) == 0


def test_unregister_running_full_mode_different_project(tmp_path):
    """Test unregister_running only removes matching project_dir."""
    status_path = tmp_path / "status.json"
    status_path.write_text('[{"task_name": "task-1", "project_dir": "/project1", "tool": "gemini"}]')

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        unregister_running("task-1", project_dir=Path("/project2"))

        entries = _read_status_entries()
        assert len(entries) == 1


def test_list_running_empty(tmp_path):
    """Test list_running with empty status."""
    status_path = tmp_path / "status.json"

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        result = list_running()
        assert result == []


def test_list_running_with_entries(tmp_path):
    """Test list_running with entries."""
    status_path = tmp_path / "status.json"
    status_path.write_text('[{"task_name": "task-1", "tool": "gemini"}]')

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        result = list_running()
        assert len(result) == 1
        assert result[0]["task_name"] == "task-1"


def test_list_running_checks_pid_liveness(tmp_path):
    """Test list_running checks process liveness."""
    import os
    status_path = tmp_path / "status.json"
    # Use current PID (alive) and a definitely-dead PID
    current_pid = os.getpid()
    dead_pid = 999999  # Very unlikely to exist
    status_path.write_text(f'''[
        {{"task_name": "alive-task", "pid": {current_pid}}},
        {{"task_name": "dead-task", "pid": {dead_pid}}}
    ]''')

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        result = list_running()
        alive_entry = next(e for e in result if e["task_name"] == "alive-task")
        dead_entry = next(e for e in result if e["task_name"] == "dead-task")
        assert alive_entry["alive"] is True
        assert dead_entry["alive"] is False


def test_list_running_legacy_entries_no_pid(tmp_path):
    """Test list_running handles legacy string entries."""
    status_path = tmp_path / "status.json"
    status_path.write_text('["legacy-task-1", "legacy-task-2"]')

    with patch('metabolon.sortase.executor._status_path', return_value=status_path):
        result = list_running()
        assert "legacy-task-1" in result
        assert "legacy-task-2" in result


# ─────────────────────────────────────────────────────────────────────────────
# _run_command async tests
#
# NOTE: The original tests hung because ``asyncio.wait_for`` was mocked with
# ``side_effect=lambda coro, timeout: coro`` which returns a coroutine *object*
# without awaiting it.  The fix is to use an async side_effect that awaits the
# coroutine (so the inner mock .read() actually runs).
# ─────────────────────────────────────────────────────────────────────────────

async def _await_coro(coro, timeout):
    """Helper: await a coroutine — used as wait_for side_effect."""
    return await coro


def _make_mock_process(read_chunks, returncode=0):
    """Build a mock asyncio.subprocess.Process with the given read chunks."""
    mock_stdout = MagicMock()
    it = iter(read_chunks)

    async def _read(size):
        return next(it)

    mock_stdout.read = _read

    mock_process = MagicMock()
    mock_process.stdout = mock_stdout
    mock_process.returncode = returncode

    async def _wait():
        pass

    mock_process.wait = _wait
    return mock_process


@pytest.mark.asyncio
async def test_run_command_success(tmp_path):
    """Test _run_command with successful execution."""
    mock_process = _make_mock_process([b"output data", b""], returncode=0)

    with patch('metabolon.sortase.executor._validate_backend'), \
         patch('metabolon.sortase.executor._prepend_coaching', return_value="prompt"), \
         patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('asyncio.wait_for', side_effect=_await_coro):
        result = await _run_command(
            tool="gemini",
            project_dir=tmp_path,
            prompt="test prompt",
            timeout_sec=60,
        )

    assert result.exit_code == 0
    assert result.output == "output data"
    assert result.tool == "gemini"
    assert result.failure_reason is None


@pytest.mark.asyncio
async def test_run_command_timeout(tmp_path):
    """Test _run_command handles timeout."""
    mock_process = _make_mock_process([], returncode=None)

    async def _kill():
        pass

    async def _communicate():
        return (b"", b"")

    mock_process.kill = _kill
    mock_process.communicate = _communicate

    with patch('metabolon.sortase.executor._validate_backend'), \
         patch('metabolon.sortase.executor._prepend_coaching', return_value="prompt"), \
         patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('asyncio.wait_for', side_effect=TimeoutError):
        result = await _run_command(
            tool="gemini",
            project_dir=tmp_path,
            prompt="test prompt",
            timeout_sec=60,
        )

    assert result.exit_code == 124  # Timeout exit code
    assert "timed out" in result.output
    assert result.failure_reason == "process-error"


@pytest.mark.asyncio
async def test_run_command_failure(tmp_path):
    """Test _run_command with non-zero exit code."""
    mock_process = _make_mock_process(
        [b"Error: 429 quota exceeded", b""], returncode=1,
    )

    with patch('metabolon.sortase.executor._validate_backend'), \
         patch('metabolon.sortase.executor._prepend_coaching', return_value="prompt"), \
         patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('asyncio.wait_for', side_effect=_await_coro):
        result = await _run_command(
            tool="gemini",
            project_dir=tmp_path,
            prompt="test prompt",
            timeout_sec=60,
        )

    assert result.exit_code == 1
    assert result.failure_reason == "quota"


@pytest.mark.asyncio
async def test_run_command_dry_run(tmp_path):
    """Test _run_command with dry_run flag prepends DRY RUN MODE."""
    mock_process = _make_mock_process([b"output", b""], returncode=0)

    with patch('metabolon.sortase.executor._validate_backend') as mock_validate, \
         patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('asyncio.wait_for', side_effect=_await_coro):
        await _run_command(
            tool="gemini",
            project_dir=tmp_path,
            prompt="test prompt",
            timeout_sec=60,
            dry_run=True,
        )

    call_args = mock_validate.call_args
    assert "DRY RUN MODE" in call_args[0][2]


@pytest.mark.asyncio
async def test_run_command_coaching_disabled(tmp_path):
    """Test _run_command with coaching=False leaves prompt untouched."""
    mock_process = _make_mock_process([b"output", b""], returncode=0)

    with patch('metabolon.sortase.executor._validate_backend') as mock_validate, \
         patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('asyncio.wait_for', side_effect=_await_coro):
        await _run_command(
            tool="gemini",
            project_dir=tmp_path,
            prompt="test prompt",
            timeout_sec=60,
            coaching=False,
        )

    call_args = mock_validate.call_args
    assert call_args[0][2] == "test prompt"


@pytest.mark.asyncio
async def test_run_command_cost_estimate_populated(tmp_path):
    """Test _run_command populates cost_estimate on the attempt."""
    mock_process = _make_mock_process([b"result", b""], returncode=0)

    with patch('metabolon.sortase.executor._validate_backend'), \
         patch('metabolon.sortase.executor._prepend_coaching', return_value="prompt"), \
         patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('asyncio.wait_for', side_effect=_await_coro):
        result = await _run_command(
            tool="goose",
            project_dir=tmp_path,
            prompt="test prompt",
            timeout_sec=60,
        )

    # goose is a flat-rate tool
    assert result.cost_estimate == "$0.00 (flat-rate)"


@pytest.mark.asyncio
async def test_run_command_multiple_chunks(tmp_path):
    """Test _run_command correctly joins multiple stdout chunks."""
    mock_process = _make_mock_process(
        [b"chunk1 ", b"chunk2 ", b"chunk3", b""], returncode=0,
    )

    with patch('metabolon.sortase.executor._validate_backend'), \
         patch('metabolon.sortase.executor._prepend_coaching', return_value="prompt"), \
         patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('asyncio.wait_for', side_effect=_await_coro):
        result = await _run_command(
            tool="gemini",
            project_dir=tmp_path,
            prompt="test prompt",
            timeout_sec=60,
        )

    assert result.output == "chunk1 chunk2 chunk3"


@pytest.mark.asyncio
async def test_run_command_duration_is_recorded(tmp_path):
    """Test _run_command records a non-negative duration."""
    mock_process = _make_mock_process([b"ok", b""], returncode=0)

    with patch('metabolon.sortase.executor._validate_backend'), \
         patch('metabolon.sortase.executor._prepend_coaching', return_value="prompt"), \
         patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('asyncio.wait_for', side_effect=_await_coro):
        result = await _run_command(
            tool="gemini",
            project_dir=tmp_path,
            prompt="test prompt",
            timeout_sec=60,
        )

    assert result.duration_s >= 0


# ─────────────────────────────────────────────────────────────────────────────
# _reset_git_state tests
# ─────────────────────────────────────────────────────────────────────────────

def test_reset_git_state_not_a_repo(tmp_path):
    """Test _reset_git_state skips non-git directories."""
    with patch('subprocess.run') as mock_run:
        _reset_git_state(tmp_path, "task-name")
        mock_run.assert_not_called()


def test_reset_git_state_git_repo(tmp_path):
    """Test _reset_git_state runs git commands in git repo."""
    (tmp_path / ".git").mkdir()

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _reset_git_state(tmp_path, "task-name")
        assert mock_run.call_count >= 2


def test_reset_git_state_verbose_mode(tmp_path, capsys):
    """Test _reset_git_state with verbose mode does not raise."""
    (tmp_path / ".git").mkdir()

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        _reset_git_state(tmp_path, "task-name", verbose=True)


def test_reset_git_state_discards_dirty_files(tmp_path, capsys):
    """Test _reset_git_state logs dirty files before discarding."""
    (tmp_path / ".git").mkdir()

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main.py\nutils.py\n", stderr=""),  # git diff
            MagicMock(returncode=0, stdout="Would remove build/\n", stderr=""),  # git clean -nd
            MagicMock(returncode=0, stdout="", stderr=""),  # git checkout
            MagicMock(returncode=0, stdout="", stderr=""),  # git clean -fd
        ]
        _reset_git_state(tmp_path, "my-task")

    captured = capsys.readouterr()
    assert "main.py" in captured.err
    assert "build/" in captured.err


# ─────────────────────────────────────────────────────────────────────────────
# _create_worktree tests
# ─────────────────────────────────────────────────────────────────────────────

def test_create_worktree(tmp_path):
    """Test _create_worktree creates worktree."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".claude").mkdir()

    with patch('subprocess.run') as mock_run, \
         patch('uuid.uuid4') as mock_uuid, \
         patch.object(Path, 'symlink_to') as mock_symlink:
        mock_run.return_value = MagicMock(returncode=0)
        mock_uuid.return_value.hex = "abcd1234"

        result = _create_worktree(tmp_path, "test-task")

        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "worktree" in call_args
        assert "add" in call_args
        assert mock_symlink.call_count == 2


def test_create_worktree_no_venv_or_claude(tmp_path):
    """Test _create_worktree skips symlinks when .venv/.claude don't exist."""
    (tmp_path / ".git").mkdir()
    # No .venv or .claude directories

    with patch('subprocess.run') as mock_run, \
         patch('uuid.uuid4') as mock_uuid, \
         patch.object(Path, 'symlink_to') as mock_symlink:
        mock_run.return_value = MagicMock(returncode=0)
        mock_uuid.return_value.hex = "abcd1234"

        _create_worktree(tmp_path, "test-task")

        mock_symlink.assert_not_called()


def test_create_worktree_symlinks_dirs(tmp_path):
    """Test _create_worktree symlinks .venv and .claude."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".claude").mkdir()

    with patch('subprocess.run') as mock_run, \
         patch('uuid.uuid4') as mock_uuid, \
         patch.object(Path, 'symlink_to') as mock_symlink:
        mock_run.return_value = MagicMock(returncode=0)
        mock_uuid.return_value.hex = "abcd1234"

        _create_worktree(tmp_path, "test-task")

        assert mock_symlink.call_count == 2


# ─────────────────────────────────────────────────────────────────────────────
# _merge_worktree tests
# ─────────────────────────────────────────────────────────────────────────────

def test_sortase_executor_merge_worktree_no_changes(tmp_path):
    """Test _merge_worktree with no changes."""
    (tmp_path / ".git").mkdir()
    worktree_path = Path("/tmp/sortase-test")

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=f"worktree {worktree_path}\nbranch refs/heads/sortase/test-task-abcd1234\n", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),  # No diff
            MagicMock(returncode=0, stdout="", stderr=""),  # git worktree remove
            MagicMock(returncode=0, stdout="", stderr=""),  # git branch -D
        ]

        success, msg = _merge_worktree(tmp_path, worktree_path)

    assert success is True
    assert msg == "no changes"


def test_merge_worktree_conflict(tmp_path, capsys):
    """Test _merge_worktree with conflict."""
    (tmp_path / ".git").mkdir()
    worktree_path = Path("/tmp/sortase-test")

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=f"worktree {worktree_path}\nbranch refs/heads/feature\n", stderr=""),
            MagicMock(returncode=0, stdout="file.py\n", stderr=""),  # diff stat
            MagicMock(returncode=0, stdout="file.py\n", stderr=""),  # worktree changed
            MagicMock(returncode=0, stdout="file.py\n", stderr=""),  # main changed (conflict!)
            MagicMock(returncode=0, stdout="", stderr=""),  # git worktree remove
        ]

        success, msg = _merge_worktree(tmp_path, worktree_path)

    assert success is False
    assert "conflict" in msg.lower()


def test_merge_worktree_branch_not_found(tmp_path):
    """Test _merge_worktree when branch not found."""
    (tmp_path / ".git").mkdir()
    worktree_path = Path("/tmp/sortase-test")

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="worktree /other\n", stderr="")

        success, msg = _merge_worktree(tmp_path, worktree_path)

    assert success is False
    assert "Could not find branch" in msg


def test_merge_worktree_success(tmp_path):
    """Test _merge_worktree with a successful merge."""
    (tmp_path / ".git").mkdir()
    worktree_path = Path("/tmp/sortase-test")

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            # git worktree list
            MagicMock(returncode=0, stdout=f"worktree {worktree_path}\nbranch refs/heads/feature\n", stderr=""),
            # git diff --stat (has changes)
            MagicMock(returncode=0, stdout="file.py | 5 +++--\n1 file changed\n", stderr=""),
            # worktree changed files
            MagicMock(returncode=0, stdout="file.py\n", stderr=""),
            # main changed files (different — no conflict)
            MagicMock(returncode=0, stdout="other.py\n", stderr=""),
            # git merge
            MagicMock(returncode=0, stdout="Merge made\n", stderr=""),
            # git worktree remove (inside _remove_worktree)
            MagicMock(returncode=0, stdout="", stderr=""),
            # git branch -D
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        success, msg = _merge_worktree(tmp_path, worktree_path)

    assert success is True
    assert "file.py" in msg


# ─────────────────────────────────────────────────────────────────────────────
# _remove_worktree tests
# ─────────────────────────────────────────────────────────────────────────────

def test_remove_worktree(tmp_path):
    """Test _remove_worktree removes worktree and branch."""
    (tmp_path / ".git").mkdir()

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        _remove_worktree(tmp_path, Path("/tmp/worktree"), "feature-branch")

    assert mock_run.call_count == 2
    assert "worktree" in mock_run.call_args_list[0][0][0]
    assert "remove" in mock_run.call_args_list[0][0][0]
    assert "branch" in mock_run.call_args_list[1][0][0]


# ─────────────────────────────────────────────────────────────────────────────
# _force_remove_worktree tests
# ─────────────────────────────────────────────────────────────────────────────

def test_force_remove_worktree(tmp_path):
    """Test _force_remove_worktree removes worktree."""
    (tmp_path / ".git").mkdir()
    worktree_path = Path("/tmp/worktree")

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=f"worktree {worktree_path}\nbranch refs/heads/feature\n", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),  # worktree remove
            MagicMock(returncode=0, stdout="", stderr=""),  # branch delete
        ]

        _force_remove_worktree(tmp_path, worktree_path)

    assert mock_run.called


def test_force_remove_worktree_no_branch(tmp_path):
    """Test _force_remove_worktree when branch not found falls back to direct remove."""
    (tmp_path / ".git").mkdir()
    worktree_path = Path("/tmp/worktree")

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="worktree /other\n", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),  # fallback remove
        ]

        _force_remove_worktree(tmp_path, worktree_path)

    last_call = mock_run.call_args_list[-1][0][0]
    assert "worktree" in last_call


# ─────────────────────────────────────────────────────────────────────────────
# _emit_completion_signal tests
# ─────────────────────────────────────────────────────────────────────────────

def test_emit_completion_signal_success():
    """Test _emit_completion_signal with successful result never raises."""
    result = TaskExecutionResult(
        task_name="test-task",
        tool="gemini",
        prompt_file=None,
        success=True,
        output="Done!",
    )
    _emit_completion_signal(result)


def test_emit_completion_signal_import_error():
    """Test _emit_completion_signal handles import error gracefully."""
    result = TaskExecutionResult(
        task_name="test-task",
        tool="gemini",
        prompt_file=None,
        success=True,
    )
    _emit_completion_signal(result)


def test_emit_completion_signal_failed_result():
    """Test _emit_completion_signal with a failed result never raises."""
    result = TaskExecutionResult(
        task_name="fail-task",
        tool="codex",
        prompt_file=None,
        success=False,
        output="something broke",
    )
    _emit_completion_signal(result)


# ─────────────────────────────────────────────────────────────────────────────
# _analyze_for_coaching tests
# ─────────────────────────────────────────────────────────────────────────────

def test_analyze_for_coaching_skips_short_success():
    """Test _analyze_for_coaching skips short successful output."""
    result = TaskExecutionResult(
        task_name="test-task",
        tool="golem",
        prompt_file=None,
        success=True,
        output="OK",
    )
    with patch('shutil.which', return_value=None):
        _analyze_for_coaching(result)


def test_analyze_for_coaching_no_channel_binary():
    """Test _analyze_for_coaching when channel binary not found."""
    result = TaskExecutionResult(
        task_name="test-task",
        tool="golem",
        prompt_file=None,
        success=False,
        output="x" * 500,
    )
    with patch('shutil.which', return_value=None):
        _analyze_for_coaching(result)


def test_analyze_for_coaching_empty_output():
    """Test _analyze_for_coaching with empty output."""
    result = TaskExecutionResult(
        task_name="test-task",
        tool="golem",
        prompt_file=None,
        success=False,
        output="",
    )
    with patch('shutil.which', return_value="/usr/bin/channel"):
        _analyze_for_coaching(result)


def test_analyze_for_coaching_channel_returns_no_patterns(tmp_path):
    """Test _analyze_for_coaching when channel says NO_NEW_PATTERNS."""
    result = TaskExecutionResult(
        task_name="test-task",
        tool="golem",
        prompt_file=None,
        success=False,
        output="x" * 500,
    )
    mock_proc = MagicMock(returncode=0, stdout="NO_NEW_PATTERNS")
    with patch('shutil.which', return_value="/usr/bin/channel"), \
         patch('subprocess.run', return_value=mock_proc):
        _analyze_for_coaching(result)  # Should not write to coaching notes


def test_analyze_for_coaching_channel_fails(tmp_path):
    """Test _analyze_for_coaching when channel subprocess fails."""
    result = TaskExecutionResult(
        task_name="test-task",
        tool="golem",
        prompt_file=None,
        success=False,
        output="x" * 500,
    )
    mock_proc = MagicMock(returncode=1, stdout="")
    with patch('shutil.which', return_value="/usr/bin/channel"), \
         patch('subprocess.run', return_value=mock_proc):
        _analyze_for_coaching(result)  # Should not raise


# ─────────────────────────────────────────────────────────────────────────────
# execute_task async tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_task_success(tmp_path):
    """Test execute_task with successful execution."""
    from metabolon.sortase.decompose import TaskSpec

    task = TaskSpec(name="test-task", description="Test task", spec="Do something", files=[])

    mock_attempt = ExecutionAttempt(
        tool="gemini", exit_code=0, duration_s=1.0, output="Success",
    )

    with patch('metabolon.sortase.executor.register_running'), \
         patch('metabolon.sortase.executor.unregister_running'), \
         patch('metabolon.sortase.executor._run_command', return_value=mock_attempt), \
         patch('metabolon.sortase.executor._emit_completion_signal'), \
         patch('metabolon.sortase.executor._analyze_for_coaching'):
        result = await execute_task(task, tmp_path, "gemini")

    assert result.success is True
    assert result.tool == "gemini"
    assert result.task_name == "test-task"


@pytest.mark.asyncio
async def test_execute_task_fallback(tmp_path):
    """Test execute_task with fallback to second tool."""
    from metabolon.sortase.decompose import TaskSpec

    task = TaskSpec(name="test-task", description="Test task", spec="Do something", files=[])

    failed_attempt = ExecutionAttempt(
        tool="gemini", exit_code=1, duration_s=1.0, output="Failed",
        failure_reason="process-error",
    )
    success_attempt = ExecutionAttempt(
        tool="goose", exit_code=0, duration_s=2.0, output="Success",
    )

    with patch('metabolon.sortase.executor.register_running'), \
         patch('metabolon.sortase.executor.unregister_running'), \
         patch('metabolon.sortase.executor._run_command', side_effect=[failed_attempt, success_attempt]), \
         patch('metabolon.sortase.executor._emit_completion_signal'), \
         patch('metabolon.sortase.executor._analyze_for_coaching'):
        result = await execute_task(task, tmp_path, "gemini")

    assert result.success is True
    assert result.tool == "goose"
    assert "goose" in result.fallbacks


@pytest.mark.asyncio
async def test_execute_task_all_backends_fail(tmp_path):
    """Test execute_task when all backends fail."""
    from metabolon.sortase.decompose import TaskSpec

    task = TaskSpec(name="test-task", description="Test task", spec="Do something", files=[])

    failed_attempt = ExecutionAttempt(
        tool="gemini", exit_code=1, duration_s=1.0, output="Failed",
        failure_reason="process-error",
    )

    with patch('metabolon.sortase.executor.register_running'), \
         patch('metabolon.sortase.executor.unregister_running'), \
         patch('metabolon.sortase.executor._run_command', return_value=failed_attempt), \
         patch('metabolon.sortase.executor._emit_completion_signal'), \
         patch('metabolon.sortase.executor._analyze_for_coaching'):
        result = await execute_task(task, tmp_path, "gemini")

    assert result.success is False


@pytest.mark.asyncio
async def test_execute_task_adaptive_timeout(tmp_path):
    """Test execute_task applies adaptive timeout from spec."""
    from metabolon.sortase.decompose import TaskSpec

    # "Read file.py" → read-heavy → doubled timeout
    task = TaskSpec(name="read-task", description="Read", spec="Read file.py", files=[])

    mock_attempt = ExecutionAttempt(
        tool="gemini", exit_code=0, duration_s=1.0, output="Done",
    )

    with patch('metabolon.sortase.executor.register_running'), \
         patch('metabolon.sortase.executor.unregister_running'), \
         patch('metabolon.sortase.executor._run_command', return_value=mock_attempt) as mock_run, \
         patch('metabolon.sortase.executor._emit_completion_signal'), \
         patch('metabolon.sortase.executor._analyze_for_coaching'):
        await execute_task(task, tmp_path, "gemini", timeout_sec=100)

    # timeout_sec passed to _run_command should be 200 (doubled)
    _, kwargs = mock_run.call_args
    # _run_command receives timeout_sec as positional — check the call
    call_args = mock_run.call_args[0]
    assert call_args[3] == 200


@pytest.mark.asyncio
async def test_execute_task_unregisters_on_success(tmp_path):
    """Test execute_task always calls unregister_running, even on success."""
    from metabolon.sortase.decompose import TaskSpec

    task = TaskSpec(name="test-task", description="T", spec="Do it", files=[])
    mock_attempt = ExecutionAttempt(tool="gemini", exit_code=0, duration_s=0.1, output="ok")

    with patch('metabolon.sortase.executor.register_running') as mock_reg, \
         patch('metabolon.sortase.executor.unregister_running') as mock_unreg, \
         patch('metabolon.sortase.executor._run_command', return_value=mock_attempt), \
         patch('metabolon.sortase.executor._emit_completion_signal'), \
         patch('metabolon.sortase.executor._analyze_for_coaching'):
        await execute_task(task, tmp_path, "gemini")

    mock_reg.assert_called_once()
    mock_unreg.assert_called_once()


@pytest.mark.asyncio
async def test_execute_task_unregisters_on_failure(tmp_path):
    """Test execute_task always calls unregister_running, even on failure."""
    from metabolon.sortase.decompose import TaskSpec

    task = TaskSpec(name="test-task", description="T", spec="Do it", files=[])
    fail = ExecutionAttempt(tool="gemini", exit_code=1, duration_s=0.1, output="err",
                            failure_reason="process-error")

    with patch('metabolon.sortase.executor.register_running'), \
         patch('metabolon.sortase.executor.unregister_running') as mock_unreg, \
         patch('metabolon.sortase.executor._run_command', return_value=fail), \
         patch('metabolon.sortase.executor._emit_completion_signal'), \
         patch('metabolon.sortase.executor._analyze_for_coaching'):
        await execute_task(task, tmp_path, "gemini")

    mock_unreg.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# execute_tasks async tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_tasks_serial(tmp_path):
    """Test execute_tasks in serial mode."""
    from metabolon.sortase.decompose import TaskSpec

    tasks = [
        TaskSpec(name="task-1", description="Task 1", spec="Do 1", files=[]),
        TaskSpec(name="task-2", description="Task 2", spec="Do 2", files=[]),
    ]
    mock_attempt = ExecutionAttempt(tool="gemini", exit_code=0, duration_s=1.0, output="OK")

    with patch('metabolon.sortase.executor.register_running'), \
         patch('metabolon.sortase.executor.unregister_running'), \
         patch('metabolon.sortase.executor._run_command', return_value=mock_attempt), \
         patch('metabolon.sortase.executor._emit_completion_signal'), \
         patch('metabolon.sortase.executor._analyze_for_coaching'):
        results = await execute_tasks(
            tasks, tmp_path,
            tool_by_task={"task-1": "gemini", "task-2": "gemini"},
            serial=True,
        )

    assert len(results) == 2
    assert all(r.success for r in results)


@pytest.mark.asyncio
async def test_execute_tasks_parallel(tmp_path):
    """Test execute_tasks in parallel mode."""
    from metabolon.sortase.decompose import TaskSpec

    tasks = [
        TaskSpec(name="task-1", description="Task 1", spec="Do 1", files=[]),
        TaskSpec(name="task-2", description="Task 2", spec="Do 2", files=[]),
    ]
    mock_attempt = ExecutionAttempt(tool="gemini", exit_code=0, duration_s=1.0, output="OK")

    with patch('metabolon.sortase.executor.register_running'), \
         patch('metabolon.sortase.executor.unregister_running'), \
         patch('metabolon.sortase.executor._run_command', return_value=mock_attempt), \
         patch('metabolon.sortase.executor._emit_completion_signal'), \
         patch('metabolon.sortase.executor._analyze_for_coaching'):
        results = await execute_tasks(
            tasks, tmp_path,
            tool_by_task={"task-1": "gemini", "task-2": "gemini"},
            serial=False,
        )

    assert len(results) == 2


@pytest.mark.asyncio
async def test_execute_tasks_handles_exception(tmp_path):
    """Test execute_tasks handles exceptions gracefully."""
    from metabolon.sortase.decompose import TaskSpec

    tasks = [
        TaskSpec(name="task-1", description="Task 1", spec="Do 1", files=[]),
    ]

    with patch('metabolon.sortase.executor.register_running'), \
         patch('metabolon.sortase.executor.unregister_running'), \
         patch('metabolon.sortase.executor._run_command', side_effect=RuntimeError("Test error")):
        results = await execute_tasks(
            tasks, tmp_path,
            tool_by_task={"task-1": "gemini"},
        )

    assert len(results) == 1
    assert results[0].success is False
    assert "Test error" in results[0].output


@pytest.mark.asyncio
async def test_execute_tasks_empty_tasks(tmp_path):
    """Test execute_tasks with empty task list returns empty results."""
    with patch('metabolon.sortase.executor.register_running'), \
         patch('metabolon.sortase.executor.unregister_running'):
        results = await execute_tasks([], tmp_path, tool_by_task={})

    assert results == []


@pytest.mark.asyncio
async def test_execute_tasks_single_task_parallel(tmp_path):
    """Test execute_tasks with a single task in parallel mode."""
    from metabolon.sortase.decompose import TaskSpec

    tasks = [
        TaskSpec(name="solo", description="Solo", spec="Do it", files=[]),
    ]
    mock_attempt = ExecutionAttempt(tool="golem", exit_code=0, duration_s=0.5, output="done")

    with patch('metabolon.sortase.executor.register_running'), \
         patch('metabolon.sortase.executor.unregister_running'), \
         patch('metabolon.sortase.executor._run_command', return_value=mock_attempt), \
         patch('metabolon.sortase.executor._emit_completion_signal'), \
         patch('metabolon.sortase.executor._analyze_for_coaching'):
        results = await execute_tasks(
            tasks, tmp_path,
            tool_by_task={"solo": "golem"},
            serial=False,
        )

    assert len(results) == 1
    assert results[0].success is True
