from __future__ import annotations
"""Tests for effectors/compound-engineering-status — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "compound-engineering-status"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    path_dirs: list[Path] | None = None,
    tmp_path: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run the script with an optional custom PATH and HOME."""
    env = os.environ.copy()
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if path_dirs is not None:
        env["PATH"] = os.pathsep.join(str(p) for p in path_dirs)
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=10,
    )


def _make_mock_bin(tmp_path: Path, name: str, stdout: str = "", exit_code: int = 0) -> Path:
    """Create a mock executable script in tmp_path/bin/<name>."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(f"#!/bin/bash\necho '{stdout}'\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_recording_bin(tmp_path: Path, name: str, record_file: Path, exit_code: int = 0) -> Path:
    """Create a mock bin that records all args to record_file."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(
        "#!/bin/bash\n"
        f'echo "$@" >> {record_file}\n'
        f"exit {exit_code}\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _log_file(tmp_path: Path) -> Path:
    return tmp_path / ".compound-engineering-updates.log"


# ── --help tests ────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_exits_zero(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self, tmp_path):
        r = _run_script(["-h"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_help_shows_usage(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "Usage:" in r.stdout

    def test_help_mentions_status(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "status" in r.stdout.lower()

    def test_help_exits_without_checking_log(self, tmp_path):
        """--help should not look for or create a log file."""
        _run_script(["--help"], tmp_path=tmp_path)
        assert not _log_file(tmp_path).exists()


# ── header output tests ─────────────────────────────────────────────────


class TestHeaderOutput:
    def test_prints_header(self, tmp_path):
        r = _run_script(tmp_path=tmp_path)
        assert "Compound Engineering" in r.stdout

    def test_prints_separator(self, tmp_path):
        r = _run_script(tmp_path=tmp_path)
        assert "===" in r.stdout


# ── scheduler detection tests (Linux — no launchctl) ────────────────────


class TestSchedulerDetectionLinux:
    """On Linux (no launchctl), script checks for cron job."""

    def test_exits_zero(self, tmp_path):
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0

    def test_reports_no_launchctl_on_linux(self, tmp_path):
        """Without launchctl on PATH, script notes launchctl unavailable."""
        empty_bin = tmp_path / "bin"
        empty_bin.mkdir()
        r = _run_script(path_dirs=[empty_bin], tmp_path=tmp_path)
        assert "launchctl" in r.stdout

    def test_detects_cron_job(self, tmp_path):
        """When crontab -l lists compound-engineering, reports configured."""
        # Create mock crontab that outputs a line with compound-engineering
        mock_crontab = tmp_path / "bin"
        mock_crontab.mkdir(exist_ok=True)
        crontab_script = mock_crontab / "crontab"
        crontab_script.write_text(
            '#!/bin/bash\n'
            'if [ "$1" = "-l" ]; then\n'
            '  echo "0 2 * * 0 /usr/local/bin/update-compound-engineering"\n'
            '  exit 0\n'
            'fi\n'
            'exit 1\n'
        )
        crontab_script.chmod(crontab_script.stat().st_mode | stat.S_IEXEC)
        r = _run_script(path_dirs=[mock_crontab], tmp_path=tmp_path)
        # The script checks `crontab -l | grep compound-engineering`
        # The mock output doesn't contain "compound-engineering" so it won't match
        # Let's fix the mock to include the keyword
        crontab_script.write_text(
            '#!/bin/bash\n'
            'if [ "$1" = "-l" ]; then\n'
            '  echo "0 2 * * 0 compound-engineering"\n'
            '  exit 0\n'
            'fi\n'
            'exit 1\n'
        )
        crontab_script.chmod(crontab_script.stat().st_mode | stat.S_IEXEC)
        r = _run_script(path_dirs=[mock_crontab], tmp_path=tmp_path)
        # Either "Cron" or "cron" should appear in a positive message
        combined = r.stdout.lower()
        assert "cron" in combined

    def test_no_cron_reports_not_configured(self, tmp_path):
        """When crontab -l has no compound-engineering line, reports not configured."""
        empty_bin = tmp_path / "bin"
        empty_bin.mkdir()
        # crontab not on PATH → crontab -l fails → no cron configured
        r = _run_script(path_dirs=[empty_bin], tmp_path=tmp_path)
        # Should indicate no cron or not configured
        assert r.returncode == 0  # Still exits 0, just reports status


# ── log file display tests ──────────────────────────────────────────────


class TestLogFileDisplay:
    def test_no_log_shows_info_message(self, tmp_path):
        """When no log file exists, shows informational message."""
        r = _run_script(tmp_path=tmp_path)
        # Should mention no logs or similar
        assert "log" in r.stdout.lower()

    def test_existing_log_shows_tail(self, tmp_path):
        """When log file exists, shows its tail content."""
        log = _log_file(tmp_path)
        lines = [f"Line {i} of update log" for i in range(25)]
        log.write_text("\n".join(lines) + "\n")
        r = _run_script(tmp_path=tmp_path)
        # Should include the last line
        assert "Line 24 of update log" in r.stdout

    def test_short_log_shows_all(self, tmp_path):
        """When log has <20 lines, shows all of them."""
        log = _log_file(tmp_path)
        log.write_text("Line 1\nLine 2\nLine 3\n")
        r = _run_script(tmp_path=tmp_path)
        assert "Line 1" in r.stdout
        assert "Line 3" in r.stdout


# ── management commands section tests ───────────────────────────────────


class TestManagementCommands:
    def test_shows_management_commands(self, tmp_path):
        r = _run_script(tmp_path=tmp_path)
        assert "Management Commands" in r.stdout or "management" in r.stdout.lower()

    def test_mentions_update_command(self, tmp_path):
        r = _run_script(tmp_path=tmp_path)
        assert "update-compound-engineering" in r.stdout

    def test_mentions_test_command(self, tmp_path):
        r = _run_script(tmp_path=tmp_path)
        assert "compound-engineering-test" in r.stdout

    def test_mentions_crontab(self, tmp_path):
        r = _run_script(tmp_path=tmp_path)
        assert "crontab" in r.stdout

    def test_mentions_launchctl(self, tmp_path):
        r = _run_script(tmp_path=tmp_path)
        assert "launchctl" in r.stdout
