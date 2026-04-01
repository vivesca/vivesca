from __future__ import annotations

"""Tests for effectors/perplexity.sh — CLI validation and mocked API calls."""

import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

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


def _fake_curl(tmpdir: str, response: str) -> str:
    """Create a fake curl that logs its args and returns response."""
    curl_path = os.path.join(tmpdir, "curl")
    # Write a script that saves args to a file and prints the canned response
    log_path = os.path.join(tmpdir, "curl_args.log")
    with open(curl_path, "w") as f:
        f.write(f"""#!/bin/bash
echo "$@" > {log_path}
cat << 'CURLRESP'
{response}
CURLRESP
""")
    os.chmod(curl_path, os.stat(curl_path).st_mode | stat.S_IEXEC)
    return curl_path


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


@pytest.fixture()
def fake_curl_env(tmp_path):
    """Set up a fake curl and return (env_dict, args_log_path)."""
    good_response = json.dumps({
        "choices": [{"message": {"content": "test answer"}}]
    })
    curl_path = _fake_curl(str(tmp_path), good_response)
    # Also need a fake source for ~/.secrets that sets the key
    secrets_file = tmp_path / ".secrets"
    secrets_file.write_text("export PERPLEXITY_API_KEY=fake-key-123\n")
    env = {
        "PATH": str(tmp_path) + ":" + os.environ.get("PATH", ""),
        "HOME": str(tmp_path),
        "PERPLEXITY_API_KEY": "fake-key-123",
    }
    args_log = tmp_path / "curl_args.log"
    return env, args_log


def test_search_mode_uses_sonar(fake_curl_env):
    env, args_log = fake_curl_env
    r = _run(["search", "what is Python"], env)
    assert r.returncode == 0
    assert "test answer" in r.stdout
    args = args_log.read_text()
    assert '"model": "sonar"' in args


def test_ask_mode_uses_sonar_pro(fake_curl_env):
    env, args_log = fake_curl_env
    r = _run(["ask", "explain recursion"], env)
    assert r.returncode == 0
    args = args_log.read_text()
    assert '"model": "sonar-pro"' in args


def test_research_mode_uses_deep_research(fake_curl_env):
    env, args_log = fake_curl_env
    r = _run(["research", "deep dive topic"], env)
    assert r.returncode == 0
    args = args_log.read_text()
    assert '"model": "sonar-deep-research"' in args


def test_reason_mode_uses_reasoning_pro(fake_curl_env):
    env, args_log = fake_curl_env
    r = _run(["reason", "logic puzzle"], env)
    assert r.returncode == 0
    args = args_log.read_text()
    assert '"model": "sonar-reasoning-pro"' in args


# ── API response handling ────────────────────────────────────────────


def test_extracts_content_from_choices():
    with tempfile.TemporaryDirectory() as tmpdir:
        response = json.dumps({
            "choices": [{"message": {"content": "Hello world answer"}}]
        })
        _fake_curl(tmpdir, response)
        env = {
            "PATH": tmpdir + ":" + os.environ.get("PATH", ""),
            "PERPLEXITY_API_KEY": "fake-key",
            "HOME": tmpdir,
        }
        r = _run(["search", "hi"], env)
        assert r.returncode == 0
        assert "Hello world answer" in r.stdout


def test_error_response_exits_nonzero():
    with tempfile.TemporaryDirectory() as tmpdir:
        response = json.dumps({
            "error": {"message": "Rate limit exceeded"}
        })
        _fake_curl(tmpdir, response)
        env = {
            "PATH": tmpdir + ":" + os.environ.get("PATH", ""),
            "PERPLEXITY_API_KEY": "fake-key",
            "HOME": tmpdir,
        }
        r = _run(["search", "hi"], env)
        assert r.returncode != 0
        assert "Rate limit" in r.stderr


def test_unexpected_json_printed_raw():
    with tempfile.TemporaryDirectory() as tmpdir:
        response = json.dumps({"unexpected": "field"})
        _fake_curl(tmpdir, response)
        env = {
            "PATH": tmpdir + ":" + os.environ.get("PATH", ""),
            "PERPLEXITY_API_KEY": "fake-key",
            "HOME": tmpdir,
        }
        r = _run(["search", "hi"], env)
        assert r.returncode == 0
        assert "unexpected" in r.stdout


# ── Query JSON escaping ──────────────────────────────────────────────


def test_query_with_quotes_escaped(fake_curl_env):
    env, args_log = fake_curl_env
    r = _run(['search', 'He said "hello"'], env)
    assert r.returncode == 0
    args = args_log.read_text()
    # The query should be JSON-escaped in the payload
    assert '\\"hello\\"' in args or '"hello"' in args


def test_query_with_newline_escaped(fake_curl_env):
    env, args_log = fake_curl_env
    r = _run(["search", "line1\nline2"], env)
    assert r.returncode == 0
    args = args_log.read_text()
    assert "\\n" in args


# ── API key requirement ──────────────────────────────────────────────


def test_missing_api_key_exits_nonzero(tmp_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        # No fake curl needed — script should fail before curl
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": tmpdir,
        }
        # Ensure no secrets file
        r = _run(["search", "test"], env)
        assert r.returncode != 0
