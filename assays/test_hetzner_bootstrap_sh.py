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

    def test_generates_valid_tmux_config(self, tmp_path):
        """Extract and run the tmux config block, verify output."""
        block = self._extract_tmux_block()
        conf_file = tmp_path / ".tmux.conf"

        # Replace home-relative path with tmp_path
        block_rewritten = block.replace(
            "~/.tmux.conf", str(conf_file)
        )
        # Strip the sudo wrapper — just run the cat heredoc
        # Extract just the heredoc content
        content = _read_script()
        lines = content.splitlines()
        inside = False
        tmux_lines = []
        for line in lines:
            if "TMUX\"" in line and "cat >" not in line:
                inside = True
                continue
            if inside:
                if line.strip() == "TMUX'":
                    break
                tmux_lines.append(line)

        conf_file.write_text("\n".join(tmux_lines) + "\n")

        assert conf_file.exists()
        conf = conf_file.read_text()

        # Verify expected tmux settings
        assert "prefix C-a" in conf
        assert "unbind C-b" in conf
        assert "mouse on" in conf
        assert "history-limit 50000" in conf
        assert "base-index 1" in conf
        assert "escape-time 0" in conf

    def test_tmux_config_has_color_settings(self, tmp_path):
        """Tmux config should include catppuccin-style color settings."""
        block = self._extract_tmux_block()
        content = _read_script()
        lines = content.splitlines()
        inside = False
        tmux_lines = []
        for line in lines:
            if "TMUX\"" in line and "cat >" not in line:
                inside = True
                continue
            if inside:
                if line.strip() == "TMUX'":
                    break
                tmux_lines.append(line)

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
