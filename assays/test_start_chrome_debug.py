from __future__ import annotations

"""Tests for effectors/start-chrome-debug.sh — Chrome remote-debugging launcher.

Uses subprocess.run (effectors are scripts, not importable modules).
Fake Chrome binaries are created in tmp directories to isolate from the host.
"""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline" / "effectors" / "start-chrome-debug.sh"


def _run(args: list[str] | None = None, *, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    """Run the script with optional args and env overrides.

    Uses /usr/bin/bash as executable so PATH overrides don't break it.
    When env provides a custom PATH, system bin dirs are appended automatically.
    """
    cmd = ["/usr/bin/bash", str(SCRIPT)] + (args or [])
    merged = {**os.environ, **(env or {})}
    # Ensure system dirs stay on PATH so curl etc. remain available
    if env and "PATH" in env:
        merged["PATH"] = env["PATH"] + ":/usr/bin:/bin"
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=merged,
        timeout=10,
    )


def _fake_chrome_dir(tmp_path: Path, name: str = "google-chrome-stable") -> Path:
    """Create a tmp bin dir containing a fake chrome executable."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    chrome = bin_dir / name
    chrome.write_text("#!/bin/bash\n# fake chrome\nexit 0\n")
    chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)
    return bin_dir


# ── Help / usage ──────────────────────────────────────────────────────


class TestHelp:
    def test_help_long_flag(self):
        r = _run(["--help"])
        assert r.returncode == 0
        assert "Usage:" in r.stdout
        assert "--port" in r.stdout

    def test_help_short_flag(self):
        r = _run(["-h"])
        assert r.returncode == 0
        assert "Usage:" in r.stdout

    def test_help_mentions_default_port(self):
        r = _run(["--help"])
        assert "9222" in r.stdout


# ── Unknown option ────────────────────────────────────────────────────


class TestUnknownOption:
    def test_unknown_flag_exits_2(self):
        r = _run(["--bogus"])
        assert r.returncode == 2

    def test_unknown_flag_stderr_message(self):
        r = _run(["--bogus"])
        assert "Unknown option" in r.stderr


# ── Chrome not found ─────────────────────────────────────────────────


class TestChromeNotFound:
    def test_exits_1_when_no_chrome(self, tmp_path, monkeypatch):
        # PATH with no chrome candidates
        empty_bin = tmp_path / "empty_bin"
        empty_bin.mkdir()
        r = _run(env={"PATH": str(empty_bin)})
        assert r.returncode == 1
        assert "not found" in r.stderr.lower()


# ── Chrome binary found but not executable ────────────────────────────


class TestChromeNotExecutable:
    def test_non_executable_chrome_exits_1(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        chrome = bin_dir / "google-chrome-stable"
        chrome.write_text("#!/bin/bash\nexit 0\n")
        # Leave it non-executable
        r = _run(env={"PATH": str(bin_dir)})
        # The script checks `command -v` first (finds it), then `-x`
        assert r.returncode == 1
        assert "not executable" in r.stderr.lower()


# ── Port flag accepted ────────────────────────────────────────────────


class TestPortFlag:
    def test_custom_port_passed_through(self, tmp_path):
        """With a fake chrome that echoes its args, verify --port is accepted."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        # Fake chrome that just sleeps briefly so background check works
        chrome = bin_dir / "google-chrome-stable"
        chrome.write_text("#!/bin/bash\necho ARGS: $@ >&2\nsleep 0.5\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(["--port", "9333"], env={"PATH": str(bin_dir)})
        # The script should start chrome (in background) and report success
        # It will also curl localhost:9333 first, which will fail (good — proceeds to launch)
        assert r.returncode == 0
        assert "9333" in r.stdout

    def test_default_port_is_9222(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        chrome = bin_dir / "google-chrome-stable"
        chrome.write_text("#!/bin/bash\nsleep 0.5\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        assert "9222" in r.stdout


# ── Chrome already running (curl succeeds) ────────────────────────────


class TestChromeAlreadyRunning:
    def test_detects_running_chrome(self, tmp_path):
        """If curl to the debug port succeeds, script exits 0 without launching."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        # A fake curl that succeeds
        curl = bin_dir / "curl"
        curl.write_text("#!/bin/bash\nexit 0\n")
        curl.chmod(curl.stat().st_mode | stat.S_IEXEC)

        # No chrome in PATH (should not be needed if curl succeeds first)
        r = _run(env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        assert "already running" in r.stdout.lower()


# ── Chrome starts and background check passes ─────────────────────────


class TestChromeStarts:
    def test_successful_start_message(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        chrome = bin_dir / "google-chrome-stable"
        chrome.write_text("#!/bin/bash\nsleep 1\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        assert "Chrome started" in r.stdout
        assert "pid" in r.stdout.lower()


# ── Chrome dies immediately ──────────────────────────────────────────


class TestChromeDiesImmediately:
    def test_immediate_exit_detected(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        chrome = bin_dir / "google-chrome-stable"
        # Chrome exits immediately
        chrome.write_text("#!/bin/bash\nexit 1\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(env={"PATH": str(bin_dir)})
        assert r.returncode == 1
        assert "failed to start" in r.stderr.lower()
