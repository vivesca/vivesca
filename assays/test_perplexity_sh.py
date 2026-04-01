from __future__ import annotations

"""Tests for effectors/perplexity.sh — CLI validation and mocked API calls."""

import json
import os
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

SCRIPT = Path("/home/terry/germline/effectors/perplexity.sh")


def _run(args: list[str], env_extra: dict | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PERPLEXITY_API_KEY", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def _setup_fake_curl(tmpdir: str, response: dict) -> Path:
    """Create a fake curl in tmpdir that logs args and returns JSON response."""
    curl_path = os.path.join(tmpdir, "curl")
    log_path = os.path.join(tmpdir, "curl_args.log")
    response_json = json.dumps(response)
    with open(curl_path, "w") as f:
        f.write(f"#!/bin/bash\necho \"$@\" > {log_path}\necho '{response_json}'\n")
    os.chmod(curl_path, os.stat(curl_path).st_mode | stat.S_IEXEC)
    return Path(log_path)


def _mock_env(tmpdir: str) -> dict:
    """Build an environment dict that uses fake curl and no real secrets."""
    return {
        "PATH": tmpdir + ":" + os.environ.get("PATH", ""),
        "HOME": tmpdir,
        "PERPLEXITY_API_KEY": "fake-key-123",
    }


GOOD_RESPONSE = {"choices": [{"message": {"content": "test answer"}}]}


# ── --help / -h ──────────────────────────────────────────────────────


def test_help_long_flag_exits_zero():
    r = _run(["--help"])
    assert r.returncode == 0
    assert "search" in r.stdout
    assert "ask" in r.stdout


def test_help_short_flag_exits_zero():
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Modes:" in r.stdout or "search" in r.stdout


# ── Missing / bad arguments ──────────────────────────────────────────


def test_no_args_exits_1():
    r = _run([])
    assert r.returncode != 0
    assert "Usage" in r.stderr


def test_unknown_mode_exits_1():
    r = _run(["explode", "test query"])
    assert r.returncode != 0
    assert "Unknown mode" in r.stderr


def test_missing_query_exits_1():
    r = _run(["search"])
    assert r.returncode != 0


# ── Mode-to-model mapping (via mocked curl) ─────────────────────────


def test_search_mode_uses_sonar():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        r = _run(["search", "what is Python"], _mock_env(tmpdir))
        assert r.returncode == 0
        assert "test answer" in r.stdout
        assert '"model": "sonar"' in log.read_text()


def test_ask_mode_uses_sonar_pro():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        r = _run(["ask", "explain recursion"], _mock_env(tmpdir))
        assert r.returncode == 0
        assert '"model": "sonar-pro"' in log.read_text()


def test_research_mode_uses_deep_research():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        r = _run(["research", "deep dive topic"], _mock_env(tmpdir))
        assert r.returncode == 0
        assert '"model": "sonar-deep-research"' in log.read_text()


def test_reason_mode_uses_reasoning_pro():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        r = _run(["reason", "logic puzzle"], _mock_env(tmpdir))
        assert r.returncode == 0
        assert '"model": "sonar-reasoning-pro"' in log.read_text()


# ── API response handling ────────────────────────────────────────────


def test_extracts_content_from_choices():
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_fake_curl(tmpdir, {"choices": [{"message": {"content": "Hello world answer"}}]})
        r = _run(["search", "hi"], _mock_env(tmpdir))
        assert r.returncode == 0
        assert "Hello world answer" in r.stdout


def test_error_response_exits_nonzero():
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_fake_curl(tmpdir, {"error": {"message": "Rate limit exceeded"}})
        r = _run(["search", "hi"], _mock_env(tmpdir))
        assert r.returncode != 0
        assert "Rate limit" in r.stderr


def test_unexpected_json_printed_raw():
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_fake_curl(tmpdir, {"unexpected": "field"})
        r = _run(["search", "hi"], _mock_env(tmpdir))
        assert r.returncode == 0
        assert "unexpected" in r.stdout


# ── Query JSON escaping ──────────────────────────────────────────────


def test_query_with_quotes_escaped():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        r = _run(["search", 'He said "hello"'], _mock_env(tmpdir))
        assert r.returncode == 0
        args = log.read_text()
        # Query with embedded quotes should be JSON-escaped
        assert '\\"hello\\"' in args or '"hello"' in args


def test_query_with_newline_escaped():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        r = _run(["search", "line1\nline2"], _mock_env(tmpdir))
        assert r.returncode == 0
        args = log.read_text()
        assert "\\n" in args


# ── API key requirement ──────────────────────────────────────────────


def test_missing_api_key_exits_nonzero():
    with tempfile.TemporaryDirectory() as tmpdir:
        r = _run(["search", "test"], {"HOME": tmpdir, "PATH": os.environ.get("PATH", "")})
        assert r.returncode != 0


# ── curl receives correct endpoint and headers ───────────────────────


def test_curl_receives_api_url():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        _run(["search", "hi"], _mock_env(tmpdir))
        args = log.read_text()
        assert "https://api.perplexity.ai/chat/completions" in args


def test_curl_receives_bearer_auth():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        _run(["search", "hi"], _mock_env(tmpdir))
        args = log.read_text()
        assert "Authorization: Bearer fake-key-123" in args


# ── Content-Type header ──────────────────────────────────────────────


def test_curl_sends_content_type_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        _run(["search", "hi"], _mock_env(tmpdir))
        args = log.read_text()
        assert "Content-Type: application/json" in args


# ── Request body structure ────────────────────────────────────────────


def test_request_body_contains_messages_array():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        _run(["search", "test question"], _mock_env(tmpdir))
        args = log.read_text()
        assert '"messages"' in args
        assert '"role": "user"' in args
        assert '"content": "test question"' in args


def test_request_body_is_valid_json():
    """The -d payload embedded by the script should be parseable JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        _run(["search", "simple query"], _mock_env(tmpdir))
        args = log.read_text()
        import re

        # The fake curl receives: -d { ... }  (bash strips the wrapping quotes)
        match = re.search(r"-d\s+(\{.*\})", args, re.DOTALL)
        assert match, f"Could not find -d JSON payload in curl args: {args}"
        payload = json.loads(match.group(1).strip())
        assert payload["model"] == "sonar"
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][0]["content"] == "simple query"


# ── Additional query escaping ─────────────────────────────────────────


def test_query_with_backslash():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        r = _run(["search", "path\\to\\file"], _mock_env(tmpdir))
        assert r.returncode == 0
        args = log.read_text()
        assert "path" in args


def test_query_with_dollar_sign():
    """Shell metacharacters in query should not cause script errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        r = _run(["search", "cost is $5"], _mock_env(tmpdir))
        assert r.returncode == 0


def test_query_with_single_quotes():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        r = _run(["search", "it's a test"], _mock_env(tmpdir))
        assert r.returncode == 0


def test_query_with_unicode():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        r = _run(["search", "日本語テスト"], _mock_env(tmpdir))
        assert r.returncode == 0


# ── Usage message content ─────────────────────────────────────────────


def test_help_lists_all_modes():
    r = _run(["--help"])
    assert r.returncode == 0
    for mode in ("search", "ask", "research", "reason"):
        assert mode in r.stdout


def test_help_shows_models():
    r = _run(["--help"])
    assert r.returncode == 0
    # The help text is extracted from lines 2-11 of the script which mentions model names
    output = r.stdout
    assert "sonar" in output or "Modes" in output


# ── Additional mode validation ────────────────────────────────────────


def test_case_sensitive_mode():
    """Modes should be case-sensitive — 'Search' is not valid."""
    r = _run(["Search", "test"])
    assert r.returncode != 0
    assert "Unknown mode" in r.stderr


def test_partial_mode_name_invalid():
    r = _run(["researc", "test"])
    assert r.returncode != 0
    assert "Unknown mode" in r.stderr


# ── Response edge cases ───────────────────────────────────────────────


def test_empty_content_in_choices():
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_fake_curl(tmpdir, {"choices": [{"message": {"content": ""}}]})
        r = _run(["search", "hi"], _mock_env(tmpdir))
        assert r.returncode == 0


def test_error_response_without_message_field():
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_fake_curl(tmpdir, {"error": {"status": 429}})
        r = _run(["search", "hi"], _mock_env(tmpdir))
        assert r.returncode != 0


def test_curl_silence_flag():
    """The script uses curl -sS (silent but show errors)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = _setup_fake_curl(tmpdir, GOOD_RESPONSE)
        _run(["search", "hi"], _mock_env(tmpdir))
        args = log.read_text()
        assert "-sS" in args
