"""Tests for effectors/perplexity.sh — bash script tested via subprocess."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "perplexity.sh"


def _run(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    """Run perplexity.sh with optional custom env."""
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        ["bash", str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        env=run_env,
        timeout=30,
    )


# ── help/usage tests ────────────────────────────────────────────────────────


class TestHelp:
    def test_help_flag_exits_zero(self):
        r = _run(["--help"])
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run(["--help"])
        assert "search" in r.stdout
        assert "ask" in r.stdout
        assert "research" in r.stdout
        assert "reason" in r.stdout

    def test_h_flag_exits_zero(self):
        r = _run(["-h"])
        assert r.returncode == 0

    def test_help_shows_models(self):
        r = _run(["--help"])
        assert "sonar" in r.stdout.lower()


# ── missing arguments tests ───────────────────────────────────────────────────


class TestMissingArgs:
    def test_no_args_exits_1(self):
        r = _run([])
        assert r.returncode == 1

    def test_no_args_shows_usage(self):
        r = _run([])
        assert "Usage" in r.stderr

    def test_mode_only_missing_query_exits_1(self):
        r = _run(["search"])
        assert r.returncode == 1

    def test_mode_only_missing_query_message(self):
        r = _run(["search"])
        assert "Missing query" in r.stderr


# ── invalid mode tests ────────────────────────────────────────────────────────


class TestInvalidMode:
    def test_invalid_mode_exits_1(self):
        r = _run(["invalid", "test query"])
        assert r.returncode == 1

    def test_invalid_mode_shows_error(self):
        r = _run(["invalid", "test query"])
        assert "Unknown mode" in r.stderr

    def test_invalid_mode_suggests_valid_modes(self):
        r = _run(["invalid", "test query"])
        assert "search|ask|research|reason" in r.stderr


# ── mode validation (no API key needed for these) ─────────────────────────────


class TestModeValidation:
    def test_search_mode_requires_api_key(self):
        """search mode exits if no API key is set."""
        r = _run(["search", "test query"])
        # Script will fail because no PERPLEXITY_API_KEY
        assert r.returncode == 1

    def test_ask_mode_requires_api_key(self):
        r = _run(["ask", "test query"])
        assert r.returncode == 1

    def test_research_mode_requires_api_key(self):
        r = _run(["research", "test query"])
        assert r.returncode == 1

    def test_reason_mode_requires_api_key(self):
        r = _run(["reason", "test query"])
        assert r.returncode == 1


# ── API error handling (mocked curl) ─────────────────────────────────────────


class TestAPIResponse:
    def test_api_error_shows_message(self, tmp_path, monkeypatch):
        """API error response is shown in stderr."""
        # Create a mock curl that returns an error
        mock_curl = tmp_path / "mock_curl.sh"
        mock_curl.write_text(
            '#!/bin/bash\necho \'{"error": {"message": "Rate limit exceeded"}}\''
        )
        mock_curl.chmod(0o755)

        # Create mock secrets file
        secrets = tmp_path / ".secrets"
        secrets.write_text("export PERPLEXITY_API_KEY=test-key-123\n")

        env = {
            "HOME": str(tmp_path),
            "PATH": str(tmp_path) + ":" + os.environ.get("PATH", ""),
        }

        # Run with mock curl in PATH
        r = subprocess.run(
            ["bash", str(SCRIPT), "search", "test query"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        # Should exit with error
        assert r.returncode == 1
        assert "Rate limit exceeded" in r.stderr

    def test_successful_response_extracts_content(self, tmp_path):
        """Successful API response extracts content field."""
        # Create a mock curl that returns a valid response
        mock_curl = tmp_path / "mock_curl.sh"
        mock_curl.write_text(
            '#!/bin/bash\necho \'{"choices": [{"message": {"content": "This is the answer"}}"]}\''
        )
        mock_curl.chmod(0o755)

        # Create mock secrets file
        secrets = tmp_path / ".secrets"
        secrets.write_text("export PERPLEXITY_API_KEY=test-key-123\n")

        env = {
            "HOME": str(tmp_path),
            "PATH": str(tmp_path) + ":" + os.environ.get("PATH", ""),
        }

        r = subprocess.run(
            ["bash", str(SCRIPT), "search", "test query"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        assert r.returncode == 0
        assert "This is the answer" in r.stdout

    def test_malformed_response_falls_back(self, tmp_path):
        """Malformed JSON response is passed through."""
        mock_curl = tmp_path / "mock_curl.sh"
        mock_curl.write_text('#!/bin/bash\necho "not json at all"')
        mock_curl.chmod(0o755)

        secrets = tmp_path / ".secrets"
        secrets.write_text("export PERPLEXITY_API_KEY=test-key-123\n")

        env = {
            "HOME": str(tmp_path),
            "PATH": str(tmp_path) + ":" + os.environ.get("PATH", ""),
        }

        r = subprocess.run(
            ["bash", str(SCRIPT), "search", "test query"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        # Falls back to raw output
        assert "not json at all" in r.stdout


# ── JSON escaping tests ─────────────────────────────────────────────────────


class TestJSONEscaping:
    def test_query_with_quotes_escaped(self, tmp_path):
        """Query with quotes is properly escaped for JSON."""
        # We'll check that the script runs without JSON parse errors
        # by using a mock curl that echoes the received data
        mock_curl = tmp_path / "mock_curl.sh"
        mock_curl.write_text(
            """#!/bin/bash
# Echo the request body to verify JSON escaping
cat
echo '{"choices": [{"message": {"content": "ok"}}]}'
"""
        )
        mock_curl.chmod(0o755)

        secrets = tmp_path / ".secrets"
        secrets.write_text("export PERPLEXITY_API_KEY=test-key-123\n")

        env = {
            "HOME": str(tmp_path),
            "PATH": str(tmp_path) + ":" + os.environ.get("PATH", ""),
        }

        # Query with quotes should not break JSON parsing
        r = subprocess.run(
            ["bash", str(SCRIPT), "search", 'what is "artificial intelligence"'],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        assert r.returncode == 0
        assert "ok" in r.stdout

    def test_query_with_newlines_handled(self, tmp_path):
        """Query with newlines is properly escaped."""
        mock_curl = tmp_path / "mock_curl.sh"
        mock_curl.write_text(
            '#!/bin/bash\necho \'{"choices": [{"message": {"content": "ok"}}]}\''
        )
        mock_curl.chmod(0o755)

        secrets = tmp_path / ".secrets"
        secrets.write_text("export PERPLEXITY_API_KEY=test-key-123\n")

        env = {
            "HOME": str(tmp_path),
            "PATH": str(tmp_path) + ":" + os.environ.get("PATH", ""),
        }

        # Query with newline
        r = subprocess.run(
            ["bash", str(SCRIPT), "search", "line1\nline2"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        assert r.returncode == 0


# ── model mapping verification ───────────────────────────────────────────────


class TestModelMapping:
    """Verify that modes map to correct models via curl request body."""

    def _capture_model(self, tmp_path, mode: str) -> str | None:
        """Run script and capture the model from curl request."""
        mock_curl = tmp_path / "mock_curl.sh"
        # This mock saves stdin to a file for inspection
        mock_curl.write_text(
            """#!/bin/bash
cat > /tmp/curl_input.json
echo '{"choices": [{"message": {"content": "test"}}]}'
"""
        )
        mock_curl.chmod(0o755)

        secrets = tmp_path / ".secrets"
        secrets.write_text("export PERPLEXITY_API_KEY=test-key-123\n")

        env = {
            "HOME": str(tmp_path),
            "PATH": str(tmp_path) + ":" + os.environ.get("PATH", ""),
        }

        subprocess.run(
            ["bash", str(SCRIPT), mode, "test query"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        # Read the captured curl input
        try:
            with open("/tmp/curl_input.json") as f:
                data = json.load(f)
                return data.get("model")
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def test_search_uses_sonar_model(self, tmp_path):
        model = self._capture_model(tmp_path, "search")
        assert model == "sonar"

    def test_ask_uses_sonar_pro_model(self, tmp_path):
        model = self._capture_model(tmp_path, "ask")
        assert model == "sonar-pro"

    def test_research_uses_deep_research_model(self, tmp_path):
        model = self._capture_model(tmp_path, "research")
        assert model == "sonar-deep-research"

    def test_reason_uses_reasoning_pro_model(self, tmp_path):
        model = self._capture_model(tmp_path, "reason")
        assert model == "sonar-reasoning-pro"
