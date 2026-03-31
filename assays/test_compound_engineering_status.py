#!/usr/bin/env python3
"""Tests for compound-engineering-status effector — bash script status checker."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

EFFECTOR = Path.home() / "germline" / "effectors" / "compound-engineering-status"


# ---------------------------------------------------------------------------
# --help / -h
# ---------------------------------------------------------------------------


class TestHelpFlag:
    """The --help and -h flags should print usage and exit 0."""

    @pytest.mark.parametrize("flag", ["--help", "-h"])
    def test_help_exits_zero(self, flag: str):
        result = subprocess.run(
            [str(EFFECTOR), flag],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    @pytest.mark.parametrize("flag", ["--help", "-h"])
    def test_help_mentions_usage(self, flag: str):
        result = subprocess.run(
            [str(EFFECTOR), flag],
            capture_output=True,
            text=True,
        )
        assert "Usage:" in result.stdout

    @pytest.mark.parametrize("flag", ["--help", "-h"])
    def test_help_mentions_command_name(self, flag: str):
        result = subprocess.run(
            [str(EFFECTOR), flag],
            capture_output=True,
            text=True,
        )
        assert "compound-engineering-status" in result.stdout


# ---------------------------------------------------------------------------
# Normal run — Linux environment (no launchctl)
# ---------------------------------------------------------------------------


class TestNormalRun:
    """Default invocation on Linux (no launchctl, no cron, no log)."""

    @pytest.fixture(autouse=True)
    def _run_script(self, tmp_path, monkeypatch):
        """Run the script with $HOME redirected so it won't read real logs."""
        monkeypatch.setenv("HOME", str(tmp_path))
        self.tmp = tmp_path
        self.result = subprocess.run(
            [str(EFFECTOR)],
            capture_output=True,
            text=True,
            env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"},
        )

    def test_exits_zero(self):
        assert self.result.returncode == 0

    def test_header_present(self):
        assert "Compound Engineering Auto-Update Status" in self.result.stdout

    def test_no_launchctl_message(self):
        """On Linux launchctl is absent, should print the fallback message."""
        assert "launchctl not available" in self.result.stdout

    def test_no_cron_message(self):
        """With empty crontab (or none), should report no cron job."""
        assert "No cron job configured" in self.result.stdout

    def test_no_log_message(self):
        """With no log file under $HOME, should say no logs yet."""
        assert "No update logs yet" in self.result.stdout

    def test_management_commands_section(self):
        assert "Management Commands" in self.result.stdout

    def test_management_mentions_update_command(self):
        assert "update-compound-engineering" in self.result.stdout


# ---------------------------------------------------------------------------
# Log file present
# ---------------------------------------------------------------------------


class TestLogFilePresent:
    """When the log file exists, the script should show its tail."""

    LOG_CONTENT = textwrap.dedent("""\
        2025-01-01 10:00:00 Starting update
        2025-01-01 10:00:01 Fetching sources
        2025-01-01 10:00:02 Processing feed A
        2025-01-01 10:00:03 Processing feed B
        2025-01-01 10:00:04 Done — 2 items updated
        line6
        line7
        line8
        line9
        line10
        line11
        line12
        line13
        line14
        line15
        line16
        line17
        line18
        line19
        line20
        LAST-VISIBLE-LINE
    """)

    @pytest.fixture(autouse=True)
    def _prepare(self, tmp_path, monkeypatch):
        log = tmp_path / ".compound-engineering-updates.log"
        log.write_text(self.LOG_CONTENT, encoding="utf-8")
        monkeypatch.setenv("HOME", str(tmp_path))
        self.result = subprocess.run(
            [str(EFFECTOR)],
            capture_output=True,
            text=True,
            env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"},
        )

    def test_exits_zero(self):
        assert self.result.returncode == 0

    def test_last_update_log_header(self):
        assert "Last update log" in self.result.stdout

    def test_tail_content_shown(self):
        """The last line of the log file should appear in output."""
        assert "LAST-VISIBLE-LINE" in self.result.stdout

    def test_early_log_lines_not_shown(self):
        """tail -20 means early lines should not appear."""
        assert "Starting update" not in self.result.stdout


# ---------------------------------------------------------------------------
# Cron configured
# ---------------------------------------------------------------------------


class TestCronConfigured:
    """When crontab contains compound-engineering, script should report it."""

    @pytest.fixture(autouse=True)
    def _prepare(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))

        # Create a fake crontab that returns a line mentioning compound-engineering
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        crontab_script = fake_bin / "crontab"
        crontab_script.write_text(
            '#!/bin/bash\nif [ "$1" = "-l" ]; then echo "0 2 * * 0 /home/terry/germline/effectors/auto-update-compound-engineering.sh"; exit 0; fi; exit 1\n',
            encoding="utf-8",
        )
        crontab_script.chmod(0o755)

        self.result = subprocess.run(
            [str(EFFECTOR)],
            capture_output=True,
            text=True,
            env={
                "HOME": str(tmp_path),
                "PATH": f"{fake_bin}:/usr/bin:/bin",
            },
        )

    def test_exits_zero(self):
        assert self.result.returncode == 0

    def test_cron_configured_message(self):
        assert "Cron job is configured" in self.result.stdout

    def test_no_cron_missing_message(self):
        """Should NOT say 'No cron job' when cron is configured."""
        assert "No cron job configured" not in self.result.stdout


# ---------------------------------------------------------------------------
# macOS launchctl path (simulated)
# ---------------------------------------------------------------------------


class TestLaunchctlAvailable:
    """When launchctl is on PATH and lists the agent, report loaded."""

    @pytest.fixture(autouse=True)
    def _prepare(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))

        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()

        # Fake launchctl that responds to `list` with the expected plist
        launchctl = fake_bin / "launchctl"
        launchctl.write_text(
            '#!/bin/bash\nif [ "$1" = "list" ]; then echo "com.terry.compound-engineering-update"; exit 0; fi; exit 0\n',
            encoding="utf-8",
        )
        launchctl.chmod(0o755)

        self.result = subprocess.run(
            [str(EFFECTOR)],
            capture_output=True,
            text=True,
            env={
                "HOME": str(tmp_path),
                "PATH": f"{fake_bin}:/usr/bin:/bin",
            },
        )

    def test_exits_zero(self):
        assert self.result.returncode == 0

    def test_launchagent_loaded_message(self):
        assert "LaunchAgent is loaded and active" in self.result.stdout

    def test_schedule_mentioned(self):
        assert "Schedule:" in self.result.stdout


class TestLaunchctlAvailableButNotLoaded:
    """When launchctl exists but the agent is not listed."""

    @pytest.fixture(autouse=True)
    def _prepare(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))

        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()

        launchctl = fake_bin / "launchctl"
        launchctl.write_text(
            '#!/bin/bash\nif [ "$1" = "list" ]; then echo ""; exit 0; fi; exit 0\n',
            encoding="utf-8",
        )
        launchctl.chmod(0o755)

        self.result = subprocess.run(
            [str(EFFECTOR)],
            capture_output=True,
            text=True,
            env={
                "HOME": str(tmp_path),
                "PATH": f"{fake_bin}:/usr/bin:/bin",
            },
        )

    def test_exits_zero(self):
        assert self.result.returncode == 0

    def test_launchagent_not_loaded_message(self):
        assert "LaunchAgent is not loaded" in self.result.stdout
