"""Tests for sortase executor."""
from __future__ import annotations

from unittest.mock import patch

from metabolon.sortase.executor import (
    ExecutionAttempt,
    TaskExecutionResult,
    _clean_env,
    _prepend_coaching,
    _tool_chain,
    classify_failure,
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


def test_clean_env_goose_removes_google_keys():
    import os
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "x", "GEMINI_API_KEY": "y"}):
        env = _clean_env("goose")
    assert "GOOGLE_API_KEY" not in env
    assert "GEMINI_API_KEY" not in env


def test_clean_env_cc_glm_sets_zhipu():
    import os
    with patch.dict(os.environ, {"ZHIPU_API_KEY": "test-key"}):
        env = _clean_env("cc-glm")
    assert env["ANTHROPIC_API_KEY"] == "test-key"
    assert "z.ai" in env["ANTHROPIC_BASE_URL"]


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
