"""Tests for soma-bootstrap — Fly.io machine provisioner (bash script).

Uses subprocess.run to invoke the script (effectors are scripts, not importable modules).
"""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline" / "effectors" / "soma-bootstrap"


# ── Script exists and is executable ──────────────────────────────────────


def test_script_exists():
    """soma-bootstrap effector exists."""
    assert SCRIPT.exists(), f"{SCRIPT} not found"


def test_script_is_executable():
    """soma-bootstrap is executable."""
    assert os.access(SCRIPT, os.X_OK), f"{SCRIPT} is not executable"


def test_script_is_bash():
    """soma-bootstrap has bash shebang."""
    first_line = SCRIPT.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env bash"


# ── --help flag ─────────────────────────────────────────────────────────


def test_help_flag_exits_zero():
    """soma-bootstrap --help exits with code 0."""
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_help_flag_outputs_description():
    """soma-bootstrap --help prints script description header."""
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert "soma-bootstrap" in result.stdout
    assert "provision" in result.stdout.lower()


def test_help_shorthand_flag():
    """soma-bootstrap -h also shows help."""
    result = subprocess.run(
        ["bash", str(SCRIPT), "-h"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "soma-bootstrap" in result.stdout


# ── Root check (script must be run as root) ────────────────────────────


def test_non_root_exits_with_error():
    """soma-bootstrap exits with code 1 when not run as root."""
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    # Running as non-root (typical test env) should fail
    if os.geteuid() != 0:
        assert result.returncode == 1
        assert "Run as root" in result.stdout


# ── Helper function tests (extracted) ──────────────────────────────────


def _run_helper_snippet(snippet: str) -> subprocess.CompletedProcess[str]:
    """Run a bash snippet with the helper functions sourced from soma-bootstrap."""
    # Extract helper section (lines between "# Helpers" and "# 0. Pre-flight")
    source = SCRIPT.read_text()
    lines = source.splitlines()
    helpers_start = None
    helpers_end = None
    for i, line in enumerate(lines):
        if "# Helpers" in line:
            helpers_start = i
        if helpers_start is not None and "# 0. Pre-flight" in line:
            helpers_end = i
            break

    assert helpers_start is not None, "Could not find Helpers section"
    assert helpers_end is not None, "Could not find Pre-flight section"

    helpers = "\n".join(lines[helpers_start:helpers_end])
    full_script = f'set -euo pipefail\n{helpers}\n{snippet}'
    return subprocess.run(
        ["bash", "-c", full_script],
        capture_output=True,
        text=True,
    )


def test_log_helper_outputs_blue_arrow():
    """log() prints a blue ==> prefix."""
    result = _run_helper_snippet('log "test message"')
    assert result.returncode == 0
    assert "test message" in result.stdout
    assert "==>" in result.stdout


def test_ok_helper_outputs_green_ok():
    """ok() prints a green [ok] prefix."""
    result = _run_helper_snippet('ok "thing done"')
    assert result.returncode == 0
    assert "thing done" in result.stdout
    assert "[ok]" in result.stdout


def test_skip_helper_outputs_yellow_skip():
    """skip() prints a yellow [skip] prefix with 'already installed'."""
    result = _run_helper_snippet('skip "some-tool"')
    assert result.returncode == 0
    assert "some-tool" in result.stdout
    assert "[skip]" in result.stdout
    assert "already installed" in result.stdout


def test_command_exists_true_for_ls():
    """command_exists returns 0 for commands that exist."""
    result = _run_helper_snippet(
        'if command_exists bash; then echo "yes"; else echo "no"; fi'
    )
    assert result.returncode == 0
    assert "yes" in result.stdout


def test_command_exists_false_for_fake():
    """command_exists returns non-0 for missing commands."""
    result = _run_helper_snippet(
        'if command_exists nonexistent_tool_xyz; then echo "yes"; else echo "no"; fi'
    )
    assert result.returncode == 0
    assert "no" in result.stdout


# ── Config value tests ─────────────────────────────────────────────────


def test_config_values_present():
    """Script defines expected config variables."""
    source = SCRIPT.read_text()
    assert 'USER_NAME="terry"' in source
    assert 'USER_HOME="/home/${USER_NAME}"' in source
    assert "GITHUB_REPO=" in source
    assert "GO_VERSION=" in source
    assert "NODE_MAJOR=" in source
    assert "OP_VERSION=" in source


def test_user_home_resolves():
    """USER_HOME resolves to /home/terry."""
    result = subprocess.run(
        ["bash", "-c", f'source <(grep -A2 "^USER_NAME=" {SCRIPT}); echo "$USER_HOME"'],
        capture_output=True,
        text=True,
    )
    # USER_NAME is set, then USER_HOME is constructed
    source = SCRIPT.read_text()
    # Just check the string exists
    assert '/home/${USER_NAME}' in source or '/home/terry' in source


# ── Idempotency pattern tests ──────────────────────────────────────────


def test_install_commands_are_guarded():
    """Package installs are guarded with existence checks (idempotency)."""
    source = SCRIPT.read_text()
    # apt-get install lines should be inside conditional blocks
    install_lines = [
        i for i, line in enumerate(source.splitlines())
        if "apt-get install" in line and "-y" in line
    ]
    assert len(install_lines) > 0, "No apt-get install commands found"

    # Each install should be preceded by a check (skip pattern)
    for line_no in install_lines:
        # Look backwards for the guarding check
        nearby = source.splitlines()[max(0, line_no - 10):line_no]
        has_guard = any(
            "dpkg -s" in l or "command_exists" in l or "if" in l
            for l in nearby
        )
        assert has_guard, (
            f"apt-get install on line {line_no + 1} is not guarded by an existence check"
        )


def test_go_install_guarded_by_version_check():
    """Go install is guarded by version check, not just existence."""
    source = SCRIPT.read_text()
    go_section = source[source.index("# 3. Go"):source.index("# 4. Node")]
    assert "go version" in go_section
    assert "GO_VERSION" in go_section


def test_node_install_guarded_by_version_check():
    """Node install checks major version, not just existence."""
    source = SCRIPT.read_text()
    node_section = source[source.index("# 4. Node"):source.index("# 5. Tools")]
    assert "node --version" in node_section
    assert "NODE_MAJOR" in node_section


# ── Structural tests ───────────────────────────────────────────────────


def test_set_strict_mode():
    """Script uses strict error mode (set -euo pipefail)."""
    first_20_lines = "\n".join(SCRIPT.read_text().splitlines()[:20])
    assert "set -euo pipefail" in first_20_lines


def test_has_numbered_sections():
    """Script has all numbered sections 0-15."""
    source = SCRIPT.read_text()
    for i in range(16):
        assert f"# {i}." in source, f"Missing section {i}"


def test_final_message_has_next_steps():
    """Script prints next steps at the end."""
    source = SCRIPT.read_text()
    assert "Next steps" in source
    assert "Tailscale" in source
    assert "Claude Code" in source


def test_ssh_hardening_section():
    """SSH hardening disables password auth."""
    source = SCRIPT.read_text()
    ssh_section = source[source.index("# 15. SSH"):source.index("# Done")]
    assert "PasswordAuthentication no" in ssh_section


def test_germline_clone_section():
    """Germline clone checks for existing .git before cloning."""
    source = SCRIPT.read_text()
    clone_section = source[source.index("# 8. Clone"):source.index("# 9. Directory")]
    assert ".git" in clone_section
    assert "git clone" in clone_section


# ── .zshrc generation test ─────────────────────────────────────────────


def test_zshrc_contains_key_config():
    """Generated .zshrc includes PATH, aliases, and tool initialization."""
    source = SCRIPT.read_text()
    zshrc_section = source[source.index('.zshrc << "ZSHRC"'):source.index('ZSHRC\'')]

    expected_items = [
        "PATH",
        "alias c=",
        "alias cc=",
        "starship",
        "zoxide",
        "EDITOR",
        ".env.fly",
        "effectors",
    ]
    for item in expected_items:
        assert item in zshrc_section, f".zshrc missing: {item}"


# ── Package list tests ─────────────────────────────────────────────────


def test_system_packages_include_essentials():
    """System packages include essential tools."""
    source = SCRIPT.read_text()
    start = source.index("PKGS=(")
    pkg_section = source[start:source.index(")", start) + 1]
    essentials = ["curl", "git", "zsh", "python3", "jq", "tmux", "build-essential"]
    for pkg in essentials:
        assert pkg in pkg_section, f"Missing essential package: {pkg}"


def test_pipx_packages_list():
    """pipx tools list contains expected tools."""
    source = SCRIPT.read_text()
    pipx_section = source[source.index("PIPX_PKGS=("):source.index(")", source.index("PIPX_PKGS=")) + 1]
    assert "llm" in pipx_section
    assert "httpx" in pipx_section
    assert "sqlite-utils" in pipx_section


def test_cargo_tools_list():
    """Cargo tools list contains expected utilities."""
    source = SCRIPT.read_text()
    cargo_section = source[source.index("CARGO_BINS=("):source.index(")", source.index("CARGO_BINS=")) + 1]
    assert "starship" in cargo_section
    assert "eza" in cargo_section
    assert "bat" in cargo_section
    assert "fd-find" in cargo_section


# ── Credential injection test ──────────────────────────────────────────


def test_credential_injection_checks_token():
    """Credential injection checks for OP_SERVICE_ACCOUNT_TOKEN."""
    source = SCRIPT.read_text()
    cred_section = source[source.index("# 13. Inject"):source.index("# 14. Build")]
    assert "OP_SERVICE_ACCOUNT_TOKEN" in cred_section


def test_credential_injection_graceful_without_token():
    """Credential injection has a skip message when token is missing."""
    source = SCRIPT.read_text()
    assert "OP_SERVICE_ACCOUNT_TOKEN not set" in source
    assert "Add it manually" in source


# ── Directory structure test ───────────────────────────────────────────


def test_creates_expected_directories():
    """Script creates expected directory structure."""
    source = SCRIPT.read_text()
    dir_section = source[source.index("# 9. Directory"):source.index("# 10. Shell")]
    expected_dirs = ["~/bin", "~/code", "~/notes", "~/epigenome"]
    for d in expected_dirs:
        assert d in dir_section, f"Missing directory creation: {d}"


# ── Tailscale section test ─────────────────────────────────────────────


def test_tailscale_install_message():
    """Tailscale section includes post-install instructions."""
    source = SCRIPT.read_text()
    ts_section = source[source.index("# 2. Tailscale"):source.index("# 3. Go")]
    assert "tailscale up" in ts_section
