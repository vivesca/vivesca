from __future__ import annotations

"""Tests for effectors/start-chrome-debug.sh — bash script tested via subprocess."""

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "start-chrome-debug.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    path_dirs: list[Path] | None = None,
    tmp_path: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run the script with optional custom PATH and HOME."""
    env = os.environ.copy()
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if path_dirs is not None:
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
    script.write_text(f"#!/bin/bash\necho '{stdout}'\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


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

    def test_help_mentions_port_option(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "--port" in r.stdout or "-p" in r.stdout


# ── argument parsing tests ───────────────────────────────────────────────


class TestArgParsing:
    def test_unknown_option_exits_2(self, tmp_path):
        r = _run_script(["--unknown"], tmp_path=tmp_path)
        assert r.returncode == 2

    def test_unknown_option_stderr_message(self, tmp_path):
        r = _run_script(["--unknown"], tmp_path=tmp_path)
        assert "Unknown option" in r.stderr

    def test_port_short_flag_requires_value(self, tmp_path):
        """-p without value should error (bash set -u or missing arg)."""
        r = _run_script(["-p"], tmp_path=tmp_path)
        # Should fail - either missing arg or shift error
        assert r.returncode != 0

    def test_port_long_flag_requires_value(self, tmp_path):
        """--port without value should error."""
        r = _run_script(["--port"], tmp_path=tmp_path)
        assert r.returncode != 0


# ── Chrome detection tests ───────────────────────────────────────────────


class TestChromeDetection:
    def test_no_chrome_found_exits_1(self, tmp_path):
        """Script exits 1 when no Chrome binary is on PATH."""
        # Build a minimal PATH with bash but no chrome
        safe_bin = tmp_path / "safe-bin"
        safe_bin.mkdir()
        bash_path = shutil.which("bash")
        os.symlink(bash_path, safe_bin / "bash")
        # Need curl for the pre-check, uname for platform detection
        for cmd in ("curl", "uname"):
            p = shutil.which(cmd)
            if p:
                os.symlink(p, safe_bin / cmd)
        r = _run_script(path_dirs=[safe_bin], tmp_path=tmp_path)
        assert r.returncode == 1

    def test_no_chrome_error_message(self, tmp_path):
        """Error message mentions Chrome not found."""
        safe_bin = tmp_path / "safe-bin"
        safe_bin.mkdir()
        bash_path = shutil.which("bash")
        os.symlink(bash_path, safe_bin / "bash")
        for cmd in ("curl", "uname"):
            p = shutil.which(cmd)
            if p:
                os.symlink(p, safe_bin / cmd)
        r = _run_script(path_dirs=[safe_bin], tmp_path=tmp_path)
        assert "Chrome" in r.stderr or "Chrome" in r.stdout


# ── already running check tests ──────────────────────────────────────────


class TestAlreadyRunningCheck:
    def test_chrome_already_running_exits_0(self, tmp_path):
        """When curl to debug port succeeds, script exits 0."""
        # Create mock curl that returns success (simulates Chrome already running)
        bindir = _make_mock_bin(tmp_path, "curl", stdout='{"Browser": "Chrome"}', exit_code=0)
        # Create mock chrome (won't be called since curl succeeds)
        _make_mock_bin(tmp_path, "google-chrome-stable")
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_chrome_already_running_message(self, tmp_path):
        """When Chrome already running, message indicates that."""
        bindir = _make_mock_bin(tmp_path, "curl", stdout='OK', exit_code=0)
        _make_mock_bin(tmp_path, "google-chrome-stable")
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert "already running" in r.stdout.lower()

    def test_already_running_uses_correct_port(self, tmp_path):
        """Curl is called with the specified port."""
        # This tests that -p flag changes the port used in the curl check
        bindir = _make_mock_bin(tmp_path, "curl", stdout='OK', exit_code=0)
        _make_mock_bin(tmp_path, "google-chrome-stable")
        r = _run_script(["-p", "9999"], path_dirs=[bindir], tmp_path=tmp_path)
        assert r.returncode == 0
        # The message should mention port 9999
        assert "9999" in r.stdout


# ── platform detection tests ─────────────────────────────────────────────


class TestPlatformDetection:
    def test_linux_uses_chromium_candidates(self, tmp_path):
        """On Linux, script looks for google-chrome-stable, google-chrome, etc."""
        # Mock curl to fail (Chrome not already running)
        bindir = _make_mock_bin(tmp_path, "curl", exit_code=1)
        # Mock a chrome candidate that exits immediately
        chrome_script = tmp_path / "bin" / "google-chrome-stable"
        chrome_script.write_text("#!/bin/bash\nexit 0\n")
        chrome_script.chmod(chrome_script.stat().st_mode | stat.S_IEXEC)
        # Script should start Chrome and succeed
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        # Should not error on "Chrome not found"
        assert "not found" not in r.stderr.lower()


# ── startup verification tests ────────────────────────────────────────────


class TestStartupVerification:
    def test_chrome_start_success_message(self, tmp_path):
        """When Chrome starts, success message is printed."""
        bindir = _make_mock_bin(tmp_path, "curl", exit_code=1)
        # Mock chrome that stays alive briefly then exits cleanly
        chrome_script = tmp_path / "bin" / "google-chrome-stable"
        chrome_script.write_text("#!/bin/bash\nsleep 0.5\nexit 0\n")
        chrome_script.chmod(chrome_script.stat().st_mode | stat.S_IEXEC)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert "Chrome started" in r.stdout or r.returncode == 0

    def test_connect_url_printed(self, tmp_path):
        """Output includes the localhost URL for connecting."""
        bindir = _make_mock_bin(tmp_path, "curl", exit_code=1)
        chrome_script = tmp_path / "bin" / "google-chrome-stable"
        chrome_script.write_text("#!/bin/bash\nsleep 0.5\nexit 0\n")
        chrome_script.chmod(chrome_script.stat().st_mode | stat.S_IEXEC)
        r = _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert "localhost" in r.stdout
