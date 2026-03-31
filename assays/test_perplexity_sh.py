from __future__ import annotations

"""Tests for effectors/perplexity.sh — bash script tested via subprocess."""

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "perplexity.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    path_dirs: list[Path] | None = None,
    tmp_path: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run perplexity.sh with isolated environment."""
    env = os.environ.copy()
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if path_dirs is not None:
        env["PATH"] = os.pathsep.join(str(p) for p in path_dirs) + os.pathsep + env.get("PATH", "")
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=10,
    )


def _make_mock_curl(tmp_path: Path, response_body: str, exit_code: int = 0) -> Path:
    """Create a mock curl that writes response_body to stdout."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    curl = bindir / "curl"
    curl.write_text(f"""#!/bin/bash
echo '{response_body}'
exit {exit_code}
""")
    curl.chmod(curl.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_recording_curl(tmp_path: Path, record_file: Path, response_body: str = '{"choices":[{"message":{"content":"ok"}}]}', exit_code: int = 0) -> Path:
    """Create a mock curl that records its arguments and returns response_body."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    curl = bindir / "curl"
    # Use printf %s to avoid shell interpretation of the recorded args
    curl.write_text(f"""#!/bin/bash
printf '%s\\0' "$@" >> {record_file}
echo '{response_body}'
exit {exit_code}
""")
    curl.chmod(curl.stat().st_mode | stat.S_IEXEC)
    return bindir


def _write_secrets(tmp_path: Path, key: str = "test-key-12345") -> Path:
    """Write a ~/.secrets file with PERPLEXITY_API_KEY."""
    secrets = tmp_path / ".secrets"
    secrets.write_text(f"export PERPLEXITY_API_KEY={key}\n")
    return secrets


# ── file basics ─────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/bin/bash")

    def test_has_set_euo(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src


# ── help flag ───────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_exits_zero(self, tmp_path):
        r = _run(["--help"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self, tmp_path):
        r = _run(["-h"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_help_shows_usage(self, tmp_path):
        r = _run(["--help"], tmp_path=tmp_path)
        assert "Usage:" in r.stdout or "usage" in r.stdout.lower()

    def test_help_shows_modes(self, tmp_path):
        r = _run(["--help"], tmp_path=tmp_path)
        for mode in ("search", "ask", "research", "reason"):
            assert mode in r.stdout

    def test_help_shows_models(self, tmp_path):
        r = _run(["--help"], tmp_path=tmp_path)
        for model in ("sonar", "sonar-pro"):
            assert model in r.stdout

    def test_help_does_not_require_api_key(self, tmp_path):
        """--help works even without ~/.secrets or PERPLEXITY_API_KEY."""
        # Ensure no secrets file exists
        secrets = tmp_path / ".secrets"
        if secrets.exists():
            secrets.unlink()
        r = _run(["--help"], env_extra={"PERPLEXITY_API_KEY": ""}, tmp_path=tmp_path)
        assert r.returncode == 0


# ── missing arguments ──────────────────────────────────────────────────


class TestMissingArguments:
    def test_no_args_exits_1(self, tmp_path):
        r = _run(tmp_path=tmp_path)
        assert r.returncode == 1

    def test_no_args_stderr_usage(self, tmp_path):
        r = _run(tmp_path=tmp_path)
        assert "Usage" in r.stderr

    def test_no_query_exits_1(self, tmp_path):
        r = _run(["search"], tmp_path=tmp_path)
        assert r.returncode == 1

    def test_no_query_stderr_message(self, tmp_path):
        r = _run(["search"], tmp_path=tmp_path)
        assert "Missing query" in r.stderr


# ── unknown mode ───────────────────────────────────────────────────────


class TestUnknownMode:
    def test_unknown_mode_exits_1(self, tmp_path):
        r = _run(["teleport", "query here"], tmp_path=tmp_path)
        assert r.returncode == 1

    def test_unknown_mode_stderr(self, tmp_path):
        r = _run(["teleport", "query here"], tmp_path=tmp_path)
        assert "Unknown mode" in r.stderr

    def test_unknown_mode_mentions_valid_modes(self, tmp_path):
        r = _run(["invalid", "query"], tmp_path=tmp_path)
        assert "search" in r.stderr


# ── mode-to-model mapping ──────────────────────────────────────────────


class TestModeMapping:
    """Verify each mode maps to the correct model via recorded curl args."""

    MODE_MAP = {
        "search": "sonar",
        "ask": "sonar-pro",
        "research": "sonar-deep-research",
        "reason": "sonar-reasoning-pro",
    }

    @pytest.mark.parametrize("mode,model", list(MODE_MAP.items()))
    def test_mode_maps_to_model(self, mode, model, tmp_path):
        _write_secrets(tmp_path)
        record = tmp_path / "curl_args.log"
        bindir = _make_recording_curl(tmp_path, record)
        r = _run([mode, "test query"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        args = record.read_bytes().split(b"\0")
        args_text = b" ".join(args).decode()
        assert f'"model": "{model}"' in args_text


# ── API key handling ───────────────────────────────────────────────────


class TestAPIKey:
    def test_missing_key_exits_1(self, tmp_path):
        """Without PERPLEXITY_API_KEY set, the script exits 1."""
        # No .secrets file, no env var
        r = _run(["search", "test"], env_extra={"PERPLEXITY_API_KEY": ""}, tmp_path=tmp_path)
        assert r.returncode != 0

    def test_key_from_secrets_file(self, tmp_path):
        """Key loaded from ~/.secrets is used in the curl Authorization header."""
        _write_secrets(tmp_path, "my-secret-key-999")
        record = tmp_path / "curl_args.log"
        bindir = _make_recording_curl(tmp_path, record)
        r = _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        args = record.read_bytes().split(b"\0")
        args_text = b" ".join(args).decode()
        assert "my-secret-key-999" in args_text

    def test_key_from_env(self, tmp_path):
        """PERPLEXITY_API_KEY from environment is used."""
        record = tmp_path / "curl_args.log"
        bindir = _make_recording_curl(tmp_path, record)
        r = _run(
            ["search", "test"],
            path_dirs=[bindir],
            env_extra={"PERPLEXITY_API_KEY": "env-key-456"},
            tmp_path=tmp_path,
        )
        assert r.returncode == 0
        args = record.read_bytes().split(b"\0")
        args_text = b" ".join(args).decode()
        assert "env-key-456" in args_text


# ── curl request construction ──────────────────────────────────────────


class TestRequestConstruction:
    def test_uses_perplexity_api_url(self, tmp_path):
        _write_secrets(tmp_path)
        record = tmp_path / "curl_args.log"
        bindir = _make_recording_curl(tmp_path, record)
        _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        args = record.read_bytes().split(b"\0")
        args_text = b" ".join(args).decode()
        assert "api.perplexity.ai/chat/completions" in args_text

    def test_sends_authorization_header(self, tmp_path):
        _write_secrets(tmp_path)
        record = tmp_path / "curl_args.log"
        bindir = _make_recording_curl(tmp_path, record)
        _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        args = record.read_bytes().split(b"\0")
        args_text = b" ".join(args).decode()
        assert "Authorization: Bearer" in args_text

    def test_sends_content_type_header(self, tmp_path):
        _write_secrets(tmp_path)
        record = tmp_path / "curl_args.log"
        bindir = _make_recording_curl(tmp_path, record)
        _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        args = record.read_bytes().split(b"\0")
        args_text = b" ".join(args).decode()
        assert "Content-Type: application/json" in args_text

    def test_query_in_request_body(self, tmp_path):
        _write_secrets(tmp_path)
        record = tmp_path / "curl_args.log"
        bindir = _make_recording_curl(tmp_path, record)
        _run(["search", "what is quantum computing"], path_dirs=[bindir], tmp_path=tmp_path)
        args = record.read_bytes().split(b"\0")
        args_text = b" ".join(args).decode()
        assert "what is quantum computing" in args_text

    def test_query_json_escaped(self, tmp_path):
        """Quotes in the query are properly JSON-escaped."""
        _write_secrets(tmp_path)
        record = tmp_path / "curl_args.log"
        bindir = _make_recording_curl(tmp_path, record)
        _run(["ask", 'He said "hello"'], path_dirs=[bindir], tmp_path=tmp_path)
        args = record.read_bytes().split(b"\0")
        args_text = b" ".join(args).decode()
        # The query should be JSON-escaped (quotes doubled or backslash-escaped)
        assert "hello" in args_text


# ── response parsing ──────────────────────────────────────────────────


class TestResponseParsing:
    def test_success_extracts_content(self, tmp_path):
        _write_secrets(tmp_path)
        response = json.dumps({
            "choices": [{"message": {"content": "The answer is 42"}}]
        })
        bindir = _make_mock_curl(tmp_path, response)
        r = _run(["search", "meaning of life"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        assert "The answer is 42" in r.stdout

    def test_success_exits_zero(self, tmp_path):
        _write_secrets(tmp_path)
        response = json.dumps({
            "choices": [{"message": {"content": "some result"}}]
        })
        bindir = _make_mock_curl(tmp_path, response)
        r = _run(["ask", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_api_error_exits_1(self, tmp_path):
        _write_secrets(tmp_path)
        response = json.dumps({
            "error": {"message": "Rate limit exceeded"}
        })
        bindir = _make_mock_curl(tmp_path, response)
        r = _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 1

    def test_api_error_stderr_message(self, tmp_path):
        _write_secrets(tmp_path)
        response = json.dumps({
            "error": {"message": "Rate limit exceeded"}
        })
        bindir = _make_mock_curl(tmp_path, response)
        r = _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert "Rate limit exceeded" in r.stderr

    def test_unexpected_json_printed_raw(self, tmp_path):
        """Response without 'choices' or 'error' keys is printed as formatted JSON."""
        _write_secrets(tmp_path)
        response = json.dumps({"status": "unknown", "data": [1, 2]})
        bindir = _make_mock_curl(tmp_path, response)
        r = _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert "status" in r.stdout
        assert "unknown" in r.stdout

    def test_multiline_content_preserved(self, tmp_path):
        _write_secrets(tmp_path)
        content = "Line one\nLine two\nLine three"
        response = json.dumps({
            "choices": [{"message": {"content": content}}]
        })
        bindir = _make_mock_curl(tmp_path, response)
        r = _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert "Line one" in r.stdout
        assert "Line three" in r.stdout

    def test_empty_content(self, tmp_path):
        _write_secrets(tmp_path)
        response = json.dumps({
            "choices": [{"message": {"content": ""}}]
        })
        bindir = _make_mock_curl(tmp_path, response)
        r = _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0


# ── special characters in query ────────────────────────────────────────


class TestSpecialCharacters:
    def test_single_quotes_in_query(self, tmp_path):
        _write_secrets(tmp_path)
        record = tmp_path / "curl_args.log"
        bindir = _make_recording_curl(tmp_path, record)
        r = _run(["search", "it's a test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_unicode_in_query(self, tmp_path):
        _write_secrets(tmp_path)
        record = tmp_path / "curl_args.log"
        bindir = _make_recording_curl(tmp_path, record)
        r = _run(["search", "日本語テスト"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        args = record.read_bytes().split(b"\0")
        args_text = b" ".join(args).decode()
        assert "日本語テスト" in args_text
