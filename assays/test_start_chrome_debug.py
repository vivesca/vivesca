from __future__ import annotations

"""Tests for effectors/start-chrome-debug.sh — Chrome remote-debugging launcher.

Uses subprocess.run (effectors are scripts, not importable modules).
Fake Chrome binaries are created in tmp directories to isolate from the host.
"""

import os
import stat
import subprocess
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "start-chrome-debug.sh"


def _wait_for_file(path: Path, timeout: float = 3.0, interval: float = 0.1) -> None:
    """Poll until *path* exists, raising AssertionError on timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(interval)
    raise AssertionError(f"File not created within {timeout}s: {path}")


def _read_script() -> str:
    return SCRIPT.read_text()


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


# ── Structural tests ──────────────────────────────────────────────────


class TestScriptStructure:
    """Verify the script has required structural elements."""

    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_executable(self):
        mode = SCRIPT.stat().st_mode
        assert mode & stat.S_IEXEC, "start-chrome-debug.sh should be executable"

    def test_shebang(self):
        lines = _read_script().splitlines()
        assert lines[0].startswith("#!") and "bash" in lines[0]

    def test_strict_mode(self):
        assert "set -euo pipefail" in _read_script()

    def test_default_port_set(self):
        assert "DEBUG_PORT=9222" in _read_script()

    def test_no_todo_or_fixme(self):
        for line in _read_script().splitlines():
            upper = line.upper()
            assert "TODO" not in upper, f"Found TODO: {line.strip()}"
            assert "FIXME" not in upper, f"Found FIXME: {line.strip()}"

    def test_script_ends_with_newline(self):
        assert _read_script().endswith("\n"), "Script should end with a newline"


class TestSyntaxCheck:
    """Verify the script is syntactically valid bash."""

    def test_bash_syntax_valid(self):
        r = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0, f"Syntax error:\n{r.stderr}"

    def test_shellcheck_if_available(self):
        r = subprocess.run(
            ["which", "shellcheck"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            pytest.skip("shellcheck not installed")
        r = subprocess.run(
            ["shellcheck", str(SCRIPT)],
            capture_output=True, text=True, timeout=10,
        )
        errors = [
            line for line in r.stdout.splitlines()
            if "error" in line.lower()
        ]
        assert not errors, f"shellcheck errors:\n{r.stdout}"


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
    def test_exits_1_when_no_chrome(self, tmp_path):
        # PATH with no chrome candidates — only system dirs will be appended
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
        """With a fake chrome that survives the 1s background check."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        # Fake chrome must sleep >2s: script does `sleep 1` then kill -0 check
        chrome = bin_dir / "google-chrome-stable"
        chrome.write_text("#!/bin/bash\nsleep 3\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(["--port", "9333"], env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        assert "9333" in r.stdout

    def test_short_flag_p(self, tmp_path):
        """Short -p flag should behave identically to --port."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        chrome = bin_dir / "google-chrome-stable"
        chrome.write_text("#!/bin/bash\nsleep 3\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(["-p", "9444"], env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        assert "9444" in r.stdout

    def test_default_port_is_9222(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        chrome = bin_dir / "google-chrome-stable"
        chrome.write_text("#!/bin/bash\nsleep 3\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        assert "9222" in r.stdout


# ── Chrome receives correct flags ─────────────────────────────────────


class TestChromeArgs:
    """Verify Chrome is launched with the correct arguments."""

    def test_remote_debugging_port_flag(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        log = tmp_path / "chrome_args.log"
        chrome = bin_dir / "google-chrome-stable"
        chrome.write_text(f"#!/bin/bash\necho \"$@\" > {log}\nsleep 3\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(["--port", "9333"], env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        _wait_for_file(log)
        args = log.read_text()
        assert "--remote-debugging-port=9333" in args

    def test_user_data_dir_flag(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        log = tmp_path / "chrome_args.log"
        chrome = bin_dir / "google-chrome-stable"
        chrome.write_text(f"#!/bin/bash\necho \"$@\" > {log}\nsleep 3\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        _wait_for_file(log)
        args = log.read_text()
        assert "--user-data-dir=" in args

    def test_connect_url_printed(self, tmp_path):
        """Script should print the connect URL after launch."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        chrome = bin_dir / "google-chrome-stable"
        chrome.write_text("#!/bin/bash\nsleep 3\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        assert "Connect via: http://localhost:9222" in r.stdout


# ── Chromium fallback ─────────────────────────────────────────────────


class TestChromiumFallback:
    """Verify the script picks up alternative Chrome/Chromium binary names."""

    @pytest.mark.parametrize("name", ["google-chrome-stable", "google-chrome",
                                       "chromium-browser", "chromium"])
    def test_fallback_binary_found(self, tmp_path, name: str):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        chrome = bin_dir / name
        chrome.write_text("#!/bin/bash\nsleep 3\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        assert "Chrome started" in r.stdout

    def test_first_candidate_wins(self, tmp_path):
        """When multiple candidates exist, the first (google-chrome-stable) wins."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        log = tmp_path / "which_chrome.log"

        for name in ("google-chrome-stable", "google-chrome",
                     "chromium-browser", "chromium"):
            chrome = bin_dir / name
            chrome.write_text(f"#!/bin/bash\necho '{name}' >> {log}\nsleep 3\n")
            chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        r = _run(env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        lines = log.read_text().strip().splitlines()
        assert lines == ["google-chrome-stable"]


# ── Platform detection ────────────────────────────────────────────────


class TestPlatformDetection:
    """Test platform detection logic."""

    def test_linux_searches_multiple_candidates(self):
        content = _read_script()
        for name in ("google-chrome-stable", "google-chrome", "chromium-browser", "chromium"):
            assert name in content

    def test_darwin_path_in_script(self):
        content = _read_script()
        assert "Darwin" in content
        assert "Google Chrome.app" in content

    def test_unsupported_platform_exits_1(self):
        mock_script = f'uname() {{ echo "FreeBSD"; }}\n. {SCRIPT}'
        r = subprocess.run(
            ["bash", "-c", mock_script],
            capture_output=True, text=True,
        )
        assert r.returncode == 1
        assert "Unsupported platform:" in r.stderr


# ── Chrome already running (curl succeeds) ────────────────────────────


class TestChromeAlreadyRunning:
    def test_detects_running_chrome(self, tmp_path):
        """If curl to the debug port succeeds, script exits 0 without launching.

        Chrome detection runs before the curl check, so we need a fake chrome
        binary in PATH as well.
        """
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        # Fake chrome (found by detection loop but never launched)
        chrome = bin_dir / "google-chrome-stable"
        chrome.write_text("#!/bin/bash\nsleep 3\n")
        chrome.chmod(chrome.stat().st_mode | stat.S_IEXEC)

        # A fake curl that succeeds — placed BEFORE /usr/bin in PATH
        curl = bin_dir / "curl"
        curl.write_text("#!/bin/bash\nexit 0\n")
        curl.chmod(curl.stat().st_mode | stat.S_IEXEC)

        r = _run(env={"PATH": str(bin_dir)})
        assert r.returncode == 0
        assert "already running" in r.stdout.lower()


# ── Chrome starts and background check passes ─────────────────────────


class TestChromeStarts:
    def test_successful_start_message(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        chrome = bin_dir / "google-chrome-stable"
        # Sleep long enough to survive the script's 1s wait + kill -0 check
        chrome.write_text("#!/bin/bash\nsleep 3\n")
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
