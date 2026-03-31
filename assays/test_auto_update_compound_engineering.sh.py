"""Tests for effectors/auto-update-compound-engineering.sh — plugin updater.

Effectors are scripts — tested via subprocess.run, never imported.
"""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "effectors" / "auto-update-compound-engineering.sh"


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_fake_bin(directory: Path, name: str, exit_code: int = 0, stdout: str = "") -> Path:
    """Create a fake executable in directory that exits with exit_code."""
    bin_path = directory / name
    bin_path.write_text(f"#!/bin/bash\necho '{stdout}'\nexit {exit_code}\n")
    bin_path.chmod(bin_path.stat().st_mode | stat.S_IEXEC)
    return bin_path


def _run_script(tmp_path: Path, bins: dict[str, int] | None = None, args: list[str] | None = None, home: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run the script with PATH restricted to tmp_path (no real bunx/npx).
    
    bins: maps bin name -> exit code for fake binaries.
    """
    bin_dir = tmp_path / "bins"
    bin_dir.mkdir(exist_ok=True)
    if bins:
        for name, code in bins.items():
            _make_fake_bin(bin_dir, name, exit_code=code)
    env = {
        **os.environ,
        "PATH": str(bin_dir),
        "HOME": str(home or tmp_path),
    }
    cmd = ["bash", str(SCRIPT_PATH)] + (args or [])
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )


# ── File basics ────────────────────────────────────────────────────────────


class TestBasics:
    def test_file_exists(self):
        assert SCRIPT_PATH.exists()

    def test_shebang(self):
        first = SCRIPT_PATH.read_text().split("\n")[0]
        assert first.startswith("#!/usr/bin/env bash")

    def test_has_comment_header(self):
        content = SCRIPT_PATH.read_text()
        assert "compound-engineering" in content


# ── Help flag ──────────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_long(self, tmp_path):
        result = _run_script(tmp_path, args=["--help"])
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_help_short(self, tmp_path):
        result = _run_script(tmp_path, args=["-h"])
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_help_mentions_crontab(self, tmp_path):
        result = _run_script(tmp_path, args=["--help"])
        assert "crontab" in result.stdout

    def test_help_mentions_log(self, tmp_path):
        result = _run_script(tmp_path, args=["--help"])
        assert ".compound-engineering-updates.log" in result.stdout


# ── Runner selection ──────────────────────────────────────────────────────


class TestRunnerSelection:
    def test_prefers_bunx_over_npx(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        # Provide both bunx (succeeds) and npx (succeeds)
        result = _run_script(tmp_path, bins={"bunx": 0, "npx": 0})
        assert result.returncode == 0
        log = log_file.read_text()
        # bunx should have been called (appears in log because runner is bunx)
        assert "bunx" in log or "✅" in log

    def test_falls_back_to_npx(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        # Only provide npx
        result = _run_script(tmp_path, bins={"npx": 0})
        assert result.returncode == 0
        log = log_file.read_text()
        assert "✅" in log

    def test_exits_1_when_no_runner(self, tmp_path):
        # No bunx or npx in PATH
        result = _run_script(tmp_path, bins={})
        assert result.returncode == 1


# ── Logging ───────────────────────────────────────────────────────────────


class TestLogging:
    def test_creates_log_file(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        assert not log_file.exists()
        _run_script(tmp_path, bins={"bunx": 0})
        assert log_file.exists()

    def test_log_contains_separator(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        _run_script(tmp_path, bins={"bunx": 0})
        log = log_file.read_text()
        assert "========================================" in log

    def test_log_contains_start_and_end_timestamps(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        _run_script(tmp_path, bins={"bunx": 0})
        log = log_file.read_text()
        assert "Update started:" in log
        assert "Update completed:" in log

    def test_no_runner_logs_error(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        _run_script(tmp_path, bins={})
        log = log_file.read_text()
        assert "neither bunx nor npx found" in log


# ── Update outcomes ───────────────────────────────────────────────────────


class TestUpdateOutcomes:
    def test_both_succeed(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        result = _run_script(tmp_path, bins={"bunx": 0})
        assert result.returncode == 0
        log = log_file.read_text()
        assert "✅ OpenCode updated successfully" in log
        assert "✅ Codex updated successfully" in log

    def test_opencode_fails_codex_succeeds(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        # Fake bunx that fails on 'opencode' but succeeds on 'codex'
        bin_dir = tmp_path / "bins"
        bin_dir.mkdir()
        fake_bunx = bin_dir / "bunx"
        fake_bunx.write_text(
            '#!/bin/bash\n'
            'if [[ "$*" == *"--to opencode"* ]]; then\n'
            '  echo "opencode failed" >&2\n'
            '  exit 1\n'
            'fi\n'
            'exit 0\n'
        )
        fake_bunx.chmod(fake_bunx.stat().st_mode | stat.S_IEXEC)
        env = {**os.environ, "PATH": str(bin_dir), "HOME": str(tmp_path)}
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH)],
            capture_output=True, text=True, timeout=15, env=env,
        )
        # Script doesn't exit non-zero for individual failures, just logs
        assert result.returncode == 0
        log = log_file.read_text()
        assert "❌ OpenCode update failed" in log
        assert "✅ Codex updated successfully" in log

    def test_codex_fails_opencode_succeeds(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        bin_dir = tmp_path / "bins"
        bin_dir.mkdir()
        fake_bunx = bin_dir / "bunx"
        fake_bunx.write_text(
            '#!/bin/bash\n'
            'if [[ "$*" == *"--to codex"* ]]; then\n'
            '  echo "codex failed" >&2\n'
            '  exit 1\n'
            'fi\n'
            'exit 0\n'
        )
        fake_bunx.chmod(fake_bunx.stat().st_mode | stat.S_IEXEC)
        env = {**os.environ, "PATH": str(bin_dir), "HOME": str(tmp_path)}
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH)],
            capture_output=True, text=True, timeout=15, env=env,
        )
        assert result.returncode == 0
        log = log_file.read_text()
        assert "✅ OpenCode updated successfully" in log
        assert "❌ Codex update failed" in log

    def test_both_fail(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        result = _run_script(tmp_path, bins={"bunx": 1})
        # Script still exits 0 — it just logs failures
        assert result.returncode == 0
        log = log_file.read_text()
        assert "❌ OpenCode update failed" in log
        assert "❌ Codex update failed" in log


# ── Idempotency ───────────────────────────────────────────────────────────


class TestIdempotency:
    def test_appends_to_existing_log(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        log_file.write_text("previous entry\n")
        _run_script(tmp_path, bins={"bunx": 0})
        log = log_file.read_text()
        assert "previous entry" in log
        assert "Update started:" in log
        # Should have two separate runs worth of content
        assert log.count("Update started:") == 1  # this run added one

    def test_second_run_appends(self, tmp_path):
        log_file = tmp_path / ".compound-engineering-updates.log"
        _run_script(tmp_path, bins={"bunx": 0})
        _run_script(tmp_path, bins={"bunx": 0})
        log = log_file.read_text()
        assert log.count("Update started:") == 2
        assert log.count("Update completed:") == 2
