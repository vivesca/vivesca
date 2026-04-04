from __future__ import annotations

"""Tests for effectors/start-chrome-debug.sh — start Chrome with remote debugging."""

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "effectors" / "start-chrome-debug.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    path_dirs: list[Path] | None = None,
    tmp_path: Path | None = None,
    replace_path: bool = False,
) -> subprocess.CompletedProcess:
    """Run start-chrome-debug.sh with an optional custom PATH."""
    env = os.environ.copy()
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if path_dirs is not None:
        if replace_path:
            env["PATH"] = os.pathsep.join(str(p) for p in path_dirs)
        else:
            env["PATH"] = (
                os.pathsep.join(str(p) for p in path_dirs) + os.pathsep + env.get("PATH", "")
            )
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)


def _make_mock_bin(
    tmp_path: Path,
    name: str,
    stdout: str = "",
    exit_code: int = 0,
) -> Path:
    """Create a mock executable in tmp_path/bin/<name>; returns the bindir."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(f"#!/bin/bash\n{stdout}\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_recording_bin(
    tmp_path: Path,
    name: str,
    record_file: Path,
    exit_code: int = 0,
) -> Path:
    """Create a mock that records its argv to record_file."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(f'#!/bin/bash\necho "$@" >> {record_file}\nexit {exit_code}\n')
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


# ── script structure ────────────────────────────────────────────────────


class TestScriptStructure:
    def test_script_exists(self):
        assert SCRIPT.exists()

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_has_shebang(self):
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line == "#!/usr/bin/env bash"


# ── --help / -h ────────────────────────────────────────────────────────


class TestHelp:
    def test_help_exits_zero(self):
        r = _run(["--help"])
        assert r.returncode == 0

    def test_help_prints_usage(self):
        r = _run(["--help"])
        assert "Usage: start-chrome-debug.sh" in r.stdout
        assert "--port" in r.stdout
        assert "9222" in r.stdout

    def test_h_short_flag(self):
        r = _run(["-h"])
        assert r.returncode == 0
        assert "Usage: start-chrome-debug.sh" in r.stdout


# ── unknown option ──────────────────────────────────────────────────────


class TestUnknownOption:
    def test_unknown_option_exits_2(self):
        r = _run(["--bogus"])
        assert r.returncode == 2

    def test_unknown_option_stderr(self):
        r = _run(["--bogus"])
        assert "Unknown option: --bogus" in r.stderr


# ── chrome not found ────────────────────────────────────────────────────


class TestChromeNotFound:
    def test_no_chrome_exits_1(self, tmp_path):
        # Provide PATH with only essential system dirs, no Chrome
        bindir = _make_mock_bin(tmp_path, "curl", exit_code=1)
        r = _run(tmp_path=tmp_path, path_dirs=[bindir])
        assert r.returncode == 1

    def test_no_chrome_error_message(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "curl", exit_code=1)
        r = _run(tmp_path=tmp_path, path_dirs=[bindir])
        assert "Chrome/Chromium not found" in r.stderr


# ── chrome already running on debug port ────────────────────────────────


class TestChromeAlreadyRunning:
    def test_already_running_exits_0(self, tmp_path):
        # Mock curl to succeed (port responds) + mock a chrome binary
        bindir = _make_mock_bin(tmp_path, "curl", stdout="mock-response", exit_code=0)
        _make_mock_bin(tmp_path, "google-chrome-stable", exit_code=0)
        r = _run(tmp_path=tmp_path, path_dirs=[bindir])
        assert r.returncode == 0

    def test_already_running_message(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "curl", stdout="mock-response", exit_code=0)
        _make_mock_bin(tmp_path, "google-chrome-stable", exit_code=0)
        r = _run(tmp_path=tmp_path, path_dirs=[bindir])
        assert "already running with debugging on port 9222" in r.stdout


# ── successful start ───────────────────────────────────────────────────


class TestSuccessfulStart:
    def test_chrome_started_with_debug_port(self, tmp_path):
        # curl fails (nothing on port), chrome mock succeeds and stays alive
        bindir = _make_mock_bin(tmp_path, "curl", exit_code=1)
        # Chrome mock that sleeps briefly so kill -0 works
        chrome_script = tmp_path / "bin" / "google-chrome-stable"
        chrome_script.parent.mkdir(exist_ok=True)
        chrome_script.write_text("#!/bin/bash\nsleep 5\n")
        chrome_script.chmod(chrome_script.stat().st_mode | stat.S_IEXEC)
        r = _run(tmp_path=tmp_path, path_dirs=[bindir])
        assert r.returncode == 0

    def test_chrome_started_output(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "curl", exit_code=1)
        chrome_script = tmp_path / "bin" / "google-chrome-stable"
        chrome_script.parent.mkdir(exist_ok=True)
        chrome_script.write_text("#!/bin/bash\nsleep 5\n")
        chrome_script.chmod(chrome_script.stat().st_mode | stat.S_IEXEC)
        r = _run(tmp_path=tmp_path, path_dirs=[bindir])
        assert "Chrome started with remote debugging on port 9222" in r.stdout
        assert "http://localhost:9222" in r.stdout

    def test_chrome_receives_debug_port_flag(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "curl", exit_code=1)
        record_file = tmp_path / "chrome_invocations.txt"
        bindir = _make_recording_bin(tmp_path, "google-chrome-stable", record_file)
        # Chrome needs to stay alive for the kill -0 check
        chrome_script = tmp_path / "bin" / "google-chrome-stable"
        chrome_script.write_text(f'#!/bin/bash\necho "$@" >> {record_file}\nsleep 5\n')
        chrome_script.chmod(chrome_script.stat().st_mode | stat.S_IEXEC)
        r = _run(tmp_path=tmp_path, path_dirs=[bindir])
        assert r.returncode == 0
        invocations = record_file.read_text()
        assert "--remote-debugging-port=9222" in invocations
        assert "--user-data-dir=" in invocations


# ── custom port ─────────────────────────────────────────────────────────


class TestCustomPort:
    def test_custom_port_passed_to_chrome(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "curl", exit_code=1)
        record_file = tmp_path / "chrome_invocations.txt"
        chrome_script = tmp_path / "bin" / "google-chrome-stable"
        chrome_script.parent.mkdir(exist_ok=True)
        chrome_script.write_text(f'#!/bin/bash\necho "$@" >> {record_file}\nsleep 5\n')
        chrome_script.chmod(chrome_script.stat().st_mode | stat.S_IEXEC)
        r = _run(args=["-p", "9333"], tmp_path=tmp_path, path_dirs=[bindir])
        assert r.returncode == 0
        invocations = record_file.read_text()
        assert "--remote-debugging-port=9333" in invocations

    def test_custom_port_long_flag(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "curl", exit_code=1)
        record_file = tmp_path / "chrome_invocations.txt"
        chrome_script = tmp_path / "bin" / "google-chrome-stable"
        chrome_script.parent.mkdir(exist_ok=True)
        chrome_script.write_text(f'#!/bin/bash\necho "$@" >> {record_file}\nsleep 5\n')
        chrome_script.chmod(chrome_script.stat().st_mode | stat.S_IEXEC)
        r = _run(args=["--port", "9444"], tmp_path=tmp_path, path_dirs=[bindir])
        assert r.returncode == 0
        invocations = record_file.read_text()
        assert "--remote-debugging-port=9444" in invocations

    def test_custom_port_already_running(self, tmp_path):
        # curl succeeds on custom port → "already running" message
        bindir = _make_mock_bin(tmp_path, "curl", stdout="ok", exit_code=0)
        _make_mock_bin(tmp_path, "google-chrome-stable", exit_code=0)
        r = _run(args=["-p", "9333"], tmp_path=tmp_path, path_dirs=[bindir])
        assert r.returncode == 0
        assert "port 9333" in r.stdout
