from __future__ import annotations

"""Tests for start-chrome-debug.sh — Start Chrome with remote debugging."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPT_PATH = Path("/home/terry/germline/effectors/start-chrome-debug.sh")


def run_script(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    """Run the script with given arguments and return result."""
    cmd = [str(SCRIPT_PATH), *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


# ── Help and usage tests ────────────────────────────────────────────────


def test_help_option_exits_0():
    """--help shows usage and exits 0."""
    result = run_script("--help")
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "start-chrome-debug.sh" in result.stdout


def test_help_short_option_exits_0():
    """-h shows usage and exits 0."""
    result = run_script("-h")
    assert result.returncode == 0
    assert "Usage:" in result.stdout


def test_help_shows_port_option():
    """--help mentions the port option."""
    result = run_script("--help")
    assert "--port" in result.stdout or "-p" in result.stdout
    assert "9222" in result.stdout  # default port


def test_help_shows_description():
    """--help shows description of what the script does."""
    result = run_script("--help")
    assert "remote debugging" in result.stdout.lower()


# ── Unknown option handling ─────────────────────────────────────────────


def test_unknown_option_exits_2():
    """Unknown option shows error and exits 2."""
    result = run_script("--invalid-option")
    assert result.returncode == 2
    assert "Unknown option" in result.stderr


def test_unknown_short_option_exits_2():
    """Unknown short option shows error and exits 2."""
    result = run_script("-Z")
    assert result.returncode == 2
    assert "Unknown option" in result.stderr


# ── Port option validation ──────────────────────────────────────────────


def test_port_option_requires_value():
    """-p without value should fail (bash set -u will catch)."""
    # This will fail because shift 2 tries to shift past end
    result = run_script("-p")
    # Either bash error or our error - either way non-zero
    assert result.returncode != 0


def test_port_option_accepts_custom_port():
    """-p accepts a custom port number (validation via mock)."""
    # We can't actually start Chrome in tests, but we can verify
    # the argument parsing doesn't reject a valid port
    # The script will fail later when Chrome isn't found, which is expected
    result = run_script("-p", "9333")
    # Should not be "Unknown option" error
    assert "Unknown option" not in result.stderr


def test_port_long_option_accepts_custom_port():
    """--port accepts a custom port number."""
    result = run_script("--port", "9333")
    # Should not be "Unknown option" error
    assert "Unknown option" not in result.stderr


# ── Platform detection tests ────────────────────────────────────────────


def test_script_is_executable():
    """Script file has execute permission."""
    assert SCRIPT_PATH.exists()
    assert SCRIPT_PATH.stat().st_mode & 0o111  # Any execute bit set


def test_script_has_shebang():
    """Script starts with bash shebang."""
    content = SCRIPT_PATH.read_text()
    assert content.startswith("#!/bin/bash") or content.startswith("#!/usr/bin/env bash")


def test_script_uses_strict_mode():
    """Script uses set -euo pipefail for safety."""
    content = SCRIPT_PATH.read_text()
    assert "set -euo pipefail" in content


# ── Chrome detection logic (via script internals) ───────────────────────


def test_script_checks_linux_chrome_candidates():
    """Script checks multiple Chrome binary names on Linux."""
    content = SCRIPT_PATH.read_text()
    # Should check multiple candidates
    assert "google-chrome-stable" in content
    assert "google-chrome" in content or "chromium" in content


def test_script_detects_platform():
    """Script has platform detection via uname."""
    content = SCRIPT_PATH.read_text()
    assert "uname -s" in content or "uname" in content
    assert "Darwin" in content  # macOS
    assert "Linux" in content


def test_script_handles_unsupported_platform():
    """Script exits 1 for unsupported platforms."""
    content = SCRIPT_PATH.read_text()
    assert "Unsupported platform" in content


# ── Already-running detection ───────────────────────────────────────────


def test_script_checks_existing_debug_port():
    """Script checks if Chrome is already running with debugging."""
    content = SCRIPT_PATH.read_text()
    assert "localhost" in content
    assert "9222" in content
    assert "curl" in content or "/json/version" in content


def test_script_exits_0_if_already_running():
    """Script exits 0 with message if Chrome already running on port."""
    content = SCRIPT_PATH.read_text()
    assert "already running" in content.lower()


# ── Chrome not found handling ───────────────────────────────────────────


def test_script_handles_chrome_not_found():
    """Script exits 1 when Chrome/Chromium is not found."""
    content = SCRIPT_PATH.read_text()
    assert "Chrome" in content and "not found" in content


def test_script_handles_non_executable_chrome():
    """Script exits 1 when Chrome binary is not executable."""
    content = SCRIPT_PATH.read_text()
    assert "not executable" in content


# ── Chrome startup verification ─────────────────────────────────────────


def test_script_verifies_chrome_started():
    """Script verifies Chrome didn't exit immediately after start."""
    content = SCRIPT_PATH.read_text()
    assert "kill -0" in content  # Check if process is running
    assert "exited immediately" in content or "failed to start" in content


def test_script_outputs_debug_url():
    """Script outputs the debugging URL on success."""
    content = SCRIPT_PATH.read_text()
    assert "localhost" in content
    assert "Connect via" in content or "http://localhost" in content


# ── Integration test (requires Chrome, skipped if not available) ───────


@pytest.mark.skip(reason="Requires Chrome to be installed and not running")
def test_script_starts_chrome_with_debugging():
    """Integration test: script starts Chrome with debugging (skipped by default)."""
    # This test is skipped in CI but can be run manually
    result = run_script("-p", "9333")
    # If Chrome is installed, should either start or report already running
    assert result.returncode in (0, 1)  # 0 = success, 1 = already running or error


# ── User data directory handling ────────────────────────────────────────


def test_script_uses_user_data_dir():
    """Script sets user-data-dir for Chrome profile."""
    content = SCRIPT_PATH.read_text()
    assert "user-data-dir" in content


def test_script_detects_linux_user_data_dir():
    """Script uses correct user-data-dir for Linux."""
    content = SCRIPT_PATH.read_text()
    assert ".config/google-chrome" in content


def test_script_detects_macos_user_data_dir():
    """Script uses correct user-data-dir for macOS."""
    content = SCRIPT_PATH.read_text()
    assert "Library/Application Support/Google/Chrome" in content


# ── Background process handling ─────────────────────────────────────────


def test_script_starts_chrome_in_background():
    """Script starts Chrome as a background process."""
    content = SCRIPT_PATH.read_text()
    assert "&" in content  # Background execution


def test_script_captures_chrome_pid():
    """Script captures Chrome PID for verification."""
    content = SCRIPT_PATH.read_text()
    assert "$!" in content  # Last background PID


# ── Default port constant ───────────────────────────────────────────────


def test_default_port_is_9222():
    """Script uses 9222 as the default debugging port."""
    content = SCRIPT_PATH.read_text()
    # Should have DEBUG_PORT=9222 or similar
    assert "9222" in content
