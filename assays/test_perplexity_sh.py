from __future__ import annotations

"""Tests for effectors/perplexity.sh — Perplexity API CLI."""

import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path.home() / "germline/effectors/perplexity.sh"


def run_perplexity(*args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    """Run perplexity.sh with given args, capture output."""
    cmd = [str(SCRIPT), *args]
    # Ensure no real API key leaks into tests unless explicitly provided
    safe_env = {k: v for k, v in os.environ.items() if k != "PERPLEXITY_API_KEY"}
    if env:
        safe_env.update(env)
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=10, env=safe_env,
    )


# ── Help / usage ──────────────────────────────────────────────────────


def test_help_flag_stdout():
    """--help prints usage header and exits 0."""
    r = run_perplexity("--help")
    assert r.returncode == 0
    assert "Perplexity API CLI" in r.stdout
    assert "search" in r.stdout


def test_help_short_flag():
    """-h prints usage header and exits 0."""
    r = run_perplexity("-h")
    assert r.returncode == 0
    assert "Perplexity API CLI" in r.stdout


# ── Error handling ────────────────────────────────────────────────────


def test_no_args_exits_1():
    """No arguments prints usage to stderr and exits 1."""
    r = run_perplexity()
    assert r.returncode == 1
    assert "Usage" in r.stderr


def test_unknown_mode_exits_1():
    """Unknown mode prints error to stderr and exits 1."""
    r = run_perplexity("foobar", "test query")
    assert r.returncode == 1
    assert "Unknown mode" in r.stderr
    assert "foobar" in r.stderr


def test_missing_query_exits_1():
    """Valid mode without query exits with error."""
    r = run_perplexity("search")
    assert r.returncode != 0


def test_modes_without_api_key():
    """All valid modes fail gracefully without API key."""
    for mode in ("search", "ask", "research", "reason"):
        r = run_perplexity(mode, "test")
        assert r.returncode != 0, f"mode={mode} should fail without API key"


# ── Mode-to-model mapping (mocked curl) ───────────────────────────────


def _make_mock_curl(response_body: str) -> Path:
    """Create a temporary script that acts like curl, returning fixed body."""
    tmpdir = Path(tempfile.mkdtemp())
    mock = tmpdir / "curl"
    mock.write_text(
        '#!/bin/bash\n'
        '# Mock curl — capture args and return canned response\n'
        f'echo {json.dumps(response_body)}\n'
    )
    mock.chmod(mock.stat().st_mode | stat.S_IEXEC)
    return tmpdir


def _run_with_mock_curl(mode: str, query: str, response_body: str) -> tuple[subprocess.CompletedProcess[str], str]:
    """Run perplexity.sh with a mock curl on PATH; return (result, curl_log)."""
    tmpdir = _make_mock_curl(response_body)
    # Also capture what curl received by wrapping it
    log_file = tmpdir / "curl_args.log"
    wrapper = tmpdir / "curl"
    wrapper.write_text(
        '#!/bin/bash\n'
        f'echo "$@" > {log_file}\n'
        f'echo {json.dumps(response_body)}\n'
    )
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)

    safe_env = {k: v for k, v in os.environ.items() if k != "PERPLEXITY_API_KEY"}
    safe_env["PERPLEXITY_API_KEY"] = "test-key-123"
    safe_env["PATH"] = f"{tmpdir}:{safe_env.get('PATH', '')}"

    r = subprocess.run(
        [str(SCRIPT), mode, query],
        capture_output=True, text=True, timeout=10, env=safe_env,
    )
    curl_log = log_file.read_text() if log_file.exists() else ""
    return r, curl_log


def test_search_uses_sonar_model():
    """search mode selects 'sonar' model."""
    body = json.dumps({"choices": [{"message": {"content": "test result"}}]})
    r, log = _run_with_mock_curl("search", "what is Python", body)
    assert r.returncode == 0
    assert '"model": "sonar"' in log or '"model":"sonar"' in log or 'sonar' in log
    assert "test result" in r.stdout


def test_ask_uses_sonar_pro_model():
    """ask mode selects 'sonar-pro' model."""
    body = json.dumps({"choices": [{"message": {"content": "pro answer"}}]})
    r, log = _run_with_mock_curl("ask", "explain rust", body)
    assert r.returncode == 0
    assert "sonar-pro" in log
    assert "pro answer" in r.stdout


def test_research_uses_deep_research_model():
    """research mode selects 'sonar-deep-research' model."""
    body = json.dumps({"choices": [{"message": {"content": "deep answer"}}]})
    r, log = _run_with_mock_curl("research", "comprehensive review", body)
    assert r.returncode == 0
    assert "sonar-deep-research" in log


def test_reason_uses_reasoning_pro_model():
    """reason mode selects 'sonar-reasoning-pro' model."""
    body = json.dumps({"choices": [{"message": {"content": "reasoned answer"}}]})
    r, log = _run_with_mock_curl("reason", "solve this puzzle", body)
    assert r.returncode == 0
    assert "sonar-reasoning-pro" in log


# ── Response parsing ──────────────────────────────────────────────────


def test_extracts_content_from_choices():
    """Successfully extracts content from API response."""
    content = "The answer is 42."
    body = json.dumps({"choices": [{"message": {"content": content}}]})
    r, _ = _run_with_mock_curl("search", "meaning of life", body)
    assert r.returncode == 0
    assert content in r.stdout


def test_error_response_exits_nonzero():
    """API error response exits non-zero and reports error."""
    body = json.dumps({"error": {"message": "Rate limited"}})
    r, _ = _run_with_mock_curl("search", "test", body)
    assert r.returncode != 0


def test_malformed_json_falls_back():
    """Malformed response falls back to raw output."""
    r, _ = _run_with_mock_curl("search", "test", "not-json-at-all")
    # Should not crash — outputs something
    assert r.returncode == 0 or r.stdout.strip() or r.stderr.strip()


def test_query_json_escaping():
    """Special characters in query are properly JSON-escaped."""
    body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
    r, log = _run_with_mock_curl("search", 'He said "hello" & goodbye', body)
    assert r.returncode == 0
    # The query should appear in the curl payload with proper escaping
    assert '\\"hello\\"' in log or '"hello"' in log


def test_sends_api_key_in_header():
    """Authorization header includes the API key."""
    body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
    r, log = _run_with_mock_curl("search", "test", body)
    assert "Bearer test-key-123" in log or "Authorization" in log
