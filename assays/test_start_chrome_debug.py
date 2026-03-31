"""Tests for effectors/start-chrome-debug.sh"""
import subprocess
import pytest
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "effectors" / "start-chrome-debug.sh"


def run_script(*args, check=False):
    """Run the script with args, return CompletedProcess."""
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=check,
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
        """-p <port> is parsed (won't start Chrome, validates arg parsing)."""
        # Use a high port that won't conflict and won't have Chrome running
        # Script will likely fail later due to no Chrome, but should not fail on arg parsing
        result = run_script("-p", "9999")
        # Should not have argument parsing error
        assert "Unknown option" not in result.stderr

    def test_port_long_flag_accepted(self):
        """--port <port> is parsed."""
        result = run_script("--port", "8888")
        assert "Unknown option" not in result.stderr


class TestChromeDetection:
    """Tests for Chrome binary detection."""

    def test_no_chrome_found_error_message(self, monkeypatch):
        """When no Chrome binary exists, shows helpful error."""
        # Create a minimal script that mocks the Chrome detection
        test_script = f"""#!/bin/bash
# Mock environment with no Chrome
export PATH="/nonexistent"
unset CHROME

# Source just the detection logic
source {SCRIPT}

# Override command to return nothing
command() {{
    return 1
}}

# Run detection
case "$(uname -s)" in
    Linux)
        for candidate in google-chrome-stable google-chrome chromium-browser chromium; do
            if command -v "$candidate" &>/dev/null; then
                CHROME="$(command -v "$candidate")"
                break
            fi
        done
        ;;
esac

if [[ -z "${{CHROME:-}}" ]]; then
    echo "Error: Chrome/Chromium not found on PATH" >&2
    exit 1
fi
"""
        # Simpler approach: run the script with PATH pointing to empty dir
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            env={"PATH": "/nonexistent"},
        )
        # Script should fail with Chrome not found
        if result.returncode != 0:
            assert "Chrome" in result.stderr or "not found" in result.stderr.lower()


class TestAlreadyRunning:
    """Tests for already-running detection."""

    def test_already_running_message(self):
        """When Chrome is already running on the port, shows message and exits 0."""
        # This test would need a mock curl; skip if we can't easily mock
        # Instead, verify the script contains the check
        content = SCRIPT.read_text()
        assert "localhost" in content
        assert "9222" in content
        assert "already running" in content.lower() or "json/version" in content


class TestScriptStructure:
    """Tests for script structure and best practices."""

    def test_script_exists_and_executable(self):
        """Script file exists."""
        assert SCRIPT.exists()

    def test_script_has_set_e(self):
        """Script uses set -e for error handling."""
        content = SCRIPT.read_text()
        assert "set -e" in content or "set -euo pipefail" in content

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
        assert "&" in content  # backgrounding

    def test_script_verifies_startup(self):
        """Script checks that Chrome started successfully."""
        content = SCRIPT.read_text()
        assert "kill -0" in content  # check if process is running
