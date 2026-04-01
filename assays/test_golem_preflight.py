from __future__ import annotations

"""Tests for golem preflight health check and rate-limit retry logic.

Tests the pre-flight curl check, retry detection for empty output,
and smart backoff from reset times.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

GOLEM = Path.home() / "germline" / "effectors" / "golem"


# ── Helper: extract and test bash functions via shell ────────────────


def _run_golem_fragment(env_extra: dict | None = None, args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run the golem script with given args and return the result."""
    env = os.environ.copy()
    # Ensure required keys exist (use dummy values for --help / summary)
    env.setdefault("ZHIPU_API_KEY", "test-key-zhipu")
    env.setdefault("VOLCANO_API_KEY", "test-key-volcano")
    env.setdefault("INFINI_API_KEY", "test-key-infini")
    if env_extra:
        env.update(env_extra)
    cmd = [str(GOLEM)] + (args or ["--help"])
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=15, env=env, cwd=str(Path.home() / "germline")
    )


# ── Script loads and help works ──────────────────────────────────────


def test_golem_help():
    """golem --help exits with 0 and shows usage."""
    r = _run_golem_fragment(args=["--help"])
    assert r.returncode == 0
    assert "golem" in r.stdout.lower()


def test_golem_unknown_provider():
    """golem --provider nonexistent exits non-zero."""
    r = _run_golem_fragment(args=["--provider", "nonexistent", "test task"])
    assert r.returncode != 0
    assert "Unknown provider" in r.stderr or "Unknown provider" in r.stdout


def test_golem_summary_no_log():
    """golem summary with a temp log dir exits with 1 (no log file)."""
    with tempfile.TemporaryDirectory() as tmp:
        env = {"GOLEM_LOG": os.path.join(tmp, "nonexistent.jsonl")}
        r = _run_golem_fragment(env_extra=env, args=["summary", "--quiet"])
        # summary exits 1 when no log file found
        assert r.returncode == 1


# ── Provider config: URL, model names ────────────────────────────────


def test_volcano_url_in_script():
    """Volcano provider uses /api/coding base URL."""
    source = GOLEM.read_text()
    assert 'https://ark.cn-beijing.volces.com/api/coding' in source


def test_volcano_model_name():
    """Volcano uses ark-code-latest model."""
    source = GOLEM.read_text()
    assert 'ark-code-latest' in source


# ── Pre-flight check function exists ─────────────────────────────────


def test_preflight_check_function_exists():
    """_preflight_check function is defined in the script."""
    source = GOLEM.read_text()
    assert "_preflight_check()" in source


def test_preflight_uses_haiku_model():
    """Pre-flight uses the cheapest model (_HAIKU) to minimize quota usage."""
    source = GOLEM.read_text()
    # Find the preflight check function and verify it uses _HAIKU
    assert '$_HAIKU' in source


def test_preflight_parses_reset_time():
    """Pre-flight parses 'reset at YYYY-MM-DD HH:MM:SS' from 429 response."""
    source = GOLEM.read_text()
    assert 'reset at' in source
    assert '_reset_epoch' in source


def test_preflight_wait_cap():
    """Pre-flight wait is capped at 600s (10 min)."""
    source = GOLEM.read_text()
    assert '-gt 600' in source


# ── Empty output = rate limit detection ───────────────────────────────


def test_empty_output_rate_limit_detection():
    """Script treats empty output + non-zero exit as rate limit."""
    source = GOLEM.read_text()
    # The key pattern: check if output is whitespace-only
    assert '${output// /}' in source
    assert '_is_ratelimit=true' in source


# ── Timeout on claude invocation ──────────────────────────────────────


def test_claude_timeout_set():
    """Script uses 'timeout' command to cap claude wall-clock time."""
    source = GOLEM.read_text()
    assert 'timeout "$_claude_timeout"' in source
    assert '_claude_timeout' in source


def test_timeout_exits_as_rate_limit():
    """Timeout exit code 124 is treated as rate limit (re-mapped to 1)."""
    source = GOLEM.read_text()
    assert 'exit_code -eq 124' in source


# ── Smart backoff from reset time ─────────────────────────────────────


def test_backoff_uses_reset_time():
    """Backoff computes wait from the reset time in the 429 error."""
    source = GOLEM.read_text()
    # Should compute _wait_secs from reset epoch minus current time
    assert '_wait_secs' in source
    assert '_reset_epoch' in source
    assert '+ 30' in source  # 30s buffer past reset


def test_backoff_minimum():
    """Minimum backoff is 30 seconds."""
    source = GOLEM.read_text()
    assert '_wait_secs -lt 30' in source


# ── Retry loop structure ──────────────────────────────────────────────


def test_max_retries_is_3():
    """Script retries up to 3 times on rate limit."""
    source = GOLEM.read_text()
    assert '_max_retries=3' in source


def test_preflight_runs_before_claude():
    """Pre-flight check runs inside the retry loop, before claude."""
    source = GOLEM.read_text()
    # Find the retry while loop and extract its body by tracking nesting
    while_start = source.index("while [[ $_attempt")
    pos = while_start
    depth = 0
    done_pos = None
    while pos < len(source):
        if source[pos:pos+6] == "while ":
            depth += 1
            pos += 6
        elif source[pos:pos+4] == "done":
            depth -= 1
            if depth == 0:
                done_pos = pos
                break
            pos += 4
        else:
            pos += 1
    assert done_pos is not None, "could not find matching 'done' for retry loop"
    while_block = source[while_start:done_pos]
    assert "preflight" in while_block.lower(), "preflight check not in retry loop"
    assert "claude" in while_block, "claude invocation not in retry loop"
    assert while_block.index("preflight") < while_block.index("claude"), \
        "preflight should run before claude"


def test_preflight_skip_on_auth_error():
    """Pre-flight auth/connection errors fall through to try claude directly."""
    source = GOLEM.read_text()
    assert "skipping health check" in source


# ── Fallback provider mapping ────────────────────────────────────────


def test_volcano_falls_back_to_infini():
    """Volcano's fallback provider is infini."""
    source = GOLEM.read_text()
    # Find the _fallback_provider function
    func_start = source.index("_fallback_provider()")
    func_end = source.index("}", func_start)
    func_body = source[func_start:func_end]
    assert "volcano) echo \"infini\"" in func_body


# ── Summary subcommand ───────────────────────────────────────────────


def test_summary_with_existing_log():
    """golem summary reads and parses JSONL entries."""
    with tempfile.TemporaryDirectory() as tmp:
        log_file = Path(tmp) / "golem.jsonl"
        log_file.write_text(
            '{"ts":"2026-04-01T00:00:00Z","provider":"volcano","duration":10,"exit":0,"turns":30,"prompt":"test","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0,"task_id":""}\n'
        )
        env = {"GOLEM_LOG": str(log_file)}
        r = _run_golem_fragment(env_extra=env, args=["summary"])
        assert r.returncode == 0
        assert "volcano" in r.stdout
        assert "1" in r.stdout  # 1 run


def test_summary_json_flag():
    """golem summary --json outputs valid JSON."""
    with tempfile.TemporaryDirectory() as tmp:
        log_file = Path(tmp) / "golem.jsonl"
        log_file.write_text(
            '{"ts":"2026-04-01T00:00:00Z","provider":"zhipu","duration":30,"exit":1,"turns":30,"prompt":"test","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0,"task_id":""}\n'
        )
        env = {"GOLEM_LOG": str(log_file)}
        r = _run_golem_fragment(env_extra=env, args=["summary", "--json"])
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "zhipu" in data
        assert data["zhipu"]["runs"] == 1
        assert data["zhipu"]["fail"] == 1


# ── Integration: preflight curl against volcano ──────────────────────


def test_volcano_preflight_returns_429():
    """Real volcano API returns 429 when quota is exceeded."""
    key = os.environ.get("VOLCANO_API_KEY", "")
    if not key:
        pytest.skip("VOLCANO_API_KEY not set")
    r = subprocess.run(
        [
            "curl", "-s", "-w", "\\n%{http_code}",
            "https://ark.cn-beijing.volces.com/api/coding/v1/messages",
            "-H", f"x-api-key: {key}",
            "-H", "Content-Type: application/json",
            "-H", "anthropic-version: 2023-06-01",
            "-d", '{"model":"ark-code-latest","max_tokens":1,"messages":[{"role":"user","content":"ping"}]}',
            "--connect-timeout", "10",
            "--max-time", "15",
        ],
        capture_output=True, text=True, timeout=20,
    )
    http_code = r.stdout.strip().split("\n")[-1]
    body = "\n".join(r.stdout.strip().split("\n")[:-1])
    # Either 429 (rate limited) or 200 (quota available)
    if http_code == "429":
        assert "AccountQuotaExceeded" in body or "quota" in body.lower()
        assert "reset at" in body
    elif http_code == "200":
        pytest.skip("Volcano quota available, not rate-limited")
    else:
        pytest.fail(f"Unexpected HTTP {http_code}: {body[:200]}")
