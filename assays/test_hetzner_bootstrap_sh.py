from __future__ import annotations

"""Tests for effectors/hetzner-bootstrap.sh — bash script tested via subprocess."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "hetzner-bootstrap.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_help(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def test_help_exits_zero(self):
        r = _run_help("--help")
        assert r.returncode == 0

    def test_help_short_flag_exits_zero(self):
        r = _run_help("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run_help("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_hetzner(self):
        r = _run_help("--help")
        assert "Hetzner" in r.stdout or "hetzner" in r.stdout.lower()

    def test_help_mentions_claude_code(self):
        r = _run_help("--help")
        assert "Claude Code" in r.stdout

    def test_help_no_stderr(self):
        r = _run_help("--help")
        assert r.stderr == ""


# ── root check ─────────────────────────────────────────────────────────


class TestRootCheck:
    def test_fails_if_not_root(self):
        """Script should exit with 1 and an error message when run as non-root."""
        # We are running as non-root in this environment
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 1
        assert "ERROR: This script must be run as root." in r.stderr

    def test_has_root_check_logic(self):
        """Script should contain the EUID check logic."""
        src = SCRIPT.read_text()
        assert "EUID -ne 0" in src or "EUID != 0" in src
        assert "must be run as root" in src.lower()


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!") and "bash" in first

    def test_has_set_euo(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src


# ── script permissions ──────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()


# ── content checks ───────────────────────────────────────────────────────


class TestContentChecks:
    def test_mentions_user_terry(self):
        src = SCRIPT.read_text()
        assert "terry" in src

    def test_mentions_fnm(self):
        src = SCRIPT.read_text()
        assert "fnm" in src

    def test_mentions_tailscale(self):
        src = SCRIPT.read_text()
        assert "Tailscale" in src or "tailscale" in src.lower()

    def test_mentions_uv(self):
        src = SCRIPT.read_text()
        assert "uv" in src

    def test_mentions_pnpm(self):
        src = SCRIPT.read_text()
        assert "pnpm" in src

    def test_mentions_tmux_config(self):
        src = SCRIPT.read_text()
        assert ".tmux.conf" in src

    def test_has_system_updates(self):
        src = SCRIPT.read_text()
        assert "apt-get update && apt-get upgrade -y" in src

    def test_installs_build_essential(self):
        src = SCRIPT.read_text()
        assert "build-essential" in src

    def test_installs_htop_jq_unzip(self):
        src = SCRIPT.read_text()
        assert "htop" in src
        assert "jq" in src
        assert "unzip" in src

    def test_eval_fnm_env(self):
        src = SCRIPT.read_text()
        assert 'eval "$(fnm env)"' in src

    def test_correct_claude_package(self):
        src = SCRIPT.read_text()
        assert "@anthropic-ai/claude-code" in src

    def test_tailscale_install_url(self):
        src = SCRIPT.read_text()
        assert "https://tailscale.com/install.sh" in src

    def test_tmux_mouse_on(self):
        src = SCRIPT.read_text()
        assert "set -g mouse on" in src

    def test_mkdir_p_code_dirs(self):
        src = SCRIPT.read_text()
        assert "mkdir -p ~/code ~/scripts ~/code/epigenome/chromatin ~/skills" in src

    def test_mentions_gh_auth_login(self):
        src = SCRIPT.read_text()
        assert "gh auth login" in src

    def test_harden_ssh_robust(self):
        """SSH hardening should match both commented and uncommented lines."""
        src = SCRIPT.read_text()
        assert r"sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/'" in src
        assert r"sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin no/'" in src

    def test_restarts_sshd(self):
        src = SCRIPT.read_text()
        assert "systemctl restart sshd" in src


# ── syntax check ─────────────────────────────────────────────────────────


class TestSyntaxCheck:
    def test_bash_syntax_valid(self):
        """bash -n should report no syntax errors."""
        r = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0, f"Syntax error in hetzner-bootstrap.sh:\n{r.stderr}"


# ── no todo/fixme ────────────────────────────────────────────────────────


class TestNoTodoFixme:
    def test_no_todo_or_fixme(self):
        """Script should not contain TODO or FIXME markers."""
        content = SCRIPT.read_text()
        for line in content.splitlines():
            upper = line.upper()
            assert "TODO" not in upper, f"Found TODO: {line.strip()}"
            assert "FIXME" not in upper, f"Found FIXME: {line.strip()}"


# ── ends with newline ─────────────────────────────────────────────────────


class TestEndsWithNewline:
    def test_script_ends_with_newline(self):
        """Script should end with a trailing newline."""
        content = SCRIPT.read_text()
        assert content.endswith("\n"), "Script should end with a newline"
