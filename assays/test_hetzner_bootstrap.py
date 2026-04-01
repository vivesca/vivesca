from __future__ import annotations

"""Tests for effectors/hetzner-bootstrap.sh — Hetzner VPS bootstrap script."""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "hetzner-bootstrap.sh"


class TestHelpFlags:
    """--help and -h should print usage and exit 0."""

    def test_help_long(self):
        result = subprocess.run(
            [str(SCRIPT), "--help"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Usage: hetzner-bootstrap.sh" in result.stdout
        assert "Bootstrap a fresh Hetzner" in result.stdout

    def test_help_short(self):
        result = subprocess.run(
            [str(SCRIPT), "-h"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Usage: hetzner-bootstrap.sh" in result.stdout

    def test_help_mentions_prerequisites(self):
        result = subprocess.run(
            [str(SCRIPT), "--help"], capture_output=True, text=True
        )
        assert "root" in result.stdout.lower()
        assert "Ubuntu" in result.stdout


class TestRootGuard:
    """Running as non-root should fail with a clear error."""

    def test_non_root_exits_1(self):
        result = subprocess.run(
            [str(SCRIPT)], capture_output=True, text=True
        )
        # We are not root, so the script should exit 1
        assert result.returncode == 1

    def test_non_root_stderr_message(self):
        result = subprocess.run(
            [str(SCRIPT)], capture_output=True, text=True
        )
        assert "must be run as root" in result.stderr


class TestSyntax:
    """Static checks on the script file."""

    def test_file_exists_and_executable(self):
        assert SCRIPT.exists()
        assert SCRIPT.stat().st_mode & 0o111  # executable bit set

    def test_bash_syntax_valid(self):
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)], capture_output=True, text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_set_strict_mode(self):
        content = SCRIPT.read_text()
        assert "set -euo pipefail" in content

    def test_shebang(self):
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line == "#!/usr/bin/env bash"


class TestContentStructure:
    """Verify all documented bootstrap steps are present."""

    @pytest.fixture(autouse=True)
    def _read_script(self):
        self.content = SCRIPT.read_text()

    def test_system_update_step(self):
        assert "apt-get update" in self.content
        assert "apt-get upgrade -y" in self.content

    def test_packages_installed(self):
        required = ["curl", "git", "tmux", "htop", "jq", "unzip", "build-essential"]
        for pkg in required:
            assert pkg in self.content, f"Missing package: {pkg}"

    def test_user_creation_step(self):
        assert 'adduser --disabled-password --gecos "" terry' in self.content
        assert "usermod -aG sudo terry" in self.content

    def test_sudoers_nopasswd(self):
        assert '"terry ALL=(ALL) NOPASSWD:ALL"' in self.content

    def test_ssh_key_copy(self):
        assert "/root/.ssh/authorized_keys" in self.content
        assert "~terry/.ssh" in self.content

    def test_fnm_node_install(self):
        assert "fnm.vercel.app/install" in self.content
        assert "fnm install --lts" in self.content

    def test_claude_code_install(self):
        assert "@anthropic-ai/claude-code" in self.content

    def test_tailscale_install(self):
        assert "tailscale.com/install.sh" in self.content
        assert "tailscale up" in self.content

    def test_pnpm_install(self):
        assert "npm install -g pnpm" in self.content

    def test_uv_install(self):
        assert "astral.sh/uv/install.sh" in self.content

    def test_tmux_config(self):
        assert ".tmux.conf" in self.content
        assert "set -g prefix C-a" in self.content
        assert "set -g mouse on" in self.content

    def test_directory_creation(self):
        for d in ["~/code", "~/scripts", "~/skills"]:
            assert d in self.content

    def test_ssh_hardening(self):
        assert "PasswordAuthentication no" in self.content
        assert "PermitRootLogin no" in self.content
        assert "systemctl restart sshd" in self.content

    def test_completion_message(self):
        assert "Bootstrap Complete" in self.content
        assert "Next steps" in self.content


class TestIdempotentUserCheck:
    """The user-creation block should be guarded with 'if ! id terry'."""

    def test_user_creation_guarded(self):
        content = SCRIPT.read_text()
        assert "if ! id terry" in content


class TestShellcheck:
    """Run shellcheck if available; skip otherwise."""

    def test_shellcheck_passes(self):
        result = subprocess.run(
            ["which", "shellcheck"], capture_output=True, text=True
        )
        if result.returncode != 0:
            pytest.skip("shellcheck not installed")

        result = subprocess.run(
            ["shellcheck", str(SCRIPT)], capture_output=True, text=True
        )
        # Allow warnings but not errors
        assert result.returncode == 0, f"Shellcheck issues:\n{result.stdout}{result.stderr}"
