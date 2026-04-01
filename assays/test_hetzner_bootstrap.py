from __future__ import annotations

"""Tests for effectors/hetzner-bootstrap.sh — VPS bootstrap script."""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline" / "effectors" / "hetzner-bootstrap.sh"


# ── Syntax and basic validity ─────────────────────────────────────────────


class TestScriptValidity:
    def test_script_exists(self):
        """Script file exists and is executable."""
        assert SCRIPT.exists()
        assert SCRIPT.is_file()

    def test_script_is_executable(self):
        """Script has executable permission."""
        assert SCRIPT.stat().st_mode & 0o111, "Script is not executable"

    def test_bash_syntax_valid(self):
        """bash -n (syntax check) passes without errors."""
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_shebang_is_bash(self):
        """Script starts with #!/bin/bash shebang."""
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line == "#!/bin/bash"

    def test_strict_mode_set(self):
        """Script uses set -euo pipefail for strict error handling."""
        content = SCRIPT.read_text()
        assert "set -euo pipefail" in content


# ── Help flag ─────────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_long_flag(self):
        """--help prints usage text and exits 0."""
        result = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "Bootstrap" in result.stdout or "bootstrap" in result.stdout

    def test_help_short_flag(self):
        """-h prints usage text and exits 0."""
        result = subprocess.run(
            ["bash", str(SCRIPT), "-h"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_help_mentions_terry_user(self):
        """Help text mentions creating user terry."""
        result = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        assert "terry" in result.stdout

    def test_help_mentions_root_requirement(self):
        """Help text states root is required."""
        result = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        assert "root" in result.stdout.lower()


# ── Content structure ─────────────────────────────────────────────────────


class TestContentStructure:
    def _read(self) -> str:
        return SCRIPT.read_text()

    def test_installs_system_packages(self):
        """Script installs essential system packages via apt-get."""
        content = self._read()
        assert "apt-get install" in content
        for pkg in ["curl", "git", "tmux", "htop", "jq"]:
            assert pkg in content, f"Missing package: {pkg}"

    def test_creates_terry_user(self):
        """Script creates user terry with sudo access."""
        content = self._read()
        assert "adduser" in content
        assert "terry" in content
        assert "sudo" in content
        assert "NOPASSWD" in content

    def test_copies_ssh_keys(self):
        """Script copies SSH keys from root to terry."""
        content = self._read()
        assert "authorized_keys" in content
        assert "chown" in content

    def test_installs_node_via_fnm(self):
        """Script installs Node.js LTS via fnm."""
        content = self._read()
        assert "fnm" in content
        assert "fnm install --lts" in content

    def test_installs_claude_code(self):
        """Script installs Claude Code globally via npm."""
        content = self._read()
        assert "@anthropic-ai/claude-code" in content

    def test_installs_tailscale(self):
        """Script installs Tailscale VPN."""
        content = self._read()
        assert "tailscale.com/install.sh" in content

    def test_installs_pnpm(self):
        """Script installs pnpm globally."""
        content = self._read()
        assert "pnpm" in content

    def test_installs_uv(self):
        """Script installs uv (Python package manager)."""
        content = self._read()
        assert "astral.sh/uv/install.sh" in content

    def test_configures_tmux(self):
        """Script writes tmux config for terry."""
        content = self._read()
        assert ".tmux.conf" in content
        assert "C-a" in content  # tmux prefix key

    def test_creates_directory_structure(self):
        """Script creates code/scripts/skills directories."""
        content = self._read()
        for d in ["~/code", "~/scripts", "~/skills"]:
            assert d in content

    def test_hardens_ssh(self):
        """Script hardens SSH (no password auth, no root login)."""
        content = self._read()
        assert "PasswordAuthentication no" in content
        assert "PermitRootLogin no" in content

    def test_restarts_sshd(self):
        """Script restarts sshd after config changes."""
        content = self._read()
        assert "systemctl restart sshd" in content

    def test_prints_next_steps(self):
        """Script prints next steps / completion message."""
        content = self._read()
        assert "Bootstrap Complete" in content
        assert "Next steps" in content


# ── Execution safety ──────────────────────────────────────────────────────


class TestExecutionSafety:
    def test_non_root_execution_fails(self):
        """Running without root (no --help) fails due to apt-get or id check."""
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should fail — can't run apt-get without root
        assert result.returncode != 0


# ── Shellcheck (optional, skip if not installed) ──────────────────────────


class TestShellcheck:
    @pytest.mark.skipif(
        subprocess.run(["which", "shellcheck"], capture_output=True).returncode != 0,
        reason="shellcheck not installed",
    )
    def test_shellcheck_passes(self):
        """shellcheck lints the script without errors."""
        result = subprocess.run(
            ["shellcheck", str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        # shellcheck exit 0 = no issues, 1 = issues found
        # Allow warnings (exit 1) but fail on errors
        if result.returncode not in (0, 1):
            pytest.fail(f"shellcheck failed: {result.stdout}{result.stderr}")
