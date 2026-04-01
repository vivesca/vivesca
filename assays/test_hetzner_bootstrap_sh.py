from __future__ import annotations

"""Tests for effectors/hetzner-bootstrap.sh — bash script tested via subprocess."""

import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "hetzner-bootstrap.sh"


def _src() -> str:
    """Return the script source text."""
    return SCRIPT.read_text()


# ── script structure tests ──────────────────────────────────────────────


class TestScriptStructure:
    def test_script_exists(self):
        assert SCRIPT.exists()

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_has_shebang(self):
        first_line = _src().splitlines()[0]
        assert first_line == "#!/usr/bin/env bash"

    def test_script_has_set_euo_pipefail(self):
        assert "set -euo pipefail" in _src()


# ── --help tests ────────────────────────────────────────────────────────


class TestHelpFlag:
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_help_exits_zero(self):
        assert self._run("--help").returncode == 0

    def test_h_short_flag_exits_zero(self):
        assert self._run("-h").returncode == 0

    def test_help_shows_usage(self):
        assert "Usage:" in self._run("--help").stdout

    def test_help_mentions_hetzner(self):
        assert "Hetzner" in self._run("--help").stdout

    def test_help_mentions_ubuntu(self):
        assert "Ubuntu" in self._run("--help").stdout

    def test_help_no_stderr(self):
        assert self._run("--help").stderr == ""

    def test_help_mentions_claude_code(self):
        assert "Claude Code" in self._run("--help").stdout

    def test_help_mentions_install_targets(self):
        out = self._run("--help").stdout
        assert "Node.js" in out
        assert "Tailscale" in out
        assert "pnpm" in out
        assert "uv" in out

    def test_help_mentions_must_be_root(self):
        assert "root" in self._run("--help").stdout.lower()


# ── permission check tests ───────────────────────────────────────────────


class TestPermissionCheck:
    def test_fails_when_not_root(self):
        """Script exits 1 with error on stderr when run as non-root."""
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 1
        assert "ERROR: This script must be run as root" in r.stderr

    def test_permission_check_source_pattern(self):
        """Source contains the EUID guard before the bootstrap body."""
        src = _src()
        # The guard must appear before the bootstrap banner
        guard_pos = src.index("EUID")
        banner_pos = src.index("=== Hetzner Claude Code Bootstrap ===")
        assert guard_pos < banner_pos

    def test_error_message_to_stderr(self):
        """The root-check error message is redirected to stderr (>&2)."""
        src = _src()
        assert '>&2' in src
        assert "ERROR: This script must be run as root" in src


# ── content analysis: bootstrap sections ─────────────────────────────────


class TestBootstrapSections:
    """Verify the script contains all expected bootstrap sections in order."""

    def _section_positions(self) -> dict[str, int]:
        src = _src()
        sections = {
            "system_updates": "apt-get update",
            "install_packages": "apt-get install",
            "create_user": "adduser",
            "sudo_nopasswd": "NOPASSWD",
            "ssh_keys_copy": "authorized_keys",
            "install_node": "fnm",
            "install_claude_code": "@anthropic-ai/claude-code",
            "install_tailscale": "tailscale.com/install.sh",
            "install_pnpm": "npm install -g pnpm",
            "install_uv": "astral.sh/uv/install.sh",
            "tmux_config": ".tmux.conf",
            "create_dirs": "mkdir -p",
            "harden_ssh_password": "PasswordAuthentication no",
            "harden_ssh_root": "PermitRootLogin no",
            "restart_sshd": "systemctl restart sshd",
        }
        positions = {}
        for name, marker in sections.items():
            assert marker in src, f"Missing section marker: {marker}"
            positions[name] = src.index(marker)
        return positions

    def test_system_updates_section(self):
        pos = self._section_positions()
        assert pos["system_updates"] < pos["install_packages"]

    def test_user_creation_before_node_install(self):
        pos = self._section_positions()
        assert pos["create_user"] < pos["install_node"]

    def test_node_before_claude_code(self):
        pos = self._section_positions()
        assert pos["install_node"] < pos["install_claude_code"]

    def test_claude_code_before_tailscale(self):
        pos = self._section_positions()
        assert pos["install_claude_code"] < pos["install_tailscale"]

    def test_tailscale_before_pnpm(self):
        pos = self._section_positions()
        assert pos["install_tailscale"] < pos["install_pnpm"]

    def test_pnpm_before_uv(self):
        pos = self._section_positions()
        assert pos["install_pnpm"] < pos["install_uv"]

    def test_uv_before_tmux(self):
        pos = self._section_positions()
        assert pos["install_uv"] < pos["tmux_config"]

    def test_tmux_before_dirs(self):
        pos = self._section_positions()
        assert pos["tmux_config"] < pos["create_dirs"]

    def test_dirs_before_ssh_hardening(self):
        pos = self._section_positions()
        assert pos["create_dirs"] < pos["harden_ssh_password"]

    def test_ssh_hardening_before_restart(self):
        pos = self._section_positions()
        assert pos["harden_ssh_password"] < pos["restart_sshd"]


# ── content analysis: user creation ──────────────────────────────────────


class TestUserCreation:
    def test_creates_user_terry(self):
        assert 'adduser --disabled-password --gecos "" terry' in _src()

    def test_adds_to_sudo_group(self):
        assert "usermod -aG sudo terry" in _src()

    def test_nopasswd_sudoers(self):
        assert 'echo "terry ALL=(ALL) NOPASSWD:ALL"' in _src()

    def test_sudoers_file_path(self):
        assert "/etc/sudoers.d/terry" in _src()

    def test_checks_user_exists_before_create(self):
        assert "id terry" in _src()

    def test_copies_ssh_keys_from_root(self):
        src = _src()
        assert "/root/.ssh/authorized_keys" in src
        assert "/home/terry/.ssh/" in src

    def test_sets_ssh_dir_permissions(self):
        src = _src()
        assert "chmod 700 /home/terry/.ssh" in src
        assert "chmod 600 /home/terry/.ssh/authorized_keys" in src

    def test_chowns_ssh_dir(self):
        assert "chown -R terry:terry /home/terry/.ssh" in _src()


# ── content analysis: packages ───────────────────────────────────────────


class TestPackageInstallation:
    def test_installs_essential_packages(self):
        src = _src()
        for pkg in ["curl", "git", "tmux", "htop", "jq", "unzip", "build-essential"]:
            assert pkg in src, f"Missing package: {pkg}"

    def test_uses_fnm_for_node(self):
        src = _src()
        assert "fnm.vercel.app/install" in src
        assert "fnm install --lts" in src

    def test_installs_claude_code_globally(self):
        assert "npm install -g @anthropic-ai/claude-code" in _src()

    def test_installs_uv_via_astral(self):
        assert "astral.sh/uv/install.sh" in _src()


# ── content analysis: tmux config ────────────────────────────────────────


class TestTmuxConfig:
    _TMUX_LINES = [
        "set -g prefix C-a",
        "unbind C-b",
        "set -g mouse on",
        "set -g history-limit 50000",
        "set -g base-index 1",
        "set -g escape-time 0",
    ]

    @pytest.mark.parametrize("line", _TMUX_LINES)
    def test_tmux_config_contains(self, line: str):
        assert line in _src()

    def test_tmux_config_written_as_terry(self):
        src = _src()
        assert "sudo -u terry bash -c" in src
        assert ".tmux.conf" in src


# ── content analysis: SSH hardening ──────────────────────────────────────


class TestSSHHardening:
    def test_disables_password_auth(self):
        assert "PasswordAuthentication no" in _src()

    def test_disables_root_login(self):
        assert "PermitRootLogin no" in _src()

    def test_restarts_sshd(self):
        assert "systemctl restart sshd" in _src()

    def test_uses_sed_for_sshd_config(self):
        src = _src()
        assert "sed -i" in src
        assert "/etc/ssh/sshd_config" in src


# ── content analysis: directory creation ─────────────────────────────────


class TestDirectoryCreation:
    def test_creates_code_dir(self):
        assert "~/code" in _src()

    def test_creates_scripts_dir(self):
        assert "~/scripts" in _src()

    def test_creates_chromatin_dir(self):
        assert "~/code/epigenome/chromatin" in _src()

    def test_creates_skills_dir(self):
        assert "~/skills" in _src()


# ── content analysis: completion message ─────────────────────────────────


class TestCompletionMessage:
    def test_bootstrap_complete_banner(self):
        assert "=== Bootstrap Complete ===" in _src()

    def test_next_steps_section(self):
        src = _src()
        assert "Next steps:" in src
        assert "SSH in as terry" in src

    def test_mentions_tailscale_auth(self):
        assert "tailscale up" in _src()

    def test_mentions_tailscale_hostname(self):
        assert "tailscale-hostname" in _src()

    def test_mentions_claude_code_auth(self):
        src = _src()
        assert "claude" in src.lower()

    def test_mentions_gh_auth(self):
        assert "gh auth login" in _src()


# ── content analysis: user execution context ─────────────────────────────


class TestUserContext:
    """Verify that dangerous operations run as the correct user."""

    def test_node_install_as_terry(self):
        src = _src()
        # The fnm/node install block should be wrapped in sudo -u terry
        fnm_pos = src.index("fnm.vercel.app/install")
        # Find the nearest "sudo -u terry" before the fnm install
        preceding = src[:fnm_pos]
        assert "sudo -u terry" in preceding

    def test_claude_code_install_as_terry(self):
        src = _src()
        cc_pos = src.index("@anthropic-ai/claude-code")
        preceding = src[:cc_pos]
        assert "sudo -u terry" in preceding

    def test_tailscale_install_as_root(self):
        """Tailscale system-level install runs as root (no sudo -u prefix)."""
        src = _src()
        ts_pos = src.index("tailscale.com/install.sh")
        preceding = src[:ts_pos]
        # There should be no 'sudo -u terry' in the few lines before tailscale
        last_sudo_u = preceding.rfind("sudo -u terry")
        last_closing = preceding.rfind("'")
        # The tailscale install is outside any sudo -u terry block
        if last_sudo_u != -1:
            assert last_closing > last_sudo_u, (
                "Tailscale install should not be inside a sudo -u terry block"
            )


# ── content analysis: idempotency guards ────────────────────────────────


class TestIdempotency:
    def test_user_creation_gated(self):
        """User creation is gated by 'id terry' check."""
        src = _src()
        # The adduser should be inside an if-block
        assert "if ! id terry &>/dev/null; then" in src

    def test_ssh_hardening_uses_sed_replace(self):
        """SSH settings use sed replace (idempotent re-run)."""
        src = _src()
        assert "sed -i 's/^#\\?PasswordAuthentication" in src
