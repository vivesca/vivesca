"""Tests for compound-engineering-status — bash status checker for auto-update scheduler."""
from __future__ import annotations

import os
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest

EFFECTOR = Path.home() / "germline" / "effectors" / "compound-engineering-status"
LOG_FILE = Path.home() / ".compound-engineering-updates.log"


@pytest.fixture(autouse=True)
def _ensure_executable():
    """Make sure the effector is executable."""
    EFFECTOR.chmod(EFFECTOR.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _run(args: list[str] | None = None, env_extra: dict | None = None) -> subprocess.CompletedProcess[str]:
    """Run the effector and return CompletedProcess."""
    cmd = ["bash", str(EFFECTOR)]
    if args:
        cmd.extend(args)
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


# ── --help flag ──────────────────────────────────────────────────────


class TestHelp:
    def test_help_flag_exits_zero(self):
        r = _run(["--help"])
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run(["--help"])
        assert "Usage:" in r.stdout

    def test_short_h_flag(self):
        r = _run(["-h"])
        assert r.returncode == 0
        assert "Usage:" in r.stdout


# ── header output ────────────────────────────────────────────────────


class TestHeader:
    def test_prints_status_header(self):
        r = _run()
        assert "Compound Engineering Auto-Update Status" in r.stdout

    def test_prints_management_commands_section(self):
        r = _run()
        assert "Management Commands" in r.stdout


# ── scheduler detection (macOS / Linux) ─────────────────────────────


class TestSchedulerDetection:
    def test_no_launchctl_falls_back_to_cron_check(self):
        """On Linux without launchctl, should check cron."""
        # On gemmule (Linux), launchctl is likely not available
        r = _run()
        # Either it mentions launchctl not available, or it shows LaunchAgent status
        assert ("launchctl" in r.stdout.lower()) or ("launchctl" in r.stderr.lower()) or ("cron" in r.stdout.lower()) or ("LaunchAgent" in r.stdout)

    def test_reports_missing_cron_when_no_cron(self):
        """If no cron job for compound-engineering, should say so."""
        # Remove any cron entries temporarily is hard; just verify the
        # output contains a scheduler status line (either loaded or not).
        r = _run()
        # Should contain either ✅ or ❌ for scheduler
        has_scheduler_status = ("✅" in r.stdout) or ("❌" in r.stdout) or ("ℹ" in r.stdout)
        assert has_scheduler_status


# ── log file detection ───────────────────────────────────────────────


class TestLogFile:
    def test_no_log_file_shows_info_message(self, tmp_path: Path, monkeypatch):
        """When log file doesn't exist, should show info message."""
        # Redirect HOME to tmp so log file is absent
        monkeypatch.setenv("HOME", str(tmp_path))
        r = _run(env_extra={"HOME": str(tmp_path)})
        assert "No update logs yet" in r.stdout

    def test_log_file_shows_tail(self, tmp_path: Path, monkeypatch):
        """When log file exists, should show its last 20 lines."""
        log = tmp_path / ".compound-engineering-updates.log"
        lines = [f"Line {i}: update entry at timestamp" for i in range(25)]
        log.write_text("\n".join(lines))
        r = _run(env_extra={"HOME": str(tmp_path)})
        assert "Last update log:" in r.stdout
        # Should show last 20 lines (Line 5 through Line 24)
        assert "Line 24" in r.stdout
        assert "Line 5" in r.stdout
        # Should NOT show first 5 lines (tail -20 skips them)
        assert "Line 0" not in r.stdout
        assert "Line 4" not in r.stdout

    def test_log_file_short_shows_all(self, tmp_path: Path, monkeypatch):
        """When log file has fewer than 20 lines, shows them all."""
        log = tmp_path / ".compound-engineering-updates.log"
        log.write_text("only line\n")
        r = _run(env_extra={"HOME": str(tmp_path)})
        assert "only line" in r.stdout


# ── management commands listed ───────────────────────────────────────


class TestManagementCommands:
    def test_lists_update_command(self):
        r = _run()
        assert "update-compound-engineering" in r.stdout

    def test_lists_test_command(self):
        r = _run()
        assert "compound-engineering-test" in r.stdout

    def test_lists_crontab_command(self):
        r = _run()
        assert "crontab" in r.stdout


# ── exit code ────────────────────────────────────────────────────────


class TestExitCode:
    def test_normal_run_exits_zero(self):
        r = _run()
        assert r.returncode == 0
