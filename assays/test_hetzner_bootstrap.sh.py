from __future__ import annotations

"""Tests for effectors/hetzner-bootstrap.sh — bash bootstrap script tested via subprocess and source analysis."""

import re
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "hetzner-bootstrap.sh"


def _src() -> str:
    return SCRIPT.read_text()


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


# ── Script structure ───────────────────────────────────────────────────


class TestScriptStructure:
    def test_exists(self):
        assert SCRIPT.exists()

    def test_executable(self):
        assert SCRIPT.stat().st_mode & 0o111

    def test_shebang(self):
        assert _src().splitlines()[0] == "#!/usr/bin/env bash"

    def test_set_strict(self):
        assert "set -euo pipefail" in _src()

    def test_set_strict_is_first_command(self):
        for line in _src().splitlines()[1:]:
            s = line.strip()
            if s and not s.startswith("#"):
                assert "set -euo pipefail" in s
                break

    def test_unix_line_endings(self):
        assert b"\r\n" not in SCRIPT.read_bytes()

    def test_ends_with_newline(self):
        assert _src().endswith("\n")


# ── --help flag ────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_zero(self):
        assert _run("--help").returncode == 0

    def test_h_short_zero(self):
        assert _run("-h").returncode == 0

    def test_help_stdout_contains_usage(self):
        assert "Usage:" in _run("--help").stdout

    def test_help_no_stderr(self):
        assert _run("--help").stderr == ""

    def test_help_mentions_hetzner(self):
        assert "Hetzner" in _run("--help").stdout

    def test_help_mentions_ubuntu(self):
        assert "Ubuntu" in _run("--help").stdout

    def test_help_mentions_root(self):
        assert "root" in _run("--help").stdout.lower()

    def test_help_mentions_claude_code(self):
        assert "Claude Code" in _run("--help").stdout

    def test_help_mentions_install_targets(self):
        out = _run("--help").stdout
        for target in ("Node.js", "Tailscale", "pnpm", "uv"):
            assert target in out

    def test_help_shows_ssh_pattern(self):
        assert "bash -s" in _run("--help").stdout

    def test_help_shows_ssh_root(self):
        assert "ssh root@" in _run("--help").stdout

    def test_help_mentions_terry(self):
        assert "terry" in _run("--help").stdout


# ── Permission / root check ───────────────────────────────────────────


class TestRootCheck:
    def test_nonroot_exits_1(self):
        r = _run()
        assert r.returncode == 1

    def test_nonroot_stderr_has_error(self):
        assert "ERROR: This script must be run as root" in _run().stderr

    def test_nonroot_no_banner(self):
        assert "=== Hetzner Claude Code Bootstrap ===" not in _run().stdout

    def test_euid_guard_before_banner(self):
        src = _src()
        assert src.index("EUID") < src.index("=== Hetzner Claude Code Bootstrap ===")

    def test_error_to_stderr(self):
        src = _src()
        assert ">&2" in src
        assert "ERROR: This script must be run as root" in src


# ── Bootstrap section ordering ────────────────────────────────────────


class TestSectionOrder:
    _SECTIONS = [
        ("sys_update", "apt-get update"),
        ("sys_upgrade", "apt-get upgrade"),
        ("sys_install", "apt-get install -y"),
        ("create_user", "adduser"),
        ("nopasswd", "NOPASSWD"),
        ("ssh_copy", "authorized_keys"),
        ("node_install", "fnm install --lts"),
        ("claude_install", "@anthropic-ai/claude-code"),
        ("tailscale", "tailscale.com/install.sh"),
        ("pnpm", "npm install -g pnpm"),
        ("uv", "astral.sh/uv/install.sh"),
        ("tmux", ".tmux.conf"),
        ("dirs", "mkdir -p ~/code"),
        ("ssh_harden_pw", "PasswordAuthentication no"),
        ("ssh_harden_root", "PermitRootLogin no"),
        ("restart_sshd", "systemctl restart sshd"),
    ]

    def _positions(self) -> dict[str, int]:
        src = _src()
        return {name: src.index(marker) for name, marker in self._SECTIONS}

    def test_all_sections_present(self):
        src = _src()
        for name, marker in self._SECTIONS:
            assert marker in src, f"Missing: {marker} ({name})"

    @pytest.mark.parametrize(
        "before,after",
        [
            ("sys_update", "sys_install"),
            ("create_user", "node_install"),
            ("node_install", "claude_install"),
            ("claude_install", "tailscale"),
            ("tailscale", "pnpm"),
            ("pnpm", "uv"),
            ("uv", "tmux"),
            ("tmux", "dirs"),
            ("dirs", "ssh_harden_pw"),
            ("ssh_harden_pw", "restart_sshd"),
        ],
    )
    def test_section_order(self, before, after):
        p = self._positions()
        assert p[before] < p[after], f"{before} should precede {after}"


# ── User creation ─────────────────────────────────────────────────────


class TestUserCreation:
    def test_adduser_terry(self):
        assert 'adduser --disabled-password --gecos "" terry' in _src()

    def test_sudo_group(self):
        assert "usermod -aG sudo terry" in _src()

    def test_nopasswd(self):
        assert 'echo "terry ALL=(ALL) NOPASSWD:ALL"' in _src()

    def test_sudoers_path(self):
        assert "/etc/sudoers.d/terry" in _src()

    def test_idempotent_user_check(self):
        assert "if ! id terry &>/dev/null; then" in _src()

    def test_ssh_copy_from_root(self):
        src = _src()
        assert "/root/.ssh/authorized_keys" in src
        assert "~terry/.ssh" in src

    def test_ssh_dir_permissions(self):
        src = _src()
        assert "chmod 700 ~terry/.ssh" in src
        assert "chmod 600 ~terry/.ssh/authorized_keys" in src

    def test_chown_ssh_dir(self):
        assert "chown -R terry:terry ~terry/.ssh" in _src()

    def test_ssh_copy_inside_user_if_block(self):
        src = _src()
        if_pos = src.index("if ! id terry")
        adduser_pos = src.index("adduser")
        ssh_pos = src.index("authorized_keys", adduser_pos)
        fi_pos = src.index("fi", ssh_pos)
        assert if_pos < adduser_pos < ssh_pos < fi_pos


# ── Package installation ──────────────────────────────────────────────


class TestPackages:
    def test_essential_packages(self):
        src = _src()
        for pkg in ("curl", "git", "tmux", "htop", "jq", "unzip", "build-essential"):
            assert pkg in src, f"Missing: {pkg}"

    def test_fnm_for_node(self):
        src = _src()
        assert "fnm.vercel.app/install" in src
        assert "fnm install --lts" in src
        assert "fnm default lts-latest" in src

    def test_claude_code_global(self):
        assert "npm install -g @anthropic-ai/claude-code" in _src()

    def test_uv_astral(self):
        assert "astral.sh/uv/install.sh" in _src()

    def test_pnpm_global(self):
        assert "npm install -g pnpm" in _src()

    def test_apt_y_flag(self):
        for line in _src().splitlines():
            if "apt-get install" in line or "apt-get upgrade" in line:
                assert " -y" in line, f"Missing -y: {line.strip()}"

    def test_apt_get_not_apt(self):
        for line in _src().splitlines():
            s = line.strip()
            if s.startswith("#"):
                continue
            if "apt " in s and "apt-get" not in s and "apt-cache" not in s:
                pytest.fail(f"Bare 'apt': {s}")


# ── tmux config ───────────────────────────────────────────────────────


class TestTmux:
    _LINES = [
        "set -g prefix C-a",
        "unbind C-b",
        "bind C-a send-prefix",
        "set -g mouse on",
        "set -g history-limit 50000",
        'set -g default-terminal "screen-256color"',
        ",xterm-256color:Tc",
        "set -g base-index 1",
        "set -g escape-time 0",
        "set -g status-style",
    ]

    @pytest.mark.parametrize("line", _LINES)
    def test_config_line(self, line):
        assert line in _src()

    def test_heredoc_quoted_delimiter(self):
        src = _src()
        assert '<< "TMUX"' in src or "<<'TMUX'" in src

    def test_heredoc_closes(self):
        assert "TMUX'" in _src()

    def test_heredoc_content_between_delimiters(self):
        src = _src()
        open_pos = src.index('<< "TMUX"')
        close_pos = src.index("TMUX'")
        body = src[open_pos:close_pos]
        assert "set -g prefix" in body
        assert "set -g mouse on" in body

    def test_written_as_terry(self):
        src = _src()
        tmux_pos = src.index(".tmux.conf")
        assert "sudo -u terry" in src[:tmux_pos][-200:]


# ── SSH hardening ─────────────────────────────────────────────────────


class TestSSHHardening:
    def test_disable_password_auth(self):
        assert "PasswordAuthentication no" in _src()

    def test_disable_root_login(self):
        assert "PermitRootLogin no" in _src()

    def test_sed_patterns_handle_commented(self):
        src = _src()
        assert "^#\\?PasswordAuthentication" in src
        assert "^#\\?PermitRootLogin" in src

    def test_restarts_sshd(self):
        assert "systemctl restart sshd" in _src()

    def test_uses_sed(self):
        src = _src()
        assert "sed -i" in src
        assert "/etc/ssh/sshd_config" in src


# ── Directory creation ────────────────────────────────────────────────


class TestDirectoryCreation:
    def test_dirs(self):
        src = _src()
        assert "~/code" in src
        assert "~/scripts" in src
        assert "~/code/epigenome/chromatin" in src
        assert "~/skills" in src

    def test_single_mkdir(self):
        assert "mkdir -p ~/code ~/scripts ~/code/epigenome/chromatin ~/skills" in _src()

    def test_created_as_terry(self):
        src = _src()
        mkdir_pos = src.index("mkdir -p ~/code")
        assert "sudo -u terry" in src[:mkdir_pos][-200:]


# ── User execution context ───────────────────────────────────────────


class TestUserContext:
    def test_node_install_as_terry(self):
        src = _src()
        fnm_pos = src.index("fnm.vercel.app/install")
        assert "sudo -u terry" in src[:fnm_pos]

    def test_claude_install_as_terry(self):
        src = _src()
        cc_pos = src.index("@anthropic-ai/claude-code")
        assert "sudo -u terry" in src[:cc_pos]

    def test_tailscale_as_root(self):
        src = _src()
        ts_pos = src.index("tailscale.com/install.sh")
        preceding = src[:ts_pos]
        last_sudo = preceding.rfind("sudo -u terry")
        if last_sudo != -1:
            last_close = preceding.rfind("'")
            assert last_close > last_sudo

    def test_sudo_u_terry_count(self):
        assert _src().count("sudo -u terry") >= 5

    def test_no_nested_sudo(self):
        src = _src()
        lines = src.splitlines()
        in_block = False
        for i, line in enumerate(lines, 1):
            if "sudo -u terry bash -c" in line:
                in_block = True
                continue
            if in_block:
                s = line.strip()
                if s == "'":
                    in_block = False
                    continue
                assert "sudo " not in s or s.startswith("#"), f"L{i}: nested sudo: {s}"


# ── fnm subshell setup ───────────────────────────────────────────────


class TestFnmSubshells:
    def test_claude_block_has_fnm_env(self):
        src = _src()
        cc = src.index("@anthropic-ai/claude-code")
        start = src.rfind("sudo -u terry", 0, cc)
        end = src.find("\n'", cc)
        assert "fnm env" in src[start:end]

    def test_pnpm_block_has_fnm_env(self):
        src = _src()
        pnpm = src.index("npm install -g pnpm")
        start = src.rfind("sudo -u terry", 0, pnpm)
        end = src.find("\n'", pnpm)
        assert "fnm env" in src[start:end]

    def test_fnm_path_before_eval(self):
        src = _src()
        block_start = src.index("fnm.vercel.app/install")
        block_end = src.index("fnm default lts-latest") + 30
        block = src[block_start:block_end]
        assert block.index("PATH") < block.index('eval "$(fnm env)"')


# ── Completion message ───────────────────────────────────────────────


class TestCompletionMessage:
    def test_banner(self):
        assert "=== Bootstrap Complete ===" in _src()

    def test_next_steps(self):
        src = _src()
        assert "Next steps:" in src
        assert "SSH in as terry" in src

    def test_numbered_steps(self):
        src = _src()
        for i in range(1, 6):
            assert f"{i}." in src

    def test_step5_gh_auth(self):
        assert "5. Set up git credentials: gh auth login" in _src()

    def test_tailscale_up_mentioned(self):
        assert "tailscale up" in _src()

    def test_tailscale_hostname(self):
        assert "tailscale-hostname" in _src()

    def test_public_ip_note(self):
        assert "public IP" in _src()

    def test_ssh_terry_in_completion(self):
        assert "ssh terry@" in _src()

    def test_completion_after_all_ops(self):
        src = _src()
        assert src.index("systemctl restart sshd") < src.index("=== Bootstrap Complete ===")


# ── Security & hygiene ────────────────────────────────────────────────


class TestSecurity:
    def test_no_hardcoded_passwords(self):
        src = _src()
        for pat in ("password=", "PASSWORD=", "passwd="):
            assert pat not in src

    def test_no_todo_fixme(self):
        src = _src()
        for m in ("TODO", "FIXME"):
            assert m not in src

    def test_all_curl_has_fail_flag(self):
        for i, line in enumerate(_src().splitlines(), 1):
            if re.search(r"(?:^|\|)\s*curl\b", line.strip()):
                assert "-f" in line or "-LsSf" in line, f"L{i}: {line.strip()}"

    def test_all_urls_https(self):
        for i, line in enumerate(_src().splitlines(), 1):
            s = line.strip()
            if "http://" in s and "localhost" not in s and "127.0" not in s:
                assert s.startswith("#"), f"L{i}: insecure: {s}"

    def test_curl_pipe_sh_trusted_only(self):
        for i, line in enumerate(_src().splitlines(), 1):
            s = line.strip()
            if "| sh" in s or "| bash" in s:
                assert any(d in s for d in ("tailscale.com", "fnm.vercel.app", "astral.sh"))

    def test_no_interactive_commands(self):
        src = _src()
        for i, line in enumerate(src.splitlines(), 1):
            s = line.strip()
            if s.startswith("#"):
                continue
            if re.search(r"\bread\b", s) and "read -" not in s:
                assert "echo" in s or "'" in s or '"' in s, f"L{i}: interactive read: {s}"


# ── Bash syntax ───────────────────────────────────────────────────────


class TestBashSyntax:
    def test_bash_n(self):
        r = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0, f"Syntax error: {r.stderr}"


class TestShellcheck:
    def test_shellcheck(self):
        r = subprocess.run(["which", "shellcheck"], capture_output=True, text=True)
        if r.returncode != 0:
            pytest.skip("shellcheck not installed")
        r = subprocess.run(
            ["shellcheck", str(SCRIPT)],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, f"Shellcheck:\n{r.stdout}{r.stderr}"


# ── Invalid flags ─────────────────────────────────────────────────────


class TestInvalidFlags:
    def test_bogus_flag_nonzero(self):
        assert _run("--bogus").returncode != 0

    def test_no_args_nonroot_nonzero(self):
        assert _run().returncode == 1


# ── Echo messages ─────────────────────────────────────────────────────


class TestEchoMessages:
    def test_tailscale_reminder(self):
        assert "Run 'sudo tailscale up' after bootstrap" in _src()

    def test_clone_repos_echo(self):
        assert "Clone your repos" in _src()

    def test_ubuntu_22_04_referenced(self):
        assert "22.04" in _src()
