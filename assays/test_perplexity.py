from __future__ import annotations

"""Tests for effectors/perplexity.sh — Perplexity API CLI wrapper.

Covers: help, usage errors, mode validation, mode-to-model mapping,
JSON query escaping, response parsing (success, error, fallback),
API key requirement, file basics.
"""

import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "perplexity.sh"


# ── helpers ─────────────────────────────────────────────────────────


def _run(
    *args: str,
    env_extra: dict | None = None,
    timeout: int = 15,
) -> subprocess.CompletedProcess:
    """Run perplexity.sh in isolation (no real API key, no real home)."""
    env = os.environ.copy()
    env.pop("PERPLEXITY_API_KEY", None)
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


def _make_fake_curl(tmpdir: Path, response_body: str) -> Path:
    """Create a fake curl that captures the -d body and prints response_body.

    The response is written via a temp file to avoid shell-escaping issues
    with complex JSON payloads.
    """
    fake = tmpdir / "curl"
    capture = tmpdir / "captured_request.json"
    resp_file = tmpdir / "mock_response.bin"
    resp_file.write_text(response_body)
    fake.write_text(
        f"""#!/usr/bin/env bash
# fake curl: capture -d argument, return canned response
while [ "$#" -gt 0 ]; do
    case "$1" in
        -d) shift; printf '%s' "$1" > {capture}; shift ;;
        *)  shift ;;
    esac
done
cat {resp_file}
"""
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return fake


def _run_with_fake_curl(
    tmpdir: Path, mode: str, query: str, response_body: str,
) -> tuple[subprocess.CompletedProcess, dict]:
    """Run perplexity.sh with a fake curl; return (proc, captured_request)."""
    _make_fake_curl(tmpdir, response_body)
    env_extra = {
        "PATH": f"{tmpdir}:{os.environ.get('PATH', '')}",
        "PERPLEXITY_API_KEY": "test-key-12345",
    }
    proc = _run(mode, query, env_extra=env_extra)
    captured = tmpdir / "captured_request.json"
    request: dict = {}
    if captured.exists():
        raw = captured.read_text()
        if raw.strip():
            request = json.loads(raw)
    return proc, request


# ── File basics ─────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first_line = SCRIPT.read_text().split("\n")[0]
        assert first_line == "#!/usr/bin/env bash"

    def test_has_set_euo(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)


# ── Help and usage ──────────────────────────────────────────────────


class TestHelp:
    def test_long_help(self):
        r = _run("--help")
        assert r.returncode == 0
        assert "Usage" in r.stdout

    def test_short_help(self):
        r = _run("-h")
        assert r.returncode == 0
        assert "Usage" in r.stdout

    def test_help_mentions_modes(self):
        r = _run("--help")
        for mode in ("search", "ask", "research", "reason"):
            assert mode in r.stdout

    def test_help_shows_models(self):
        r = _run("--help")
        assert "sonar" in r.stdout


# ── Usage errors ────────────────────────────────────────────────────


class TestUsageErrors:
    def test_no_args_exits_1(self):
        r = _run()
        assert r.returncode == 1
        assert "Usage" in r.stderr

    def test_missing_query_exits_1(self):
        r = _run("search")
        assert r.returncode != 0

    def test_empty_query_exits_1(self):
        r = _run("search", "")
        assert r.returncode != 0

    def test_unknown_mode_exits_1(self):
        r = _run("telepath", "hello world")
        assert r.returncode != 0
        assert "Unknown mode" in r.stderr

    def test_unknown_mode_suggests_valid_modes(self):
        r = _run("foobar", "test")
        assert r.returncode != 0
        assert "search" in r.stderr


# ── Mode-to-model mapping ──────────────────────────────────────────


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
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        assert request.get("model") == expected_model

    def test_query_passed_through(self, tmp_path):
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        proc, request = _run_with_fake_curl(tmp_path, "search", "what is life?", body)
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        messages = request.get("messages", [])
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "what is life?"

    @pytest.mark.parametrize("mode", ["search", "ask", "research", "reason"])
    def test_valid_modes_pass_mode_check(self, mode):
        """Valid modes should fail at API key, not at mode validation."""
        r = _run(mode, "test query")
        assert "Unknown mode" not in r.stderr


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

    def test_non_json_response_passthrough(self, tmp_path):
        """Non-JSON from curl should be printed as-is (parse error path)."""
        body = "This is plain text, not JSON"
        proc, _ = _run_with_fake_curl(tmp_path, "reason", "test", body)
        assert proc.returncode == 0
        assert "plain text" in proc.stdout


# ── API key requirement ─────────────────────────────────────────────


class TestAPIKey:
    def test_missing_api_key_exits_nonzero(self):
        r = _run("search", "test")
        assert r.returncode != 0

    def test_missing_api_key_error_mentions_var(self):
        r = _run("ask", "what is 2+2")
        assert r.returncode != 0
        assert "PERPLEXITY_API_KEY" in r.stderr


# ── JSON query escaping ─────────────────────────────────────────────


class TestQueryEscaping:
    def test_query_with_quotes_escaped(self, tmp_path):
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        proc, request = _run_with_fake_curl(
            tmp_path, "search", 'He said "hello"', body,
        )
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        assert request["messages"][0]["content"] == 'He said "hello"'

    def test_query_with_special_chars(self, tmp_path):
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        proc, request = _run_with_fake_curl(
            tmp_path, "search", "price: $5 & <tag>", body,
        )
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        assert request["messages"][0]["content"] == "price: $5 & <tag>"

    def test_query_with_single_quotes(self, tmp_path):
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        proc, request = _run_with_fake_curl(
            tmp_path, "search", "it's a test", body,
        )
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        assert request["messages"][0]["content"] == "it's a test"

    def test_query_with_unicode(self, tmp_path):
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        proc, request = _run_with_fake_curl(
            tmp_path, "ask", "Héllo wörld 日本語", body,
        )
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        assert request["messages"][0]["content"] == "Héllo wörld 日本語"


# ── Extra args / edge cases ─────────────────────────────────────────


class TestExtraArgs:
    def test_three_args_ignores_third(self, tmp_path):
        """Extra positional args are ignored by bash — only $1 and $2 are used."""
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        env_extra = {
            "PATH": f"{tmp_path}:{os.environ.get('PATH', '')}",
            "PERPLEXITY_API_KEY": "test-key-12345",
        }
        _make_fake_curl(tmp_path, body)
        proc = _run("search", "hello", "extra", env_extra=env_extra)
        assert proc.returncode == 0, f"stderr: {proc.stderr}"

    def test_response_with_empty_choices(self, tmp_path):
        """Empty choices list should produce fallback output (no crash)."""
        body = json.dumps({"choices": []})
        proc, _ = _run_with_fake_curl(tmp_path, "search", "test", body)
        # Script's python3 tries d['choices'][0] which raises IndexError,
        # caught by the except block which dumps raw JSON.
        assert proc.returncode == 0
        assert "choices" in proc.stdout


class TestAuthHeader:
    def test_curl_receives_bearer_token(self, tmp_path):
        """Verify the fake curl sees the Authorization header with Bearer."""
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})

        # Build a fake curl that captures -H args
        fake = tmp_path / "curl"
        capture = tmp_path / "captured_headers.txt"
        resp_file = tmp_path / "mock_response.bin"
        resp_file.write_text(body)
        fake.write_text(
            f"""#!/usr/bin/env bash
while [ "$#" -gt 0 ]; do
    case "$1" in
        -H) shift; echo "$1" >> {capture}; shift ;;
        -d) shift; shift ;;
        *)  shift ;;
    esac
done
cat {resp_file}
"""
        )
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

        env_extra = {
            "PATH": f"{tmp_path}:{os.environ.get('PATH', '')}",
            "PERPLEXITY_API_KEY": "test-key-12345",
        }
        proc = _run("search", "test", env_extra=env_extra)
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        headers = capture.read_text().strip().split("\n")
        assert any("Bearer test-key-12345" in h for h in headers), f"Headers: {headers}"


class TestPayloadStructure:
    def test_request_is_valid_json(self, tmp_path):
        """The full -d payload should be parseable JSON with expected keys."""
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        proc, request = _run_with_fake_curl(tmp_path, "search", "test", body)
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        assert "model" in request
        assert "messages" in request

    def test_long_query_handled(self, tmp_path):
        """A 10KB query string should survive JSON escaping intact."""
        long_query = "x" * 10000
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]})
        proc, request = _run_with_fake_curl(tmp_path, "search", long_query, body)
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        assert request["messages"][0]["content"] == long_query
