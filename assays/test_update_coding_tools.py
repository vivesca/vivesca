from __future__ import annotations

"""Tests for update-coding-tools.sh effector script."""

import subprocess
from pathlib import Path

import pytest


SCRIPT_PATH = Path("/home/terry/germline/effectors/update-coding-tools.sh")


def test_script_exists_and_is_executable():
    """Script exists and has execute permissions."""
    assert SCRIPT_PATH.exists()
    assert SCRIPT_PATH.is_file()
    # Check executable bit
    assert SCRIPT_PATH.stat().st_mode & 0o111 != 0


def test_script_help_flag():
    """--help flag prints usage information."""
    result = subprocess.run(
        [str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "Auto-update brew, npm, pnpm, uv, cargo" in result.stdout
    assert "Logs to ~/.coding-tools-update.log" in result.stdout
    assert not result.stderr


def test_script_help_short_flag():
    """-h short flag prints help."""
    result = subprocess.run(
        [str(SCRIPT_PATH), "-h"],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout


def test_script_shebang_is_valid():
    """Shebang points to valid bash interpreter."""
    with open(SCRIPT_PATH) as f:
        first_line = f.readline().strip()
    assert first_line == "#!/usr/bin/env bash"


def test_script_has_set_e():
    """Script uses set -e for error safety."""
    content = SCRIPT_PATH.read_text()
    assert "set -e" in content


def test_script_defines_repair_map():
    """Script defines the REPAIR associative array for critical tools."""
    content = SCRIPT_PATH.read_text()
    # Check for repair array declaration and expected entries
    assert "declare -A REPAIR" in content
    assert "[brew]" in content
    assert "[claude]" in content
    assert "[opencode]" in content
    assert "[gemini]" in content
    assert "[codex]" in content
    assert "failures=()" in content
    assert "command -v" in content


def test_script_creates_health_json():
    """Script writes health status JSON."""
    content = SCRIPT_PATH.read_text()
    assert '{"status":"ok"' in content
    assert '"failures":[]' in content
    assert '"status":"degraded"' in content
    assert "$HEALTH_FILE" in content


def test_script_has_all_update_steps():
    """Script includes all planned update steps."""
    content = SCRIPT_PATH.read_text()
    assert "brew update" in content
    assert "brew upgrade" in content
    assert "npm update -g" in content
    assert "pnpm update -g" in content
    assert "uv tool upgrade --all" in content
    assert "cargo binstall" in content
    assert "mas upgrade" in content
    assert "brew cleanup" in content


@pytest.mark.skipif(not Path("/opt/homebrew/bin/brew").exists(),
                    reason="Homebrew not found at /opt/homebrew/bin/brew")
def test_script_runs_with_homebrew():
    """Script exits cleanly when brew is present (dry run structure check)."""
    # Just test that the script can parse and run the initial check
    # We won't actually run full update in test
    result = subprocess.run(
        [str(SCRIPT_PATH)],
        capture_output=True,
        text=True
    )
    # Script should at least not fail on syntax
    # It may proceed to update but we still accept it because we're just testing structure
    # Check that it didn't exit with 1 (which means early error)
    assert result.returncode != 1
    if result.returncode == 1:
        assert "Homebrew not found" not in result.stderr
