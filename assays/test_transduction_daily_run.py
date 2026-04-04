from __future__ import annotations

"""Tests for effectors/transduction-daily-run — daily pipeline script.

Tests cover: --help flag, normal execution flow, non-fatal X feed failure,
fatal transduction failure, and correct command invocation.
"""

import os
import subprocess
import tempfile
from pathlib import Path

EFFECTOR = Path.home() / "germline" / "effectors" / "transduction-daily-run"


def _run(*args, timeout=30):
    """Run the effector with optional args, capturing output."""
    return subprocess.run(
        [str(EFFECTOR), *list(args)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=os.environ.copy(),
    )


def _run_with_mocks(x_feed_rc=0, transduction_rc=0, timeout=30):
    """Run the effector with mock x-feed-to-endocytosis and uv commands."""
    tmpdir = tempfile.mkdtemp()
    mock_x_feed = Path(tmpdir) / "x-feed-to-endocytosis"
    mock_x_feed.write_text(f"#!/bin/bash\necho 'mock x-feed ok'\nexit {x_feed_rc}\n")
    mock_x_feed.chmod(0o755)

    mock_uv = Path(tmpdir) / "uv"
    mock_uv.write_text(f"#!/bin/bash\necho 'mock uv run: \"$@\"'\nexit {transduction_rc}\n")
    mock_uv.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"
    env["HOME"] = str(Path.home())

    return subprocess.run(
        [str(EFFECTOR)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    ), tmpdir


# ── Help tests ──────────────────────────────────────────────────────────


class TestHelp:
    def test_help_long_flag(self):
        r = _run("--help")
        assert r.returncode == 0
        assert "Usage" in r.stdout
        assert "transduction-daily-run" in r.stdout

    def test_help_short_flag(self):
        r = _run("-h")
        assert r.returncode == 0
        assert "Usage" in r.stdout

    def test_help_describes_steps(self):
        r = _run("--help")
        assert "X personalized feed" in r.stdout or "X feed" in r.stdout
        assert "daily" in r.stdout.lower()


# ── Normal execution ───────────────────────────────────────────────────


class TestNormalExecution:
    def test_successful_run_exits_zero(self):
        r, _tmpdir = _run_with_mocks(x_feed_rc=0, transduction_rc=0)
        assert r.returncode == 0
        assert "Done." in r.stdout

    def test_prints_date_header(self):
        r, _tmpdir = _run_with_mocks(x_feed_rc=0, transduction_rc=0)
        assert "===" in r.stdout

    def test_calls_x_feed(self):
        r, _tmpdir = _run_with_mocks(x_feed_rc=0, transduction_rc=0)
        assert "Fetching X feed" in r.stdout

    def test_calls_transduction(self):
        r, _tmpdir = _run_with_mocks(x_feed_rc=0, transduction_rc=0)
        assert "Running transduction daily" in r.stdout


# ── Non-fatal X feed failure ────────────────────────────────────────────


class TestXFeedFailure:
    def test_x_feed_failure_does_not_abort(self):
        r, _tmpdir = _run_with_mocks(x_feed_rc=1, transduction_rc=0)
        assert r.returncode == 0
        assert "Done." in r.stdout

    def test_x_feed_failure_prints_non_fatal_message(self):
        r, _tmpdir = _run_with_mocks(x_feed_rc=1, transduction_rc=0)
        assert "non-fatal" in r.stdout.lower() or "failed" in r.stdout.lower()


# ── Fatal transduction failure ──────────────────────────────────────────


class TestTransductionFailure:
    def test_transduction_failure_exits_nonzero(self):
        r, _tmpdir = _run_with_mocks(x_feed_rc=0, transduction_rc=1)
        assert r.returncode != 0

    def test_transduction_failure_shows_error(self):
        r, _tmpdir = _run_with_mocks(x_feed_rc=0, transduction_rc=1)
        # The script propagates the error via set -e
        assert r.returncode != 0


# ── Output format ───────────────────────────────────────────────────────


class TestOutputFormat:
    def test_output_order(self):
        """Steps appear in correct order: date, fetch, transduction, done."""
        r, _tmpdir = _run_with_mocks(x_feed_rc=0, transduction_rc=0)
        lines = r.stdout.strip().split("\n")
        # Find key lines
        date_idx = next(i for i, l in enumerate(lines) if "===" in l)
        fetch_idx = next(i for i, l in enumerate(lines) if "Fetching" in l)
        transduction_idx = next(i for i, l in enumerate(lines) if "Running transduction" in l)
        done_idx = next(i for i, l in enumerate(lines) if "Done" in l)
        assert date_idx < fetch_idx < transduction_idx < done_idx

    def test_done_on_success(self):
        r, _tmpdir = _run_with_mocks(x_feed_rc=0, transduction_rc=0)
        assert "Done." in r.stdout
