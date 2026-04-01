from __future__ import annotations

"""Tests for effectors/perplexity.sh — Perplexity API CLI wrapper.

Tests use subprocess.run (effectors are scripts, not importable modules).
API-dependent tests mock curl via a wrapper on PATH.
"""

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "perplexity.sh"


def _run(args: list[str], env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run perplexity.sh with optional extra env vars."""
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


def _make_curl_mock(response_body: str) -> str:
    """Create a temporary script that mocks curl and prints response_body to stdout."""
    tmpdir = tempfile.mkdtemp()
    curl_path = os.path.join(tmpdir, "curl")
    with open(curl_path, "w") as f:
        f.write(f"#!/bin/bash\n# mock curl\necho '{response_body}'\n")
    os.chmod(curl_path, os.stat(curl_path).st_mode | stat.S_IEXEC)
    return tmpdir


# ── Help / usage ──────────────────────────────────────────────────────


class TestHelp:
    def test_help_long_flag(self):
        r = _run(["--help"])
        assert r.returncode == 0
        assert "Perplexity" in r.stdout or "search" in r.stdout

    def test_help_short_flag(self):
        r = _run(["-h"])
        assert r.returncode == 0
        assert "search" in r.stdout


# ── Missing arguments ─────────────────────────────────────────────────


class TestMissingArgs:
    def test_no_args_exits_1(self):
        r = _run([])
        assert r.returncode != 0
        assert "Usage" in r.stderr

    def test_mode_without_query_exits_1(self):
        r = _run(["search"])
        assert r.returncode != 0

    def test_empty_query_exits_1(self):
        r = _run(["search", ""])
        assert r.returncode != 0


# ── Invalid mode ──────────────────────────────────────────────────────


class TestInvalidMode:
    def test_unknown_mode_exits_1(self):
        r = _run(["teleport", "hello world"])
        assert r.returncode != 0
        assert "Unknown mode" in r.stderr

    def test_unknown_mode_suggests_valid(self):
        r = _run(["foobar", "test"])
        assert r.returncode != 0
        assert "search" in r.stderr


# ── Mode validation (no API key needed) ───────────────────────────────


class TestModeValidation:
    """Modes that are valid should get past the mode check and fail at API key."""

    @pytest.mark.parametrize("mode", ["search", "ask", "research", "reason"])
    def test_valid_modes_pass_mode_check(self, mode):
        r = _run([mode, "test query"])
        # Should fail at API key stage, not at mode validation
        assert "Unknown mode" not in r.stderr


# ── API key requirement ───────────────────────────────────────────────


class TestApiKey:
    def test_missing_api_key_exits_nonzero(self):
        r = _run(["search", "hello"])
        assert r.returncode != 0

    def test_missing_api_key_error_message(self):
        r = _run(["ask", "what is 2+2"])
        # Error about missing key
        assert "PERPLEXITY_API_KEY" in r.stderr or r.returncode != 0


# ── JSON response parsing (mocked curl) ───────────────────────────────


class TestJsonParsing:
    """Mock curl to test the response parsing pipeline."""

    def test_extracts_choices_content(self):
        payload = json.dumps({
            "choices": [{"message": {"content": "The sky is blue."}}]
        })
        mock_dir = _make_curl_mock(payload.replace("'", "'\\''"))
        env = {
            "PERPLEXITY_API_KEY": "test-key-123",
            "PATH": mock_dir + ":" + os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/home/terry"),
        }
        r = _run(["search", "why is the sky blue"], env_extra=env)
        assert r.returncode == 0
        assert "The sky is blue." in r.stdout

    def test_api_error_returns_nonzero(self):
        payload = json.dumps({
            "error": {"message": "Rate limit exceeded"}
        })
        mock_dir = _make_curl_mock(payload.replace("'", "'\\''"))
        env = {
            "PERPLEXITY_API_KEY": "test-key-123",
            "PATH": mock_dir + ":" + os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/home/terry"),
        }
        r = _run(["search", "test"], env_extra=env)
        assert r.returncode != 0
        assert "Rate limit" in r.stderr

    def test_unexpected_json_prints_raw(self):
        payload = json.dumps({"id": "abc", "data": [1, 2, 3]})
        mock_dir = _make_curl_mock(payload.replace("'", "'\\''"))
        env = {
            "PERPLEXITY_API_KEY": "test-key-123",
            "PATH": mock_dir + ":" + os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/home/terry"),
        }
        r = _run(["ask", "test"], env_extra=env)
        assert r.returncode == 0
        assert "abc" in r.stdout

    def test_non_json_response_passthrough(self):
        mock_dir = _make_curl_mock("This is plain text, not JSON")
        env = {
            "PERPLEXITY_API_KEY": "test-key-123",
            "PATH": mock_dir + ":" + os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/home/terry"),
        }
        r = _run(["reason", "test"], env_extra=env)
        # The python parser catches the exception, prints raw text
        assert "plain text" in r.stdout


# ── Mode to model mapping (via curl mock inspecting args) ─────────────


class TestModeToModel:
    """Verify that each mode maps to the correct model by inspecting curl args."""

    def _run_with_arg_capturing_curl(self, mode: str, query: str) -> list[str]:
        """Create a curl mock that captures its own arguments."""
        tmpdir = tempfile.mkdtemp()
        curl_path = os.path.join(tmpdir, "curl")
        capture_path = os.path.join(tmpdir, "captured_args.txt")
        mock_response = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        # Write a mock curl that saves args and returns a valid API response
        with open(curl_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f'echo "$@" > {capture_path}\n')
            f.write(f"echo '{mock_response}'\n")
        os.chmod(curl_path, os.stat(curl_path).st_mode | stat.S_IEXEC)
        env = {
            "PERPLEXITY_API_KEY": "test-key-123",
            "PATH": tmpdir + ":" + os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/home/terry"),
        }
        r = _run([mode, query], env_extra=env)
        assert r.returncode == 0, f"Script failed: {r.stderr}"
        with open(capture_path) as f:
            return f.read()

    @pytest.mark.parametrize("mode,expected_model", [
        ("search", "sonar"),
        ("ask", "sonar-pro"),
        ("research", "sonar-deep-research"),
        ("reason", "sonar-reasoning-pro"),
    ])
    def test_mode_maps_to_model(self, mode, expected_model):
        args = self._run_with_arg_capturing_curl(mode, "test query")
        assert expected_model in args, f"Expected {expected_model} in curl args, got: {args}"
