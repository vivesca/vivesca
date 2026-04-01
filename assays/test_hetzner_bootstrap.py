from __future__ import annotations

"""Tests for hetzner-bootstrap.sh — Hetzner VPS bootstrap script.

Since the script requires root and modifies a live system, tests focus on:
- --help output and exit code
- Syntax validation (bash -n)
- Structural correctness of each bootstrap step
- Configuration block content (tmux, SSH hardening, user creation)
"""

import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "effectors" / "hetzner-bootstrap.sh"


def _read_script() -> str:
    return SCRIPT.read_text()


# ── Invocation tests ─────────────────────────────────────────────────


def test_help_flag_exits_zero():
    """--help flag exits with code 0."""
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_help_flag_shows_usage():
    """--help outputs usage information."""
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert "Usage:" in result.stdout
    assert "hetzner-bootstrap.sh" in result.stdout


def test_help_mentions_claude_code():
    """--help mentions Claude Code."""
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert "Claude Code" in result.stdout


def test_help_mentions_required_software():
    """--help mentions key software to be installed."""
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert "Node.js" in result.stdout
    assert "Tailscale" in result.stdout
    assert "pnpm" in result.stdout
    assert "uv" in result.stdout


def test_help_mentions_root_requirement():
    """--help mentions root requirement."""
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert "root" in result.stdout.lower()


def test_h_flag_same_as_help():
    """Short -h flag works the same as --help."""
    result = subprocess.run(
        ["bash", str(SCRIPT), "-h"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout


# ── Syntax validation ────────────────────────────────────────────────


def test_bash_syntax_valid():
    """Script passes bash -n syntax check."""
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


# ── Script structure tests ───────────────────────────────────────────


def test_shebang_is_bash():
    """Script has correct bash shebang."""
    first_line = _read_script().splitlines()[0]
    assert first_line == "#!/bin/bash"


def test_uses_strict_mode():
    """Script uses set -euo pipefail for strict error handling."""
    content = _read_script()
    assert "set -euo pipefail" in content


def test_has_system_update_step():
    """Script includes apt-get update and upgrade."""
    content = _read_script()
    assert "apt-get update" in content
    assert "apt-get upgrade" in content


def test_installs_required_packages():
    """Script installs essential packages."""
    content = _read_script()
    required = ["curl", "git", "tmux", "htop", "jq", "unzip", "build-essential"]
    for pkg in required:
        assert pkg in content, f"Missing package: {pkg}"


# ── User creation tests ──────────────────────────────────────────────


def test_creates_terry_user():
    """Script creates user 'terry' with sudo access."""
    content = _read_script()
    assert "adduser" in content
    assert "terry" in content
    assert "usermod -aG sudo terry" in content


def test_terry_sudo_nopasswd():
    """Script grants terry passwordless sudo."""
    content = _read_script()
    assert 'terry ALL=(ALL) NOPASSWD:ALL' in content


def test_checks_terry_exists_before_creating():
    """Script checks if terry already exists before creating."""
    content = _read_script()
    assert "if ! id terry" in content


def test_copies_ssh_keys():
    """Script copies root SSH keys to terry."""
    content = _read_script()
    assert "cp /root/.ssh/authorized_keys /home/terry/.ssh/" in content


def test_sets_ssh_key_permissions():
    """Script sets correct SSH key directory permissions."""
    content = _read_script()
    assert "chmod 700 /home/terry/.ssh" in content
    assert "chmod 600 /home/terry/.ssh/authorized_keys" in content


def test_chowns_ssh_dir():
    """Script chowns .ssh to terry."""
    content = _read_script()
    assert "chown -R terry:terry /home/terry/.ssh" in content


# ── Node.js / fnm installation tests ─────────────────────────────────


def test_installs_node_via_fnm():
    """Script installs Node.js LTS via fnm."""
    content = _read_script()
    assert "fnm" in content
    assert "fnm install --lts" in content
    assert "fnm default lts-latest" in content


def test_fnm_url_correct():
    """Script uses correct fnm install URL."""
    content = _read_script()
    assert "https://fnm.vercel.app/install" in content


# ── Claude Code installation tests ───────────────────────────────────


def test_installs_claude_code():
    """Script installs Claude Code globally via npm."""
    content = _read_script()
    assert "npm install -g @anthropic-ai/claude-code" in content


# ── Tailscale tests ──────────────────────────────────────────────────


def test_installs_tailscale():
    """Script installs Tailscale."""
    content = _read_script()
    assert "https://tailscale.com/install.sh" in content


def test_tailscale_up_reminder():
    """Script reminds user to run tailscale up."""
    content = _read_script()
    assert "tailscale up" in content


# ── pnpm installation tests ──────────────────────────────────────────


def test_installs_pnpm():
    """Script installs pnpm globally."""
    content = _read_script()
    assert "npm install -g pnpm" in content


# ── uv installation tests ────────────────────────────────────────────


def test_installs_uv():
    """Script installs uv (Python package manager)."""
    content = _read_script()
    assert "https://astral.sh/uv/install.sh" in content


# ── tmux config tests ────────────────────────────────────────────────


def test_tmux_config_present():
    """Script writes a tmux.conf for terry."""
    content = _read_script()
    assert ".tmux.conf" in content


def test_tmux_prefix_ctrl_a():
    """tmux config uses Ctrl-a prefix (not default Ctrl-b)."""
    content = _read_script()
    assert "set -g prefix C-a" in content
    assert "unbind C-b" in content


def test_tmux_mouse_enabled():
    """tmux config enables mouse support."""
    content = _read_script()
    assert "set -g mouse on" in content


def test_tmux_large_history():
    """tmux config sets large scrollback history."""
    content = _read_script()
    assert "set -g history-limit 50000" in content


def test_tmux_256color():
    """tmux config sets 256-color terminal."""
    content = _read_script()
    assert "screen-256color" in content
    assert "xterm-256color" in content


def test_tmux_base_index_1():
    """tmux config sets base-index to 1."""
    content = _read_script()
    assert "set -g base-index 1" in content


def test_tmux_no_escape_delay():
    """tmux config disables escape delay."""
    content = _read_script()
    assert "set -g escape-time 0" in content


# ── SSH hardening tests ──────────────────────────────────────────────


def test_disables_password_auth():
    """Script disables SSH password authentication."""
    content = _read_script()
    assert "PasswordAuthentication no" in content


def test_disables_root_login():
    """Script disables root SSH login."""
    content = _read_script()
    assert "PermitRootLogin no" in content


def test_restarts_sshd():
    """Script restarts sshd after config changes."""
    content = _read_script()
    assert "systemctl restart sshd" in content


# ── Directory creation tests ─────────────────────────────────────────


def test_creates_code_directories():
    """Script creates expected directory structure for terry."""
    content = _read_script()
    assert "mkdir -p ~/code" in content or "mkdir -p $HOME/code" in content or "mkdir -p /home/terry/code" in content or "mkdir -p ~/code ~/scripts" in content
    assert "~/scripts" in content or "/home/terry/scripts" in content


def test_creates_skills_dir():
    """Script creates skills directory."""
    content = _read_script()
    assert "~/skills" in content or "/home/terry/skills" in content


# ── Bootstrap completion tests ───────────────────────────────────────


def test_prints_completion_message():
    """Script prints a bootstrap completion message."""
    content = _read_script()
    assert "Bootstrap Complete" in content


def test_prints_next_steps():
    """Script prints next steps after bootstrap."""
    content = _read_script()
    assert "Next steps" in content


def test_mentions_ssh_as_terry():
    """Next steps mention SSH as terry user."""
    content = _read_script()
    assert "ssh terry@" in content


def test_mentions_gh_auth():
    """Next steps mention GitHub auth."""
    content = _read_script()
    assert "gh auth login" in content


def test_mentions_tailscale_hostname():
    """Next steps mention connecting via Tailscale hostname."""
    content = _read_script()
    assert "tailscale-hostname" in content


# ── Safety / ordering tests ──────────────────────────────────────────


def test_ssh_hardening_after_user_creation():
    """SSH hardening happens after user is created (so you can still get in)."""
    content = _read_script()
    user_pos = content.index("adduser")
    ssh_pos = content.index("PermitRootLogin no")
    assert user_pos < ssh_pos, "User must be created before SSH is hardened"


def test_help_before_system_changes():
    """--help check is at the top, before any system-modifying commands."""
    content = _read_script()
    help_pos = content.index("--help")
    apt_pos = content.index("apt-get update")
    assert help_pos < apt_pos, "--help should be checked before system changes"


def test_node_before_claude_code():
    """Node.js is installed before Claude Code."""
    content = _read_script()
    fnm_pos = content.index("fnm install")
    claude_pos = content.index("claude-code")
    assert fnm_pos < claude_pos, "Node.js must be installed before Claude Code"


def test_runs_as_sudo_u_terry_for_user_steps():
    """User-scoped steps use sudo -u terry."""
    content = _read_script()
    assert "sudo -u terry bash -c" in content


def test_fnm_env_sourced_for_npm():
    """fnm env is evaluated before npm commands."""
    content = _read_script()
    # Find the Claude Code install block and check fnm env is sourced there
    claude_block_start = content.index("npm install -g @anthropic-ai/claude-code")
    block_before = content[:claude_block_start]
    # The last occurrence of fnm env before the npm install
    assert 'eval "$(fnm env)"' in block_before
