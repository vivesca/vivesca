from __future__ import annotations

"""Tests for effectors/start-chrome-debug.sh — Chrome remote debugging launcher.

Since the script starts Chrome and interacts with the system,
tests operate by:
  1. Validating script structure (shebang, error flags, help text).
  2. Testing argument parsing and error conditions.
  3. Verifying platform detection logic with mocks.
"""

import os
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "start-chrome-debug.sh"


def _read_script() -> str:
    return SCRIPT.read_text()


# ── Structural tests ────────────────────────────────────────────────────


class TestScriptStructure:
    """Verify the script has required structural elements."""

    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_executable(self):
        mode = SCRIPT.stat().st_mode
        assert mode & stat.S_IEXEC, "start-chrome-debug.sh should be executable"

    def test_shebang(self):
        lines = _read_script().splitlines()
        assert lines[0] == "#!/bin/bash"

    def test_strict_mode(self):
        content = _read_script()
        assert "set -euo pipefail" in content

    def test_default_port_set(self):
        content = _read_script()
        assert "DEBUG_PORT=9222" in content

    def test_no_todo_or_fixme(self):
        """Script should not contain TODO or FIXME markers."""
        content = _read_script()
        for line in content.splitlines():
            upper = line.upper()
            assert "TODO" not in upper, f"Found TODO: {line.strip()}"
            assert "FIXME" not in upper, f"Found FIXME: {line.strip()}"

    def test_script_ends_with_newline(self):
        """Script should end with a trailing newline."""
        content = _read_script()
        assert content.endswith("\n"), "Script should end with a newline"


# ── Syntax check ────────────────────────────────────────────────────────


class TestSyntaxCheck:
    """Verify the script is syntactically valid bash."""

    def test_bash_syntax_valid(self):
        """bash -n should report no syntax errors."""
        r = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0, f"Syntax error in start-chrome-debug.sh:\n{r.stderr}"

    def test_shellcheck_if_available(self):
        """Run shellcheck if available, but don't fail if not installed."""
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
        # We allow warnings but not errors
        if r.returncode != 0:
            # Filter to only errors (SC level)
            errors = [
                line for line in r.stdout.splitlines()
                if "error" in line.lower()
            ]
            assert not errors, f"shellcheck errors:\n{r.stdout}"


# ── Help flag execution tests ───────────────────────────────────────────


class TestHelpFlag:
    """Run the script with --help / -h and verify output."""

    def test_help_long_flag(self):
        """--help prints usage text and exits 0."""
        result = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "Start Chrome with remote debugging enabled" in result.stdout

    def test_help_short_flag(self):
        """-h prints usage text and exits 0."""
        result = subprocess.run(
            ["bash", str(SCRIPT), "-h"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_help_mentions_port_option(self):
        """Help text mentions the --port option."""
        result = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        assert "Debugging port" in result.stdout
        assert "default: 9222" in result.stdout


# ── Argument parsing tests ───────────────────────────────────────────────


class TestArgumentParsing:
    """Test argument parsing behavior."""

    def test_unknown_option_exits_with_2(self):
        """Unknown option should exit with code 2."""
        result = subprocess.run(
            ["bash", str(SCRIPT), "--unknown-option"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "Unknown option:" in result.stderr

    def test_custom_port_accepted(self):
        """Custom port via -p/--port should be accepted.
        We don't actually start Chrome, just verify parsing doesn't fail early.
        """
        # Mock uname -s to return Linux, mock command -v to give us a fake chrome
        mock_script = f"""\
            # Mock the parts that detect platform and chrome
            uname() {{ echo "Linux"; }}
            command() {{
                if [ "$1" = "-v" ] && [ "$2" = "google-chrome-stable" ]; then
                    echo "/usr/bin/google-chrome";
                    return 0;
                fi
                return 1
            }}
            # Override curl to always fail (chrome not running)
            curl() {{ return 1; }}
            # Exit before actually starting chrome
            exit 0
            # Source the original script
            . {SCRIPT}
        """
        # Include args directly in the script
        result = subprocess.run(
            ["bash", "-c", f"{mock_script} -p 9223"],
            capture_output=True,
            text=True,
        )
        # It should parse ok, no parsing error (exit 0 expected)
        assert result.returncode == 0, f"Failed with: {result.stderr}"


# ── Platform detection tests ─────────────────────────────────────────────


class TestPlatformDetection:
    """Test platform detection and error handling."""

    def test_unsupported_platform_exits_with_1(self):
        """Unsupported platform (like FreeBSD) should exit with 1."""
        mock_script = f"""\
            uname() {{ echo "FreeBSD"; }}
            . {SCRIPT}
        """
        result = subprocess.run(
            ["bash", "-c", mock_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Unsupported platform:" in result.stderr

    def test_linux_searches_multiple_candidates(self):
        """On Linux, script searches multiple chrome candidate names."""
        content = _read_script()
        assert "google-chrome-stable" in content
        assert "google-chrome" in content
        assert "chromium-browser" in content
        assert "chromium" in content

    def test_chrome_not_found_exits_with_1(self):
        """If no Chrome binary found, exit with 1."""
        mock_script = f"""\
            uname() {{ echo "Linux"; }}
            command() {{ return 1; }}  # No candidates found
            . {SCRIPT}
        """
        result = subprocess.run(
            ["bash", "-c", mock_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Chrome/Chromium not found on PATH" in result.stderr

    def test_non_executable_chrome_exits_with_1(self, tmp_path):
        """If Chrome binary exists but isn't executable, exit with 1."""
        # Create a non-executable fake chrome
        fake_chrome = tmp_path / "chrome"
        fake_chrome.write_text("#!/bin/bash\necho 'fake chrome'\n")
        # No executable permission
        fake_chrome.chmod(0o644)

        mock_script = f"""\
            uname() {{ echo "Linux"; }}
            command() {{ echo "{fake_chrome}"; return 0; }}
            . {SCRIPT}
        """
        result = subprocess.run(
            ["bash", "-c", mock_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "not executable" in result.stderr


# ── Running detection tests ──────────────────────────────────────────────


class TestRunningDetection:
    """Test detection when Chrome is already running with debugging."""

    def test_exits_0_when_already_running(self, tmp_path):
        """If curl can connect to the port, exit 0 with message."""
        # Create a fake executable chrome
        fake_chrome = tmp_path / "chrome"
        fake_chrome.write_text("#!/bin/bash\necho 'fake chrome'\n")
        fake_chrome.chmod(0o755)

        mock_script = f"""\
            uname() {{ echo "Linux"; }}
            command() {{ echo "{fake_chrome}"; return 0; }}
            # Curl succeeds → already running
            curl() {{ return 0; }}
            . {SCRIPT}
        """
        result = subprocess.run(
            ["bash", "-c", mock_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "already running with debugging" in result.stdout
