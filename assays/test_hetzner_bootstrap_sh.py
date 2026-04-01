from __future__ import annotations

"""Tests for effectors/hetzner-bootstrap.sh — Hetzner VPS bootstrap script.

Since the script modifies the system (creates users, installs packages),
tests operate by:
  1. Validating script structure (shebang, error flags, help text).
  2. Testing argument parsing and help output.
  3. Verifying syntax correctness with bash -n.
  4. Checking for required components mentioned in the script.
"""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "hetzner-bootstrap.sh"


def _read_script() -> str:
    return SCRIPT.read_text()


# ── Structural tests ────────────────────────────────────────────────────


class TestScriptStructure:
    """Verify the script has required structural elements."""

    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_executable(self):
        mode = SCRIPT.stat().st_mode
        assert mode & stat.S_IEXEC, "hetzner-bootstrap.sh should be executable"

    def test_shebang(self):
        lines = _read_script().splitlines()
        assert lines[0] == "#!/bin/bash"

    def test_strict_mode(self):
        content = _read_script()
        assert "set -euo pipefail" in content

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

    def test_contains_all_expected_components(self):
        """Script contains all the expected bootstrap components it claims to install."""
        content = _read_script()
        # System updates
        assert "apt-get update" in content
        assert "apt-get upgrade" in content
        # Create user terry
        assert "id terry" in content
        assert "adduser --disabled-password --gecos \"\" terry" in content
        # Install Node.js via fnm
        assert "fnm.vercel.app/install" in content
        assert "fnm install --lts" in content
        # Install Claude Code
        assert "npm install -g @anthropic-ai/claude-code" in content
        # Install Tailscale
        assert "tailscale.com/install.sh" in content
        # Install pnpm
        assert "npm install -g pnpm" in content
        # Install uv
        assert "astral.sh/uv/install.sh" in content
        # tmux config
        assert ".tmux.conf" in content
        # SSH hardening
        assert "PasswordAuthentication no" in content
        assert "PermitRootLogin no" in content
        assert "systemctl restart sshd" in content


# ── Syntax check ────────────────────────────────────────────────────────


class TestSyntaxCheck:
    """Verify the script is syntactically valid bash."""

    def test_bash_syntax_valid(self):
        """bash -n should report no syntax errors."""
        r = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0, f"Syntax error in hetzner-bootstrap.sh:\n{r.stderr}"

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
        assert "Bootstrap a fresh Hetzner Ubuntu 22.04 VPS for Claude Code" in result.stdout

    def test_help_short_flag(self):
        """-h prints usage text and exits 0."""
        result = subprocess.run(
            ["bash", str(SCRIPT), "-h"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_help_mentions_required_components(self):
        """Help text mentions what the script installs."""
        result = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        assert "Creates user" in result.stdout
        assert "Node.js" in result.stdout
        assert "Claude Code" in result.stdout
        assert "Tailscale" in result.stdout
        assert "pnpm" in result.stdout
        assert "uv" in result.stdout
        assert "Must be run as root" in result.stdout
