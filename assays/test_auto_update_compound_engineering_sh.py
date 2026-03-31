"""Tests for effectors/auto-update-compound-engineering.sh — bash script tested via subprocess."""
from __future__ import annotations

import os
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "auto-update-compound-engineering.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    path_dirs: list[Path] | None = None,
    tmp_path: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run the script with an optional custom PATH.

    If path_dirs provided, prepend them to PATH but keep system entries
    so essential commands like bash are still found. This works for
        tests that block all bunx/npx except what they explicitly provide.
    """
    env = os.environ.copy()
    # Unset HOME override if present so script uses tmp_path as HOME
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if path_dirs is not None:
        # Prepend custom path dirs, keep system PATH after
        # This ensures bash is still found but any system-level
        # bunx/npx comes AFTER our mocks and only gets used if
        # we don't provide a mock
        env["PATH"] = os.pathsep.join(str(p) for p in path_dirs) + os.pathsep + env.get("PATH", "")
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
    script.write_text(f"#!/bin/bash\necho {stdout}\nexit {exit_code}\n")
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

    def test_help_mentions_crontab(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "crontab" in r.stdout

    def test_help_does_not_create_log(self, tmp_path):
        _run_script(["--help"], tmp_path=tmp_path)
        assert not _log_file(tmp_path).exists()


# ── runner selection tests ──────────────────────────────────────────────


class TestRunnerSelection:
    def test_no_runner_exits_1(self, tmp_path):
        """Script exits 1 when neither bunx nor npx is on PATH."""
        # Filter system PATH to remove any dirs that might contain bunx/npx
        filtered_path_dirs = []
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            # Check if this directory already has bunx or npx
            has_bunx = (Path(dir_path) / "bunx").exists()
            has_npx = (Path(dir_path) / "npx").exists()
            if not has_bunx and not has_npx:
                filtered_path_dirs.append(Path(dir_path))
        r = _run_script(path_dirs=filtered_path_dirs, tmp_path=tmp_path)
        assert r.returncode == 1

    def test_no_runner_logs_error(self, tmp_path):
        # Filter system PATH to remove any dirs that might contain bunx/npx
        filtered_path_dirs = []
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            has_bunx = (Path(dir_path) / "bunx").exists()
            has_npx = (Path(dir_path) / "npx").exists()
            if not has_bunx and not has_npx:
                filtered_path_dirs.append(Path(dir_path))
        _run_script(path_dirs=filtered_path_dirs, tmp_path=tmp_path)
        log = _log_file(tmp_path)
        assert log.exists()
        assert "neither bunx nor npx found" in log.read_text()

    def test_uses_bunx_when_available(self, tmp_path):
        """bunx on PATH → uses bunx as runner."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        calls = record.read_text()
        # Should have been called twice (opencode + codex)
        assert "@every-env/compound-plugin" in calls

    def test_uses_npx_when_bunx_missing(self, tmp_path):
        """npx on PATH (no bunx) → uses npx."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "npx", record)
        # Filter system PATH to remove any dir that contains bunx
        filtered_path = [bindir]
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            if not (Path(dir_path) / "bunx").exists():
                filtered_path.append(Path(dir_path))
        r = _run_script(path_dirs=filtered_path, tmp_path=tmp_path)
        assert r.returncode == 0
        calls = record.read_text()
        assert "@every-env/compound-plugin" in calls

    def test_prefers_bunx_over_npx(self, tmp_path):
        """Both bunx and npx available → bunx is used."""
        bunx_record = tmp_path / "bunx_calls.log"
        npx_record = tmp_path / "npx_calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", bunx_record)
        _make_recording_bin(tmp_path, "npx", npx_record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert bunx_record.exists() and bunx_record.read_text().strip() != ""
        assert not npx_record.exists() or npx_record.read_text().strip() == ""


# ── logging tests ───────────────────────────────────────────────────────


class TestLogging:
    def test_creates_log_file(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert _log_file(tmp_path).exists()

    def test_log_contains_start_marker(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Update started:" in log_text
        assert "========================================" in log_text

    def test_log_contains_end_marker(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Update completed:" in log_text

    def test_log_contains_dates(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        # Should contain a date-like string (e.g. "Mon 31 Mar 2026")
        # Just check that timestamps are present via the date command output
        import re
        # date outputs vary but always contain a year
        assert re.search(r"20\d{2}", log_text) is not None


# ── opencode / codex update tests ───────────────────────────────────────


class TestUpdateTargets:
    def test_runs_opencode_update(self, tmp_path):
        """Script runs compound-engineering install --to opencode."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = record.read_text()
        assert "--to opencode" in calls

    def test_runs_codex_update(self, tmp_path):
        """Script runs compound-engineering install --to codex."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = record.read_text()
        assert "--to codex" in calls

    def test_opencode_success_logged(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "OpenCode updated successfully" in log_text

    def test_codex_success_logged(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Codex updated successfully" in log_text

    def test_opencode_failure_logged(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx", exit_code=1)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "OpenCode update failed" in log_text

    def test_codex_failure_logged(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx", exit_code=1)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Codex update failed" in log_text

    def test_failure_does_not_stop_second_update(self, tmp_path):
        """Even if opencode fails, codex update still runs."""
        record = tmp_path / "calls.log"
        bindir = _make_recording_bin(tmp_path, "bunx", record, exit_code=1)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        calls = record.read_text().strip().splitlines()
        assert len(calls) == 2  # Both opencode and codex attempted


# ── log file location ───────────────────────────────────────────────────


class TestLogFileLocation:
    def test_log_uses_home_env(self, tmp_path):
        """Log file is written to $HOME/.compound-engineering-updates.log."""
        bindir = _make_mock_bin(tmp_path, "bunx")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log = tmp_path / ".compound-engineering-updates.log"
        assert log.exists()

    def test_script_exits_0_on_success(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "bunx")
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
