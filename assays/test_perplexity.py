from __future__ import annotations

"""Tests for effectors/perplexity.sh — Perplexity API CLI wrapper.

Covers: help, usage errors, mode validation, mode-to-model mapping,
JSON query escaping, response parsing (success and error).
"""

import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline" / "effectors" / "perplexity.sh"


def _make_fake_curl(tmpdir: Path, response_body: str) -> Path:
    """Create a fake curl that writes the request body to a file and returns response_body."""
    fake = tmpdir / "curl"
    capture = tmpdir / "captured_request.json"
    fake.write_text(
        f"""#!/usr/bin/env bash
# Capture the -d argument (the request body)
while [ "$#" -gt 0 ]; do
    case "$1" in
        -d) shift; echo -n "$1" > {capture}; shift ;;
        *) shift ;;
    esac
done
echo -n {json.dumps(response_body)}
"""
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return fake


def _run(*args, env_extra: dict | None = None, timeout: int = 15) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PERPLEXITY_API_KEY"] = "test-key-12345"
    # Prevent sourcing real ~/.secrets from interfering
    env["HOME"] = "/nonexistent-home-for-test"
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [str(SCRIPT)] + list(args),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def _run_with_fake_curl(
    tmpdir: Path, mode: str, query: str, response_body: str
) -> tuple[subprocess.CompletedProcess, dict]:
    """Run perplexity.sh with a fake curl; return (proc, captured_request)."""
    fake_curl = _make_fake_curl(tmpdir, response_body)
    env_extra = {"PATH": f"{tmpdir}:{os.environ.get('PATH', '')}"}
    proc = _run(mode, query, env_extra=env_extra)
    captured = tmpdir / "captured_request.json"
    request = json.loads(captured.read_text()) if captured.exists() else {}
    return proc, request


# ── Help and usage ───────────────────────────────────────────────────


class TestHelp:
    def test_long_help(self):
        r = _run("--help")
        assert r.returncode == 0
        assert "Usage" in r.stdout or "perplexity" in r.stdout

    def test_short_help(self):
        r = _run("-h")
        assert r.returncode == 0
        assert "Usage" in r.stdout or "perplexity" in r.stdout


class TestUsageErrors:
    def test_no_args_exits_1(self):
        r = _run()
        assert r.returncode != 0
        assert "Usage" in r.stderr

    def test_missing_query_exits_1(self):
        r = _run("search")
        assert r.returncode != 0

    def test_unknown_mode_exits_1(self):
        r = _run("telepath", "hello world")
        assert r.returncode != 0
        assert "Unknown mode" in r.stderr


# ── Mode-to-model mapping ───────────────────────────────────────────


class TestModeMapping:
    @pytest.mark.parametrize(
        "mode,expected_model",
        [
            ("search", "sonar"),
            ("ask", "sonar-pro"),
            ("research", "sonar-deep-research"),
            ("reason", "sonar-reasoning-pro"),
        ],
    )
    def test_mode_maps_to_correct_model(self, tmp_path, mode, expected_model):
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        proc, request = _run_with_fake_curl(tmp_path, mode, "test query", body)
        assert proc.returncode == 0
        assert request.get("model") == expected_model

    def test_query_passed_through(self, tmp_path):
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        proc, request = _run_with_fake_curl(tmp_path, "search", "what is life?", body)
        assert proc.returncode == 0
        messages = request.get("messages", [])
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "what is life?"


# ── Response parsing ────────────────────────────────────────────────


class TestResponseParsing:
    def test_extracts_content_from_choices(self, tmp_path):
        content = "Paris is the capital of France."
        body = json.dumps({"choices": [{"message": {"content": content}}]})
        proc, _ = _run_with_fake_curl(tmp_path, "search", "capital of france", body)
        assert proc.returncode == 0
        assert content in proc.stdout

    def test_multiline_content(self, tmp_path):
        content = "Line 1\nLine 2\nLine 3"
        body = json.dumps({"choices": [{"message": {"content": content}}]})
        proc, _ = _run_with_fake_curl(tmp_path, "ask", "multi", body)
        assert proc.returncode == 0
        assert "Line 1" in proc.stdout
        assert "Line 3" in proc.stdout

    def test_error_response_exits_nonzero(self, tmp_path):
        body = json.dumps({"error": {"message": "Rate limit exceeded"}})
        proc, _ = _run_with_fake_curl(tmp_path, "search", "test", body)
        assert proc.returncode != 0
        assert "Rate limit" in proc.stderr

    def test_unexpected_json_dumped_as_is(self, tmp_path):
        """When response has no 'choices' or 'error', dump raw JSON."""
        body = json.dumps({"weird": "structure", "foo": 42})
        proc, _ = _run_with_fake_curl(tmp_path, "search", "test", body)
        assert proc.returncode == 0
        assert "weird" in proc.stdout


# ── API key requirement ─────────────────────────────────────────────


class TestAPIKey:
    def test_missing_api_key_exits_nonzero(self):
        r = subprocess.run(
            [str(SCRIPT), "search", "test"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**{k: v for k, v in os.environ.items() if k != "PERPLEXITY_API_KEY"},
                 "HOME": "/nonexistent-home-for-test"},
        )
        assert r.returncode != 0


# ── JSON query escaping ─────────────────────────────────────────────


class TestQueryEscaping:
    def test_query_with_quotes_escaped(self, tmp_path):
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        proc, request = _run_with_fake_curl(tmp_path, "search", 'He said "hello"', body)
        assert proc.returncode == 0
        assert request["messages"][0]["content"] == 'He said "hello"'

    def test_query_with_special_chars(self, tmp_path):
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        proc, request = _run_with_fake_curl(tmp_path, "search", "price: $5 & <tag>", body)
        assert proc.returncode == 0
        assert request["messages"][0]["content"] == "price: $5 & <tag>"
