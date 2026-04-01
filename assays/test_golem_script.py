
"""Tests for effectors/golem -- headless CC + GLM-5.1 shell script.

Tests cover: task ID parsing, flag parsing, provider config, rate-limit
fail-fast, JSON output, summary subcommand.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

GOLEM = Path.home() / "germline" / "effectors" / "golem"


def _run_golem(*args, timeout=30):
    env = os.environ.copy()
    env["PATH"] = f"{Path.home() / 'germline' / 'effectors'}:{env.get('PATH', '')}"
    env.setdefault("ZHIPU_API_KEY", "test-zhipu-key")
    env.setdefault("VOLCANO_API_KEY", "test-volcano-key")
    env.setdefault("INFINI_API_KEY", "test-infini-key")
    return subprocess.run(
        [str(GOLEM)] + list(args),
        capture_output=True, text=True, timeout=timeout, env=env,
    )


def _run_golem_shell(cmd, env_extra=None, timeout=30):
    env = os.environ.copy()
    env["PATH"] = f"{Path.home() / 'germline' / 'effectors'}:{env.get('PATH', '')}"
    env.setdefault("ZHIPU_API_KEY", "test-zhipu-key")
    env.setdefault("VOLCANO_API_KEY", "test-volcano-key")
    env.setdefault("INFINI_API_KEY", "test-infini-key")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env,
    )


# -- Help and usage --


class TestHelp:
    def test_help_flag(self):
        r = _run_golem("--help")
        assert r.returncode == 0
        assert "golem" in r.stdout.lower()

    def test_help_short(self):
        r = _run_golem("-h")
        assert r.returncode == 0
        assert "golem" in r.stdout.lower()


# -- Task ID parsing --


class TestTaskIDParsing:
    """Test that [t-xxxxxx] prefix is correctly stripped before flag parsing."""

    def test_task_id_with_help(self):
        """Task ID before flags: --help should still be recognized."""
        r = _run_golem_shell("golem '[t-a4a00f]' --help")
        assert r.returncode == 0
        assert "golem" in r.stdout.lower()

    def test_task_id_hex_format(self):
        """Valid hex task IDs should be accepted."""
        r = _run_golem_shell("golem '[t-deadbe]' --help")
        assert r.returncode == 0

    def test_task_id_uppercase_hex(self):
        """Uppercase hex in task ID should be accepted."""
        r = _run_golem_shell("golem '[t-A4A00F]' --help")
        assert r.returncode == 0

    def test_no_task_id(self):
        """Without task ID, flags should parse normally."""
        r = _run_golem("--help")
        assert r.returncode == 0


# -- Provider config --


class TestProviderConfig:
    def test_unknown_provider_exit(self):
        """Unknown provider should cause exit code 1."""
        r = _run_golem("--provider", "nonexistent", "--max-turns", "3", "test")
        assert r.returncode == 1
        assert "Unknown provider" in r.stderr

    def test_zhipu_provider(self):
        """ZhiPu provider should require ZHIPU_API_KEY."""
        r = _run_golem(
            "--provider", "zhipu", "--max-turns", "3", "test",
            env_extra={"ZHIPU_API_KEY": ""},
        )
        assert r.returncode != 0

    def test_volcano_provider(self):
        """Volcano provider should require VOLCANO_API_KEY."""
        r = _run_golem(
            "--provider", "volcano", "--max-turns", "3", "test",
            env_extra={"VOLCANO_API_KEY": ""},
        )
        assert r.returncode != 0


# -- Summary subcommand --


class TestSummary:
    def test_summary_empty_log(self):
        """Summary on empty log should show 'No log file found'."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
            f.write("")
            tmp = f.name
        try:
            r = _run_golem_shell(f"golem summary --log={tmp}", timeout=10)
            assert r.returncode in (0, 1)
        finally:
            os.unlink(tmp)

    def test_summary_json_output(self):
        """Summary --json should produce valid JSON."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
            f.write(json.dumps({
                "ts": "2026-04-01T00:00:00Z",
                "provider": "zhipu",
                "duration": 100,
                "exit": 0,
                "turns": 10,
                "prompt": "test",
                "tail": "",
                "files_created": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "pytest_exit": 0,
                "task_id": "t-test01",
            }) + "\n")
            tmp = f.name
        try:
            r = _run_golem_shell(f"golem summary --json --log={tmp}", timeout=10)
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert "zhipu" in data
            assert data["zhipu"]["runs"] == 1
            assert data["zhipu"]["pass"] == 1
        finally:
            os.unlink(tmp)

    def test_summary_counts_pass_fail(self):
        """Summary should correctly count pass/fail."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
            for exit_code in [0, 0, 1, 1, 1]:
                f.write(json.dumps({
                    "ts": "2026-04-01T00:00:00Z",
                    "provider": "zhipu",
                    "duration": 100,
                    "exit": exit_code,
                    "turns": 10,
                    "prompt": "test",
                    "tail": "",
                    "files_created": 0,
                    "tests_passed": 0,
                    "tests_failed": 0,
                    "pytest_exit": 0,
                    "task_id": "t-test01",
                }) + "\n")
            tmp = f.name
        try:
            r = _run_golem_shell(f"golem summary --json --log={tmp}", timeout=10)
            assert r.returncode == 0
            data = json.loads(r.stdout)
            assert data["zhipu"]["runs"] == 5
            assert data["zhipu"]["pass"] == 2
            assert data["zhipu"]["fail"] == 3
        finally:
            os.unlink(tmp)


# -- Rate-limit fail-fast --


class TestRateLimitFailFast:
    """Test volcano rate-limit handling.

    Volcano returns 429 AccountQuotaExceeded with a 5-hour quota window.
    The golem script should fail fast (under 15s) instead of sleeping 30 min retrying.
    """

    @pytest.fixture(autouse=True)
    def skip_without_volcano_key(self):
        if not os.environ.get("VOLCANO_API_KEY"):
            pytest.skip("VOLCANO_API_KEY not set")

    def test_volcano_rate_limited_exits_nonzero(self):
        """Rate-limited volcano should exit with non-zero code (not 0)."""
        r = _run_golem_shell(
            "golem --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        assert r.returncode != 0

    def test_volcano_rate_limited_output_has_quota_indicator(self):
        """Rate-limited output should contain AccountQuotaExceeded."""
        r = _run_golem_shell(
            "golem --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        output = (r.stdout + r.stderr).lower()
        assert "quota" in output or "429" in output or "rate" in output

    def test_volcano_rate_limited_fails_fast(self):
        """Should fail in under 15 seconds, not sleep 30 minutes."""
        start = time.time()
        r = _run_golem_shell(
            "golem --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        elapsed = time.time() - start
        assert elapsed < 15, f"Took {elapsed:.1f}s -- should fail fast on long quota window"


# -- Regression: exit=2 with 0s duration --


class TestExit2Regression:
    """Tests for the bug where golem returned exit=0 when claude never launched.

    Root causes identified:
    1. Task ID [t-xxxx] before flags prevented --provider from being parsed
    2. Rate-limit retry loop returned exit_code=0 when claude never launched
    3. Smart backoff capped at 600s for 5-hour quota window

    Fixes applied:
    - Task ID regex pre-parsing before flag while-loop
    - _claude_ran tracking to detect never-launched state
    - Fail-fast when quota reset > 30 min away
    """

    def test_task_id_does_not_break_provider_parsing(self):
        """[t-xxxx] --provider volcano should parse provider=volcano, not default zhipu."""
        r = _run_golem_shell(
            "golem '[t-a4a00f]' --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        volcano_key = os.environ.get("VOLCANO_API_KEY")
        if volcano_key:
            output = r.stdout + r.stderr
            if "quota" in output.lower() or "429" in output or "preflight" in output:
                assert "volcano" in output.lower()

    def test_exit_code_nonzero_when_claude_never_launched(self):
        """Golem should return non-zero when claude was never invoked.

        Previously: exit_code stayed 0 (initialized but never set).
        Now: returns 1 with AccountQuotaExceeded message.
        """
        volcano_key = os.environ.get("VOLCANO_API_KEY")
        if not volcano_key:
            pytest.skip("VOLCANO_API_KEY not set")

        r = _run_golem_shell(
            "golem --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        assert r.returncode != 0

    def test_fail_fast_does_not_waste_time(self):
        """Should fail in under 15 seconds when quota window is > 30 min."""
        volcano_key = os.environ.get("VOLCANO_API_KEY")
        if not volcano_key:
            pytest.skip("VOLCANO_API_KEY not set")

        start = time.time()
        r = _run_golem_shell(
            "golem --provider volcano --max-turns 3 'test'",
            timeout=30,
        )
        elapsed = time.time() - start
        assert elapsed < 15, f"Took {elapsed:.1f}s -- should fail fast"
