#!/usr/bin/env python3
"""Test for hetzner-bootstrap.sh effector script."""

import subprocess
import os
import pytest


SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "effectors", "hetzner-bootstrap.sh")


def test_hetzner_bootstrap_script_exists_and_is_executable():
    """Test that the script exists and has executable permissions."""
    assert os.path.exists(SCRIPT_PATH)
    assert os.access(SCRIPT_PATH, os.X_OK), "Script should be executable"


def test_script_has_correct_shebang():
    """Test that the script has the correct shebang line."""
    with open(SCRIPT_PATH, "r") as f:
        first_line = f.readline().strip()
    assert first_line == "#!/bin/bash"


def test_help_flag_works():
    """Test that --help outputs expected usage information."""
    result = subprocess.run(
        [SCRIPT_PATH, "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Usage: hetzner-bootstrap.sh" in result.stdout
    assert "Bootstrap a fresh Hetzner Ubuntu 22.04 VPS for Claude Code" in result.stdout
    assert "Creates user 'terry', installs Node.js, Claude Code, Tailscale, pnpm, uv" in result.stdout


def test_script_has_no_bash_syntax_errors():
    """Check bash script syntax with bash -n."""
    result = subprocess.run(
        ["bash", "-n", SCRIPT_PATH],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Syntax errors found: {result.stderr}"
    assert not result.stderr, f"Unexpected stderr output: {result.stderr}"


def test_script_contains_all_expected_components():
    """Test that the script includes all expected installation steps."""
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()
    
    # Check all major components are present
    assert "apt-get update && apt-get upgrade -y" in content
    assert "adduser --disabled-password --gecos \"\" terry" in content
    assert "fnm install --lts" in content
    assert "npm install -g @anthropic-ai/claude-code" in content
    assert "curl -fsSL https://tailscale.com/install.sh | sh" in content
    assert "npm install -g pnpm" in content
    assert "curl -LsSf https://astral.sh/uv/install.sh | sh" in content
    assert "PasswordAuthentication no" in content
    assert "PermitRootLogin no" in content
