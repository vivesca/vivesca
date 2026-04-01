"""Tests for effectors/start-chrome-debug.sh"""
import os
import stat
import subprocess
import tempfile
import pytest
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "effectors" / "start-chrome-debug.sh"


def run_script(*args, check=False, env=None, timeout=None):
    """Run the script with args, return CompletedProcess."""
    return subprocess.run(
        ["/usr/bin/bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=check,
        env=env,
        timeout=timeout,
    )


class TestHelpOption:
    """Tests for --help flag."""

    def test_help_short_flag(self):
        """-h shows usage."""
        result = run_script("-h")
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "--help" in result.stdout
        assert "--port" in result.stdout

    def test_help_long_flag(self):
        """--help shows usage."""
        result = run_script("--help")
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "OPTIONS" in result.stdout or "Options:" in result.stdout

    def test_help_shows_default_port(self):
        """Help mentions default port 9222."""
        result = run_script("--help")
        assert "9222" in result.stdout


class TestInvalidOptions:
    """Tests for invalid argument handling."""

    def test_unknown_option_exits_2(self):
        """Unknown option exits with code 2."""
        result = run_script("--invalid-option")
        assert result.returncode == 2
        assert "Unknown option" in result.stderr

    def test_unknown_option_shows_usage_to_stderr(self):
        """Unknown option prints usage to stderr."""
        result = run_script("--bad-arg")
        assert "Usage:" in result.stderr


class TestPortOption:
    """Tests for --port flag."""

    def test_port_short_flag_accepted(self):
        """-p <port> is parsed without argument errors."""
        result = run_script("-p", "9999")
        assert "Unknown option" not in result.stderr

    def test_port_long_flag_accepted(self):
        """--port <port> is parsed without argument errors."""
        result = run_script("--port", "8888")
        assert "Unknown option" not in result.stderr


class TestChromeDetection:
    """Tests for Chrome binary detection using a fake Chrome in a temp dir."""

    def test_no_chrome_found_error_message(self, tmp_path):
        """When no Chrome binary exists on PATH, exits 1 with error."""
        env = os.environ.copy()
        env["PATH"] = f"{tmp_path}:/usr/bin:/bin"
        result = run_script(env=env)
        assert result.returncode == 1
        assert "Chrome/Chromium not found" in result.stderr

    def test_non_executable_chrome_error(self, tmp_path):
        """When Chrome candidate exists but is not executable, exits 1."""
        fake_chrome = tmp_path / "google-chrome-stable"
        fake_chrome.write_text("#!/bin/bash\nexit 0")
        # NOT chmod +x, so -x test fails
        env = os.environ.copy()
        env["PATH"] = f"{tmp_path}:/usr/bin:/bin"
        result = run_script(env=env)
        assert result.returncode == 1
        assert "not executable" in result.stderr

    def test_executable_chrome_is_launched(self, tmp_path):
        """When a valid Chrome candidate exists on PATH, script attempts to launch it."""
        # Create a fake chrome that writes a marker and stays alive briefly
        marker = tmp_path / "launched.txt"
        fake_chrome = tmp_path / "google-chrome-stable"
        fake_chrome.write_text(
            f"#!/bin/bash\n"
            f"echo launched >> {marker}\n"
            f"echo args: $@ >> {marker}\n"
            # Stay alive long enough for kill -0 check
            f"sleep 5\n"
        )
        fake_chrome.chmod(fake_chrome.stat().st_mode | stat.S_IEXEC)

        # Provide a fake curl that simulates "not already running"
        fake_curl = tmp_path / "curl"
        fake_curl.write_text("#!/bin/bash\nexit 1\n")
        fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IEXEC)

        env = os.environ.copy()
        env["PATH"] = str(tmp_path)
        env["HOME"] = str(tmp_path)

        result = run_script(env=env, timeout=10)
        # Script should report successful start
        assert result.returncode == 0
        assert "Chrome started" in result.stdout
        # Verify our fake chrome was actually invoked
        assert marker.exists()
        launch_log = marker.read_text()
        assert "launched" in launch_log
        assert "--remote-debugging-port=9222" in launch_log

    def test_custom_port_passed_to_chrome(self, tmp_path):
        """--port value is forwarded to the Chrome invocation."""
        marker = tmp_path / "launched.txt"
        fake_chrome = tmp_path / "google-chrome-stable"
        fake_chrome.write_text(
            f"#!/bin/bash\necho $@ >> {marker}\nsleep 5\n"
        )
        fake_chrome.chmod(fake_chrome.stat().st_mode | stat.S_IEXEC)

        fake_curl = tmp_path / "curl"
        fake_curl.write_text("#!/bin/bash\nexit 1\n")
        fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IEXEC)

        env = os.environ.copy()
        env["PATH"] = str(tmp_path)
        env["HOME"] = str(tmp_path)

        result = run_script("-p", "12345", env=env, timeout=10)
        assert result.returncode == 0
        assert "--remote-debugging-port=12345" in marker.read_text()

    def test_user_data_dir_passed(self, tmp_path):
        """--user-data-dir is passed with the Linux default path."""
        marker = tmp_path / "launched.txt"
        fake_chrome = tmp_path / "google-chrome-stable"
        fake_chrome.write_text(
            f"#!/bin/bash\necho $@ >> {marker}\nsleep 5\n"
        )
        fake_chrome.chmod(fake_chrome.stat().st_mode | stat.S_IEXEC)

        fake_curl = tmp_path / "curl"
        fake_curl.write_text("#!/bin/bash\nexit 1\n")
        fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IEXEC)

        env = os.environ.copy()
        env["PATH"] = str(tmp_path)
        env["HOME"] = str(tmp_path)

        result = run_script(env=env, timeout=10)
        assert result.returncode == 0
        assert f"--user-data-dir={tmp_path}/.config/google-chrome" in marker.read_text()


class TestAlreadyRunning:
    """Tests for already-running Chrome detection."""

    def test_already_running_exits_zero(self, tmp_path):
        """When curl succeeds on the debug port, exits 0 without launching Chrome."""
        fake_curl = tmp_path / "curl"
        fake_curl.write_text("#!/bin/bash\nexit 0\n")
        fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IEXEC)

        env = os.environ.copy()
        env["PATH"] = str(tmp_path)
        env["HOME"] = str(tmp_path)

        result = run_script(env=env)
        assert result.returncode == 0
        assert "already running" in result.stdout

    def test_already_running_with_custom_port(self, tmp_path):
        """Already-running check uses the custom port, not the default."""
        fake_curl = tmp_path / "curl"
        # Only succeed when called with the custom port
        fake_curl.write_text(
            '#!/bin/bash\n'
            'case "$@" in\n'
            '  *":7777/"*) exit 0;;\n'
            '  *) exit 1;;\n'
            'esac\n'
        )
        fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IEXEC)

        env = os.environ.copy()
        env["PATH"] = str(tmp_path)
        env["HOME"] = str(tmp_path)

        result = run_script("-p", "7777", env=env)
        assert result.returncode == 0
        assert "already running" in result.stdout
        assert "7777" in result.stdout

    def test_already_running_does_not_launch_chrome(self, tmp_path):
        """Already-running path does NOT invoke the Chrome binary."""
        fake_curl = tmp_path / "curl"
        fake_curl.write_text("#!/bin/bash\nexit 0\n")
        fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IEXEC)

        # Create a fake chrome that would fail the test if called
        fake_chrome = tmp_path / "google-chrome-stable"
        fake_chrome.write_text("#!/bin/bash\necho SHOULD_NOT_BE_CALLED >&2\nexit 99\n")
        fake_chrome.chmod(fake_chrome.stat().st_mode | stat.S_IEXEC)

        env = os.environ.copy()
        env["PATH"] = str(tmp_path)
        env["HOME"] = str(tmp_path)

        result = run_script(env=env)
        assert result.returncode == 0
        assert "SHOULD_NOT_BE_CALLED" not in result.stderr


class TestChromeStartupFailure:
    """Tests for when Chrome exits immediately after launch."""

    def test_chrome_dies_immediately(self, tmp_path):
        """When launched Chrome exits immediately, script reports error."""
        fake_chrome = tmp_path / "google-chrome-stable"
        fake_chrome.write_text("#!/bin/bash\nexit 1\n")
        fake_chrome.chmod(fake_chrome.stat().st_mode | stat.S_IEXEC)

        fake_curl = tmp_path / "curl"
        fake_curl.write_text("#!/bin/bash\nexit 1\n")
        fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IEXEC)

        env = os.environ.copy()
        env["PATH"] = str(tmp_path)
        env["HOME"] = str(tmp_path)

        result = run_script(env=env, timeout=10)
        assert result.returncode == 1
        assert "failed to start" in result.stderr


class TestScriptStructure:
    """Tests for script structure and best practices."""

    def test_script_exists(self):
        """Script file exists."""
        assert SCRIPT.exists()

    def test_script_has_strict_error_handling(self):
        """Script uses set -euo pipefail."""
        content = SCRIPT.read_text()
        assert "set -euo pipefail" in content

    def test_script_has_usage_function(self):
        """Script defines a usage function."""
        content = SCRIPT.read_text()
        assert "usage()" in content

    def test_script_handles_both_platforms(self):
        """Script handles Darwin and Linux."""
        content = SCRIPT.read_text()
        assert "Darwin" in content
        assert "Linux" in content

    def test_script_uses_remote_debugging_port(self):
        """Script passes remote-debugging-port to Chrome."""
        content = SCRIPT.read_text()
        assert "--remote-debugging-port" in content

    def test_script_backgrounds_chrome(self):
        """Script starts Chrome in background."""
        content = SCRIPT.read_text()
        assert "&" in content

    def test_script_verifies_startup(self):
        """Script checks that Chrome started successfully via kill -0."""
        content = SCRIPT.read_text()
        assert "kill -0" in content
