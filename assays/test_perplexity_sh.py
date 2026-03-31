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
    """Run the perplexity.sh script with optional custom PATH and env."""
    env = os.environ.copy()
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if path_dirs is not None:
        env["PATH"] = os.pathsep.join(str(p) for p in path_dirs)
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)


def _mock_curl_bin(tmp_path: Path, response_body: str, exit_code: int = 0) -> Path:
    """Create a fake curl that writes canned response_body to stdout."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    fake = bindir / "curl"
    # Write response body to a temp file so quoting is easy
    resp_file = tmp_path / "_curl_response.json"
    resp_file.write_text(response_body)
    fake.write_text(
        "#!/bin/bash\n"
        f"cat {resp_file}\n"
        f"exit {exit_code}\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return bindir


def _recording_curl_bin(tmp_path: Path, response_body: str = '{"choices":[{"message":{"content":"ok"}}]}') -> tuple[Path, Path]:
    """Create a fake curl that records its args and returns response_body."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    record = tmp_path / "_curl_args.txt"
    resp_file = tmp_path / "_curl_response.json"
    resp_file.write_text(response_body)
    fake = bindir / "curl"
    fake.write_text(
        "#!/bin/bash\n"
        f'echo "$@" >> {record}\n'
        f"cat {resp_file}\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return bindir, record


def _make_secrets(tmp_path: Path, key: str = "pplx-test-fake-key") -> Path:
    """Write a ~/.secrets file with PERPLEXITY_API_KEY."""
    secrets = tmp_path / ".secrets"
    secrets.write_text(f"PERPLEXITY_API_KEY={key}\n")
    return secrets


def _api_response(content: str, model: str = "sonar") -> str:
    """Build a plausible Perplexity API JSON response."""
    return json.dumps({
        "id": "fake-id",
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}],
    })


def _api_error(message: str = "Rate limited") -> str:
    """Build a Perplexity API error JSON response."""
    return json.dumps({"error": {"message": message, "type": "rate_limit_error"}})


# ── --help / usage tests ────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_exits_zero(self, tmp_path):
        r = _run(["--help"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self, tmp_path):
        r = _run(["-h"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_help_shows_usage_lines(self, tmp_path):
        r = _run(["--help"], tmp_path=tmp_path)
        assert "Perplexity API CLI" in r.stdout
        assert "search" in r.stdout
        assert "ask" in r.stdout
        assert "research" in r.stdout
        assert "reason" in r.stdout


class TestMissingArgs:
    def test_no_args_exits_1(self, tmp_path):
        r = _run([], tmp_path=tmp_path)
        assert r.returncode == 1

    def test_no_args_stderr_usage(self, tmp_path):
        r = _run([], tmp_path=tmp_path)
        assert "Usage" in r.stderr


class TestUnknownMode:
    def test_bad_mode_exits_1(self, tmp_path):
        r = _run(["badmode", "hello"], tmp_path=tmp_path)
        assert r.returncode == 1

    def test_bad_mode_stderr_message(self, tmp_path):
        r = _run(["foobar", "hello"], tmp_path=tmp_path)
        assert "Unknown mode" in r.stderr
        assert "foobar" in r.stderr


class TestMissingQuery:
    def test_missing_query_exits_nonzero(self, tmp_path):
        # ${2:?Missing query} causes bash to write to stderr and exit
        r = _run(["search"], tmp_path=tmp_path)
        assert r.returncode != 0

    def test_missing_query_stderr(self, tmp_path):
        r = _run(["search"], tmp_path=tmp_path)
        assert "Missing query" in r.stderr or "query" in r.stderr.lower()


# ── mode → model mapping tests ──────────────────────────────────────────


class TestModeMapping:
    """Verify each mode sends the correct model name to the API."""

    @pytest.fixture()
    def env(self, tmp_path):
        """Set up tmp HOME with .secrets and recording fake curl."""
        _make_secrets(tmp_path)
        bindir, record = _recording_curl_bin(tmp_path)
        return bindir, record

    @pytest.mark.parametrize("mode,model", [
        ("search", "sonar"),
        ("ask", "sonar-pro"),
        ("research", "sonar-deep-research"),
        ("reason", "sonar-reasoning-pro"),
    ])
    def test_mode_uses_correct_model(self, tmp_path, env, mode, model):
        bindir, record = env
        r = _run([mode, "test query"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0, f"stderr: {r.stderr}"
        curl_args = record.read_text()
        assert f'"model": "{model}"' in curl_args


# ── successful API response tests ───────────────────────────────────────


class TestSuccessfulResponse:
    @pytest.fixture()
    def env(self, tmp_path):
        _make_secrets(tmp_path)
        bindir = _mock_curl_bin(tmp_path, _api_response("Paris is the capital of France."))
        return bindir

    def test_exits_zero(self, tmp_path, env):
        r = _run(["search", "capital of france"], path_dirs=[env], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_prints_content(self, tmp_path, env):
        r = _run(["search", "capital of france"], path_dirs=[env], tmp_path=tmp_path)
        assert "Paris is the capital of France." in r.stdout

    def test_multiline_content(self, tmp_path):
        _make_secrets(tmp_path)
        content = "Line one.\nLine two.\nLine three."
        bindir = _mock_curl_bin(tmp_path, _api_response(content))
        r = _run(["ask", "tell me"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        assert "Line one." in r.stdout
        assert "Line three." in r.stdout


# ── API error response tests ────────────────────────────────────────────


class TestAPIError:
    def test_error_response_exits_nonzero(self, tmp_path):
        _make_secrets(tmp_path)
        bindir = _mock_curl_bin(tmp_path, _api_error("You exceeded your quota"))
        r = _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode != 0

    def test_error_response_stderr_message(self, tmp_path):
        _make_secrets(tmp_path)
        bindir = _mock_curl_bin(tmp_path, _api_error("You exceeded your quota"))
        r = _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert "You exceeded your quota" in r.stderr


# ── API key handling tests ──────────────────────────────────────────────


class TestAPIKey:
    def test_missing_key_exits_nonzero(self, tmp_path):
        # No .secrets file, no env var — should fail
        bindir = _mock_curl_bin(tmp_path, _api_response("ok"))
        r = _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode != 0

    def test_key_from_env_var(self, tmp_path):
        # No .secrets, but key provided via env
        bindir = _mock_curl_bin(tmp_path, _api_response("env key works"))
        r = _run(
            ["search", "test"],
            path_dirs=[bindir],
            tmp_path=tmp_path,
            env_extra={"PERPLEXITY_API_KEY": "pplx-from-env"},
        )
        assert r.returncode == 0
        assert "env key works" in r.stdout

    def test_key_sent_in_header(self, tmp_path):
        _make_secrets(tmp_path, key="pplx-secret-123")
        bindir, record = _recording_curl_bin(tmp_path)
        r = _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        curl_args = record.read_text()
        assert "Bearer pplx-secret-123" in curl_args


# ── query escaping tests ────────────────────────────────────────────────


class TestQueryEscaping:
    def test_quotes_in_query(self, tmp_path):
        _make_secrets(tmp_path)
        bindir, record = _recording_curl_bin(tmp_path)
        r = _run(["search", 'he said "hello"'], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        curl_args = record.read_text()
        # The query should appear JSON-escaped in the payload
        assert '"hello"' in curl_args

    def test_special_chars_in_query(self, tmp_path):
        _make_secrets(tmp_path)
        bindir, record = _recording_curl_bin(tmp_path)
        r = _run(["ask", "price: $5 & tax < 10%"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        curl_args = record.read_text()
        # $ and & and < should be present in the JSON body (escaped by python3)
        assert "price" in curl_args


# ── unexpected response shape tests ─────────────────────────────────────


class TestUnexpectedResponse:
    def test_non_json_response(self, tmp_path):
        """If the API returns non-JSON, script should still output something."""
        _make_secrets(tmp_path)
        bindir = _mock_curl_bin(tmp_path, "<html>Gateway Timeout</html>")
        r = _run(["search", "test"], path_dirs=[bindir], tmp_path=tmp_path)
        # Script prints the raw response as fallback
        assert "Gateway Timeout" in r.stdout or "Gateway Timeout" in r.stderr
