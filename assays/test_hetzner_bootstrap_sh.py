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
            "create_dirs": "~/code ~/scripts",
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
        assert "~terry/.ssh" in src

    def test_sets_ssh_dir_permissions(self):
        src = _src()
        assert "chmod 700 ~terry/.ssh" in src
        assert "chmod 600 ~terry/.ssh/authorized_keys" in src

    def test_chowns_ssh_dir(self):
        assert "chown -R terry:terry ~terry/.ssh" in _src()


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

    def test_no_todo_fixme_markers(self):
        """Script must not contain TODO or FIXME markers."""
        src = _src()
        for marker in ("TODO", "FIXME"):
            assert marker not in src, f"Script contains {marker}"

    def test_mentions_ubuntu_22_04(self):
        """Help text and/or comments reference Ubuntu 22.04."""
        src = _src()
        assert "22.04" in src

    def test_fnm_env_evaluated(self):
        """fnm env is evaluated before using fnm."""
        src = _src()
        assert 'eval "$(fnm env)"' in src

    def test_fnm_default_lts(self):
        """fnm default is set to lts-latest."""
        src = _src()
        assert "fnm default lts-latest" in src

    def test_banner_not_printed_as_nonroot(self):
        """Banner is NOT printed when run as non-root (fails first)."""
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 1
        assert "=== Hetzner Claude Code Bootstrap ===" not in r.stdout

    def test_no_hardcoded_passwords(self):
        """Script must not contain hardcoded passwords."""
        src = _src()
        # Common patterns that indicate hardcoded passwords
        for pattern in ("password=", "PASSWORD=", "passwd="):
            assert pattern not in src

    def test_completion_message_is_last_section(self):
        """Completion message appears after all operational sections."""
        src = _src()
        completion_pos = src.index("=== Bootstrap Complete ===")
        sshd_restart_pos = src.index("systemctl restart sshd")
        assert sshd_restart_pos < completion_pos

    def test_all_curl_uses_fail_silent_flags(self):
        """All curl invocations use -f (fail silently on HTTP errors) or -LsSf."""
        import re as _re
        src = _src()
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.strip()
            # Match curl as a command (pipelines, standalone), not as package name
            if _re.search(r"(?:^|\|)\s*curl\b", stripped):
                assert "-f" in stripped or "-LsSf" in stripped, (
                    f"Line {i}: curl without fail flag: {stripped}"
                )

    def test_apt_get_uses_assume_yes(self):
        """All apt-get install/upgrade commands use -y flag."""
        src = _src()
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.strip()
            if "apt-get install" in stripped or "apt-get upgrade" in stripped:
                assert " -y" in stripped, (
                    f"Line {i}: apt-get without -y: {stripped}"
                )

    def test_no_interactive_commands(self):
        """Script must not contain interactive prompts (read, select)."""
        src = _src()
        # 'read' at start of command (not in comments/strings)
        import re
        # Avoid matching 'read' in words like 'unreadable' or in comments
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Match 'read ' as a command but not in a string context
            if re.search(r"\bread\b", stripped) and "read -" not in stripped:
                # Allow 'read' in echo strings
                assert "echo" in stripped or "'" in stripped or '"' in stripped, (
                    f"Line {i}: interactive 'read' command: {stripped}"
                )

    def test_tailscale_install_message(self):
        """Script prints Tailscale authentication reminder."""
        src = _src()
        assert "tailscale up" in src


# ── bash syntax & shellcheck ───────────────────────────────────────────────


class TestBashSyntax:
    """Verify the script is valid bash."""

    def test_bash_n_syntax_check(self):
        """bash -n (noexec syntax check) passes on the script."""
        r = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0, f"Syntax error: {r.stderr}"


class TestShellcheck:
    """Run shellcheck if available; skip otherwise."""

    def test_shellcheck_passes(self):
        r = subprocess.run(
            ["which", "shellcheck"], capture_output=True, text=True
        )
        if r.returncode != 0:
            pytest.skip("shellcheck not installed")

        r = subprocess.run(
            ["shellcheck", str(SCRIPT)], capture_output=True, text=True
        )
        assert r.returncode == 0, f"Shellcheck issues:\n{r.stdout}{r.stderr}"


# ── additional edge-case tests ─────────────────────────────────────────────


class TestEdgeCases:
    """Misc edge cases not covered by other test classes."""

    def test_no_empty_subshells(self):
        """No empty sudo -u terry blocks (would be a no-op)."""
        src = _src()
        # Check every sudo -u terry bash -c block has non-empty body
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "sudo -u terry bash -c" in line and "<<" not in line:
                # Next line should not be just a closing quote
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    assert next_line != "'", f"Line {i+2}: empty sudo -u terry block"

    def test_all_urls_use_https(self):
        """All download URLs use HTTPS, not HTTP."""
        src = _src()
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.strip()
            if "http://" in stripped and "127.0.0" not in stripped and "localhost" not in stripped:
                # Allow http in comments
                assert stripped.startswith("#"), (
                    f"Line {i}: insecure HTTP URL: {stripped}"
                )

    def test_no_curl_piped_to_sh_without_check(self):
        """Curl | sh patterns should be from trusted sources only."""
        src = _src()
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.strip()
            if "| sh" in stripped or "| bash" in stripped:
                # Must be from known trusted domains
                assert any(
                    domain in stripped
                    for domain in ("tailscale.com", "fnm.vercel.app", "astral.sh")
                ), f"Line {i}: untrusted curl|sh: {stripped}"

    def test_no_deprecated_apt_commands(self):
        """No deprecated apt-get commands (e.g., apt-get dist-upgrade)."""
        src = _src()
        # dist-upgrade can be risky in automated scripts
        assert "dist-upgrade" not in src

    def test_user_creation_guards_ssh_copy(self):
        """SSH key copy is inside the same if-block as user creation."""
        src = _src()
        adduser_pos = src.index("adduser")
        ssh_copy_pos = src.index("authorized_keys", adduser_pos)
        # Find the if block boundaries
        if_pos = src.rfind("if ! id terry", 0, adduser_pos)
        fi_pos = src.find("fi", ssh_copy_pos)
        # Both should be in the same if block
        assert if_pos < adduser_pos < ssh_copy_pos < fi_pos

    def test_fnm_path_set_before_eval(self):
        """fnm PATH is set before eval "$(fnm env)" in node install block."""
        src = _src()
        # Find the fnm install block
        fnm_install = src.index("fnm.vercel.app/install")
        fnm_block = src[fnm_install:src.index("fnm default lts-latest") + 30]
        path_pos = fnm_block.index("PATH")
        eval_pos = fnm_block.index('eval "$(fnm env)"')
        assert path_pos < eval_pos

    def test_tmux_config_uses_heredoc(self):
        """tmux config is written via heredoc, not echo per line."""
        src = _src()
        # The tmux section should use a heredoc (<<) for clean multiline write
        tmux_pos = src.index(".tmux.conf")
        preceding = src[:tmux_pos + 100]
        assert "<<" in preceding


# ── additional coverage: tmux, heredoc, hygiene, fnm subshells ────────────


class TestTmuxExtended:
    """Test tmux config lines not in the parametrized TestTmuxConfig."""

    _EXTRA_LINES = [
        "bind C-a send-prefix",
        'set -g default-terminal "screen-256color"',
        ',xterm-256color:Tc',
        "set -g status-style",
    ]

    @pytest.mark.parametrize("line", _EXTRA_LINES)
    def test_tmux_extra_config_contains(self, line: str):
        assert line in _src()

    def test_tmux_heredoc_delimiter_quoted(self):
        """Heredoc delimiter is quoted to prevent variable expansion."""
        src = _src()
        assert '<< "TMUX"' in src or "<<'TMUX'" in src

    def test_tmux_heredoc_closes(self):
        """Heredoc has a matching close delimiter."""
        src = _src()
        assert "TMUX'" in src


class TestFileHygiene:
    """File-level hygiene checks."""

    def test_no_crlf_line_endings(self):
        """Script must use Unix line endings only."""
        raw = SCRIPT.read_bytes()
        assert b"\r\n" not in raw

    def test_script_ends_with_newline(self):
        """Script ends with a trailing newline (POSIX)."""
        raw = SCRIPT.read_text()
        assert raw.endswith("\n")

    def test_no_trailing_whitespace_on_commands(self):
        """No significant lines have trailing whitespace."""
        for i, line in enumerate(_src().splitlines(), 1):
            stripped = line.rstrip()
            if stripped and not stripped.startswith("#"):
                assert line == stripped or line == stripped + "\n", (
                    f"Line {i}: trailing whitespace"
                )


class TestFnmSubshells:
    """Each sudo -u terry block that needs node/fnm sets up PATH + eval."""

    def test_claude_code_block_has_fnm_env(self):
        """The Claude Code install block evaluates fnm env."""
        src = _src()
        cc_block_start = src.index("@anthropic-ai/claude-code")
        # Find the sudo -u terry block containing claude-code
        block_start = src.rfind("sudo -u terry", 0, cc_block_start)
        block_end = src.find("\n'", cc_block_start) + 1
        block = src[block_start:block_end]
        assert "fnm env" in block

    def test_pnpm_block_has_fnm_env(self):
        """The pnpm install block evaluates fnm env."""
        src = _src()
        pnpm_pos = src.index("npm install -g pnpm")
        block_start = src.rfind("sudo -u terry", 0, pnpm_pos)
        block_end = src.find("\n'", pnpm_pos) + 1
        block = src[block_start:block_end]
        assert "fnm env" in block

    def test_no_sudo_inside_sudo_u_blocks(self):
        """No 'sudo' used inside sudo -u terry subshell blocks."""
        src = _src()
        lines = src.splitlines()
        in_sudo_block = False
        for i, line in enumerate(lines, 1):
            if "sudo -u terry bash -c" in line:
                in_sudo_block = True
                continue
            if in_sudo_block:
                stripped = line.strip()
                if stripped == "'":
                    in_sudo_block = False
                    continue
                assert "sudo " not in stripped or stripped.startswith("#"), (
                    f"Line {i}: sudo inside sudo -u terry block: {stripped}"
                )


class TestHelpUsagePattern:
    """Test the --help output mentions the recommended invocation."""

    def _run(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_help_shows_bash_s_usage(self):
        out = self._run().stdout
        assert "bash -s" in out

    def test_help_shows_ssh_root_pattern(self):
        out = self._run().stdout
        assert "ssh root@" in out

    def test_help_exits_cleanly(self):
        """No stdout/stderr leakage after help."""
        r = self._run()
        lines = r.stdout.strip().splitlines()
        assert len(lines) >= 3, "Help should have multiple lines"

    def test_help_mentions_user_terry(self):
        assert "terry" in self._run().stdout


class TestSSHSedPatterns:
    """Verify the sed patterns are correct for SSH hardening."""

    def test_password_auth_sed_handles_commented_and_uncommented(self):
        """Pattern matches both #PasswordAuthentication and PasswordAuthentication."""
        src = _src()
        assert "^#\\?PasswordAuthentication" in src

    def test_root_login_sed_handles_commented_and_uncommented(self):
        """Pattern matches both #PermitRootLogin and PermitRootLogin."""
        src = _src()
        assert "^#\\?PermitRootLogin" in src

    def test_sed_replaces_value_to_no(self):
        """Both sed patterns replace to 'no'."""
        src = _src()
        lines = [l for l in src.splitlines() if "sed -i" in l and "sshd_config" in l]
        for line in lines:
            assert line.strip().endswith("no'/") or "no/" in line


class TestDirectoryOwnership:
    """Verify directories are created as the correct user."""

    def test_dirs_created_as_terry(self):
        """Directory creation is inside a sudo -u terry block."""
        src = _src()
        mkdir_pos = src.index("mkdir -p ~/code")
        preceding = src[:mkdir_pos]
        assert "sudo -u terry" in preceding[-200:]

    def test_mkdir_creates_all_dirs_at_once(self):
        """All directories are created in a single mkdir -p call."""
        src = _src()
        assert "mkdir -p ~/code ~/scripts ~/code/epigenome/chromatin ~/skills" in src


class TestInvalidFlags:
    """Verify script behavior with unexpected arguments."""

    def test_unknown_flag_exits_nonzero(self):
        """An unrecognized flag should cause an error (set -e)."""
        r = subprocess.run(
            ["bash", str(SCRIPT), "--bogus"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode != 0

    def test_no_args_fails_as_nonroot(self):
        """Running without args (not root) exits 1."""
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 1


# ── additional coverage: set -euo pipefail, echo messages, heredoc ─────────


class TestSetFlags:
    """Verify strict bash flags are properly set."""

    def test_set_e_is_active(self):
        """set -e exits on first error."""
        src = _src()
        assert "set -e" in src

    def test_set_u_is_active(self):
        """set -u treats unset variables as errors."""
        assert "set -u" in _src() or "set -euo pipefail" in _src()

    def test_set_o_pipefail_is_active(self):
        """set -o pipefail catches failures in piped commands."""
        assert "pipefail" in _src()

    def test_set_flag_is_first_non_shebang(self):
        """set -euo pipefail appears before any real commands."""
        lines = _src().splitlines()
        # Skip shebang and blank/comment lines
        for line in lines[1:]:
            stripped = line.strip()
            if stripped == "" or stripped.startswith("#"):
                continue
            assert "set -euo pipefail" in stripped, (
                f"First non-comment line after shebang should be set: {stripped}"
            )
            break


class TestEchoMessages:
    """Verify informational echo messages in the script."""

    def test_bootstrap_banner_at_start(self):
        """Bootstrap banner appears early in execution (after guard checks)."""
        src = _src()
        banner_pos = src.index("=== Hetzner Claude Code Bootstrap ===")
        # Banner must come after the EUID guard
        guard_pos = src.index("EUID")
        assert guard_pos < banner_pos

    def test_tailscale_reminder_message(self):
        """Script prints a Tailscale reminder after install."""
        src = _src()
        reminder = "Run 'sudo tailscale up' after bootstrap"
        assert reminder in src

    def test_clone_repos_echo_messages(self):
        """Script prints guidance about cloning repos."""
        src = _src()
        assert "Clone your repos" in src

    def test_next_steps_are_numbered(self):
        """Next steps in completion message are numbered."""
        src = _src()
        for i in range(1, 6):
            assert f"{i}." in src, f"Missing numbered step {i} in completion message"

    def test_completion_mentions_ssh_as_terry(self):
        """Completion message mentions SSH as terry."""
        src = _src()
        assert "ssh terry@" in src

    def test_public_ip_note(self):
        """Completion message mentions public IP becomes irrelevant."""
        src = _src()
        assert "public IP" in src


class TestHeredocIntegrity:
    """Verify heredoc blocks are well-formed."""

    def test_tmux_heredoc_has_open_and_close(self):
        """The TMUX heredoc has both open and close delimiters."""
        src = _src()
        assert '<< "TMUX"' in src
        assert "TMUX'" in src

    def test_tmux_heredoc_contains_six_or_more_lines(self):
        """The tmux config heredoc has substantive content."""
        src = _src()
        # Count tmux set/bind/unbind directives
        lines = [l.strip() for l in src.splitlines() if l.strip().startswith(("set ", "bind ", "unbind "))]
        assert len(lines) >= 6

    def test_tmux_heredoc_content_between_delimiters(self):
        """All tmux config lines appear between the heredoc open and close."""
        src = _src()
        open_pos = src.index('<< "TMUX"')
        close_pos = src.index("TMUX'")
        content = src[open_pos:close_pos]
        assert "set -g prefix" in content
        assert "set -g mouse on" in content


class TestAptUsage:
    """Verify apt-get usage patterns."""

    def test_apt_get_update_before_install(self):
        """apt-get update appears before apt-get install."""
        src = _src()
        update_pos = src.index("apt-get update")
        install_pos = src.index("apt-get install")
        assert update_pos < install_pos

    def test_apt_get_upgrade_before_install(self):
        """apt-get upgrade appears before apt-get install."""
        src = _src()
        upgrade_pos = src.index("apt-get upgrade")
        install_pos = src.index("apt-get install")
        assert upgrade_pos < install_pos

    def test_no_apt_without_get(self):
        """Script uses apt-get, not bare apt (more scriptable)."""
        src = _src()
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "apt " in stripped and "apt-get" not in stripped and "apt-cache" not in stripped:
                pytest.fail(f"Line {i}: bare 'apt' instead of 'apt-get': {stripped}")


class TestSudoUsage:
    """Verify sudo usage patterns."""

    def test_sudo_u_terry_count(self):
        """There are multiple sudo -u terry blocks for user-scoped installs."""
        src = _src()
        count = src.count("sudo -u terry")
        assert count >= 5, f"Expected >= 5 sudo -u terry blocks, got {count}"

    def test_system_commands_run_as_root(self):
        """apt-get, systemctl, and user creation run as root (no sudo prefix)."""
        src = _src()
        for cmd in ["apt-get update", "adduser", "systemctl restart"]:
            pos = src.index(cmd)
            preceding = src[max(0, pos - 200):pos]
            # These commands should NOT be inside a sudo -u terry block
            # Check there's no open sudo block between the last close and this command
            lines_before = preceding.splitlines()
            in_sudo_block = False
            for line in lines_before:
                if "sudo -u terry" in line:
                    in_sudo_block = True
                if in_sudo_block and line.strip() == "'":
                    in_sudo_block = False
            assert not in_sudo_block, f"{cmd} should run as root, not inside sudo -u terry"


class TestNodeInstall:
    """Verify Node.js installation via fnm."""

    def test_fnm_install_uses_lts(self):
        """fnm install uses --lts flag."""
        assert "fnm install --lts" in _src()

    def test_fnm_path_includes_local_share(self):
        """fnm PATH includes .local/share/fnm."""
        assert ".local/share/fnm" in _src()

    def test_fnm_env_eval_in_node_block(self):
        """Node install block has eval (fnm env) after PATH setup."""
        src = _src()
        fnm_install_pos = src.index("fnm.vercel.app/install")
        block_end = src.index("fnm default lts-latest")
        block = src[fnm_install_pos:block_end]
        assert "PATH=" in block
        assert 'eval "$(fnm env)"' in block


class TestCompletionOrdering:
    """Verify the completion message sections are in correct order."""

    def test_tailscale_step_before_claude_step(self):
        """Step 2 (Tailscale) appears before step 3 (Claude Code)."""
        src = _src()
        ts_pos = src.index("tailscale up")
        # Find claude mention in next steps (after "Next steps:")
        next_steps_pos = src.index("Next steps:")
        claude_after_steps = src.index("claude", next_steps_pos)
        assert ts_pos < claude_after_steps

    def test_ssh_step_is_first(self):
        """Step 1 is SSH in as terry."""
        src = _src()
        next_steps_pos = src.index("Next steps:")
        step1_pos = src.index("1.", next_steps_pos)
        assert "SSH in as terry" in src[step1_pos:step1_pos + 60]

    def test_gh_auth_is_last_step(self):
        """Step 5 (gh auth login) is the last numbered step."""
        src = _src()
        assert "5. Set up git credentials: gh auth login" in src
