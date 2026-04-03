"""Tests for golem wall-limit feature (t-timeout1).

The golem bash script should respect GOLEM_WALL_LIMIT env var to avoid
exceeding the Temporal worker's 30min activity timeout. The wall-limit
only gates whether to START a new retry, never kills an in-progress run.
"""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

GOLEM_SCRIPT = str(Path.home() / "germline" / "effectors" / "golem")


def _run_golem_snippet(env_override: dict, timeout: int = 15) -> subprocess.CompletedProcess:
    """Run golem with a fake provider that always 429s, to trigger retry logic."""
    env = {**os.environ, **env_override}
    # Use a nonexistent API endpoint so preflight fails fast with rate-limit
    env["GOLEM_PROVIDER"] = "zhipu"
    env["ANTHROPIC_API_KEY"] = "fake-key-for-test"
    env["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:1"  # connection refused = fast fail
    return subprocess.run(
        ["bash", GOLEM_SCRIPT, "--provider", "zhipu", "--max-turns", "1", "echo test"],
        capture_output=True, text=True, timeout=timeout, env=env,
    )


class TestWallLimitSkipsRetry:
    """When wall-limit is very short, golem should not retry after first failure."""

    def test_wall_limit_exits_without_full_retries(self):
        """With GOLEM_WALL_LIMIT=5 (5 seconds), golem should not sleep 30s for backoff."""
        start = time.monotonic()
        result = _run_golem_snippet({"GOLEM_WALL_LIMIT": "5"}, timeout=30)
        elapsed = time.monotonic() - start

        # Should finish well under 30s (the normal backoff sleep).
        # If wall-limit isn't implemented yet, this will either timeout or take >30s.
        assert elapsed < 20, f"Golem took {elapsed:.0f}s — wall-limit did not prevent retry backoff"
        assert result.returncode != 0  # task should fail (fake endpoint)

    def test_wall_limit_logged_to_stderr(self):
        """When wall-limit prevents a retry, stderr should mention it."""
        result = _run_golem_snippet({"GOLEM_WALL_LIMIT": "5"}, timeout=30)
        assert "wall-limit" in result.stderr.lower() or "wall_limit" in result.stderr.lower(), (
            f"Expected 'wall-limit' in stderr, got: {result.stderr[:500]}"
        )


class TestWallLimitAllowsFirstAttempt:
    """Wall-limit should never prevent the first attempt from running."""

    def test_first_attempt_runs_with_large_limit(self):
        """With a generous wall-limit, the first attempt should proceed normally."""
        result = _run_golem_snippet({"GOLEM_WALL_LIMIT": "9999"}, timeout=30)
        # Will fail due to fake endpoint, but should have attempted to run
        assert result.returncode != 0
        # Should NOT contain wall-limit message (limit wasn't hit)
        stderr_lower = result.stderr.lower()
        assert "wall-limit" not in stderr_lower or "wall_limit" not in stderr_lower


class TestWallLimitDefault:
    """When GOLEM_WALL_LIMIT is unset, default should be 1680 (28 min)."""

    def test_default_value_is_1680(self):
        """Parse the golem script source to verify the default."""
        source = Path(GOLEM_SCRIPT).read_text()
        # The implementation should have a line like:
        # GOLEM_WALL_LIMIT="${GOLEM_WALL_LIMIT:-1680}"
        # or similar defaulting pattern
        assert "1680" in source, (
            "Expected default wall-limit of 1680 (28min) in golem script"
        )
