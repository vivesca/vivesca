from __future__ import annotations

"""Tests for effectors/hetzner-bootstrap.sh — bash provisioning script.

Since the script requires root and runs system commands (apt-get, adduser, etc.),
tests operate by:
  1. Validating script structure (shebang, error flags, section markers).
  2. Extracting individual blocks and running them via subprocess with
     mocked commands via PATH overrides.
  3. Verifying file-generation logic (tmux config, SSH hardening sed).
"""

import os
import stat
import subprocess
import textwrap
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

    def test_has_all_numbered_sections(self):
        """All 10 numbered sections must be present."""
        content = _read_script()
        for n in range(1, 11):
            assert f"# {n}." in content, f"Section {n} header missing"

    def test_has_bootstrap_banner(self):
        content = _read_script()
        assert "=== Hetzner Claude Code Bootstrap ===" in content

    def test_has_completion_banner(self):
        content = _read_script()
        assert "=== Bootstrap Complete ===" in content

    def test_has_next_steps(self):
        content = _read_script()
        assert "Next steps:" in content

    def test_mentions_usage_comment(self):
        content = _read_script()
        assert "ssh root@<IP>" in content


# ── User creation block ─────────────────────────────────────────────────


class TestUserCreation:
    """Test the 'terry' user creation block in isolation."""

    def _extract_user_block(self) -> str:
        """Extract the if/fi block for user creation."""
        content = _read_script()
        lines = content.splitlines()
        start = end = None
        for i, line in enumerate(lines):
            if "if ! id terry" in line:
                start = i
            if start is not None and line.strip() == "fi":
                end = i
                break
        assert start is not None, "Could not find user creation block"
        assert end is not None, "Could not find closing fi"
        return "\n".join(lines[start : end + 1])

    def test_skips_when_user_exists(self, tmp_path):
        """If 'id terry' succeeds (user exists), no adduser should run."""
        block = self._extract_user_block()

        # Create a fake 'id' that succeeds, and a fake 'adduser' that fails loudly
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        (bin_dir / "id").write_text("#!/bin/bash\nexit 0\n")
        (bin_dir / "id").chmod(0o755)

        (bin_dir / "adduser").write_text("#!/bin/bash\necho 'ADDUSER_WAS_CALLED' >&2\nexit 1\n")
        (bin_dir / "adduser").chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

        r = subprocess.run(
            ["bash", "-c", block],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert r.returncode == 0
        assert "ADDUSER_WAS_CALLED" not in r.stderr

    def test_creates_user_when_missing(self, tmp_path):
        """If 'id terry' fails, adduser/usermod/etc. should be called."""
        block = self._extract_user_block()

        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        fake_root = tmp_path / "fakeroot"
        fake_root.mkdir()

        # id terry → fails (user doesn't exist)
        (bin_dir / "id").write_text("#!/bin/bash\nexit 1\n")
        (bin_dir / "id").chmod(0o755)

        # Record which commands were called
        log = tmp_path / "calls.log"

        for cmd in ["adduser", "usermod", "chown", "chmod", "cp", "mkdir"]:
            (bin_dir / cmd).write_text(
                f'#!/bin/bash\necho "{cmd} $@" >> {log}\n'
            )
            (bin_dir / cmd).chmod(0o755)

        # Create fake authorized_keys
        ssh_dir = fake_root / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "authorized_keys").write_text("ssh-rsa FAKEKEY")

        # Rewrite paths in the block to use our fake root
        block_rewritten = block.replace("/root/.ssh", str(ssh_dir.parent))
        block_rewritten = block_rewritten.replace("/home/terry/.ssh", str(tmp_path / "home" / "terry" / ".ssh"))
        block_rewritten = block_rewritten.replace("/etc/sudoers.d/terry", str(tmp_path / "sudoers.d" / "terry"))

        # Create target dirs
        (tmp_path / "home" / "terry" / ".ssh").mkdir(parents=True)
        (tmp_path / "sudoers.d").mkdir(parents=True)

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

        r = subprocess.run(
            ["bash", "-c", block_rewritten],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert r.returncode == 0
        calls = log.read_text()
        assert "adduser" in calls
        assert "usermod" in calls


# ── SSH hardening sed commands ──────────────────────────────────────────


class TestSSSHardening:
    """Test the sed commands used to harden sshd_config."""

    def _extract_sed_lines(self) -> list[str]:
        content = _read_script()
        lines = content.splitlines()
        sed_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("sed -i") and "sshd_config" in stripped:
                sed_lines.append(stripped)
        return sed_lines

    def test_disables_password_auth(self, tmp_path):
        """sed should change PasswordAuthentication to no."""
        sshd = tmp_path / "sshd_config"
        sshd.write_text("#PasswordAuthentication yes\n")
        sed_lines = self._extract_sed_lines()

        for sed_cmd in sed_lines:
            cmd = sed_cmd.replace("/etc/ssh/sshd_config", str(sshd))
            subprocess.run(["bash", "-c", cmd], timeout=10)

        content = sshd.read_text()
        assert "PasswordAuthentication no" in content

    def test_disables_root_login(self, tmp_path):
        """sed should change PermitRootLogin to no."""
        sshd = tmp_path / "sshd_config"
        sshd.write_text("PermitRootLogin yes\n")
        sed_lines = self._extract_sed_lines()

        for sed_cmd in sed_lines:
            cmd = sed_cmd.replace("/etc/ssh/sshd_config", str(sshd))
            subprocess.run(["bash", "-c", cmd], timeout=10)

        content = sshd.read_text()
        assert "PermitRootLogin no" in content

    def test_idempotent(self, tmp_path):
        """Running sed twice should produce same result."""
        sshd = tmp_path / "sshd_config"
        sshd.write_text("#PasswordAuthentication yes\nPermitRootLogin yes\n")
        sed_lines = self._extract_sed_lines()

        for _ in range(2):
            for sed_cmd in sed_lines:
                cmd = sed_cmd.replace("/etc/ssh/sshd_config", str(sshd))
                subprocess.run(["bash", "-c", cmd], timeout=10)

        content = sshd.read_text()
        assert "PasswordAuthentication no" in content
        assert "PermitRootLogin no" in content
        # No duplicate lines
        lines = [l for l in content.splitlines() if l.strip()]
        assert len(lines) == 2


# ── Tmux config generation ─────────────────────────────────────────────


class TestTmuxConfig:
    """Test the tmux config heredoc block."""

    def _extract_tmux_block(self) -> str:
        """Extract the sudo -u terry tmux heredoc block."""
        content = _read_script()
        lines = content.splitlines()
        start = end = None
        for i, line in enumerate(lines):
            if "cat > ~/.tmux.conf" in line:
                start = i
            if start is not None and "TMUX'" in line:
                end = i
                break
        assert start is not None, "Could not find tmux config block"
        assert end is not None, "Could not find TMUX heredoc end"
        return "\n".join(lines[start : end + 1])

    def _extract_tmux_config_lines(self) -> list[str]:
        """Extract just the tmux config directives from the heredoc."""
        content = _read_script()
        lines = content.splitlines()
        inside = False
        tmux_lines = []
        for line in lines:
            if '<< "TMUX"' in line or "<<\"TMUX\"" in line:
                inside = True
                continue
            if inside:
                if line.strip() == "TMUX'":
                    break
                tmux_lines.append(line)
        return tmux_lines

    def test_generates_valid_tmux_config(self, tmp_path):
        """Extract and run the tmux config block, verify output."""
        tmux_lines = self._extract_tmux_config_lines()
        assert len(tmux_lines) > 0, "No tmux config lines extracted"

        conf_file = tmp_path / ".tmux.conf"
        conf_file.write_text("\n".join(tmux_lines) + "\n")

        conf = conf_file.read_text()
        # Verify expected tmux settings
        assert "prefix C-a" in conf
        assert "unbind C-b" in conf
        assert "mouse on" in conf
        assert "history-limit 50000" in conf
        assert "base-index 1" in conf
        assert "escape-time 0" in conf

    def test_tmux_config_has_color_settings(self):
        """Tmux config should include catppuccin-style color settings."""
        tmux_lines = self._extract_tmux_config_lines()
        conf = "\n".join(tmux_lines)
        assert "status-style" in conf
        assert "1e1e2e" in conf  # catppuccin mocha bg


# ── Directory creation block ────────────────────────────────────────────


class TestDirectoryCreation:
    """Test the directory creation block."""

    def test_creates_expected_dirs(self, tmp_path):
        """All expected directories should be created."""
        content = _read_script()
        lines = content.splitlines()
        # Find the mkdir -p line
        mkdir_line = None
        for line in lines:
            if "mkdir -p" in line and "code" in line:
                mkdir_line = line.strip()
                break
        assert mkdir_line is not None

        # Extract the path list from the mkdir command
        # The line looks like: mkdir -p ~/code ~/scripts ~/code/epigenome/chromatin ~/skills
        # Run with HOME=tmp_path
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        subprocess.run(
            ["bash", "-c", mkdir_line.replace("mkdir -p", "mkdir -p")],
            capture_output=True, text=True, env=env, timeout=10,
        )

        expected = [
            tmp_path / "code",
            tmp_path / "scripts",
            tmp_path / "code" / "epigenome" / "chromatin",
            tmp_path / "skills",
        ]
        for d in expected:
            assert d.is_dir(), f"Expected directory {d} was not created"


# ── Output messages ────────────────────────────────────────────────────


class TestOutputMessages:
    """Verify the script contains expected informational output."""

    def test_tailscale_message(self):
        content = _read_script()
        assert "tailscale up" in content

    def test_next_steps_mention_ssh(self):
        content = _read_script()
        assert "ssh terry" in content

    def test_next_steps_mention_claude(self):
        content = _read_script()
        assert "claude" in content.lower()

    def test_next_steps_mention_git(self):
        content = _read_script()
        assert "gh auth login" in content

    def test_mentions_tailscale_hostname(self):
        content = _read_script()
        assert "tailscale-hostname" in content

    def test_clone_repo_suggestions(self):
        content = _read_script()
        assert "agent-config" in content
        assert "skills" in content
        assert "chromatin" in content


# ── Package installation ───────────────────────────────────────────────


class TestPackageInstallation:
    """Verify the script installs expected packages."""

    def test_installs_essential_packages(self):
        content = _read_script()
        essential = ["curl", "git", "tmux", "htop", "jq", "unzip", "build-essential"]
        apt_line = None
        for line in content.splitlines():
            if "apt-get install" in line:
                apt_line = line
                break
        assert apt_line is not None
        for pkg in essential:
            assert pkg in apt_line, f"Package '{pkg}' not found in apt-get install line"

    def test_runs_apt_update_before_install(self):
        """apt-get update should precede apt-get install."""
        content = _read_script()
        lines = content.splitlines()
        update_line = install_line = None
        for i, line in enumerate(lines):
            if "apt-get update" in line:
                update_line = i
            if "apt-get install" in line and install_line is None:
                install_line = i
        assert update_line is not None, "apt-get update not found"
        assert install_line is not None, "apt-get install not found"
        assert update_line < install_line, "apt-get update should precede install"


# ── Node.js installation ──────────────────────────────────────────────


class TestNodeInstall:
    """Verify fnm/Node.js installation approach."""

    def test_uses_fnm(self):
        content = _read_script()
        assert "fnm" in content
        assert "fnm.vercel.app" in content

    def test_installs_lts(self):
        content = _read_script()
        assert "fnm install --lts" in content

    def test_sets_default(self):
        content = _read_script()
        assert "fnm default lts-latest" in content


# ── Claude Code installation ──────────────────────────────────────────


class TestClaudeCodeInstall:
    """Verify Claude Code installation."""

    def test_installs_claude_code_globally(self):
        content = _read_script()
        assert "npm install -g @anthropic-ai/claude-code" in content


# ── uv installation ────────────────────────────────────────────────────


class TestUvInstall:
    """Verify uv (Python) installation."""

    def test_installs_uv_via_official_installer(self):
        content = _read_script()
        assert "astral.sh/uv/install.sh" in content


# ── Tailscale installation ─────────────────────────────────────────────


class TestTailscaleInstall:
    """Verify Tailscale installation."""

    def test_uses_official_install_script(self):
        content = _read_script()
        assert "tailscale.com/install.sh" in content


# ── Script runs with bash (not sh) ────────────────────────────────────


class TestScriptInvocation:
    """Verify the script is meant to be run with bash."""

    def test_shebang_is_bash(self):
        lines = _read_script().splitlines()
        assert lines[0].startswith("#!/bin/bash")

    def test_usage_comment_mentions_bash(self):
        content = _read_script()
        assert "bash -s" in content

    def test_pipe_safe(self):
        """Script should be pipeable (ssh root@ip 'bash -s' < script)."""
        # This just verifies the usage comment is present
        content = _read_script()
        assert "'bash -s'" in content or "bash -s" in content


# ── Security checks ───────────────────────────────────────────────────


class TestSecurity:
    """Verify security-related aspects of the bootstrap."""

    def test_sudoers_nopasswd(self):
        """terry should get NOPASSWD sudo."""
        content = _read_script()
        assert "NOPASSWD:ALL" in content

    def test_ssh_key_permissions(self):
        """SSH keys should have restrictive permissions (700 dir, 600 key)."""
        content = _read_script()
        assert "chmod 700" in content
        assert "chmod 600" in content

    def test_ssh_dir_ownership(self):
        """SSH directory should be owned by terry."""
        content = _read_script()
        assert "chown -R terry:terry" in content

    def test_password_auth_disabled(self):
        """SSH password authentication should be disabled."""
        content = _read_script()
        assert "PasswordAuthentication no" in content

    def test_root_login_disabled(self):
        """SSH root login should be disabled."""
        content = _read_script()
        assert "PermitRootLogin no" in content

    def test_user_is_disabled_password(self):
        """User should be created with disabled password."""
        content = _read_script()
        assert "--disabled-password" in content


# ── pnpm installation ─────────────────────────────────────────────────


class TestPnpmInstall:
    """Verify pnpm installation."""

    def test_installs_pnpm_globally(self):
        content = _read_script()
        assert "npm install -g pnpm" in content


# ── Full script dry-run (syntax check) ────────────────────────────────


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


# ── Heredoc execution tests ────────────────────────────────────────────


class TestHeredocExecution:
    """Run extracted heredoc blocks through bash and verify output."""

    def test_tmux_heredoc_produces_exact_config(self, tmp_path):
        """Execute the tmux heredoc block through bash and verify output file."""
        content = _read_script()
        lines = content.splitlines()
        # Find the sudo -u terry line with cat > ~/.tmux.conf
        heredoc_start = None
        for i, line in enumerate(lines):
            if "cat > ~/.tmux.conf" in line:
                heredoc_start = i
                break
        assert heredoc_start is not None

        # Build a standalone script: extract from cat line through TMUX'
        script_lines = []
        for line in lines[heredoc_start:]:
            script_lines.append(line)
            if line.strip() == "TMUX'":
                break

        # Replace ~ with tmp_path for the output
        conf_file = tmp_path / ".tmux.conf"
        block = "\n".join(script_lines)
        block = block.replace("~/.tmux.conf", str(conf_file))
        # Strip the sudo wrapper — just the cat heredoc
        # The line looks like: sudo -u terry bash -c 'cat > ... << "TMUX"
        # Replace with just the cat command
        block = block.replace("sudo -u terry bash -c '", "")

        result = subprocess.run(
            ["bash", "-c", block],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"tmux heredoc failed: {result.stderr}"
        assert conf_file.exists()
        conf = conf_file.read_text()
        # 9 config directives expected
        assert conf.count("set -g") >= 5
        assert conf.count("unbind") >= 1
        assert conf.count("bind") >= 1

    def test_echo_messages_render_correctly(self):
        """Extract pure echo statements and verify they render without error."""
        content = _read_script()
        echo_lines = [
            line.strip() for line in content.splitlines()
            if line.strip().startswith("echo ")
            and ">>>" not in line
            and ">" not in line.strip().replace(">>>", "")
        ]
        assert len(echo_lines) > 0
        for echo_line in echo_lines:
            result = subprocess.run(
                ["bash", "-c", echo_line],
                capture_output=True, text=True, timeout=5,
            )
            assert result.returncode == 0, f"Bad echo: {echo_line}"


# ── URL safety tests ──────────────────────────────────────────────────


class TestURLSafety:
    """Verify all external URLs use HTTPS."""

    def test_all_curl_urls_are_https(self):
        """Every curl invocation should use https, not http."""
        content = _read_script()
        for line in content.splitlines():
            if "curl" in line and "http://" in line:
                # http:// is acceptable only if it redirects; verify no plain http URLs
                assert False, f"Found http:// in curl line: {line.strip()}"

    def test_known_download_urls_present(self):
        """All expected download URLs are present."""
        content = _read_script()
        expected_urls = [
            "fnm.vercel.app/install",
            "tailscale.com/install.sh",
            "astral.sh/uv/install.sh",
        ]
        for url in expected_urls:
            assert url in content, f"Expected URL not found: {url}"

    def test_claude_code_package_is_official(self):
        """Claude Code package should be the official @anthropic-ai scope."""
        content = _read_script()
        assert "@anthropic-ai/claude-code" in content


# ── User block internal ordering ───────────────────────────────────────


class TestUserBlockOrdering:
    """Verify steps within the user creation block are in correct order."""

    def _extract_user_block(self) -> str:
        content = _read_script()
        lines = content.splitlines()
        start = end = None
        for i, line in enumerate(lines):
            if "if ! id terry" in line:
                start = i
            if start is not None and line.strip() == "fi":
                end = i
                break
        assert start is not None
        assert end is not None
        return "\n".join(lines[start : end + 1])

    def test_adduser_before_usermod(self):
        block = self._extract_user_block()
        assert block.index("adduser") < block.index("usermod")

    def test_adduser_before_sudoers(self):
        block = self._extract_user_block()
        assert block.index("adduser") < block.index("sudoers.d")

    def test_mkdir_before_cp(self):
        """mkdir for .ssh should come before cp of authorized_keys."""
        block = self._extract_user_block()
        assert block.index("mkdir") < block.index("cp ")

    def test_cp_before_chown(self):
        """cp authorized_keys should come before chown."""
        block = self._extract_user_block()
        assert block.index("cp ") < block.index("chown")

    def test_chown_before_chmod(self):
        """chown should come before chmod."""
        block = self._extract_user_block()
        assert block.index("chown") < block.index("chmod")


# ── SSH hardening edge cases ───────────────────────────────────────────


class TestSSSHardeningEdgeCases:
    """Additional SSH hardening tests for edge cases."""

    def _extract_sed_lines(self) -> list[str]:
        content = _read_script()
        return [
            line.strip() for line in content.splitlines()
            if line.strip().startswith("sed -i") and "sshd_config" in line
        ]

    def test_does_not_corrupt_other_lines(self, tmp_path):
        """sed should not modify unrelated sshd_config lines."""
        sshd = tmp_path / "sshd_config"
        sshd.write_text(
            "#Port 22\n"
            "#PasswordAuthentication yes\n"
            "PermitRootLogin yes\n"
            "X11Forwarding yes\n"
        )
        for sed_cmd in self._extract_sed_lines():
            cmd = sed_cmd.replace("/etc/ssh/sshd_config", str(sshd))
            subprocess.run(["bash", "-c", cmd], timeout=10)
        content = sshd.read_text()
        # Unrelated lines should be preserved
        assert "#Port 22" in content
        assert "X11Forwarding yes" in content

    def test_handles_already_hardened_config(self, tmp_path):
        """sed should not break an already-hardened sshd_config."""
        sshd = tmp_path / "sshd_config"
        sshd.write_text(
            "PasswordAuthentication no\n"
            "PermitRootLogin no\n"
        )
        for sed_cmd in self._extract_sed_lines():
            cmd = sed_cmd.replace("/etc/ssh/sshd_config", str(sshd))
            subprocess.run(["bash", "-c", cmd], timeout=10)
        content = sshd.read_text()
        assert "PasswordAuthentication no" in content
        assert "PermitRootLogin no" in content
        # No duplicate lines
        lines = [l for l in content.splitlines() if l.strip()]
        assert len(lines) == 2


# ── fnm eval pattern test ──────────────────────────────────────────────


class TestFnmEvalPattern:
    """Verify the fnm eval pattern is correct bash."""

    def test_fnm_eval_pattern_is_valid_bash(self):
        """The fnm setup pattern (export PATH + eval) is valid bash syntax."""
        pattern = textwrap.dedent("""\
            export PATH="$HOME/.local/share/fnm:$PATH"
            eval "$(fnm env)"
        """)
        result = subprocess.run(
            ["bash", "-n", "-c", pattern],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0, f"fnm pattern syntax error: {result.stderr}"

    def test_fnm_path_expansion(self):
        """$HOME/.local/share/fnm expands correctly."""
        result = subprocess.run(
            ["bash", "-c", 'echo "$HOME/.local/share/fnm"'],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0
        assert "/.local/share/fnm" in result.stdout


# ── Tmux config completeness ──────────────────────────────────────────


class TestTmuxConfigCompleteness:
    """Verify the tmux config has all expected directives."""

    def _extract_config(self) -> str:
        content = _read_script()
        lines = content.splitlines()
        inside = False
        tmux_lines = []
        for line in lines:
            if '<< "TMUX"' in line or "<<\"TMUX\"" in line:
                inside = True
                continue
            if inside:
                if line.strip() == "TMUX'":
                    break
                tmux_lines.append(line)
        return "\n".join(tmux_lines)

    def test_has_default_terminal(self):
        conf = self._extract_config()
        assert "default-terminal" in conf
        assert "screen-256color" in conf

    def test_has_terminal_overrides(self):
        conf = self._extract_config()
        assert "terminal-overrides" in conf
        assert "xterm-256color:Tc" in conf

    def test_has_send_prefix_bind(self):
        conf = self._extract_config()
        assert "send-prefix" in conf
        assert "bind C-a" in conf

    def test_no_duplicate_settings(self):
        """Each tmux directive should appear exactly once."""
        conf = self._extract_config()
        directives = [l.strip() for l in conf.splitlines() if l.strip()]
        assert len(directives) == len(set(directives)), \
            f"Duplicate tmux directives found: {directives}"


# ── Script integrity ──────────────────────────────────────────────────


class TestScriptIntegrity:
    """Verify the script has no obvious issues."""

    def test_no_hardcoded_ip_addresses(self):
        """Script should not contain hardcoded IP addresses."""
        content = _read_script()
        import re
        # Look for IPv4 patterns (but not in comments or <IP> placeholders)
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Skip <IP> placeholders
            if "<IP>" in stripped:
                continue
            ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', stripped)
            assert not ips, f"Hardcoded IP found: {ips} in: {stripped}"

    def test_no_todo_or_fixme(self):
        """Script should not contain TODO or FIXME markers."""
        content = _read_script()
        for line in content.splitlines():
            upper = line.upper()
            assert "TODO" not in upper, f"Found TODO: {line.strip()}"
            assert "FIXME" not in upper, f"Found FIXME: {line.strip()}"

    def test_all_numbered_comments_are_sequential(self):
        """Numbered section comments go 1–10 without gaps."""
        content = _read_script()
        import re
        section_nums = []
        for line in content.splitlines():
            m = re.match(r'^# (\d+)\.', line.strip())
            if m:
                section_nums.append(int(m.group(1)))
        assert section_nums == list(range(1, 11)), \
            f"Sections not sequential 1-10: {section_nums}"

    def test_script_ends_with_newline(self):
        """Script should end with a trailing newline."""
        content = _read_script()
        assert content.endswith("\n"), "Script should end with a newline"
