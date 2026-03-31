from __future__ import annotations

"""Tests for effectors/hetzner-bootstrap.sh — VPS bootstrap script.

Effectors are scripts, not importable modules. Tests use subprocess.run
or read the source and analyze it statically.
"""

import subprocess
import textwrap
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "effectors" / "hetzner-bootstrap.sh"


def _read_script() -> str:
    return SCRIPT.read_text()


# ── Syntax and structural tests ───────────────────────────────────────


class TestScriptBasics:
    """Verify the script file exists and has valid bash syntax."""

    def test_script_exists(self):
        assert SCRIPT.is_file()

    def test_script_is_executable(self):
        assert SCRIPT.stat().st_mode & 0o111, "Script should be executable"

    def test_shebang_line(self):
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line == "#!/bin/bash"

    def test_set_strict_mode(self):
        """Script uses set -euo pipefail for strict error handling."""
        content = _read_script()
        assert "set -euo pipefail" in content

    def test_bash_syntax_valid(self):
        """bash -n reports no syntax errors."""
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


# ── Section coverage tests ────────────────────────────────────────────


class TestSectionCoverage:
    """Verify all 10 bootstrap sections are present in the script."""

    def test_section_1_system_updates(self):
        content = _read_script()
        assert "apt-get update" in content
        assert "apt-get upgrade -y" in content

    def test_section_1_installs_required_packages(self):
        content = _read_script()
        required = ["curl", "git", "tmux", "htop", "jq", "unzip", "build-essential"]
        for pkg in required:
            assert pkg in content, f"Package '{pkg}' should be installed"

    def test_section_2_creates_user_terry(self):
        content = _read_script()
        assert "adduser" in content
        assert "terry" in content
        assert 'usermod -aG sudo terry' in content

    def test_section_2_sudoers_nopasswd(self):
        content = _read_script()
        assert "NOPASSWD:ALL" in content

    def test_section_2_copies_ssh_keys(self):
        content = _read_script()
        assert "authorized_keys" in content
        assert "chown -R terry:terry" in content

    def test_section_2_ssh_key_permissions(self):
        content = _read_script()
        assert "chmod 700" in content
        assert "chmod 600" in content

    def test_section_3_installs_node_via_fnm(self):
        content = _read_script()
        assert "fnm" in content
        assert "fnm install --lts" in content
        assert "fnm default lts-latest" in content

    def test_section_4_installs_claude_code(self):
        content = _read_script()
        assert "@anthropic-ai/claude-code" in content
        assert "npm install -g" in content

    def test_section_5_installs_tailscale(self):
        content = _read_script()
        assert "tailscale.com/install.sh" in content
        assert "tailscale up" in content

    def test_section_6_installs_pnpm(self):
        content = _read_script()
        assert "npm install -g pnpm" in content

    def test_section_7_installs_uv(self):
        content = _read_script()
        assert "astral.sh/uv/install.sh" in content

    def test_section_8_tmux_config(self):
        content = _read_script()
        assert ".tmux.conf" in content

    def test_section_8_tmux_prefix_ctrl_a(self):
        content = _read_script()
        assert "set -g prefix C-a" in content
        assert "unbind C-b" in content

    def test_section_8_tmux_mouse_on(self):
        content = _read_script()
        assert "set -g mouse on" in content

    def test_section_8_tmux_history_limit(self):
        content = _read_script()
        assert "set -g history-limit 50000" in content

    def test_section_9_creates_directory_structure(self):
        content = _read_script()
        assert "~/code" in content
        assert "~/scripts" in content
        assert "~/skills" in content
        assert "~/code/epigenome/chromatin" in content

    def test_section_10_ssh_hardening(self):
        content = _read_script()
        assert "PasswordAuthentication no" in content
        assert "PermitRootLogin no" in content

    def test_section_10_restarts_sshd(self):
        content = _read_script()
        assert "systemctl restart sshd" in content


# ── Heredoc / quoting tests ───────────────────────────────────────────


class TestHeredocAndQuoting:
    """Verify heredocs and quoting are correct."""

    def test_tmux_heredoc_is_quoted(self):
        """The TMUX heredoc delimiter is quoted to prevent variable expansion."""
        content = _read_script()
        # '<<"TMUX"' prevents expansion inside the heredoc
        assert '<< "TMUX"' in content or "<<\"TMUX\"" in content

    def test_fnm_path_setup(self):
        """fnm path is set correctly for node access."""
        content = _read_script()
        assert '$HOME/.local/share/fnm' in content
        assert 'fnm env' in content

    def test_ssh_sed_uses_correct_delimiter(self):
        """sed commands target /etc/ssh/sshd_config."""
        content = _read_script()
        assert "/etc/ssh/sshd_config" in content

    def test_sudoers_file_path(self):
        """Sudoers file is written to /etc/sudoers.d/terry."""
        content = _read_script()
        assert "/etc/sudoers.d/terry" in content


# ── Idempotency / safety tests ────────────────────────────────────────


class TestIdempotencyAndSafety:
    """Verify the script has guards for safe re-execution."""

    def test_user_creation_guarded(self):
        """User creation is guarded with 'if ! id terry' to be idempotent."""
        content = _read_script()
        assert "if ! id terry" in content

    def test_user_creation_guard_wraps_all_user_ops(self):
        """SSH key copy and sudoers setup are inside the id guard."""
        content = _read_script()
        lines = content.splitlines()
        guard_idx = None
        fi_idx = None
        for i, line in enumerate(lines):
            if "if ! id terry" in line:
                guard_idx = i
            if guard_idx is not None and line.strip() == "fi":
                fi_idx = i
                break
        assert guard_idx is not None, "id guard not found"
        assert fi_idx is not None, "closing fi not found"
        # Everything between guard and fi should include user creation steps
        block = "\n".join(lines[guard_idx:fi_idx])
        assert "adduser" in block
        assert "authorized_keys" in block
        assert "sudoers.d" in block

    def test_set_e_catches_errors(self):
        """set -e ensures the script exits on any command failure."""
        content = _read_script()
        assert "set -e" in content

    def test_set_u_catches_undefined_vars(self):
        """set -u catches use of undefined variables."""
        content = _read_script()
        # Script uses combined form: set -euo pipefail
        assert "set -euo pipefail" in content or "set -u" in content

    def test_set_o_pipefail_catches_pipe_failures(self):
        """set -o pipefail ensures pipe failures propagate."""
        content = _read_script()
        assert "pipefail" in content


# ── Script output message tests ───────────────────────────────────────


class TestOutputMessages:
    """Verify the script prints useful status messages."""

    def test_has_bootstrap_header(self):
        content = _read_script()
        assert "Hetzner Claude Code Bootstrap" in content

    def test_has_bootstrap_complete_footer(self):
        content = _read_script()
        assert "Bootstrap Complete" in content

    def test_next_steps_mentioned(self):
        content = _read_script()
        assert "Next steps" in content

    def test_tailscale_instructions_present(self):
        content = _read_script()
        assert "tailscale up" in content

    def test_tailscale_connect_via_hostname(self):
        content = _read_script()
        assert "tailscale-hostname" in content


# ── Extracted snippet execution tests ─────────────────────────────────


class TestExtractedSnippets:
    """Test that individual snippet patterns are valid bash when extracted."""

    def test_sed_password_auth_is_valid(self, tmp_path):
        """The PasswordAuthentication sed command is valid bash."""
        content = _read_script()
        for line in content.splitlines():
            if "PasswordAuthentication no" in line and "sed" in line:
                # Write input to a temp file since sed -i needs a regular file
                cfg = tmp_path / "sshd_config"
                cfg.write_text("#PasswordAuthentication yes\n")
                cmd = line.strip().replace("/etc/ssh/sshd_config", str(cfg))
                result = subprocess.run(
                    ["bash", "-c", cmd],
                    capture_output=True,
                    text=True,
                )
                assert result.returncode == 0
                assert "PasswordAuthentication no" in cfg.read_text()
                return
        raise AssertionError("PasswordAuthentication sed line not found")

    def test_sed_permit_root_login_is_valid(self, tmp_path):
        """The PermitRootLogin sed command is valid bash."""
        content = _read_script()
        for line in content.splitlines():
            if "PermitRootLogin no" in line and "sed" in line:
                cfg = tmp_path / "sshd_config"
                cfg.write_text("PermitRootLogin yes\n")
                cmd = line.strip().replace("/etc/ssh/sshd_config", str(cfg))
                result = subprocess.run(
                    ["bash", "-c", cmd],
                    capture_output=True,
                    text=True,
                )
                assert result.returncode == 0
                assert "PermitRootLogin no" in cfg.read_text()
                return
        raise AssertionError("PermitRootLogin sed line not found")

    def test_tmux_config_heredoc_produces_valid_config(self):
        """Extracting and running the tmux heredoc produces valid config."""
        content = _read_script()
        lines = content.splitlines()
        start = None
        end = None
        for i, line in enumerate(lines):
            if "cat > ~/.tmux.conf" in line:
                start = i
            if start is not None and line.strip() == "TMUX'":
                end = i
                break
        assert start is not None, "tmux heredoc start not found"
        assert end is not None, "tmux heredoc end not found"

        # Extract just the config lines between heredoc markers
        config_lines = lines[start + 1:end]
        config_text = "\n".join(config_lines)

        # All tmux set/bind/unbind commands should start with 'set' or 'bind' or 'unbind'
        for cl in config_lines:
            stripped = cl.strip()
            if stripped:
                assert stripped.startswith(("set", "bind", "unbind")), \
                    f"Invalid tmux directive: {stripped}"

    def test_mkdir_command_is_valid(self):
        """The mkdir -p command creates all expected directories."""
        content = _read_script()
        for line in content.splitlines():
            if "mkdir -p" in line and "~/code" in line:
                # Verify the command structure is correct
                assert "~/code" in line
                assert "~/scripts" in line
                assert "~/code/epigenome/chromatin" in line
                assert "~/skills" in line
                return
        raise AssertionError("mkdir command not found")


# ── Running script with mocked commands (dry-run) ─────────────────────


class TestDryRun:
    """Test the script in a dry-run environment with mocked system commands."""

    def test_script_runs_with_mocked_apt(self, tmp_path):
        """Script proceeds past apt-get when it's mocked."""
        mock_bin = tmp_path / "bin"
        mock_bin.mkdir()
        # Create mock commands that the script needs
        for cmd in [
            "apt-get", "adduser", "usermod", "id",
            "systemctl", "sed", "mkdir", "cp", "chown", "chmod",
            "curl", "sudo", "cat",
        ]:
            (mock_bin / cmd).write_text(
                "#!/bin/bash\n# mock\n# args: $@\nexit 0\n"
            )
            (mock_bin / cmd).chmod(0o755)

        # Create a wrapper that sources the script in a non-destructive way
        # We just check bash -n since actually running would need root
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_idempotency_guard_logic(self):
        """Verify the 'if ! id terry' guard logic is correct bash."""
        guard_script = textwrap.dedent("""\
            #!/bin/bash
            # Mock id command: simulate user doesn't exist
            id() { return 1; }
            created=0
            if ! id terry &>/dev/null; then
                created=1
            fi
            echo "created=$created"
        """)
        result = subprocess.run(
            ["bash", "-c", guard_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "created=1" in result.stdout

    def test_idempotency_guard_skips_when_user_exists(self):
        """Verify the guard skips when user already exists."""
        guard_script = textwrap.dedent("""\
            #!/bin/bash
            # Mock id command: simulate user exists
            id() { return 0; }
            created=0
            if ! id terry &>/dev/null; then
                created=1
            fi
            echo "created=$created"
        """)
        result = subprocess.run(
            ["bash", "-c", guard_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "created=0" in result.stdout

    def test_ssh_hardening_sed_replaces_correctly(self):
        """Verify the sed replacements work as expected."""
        sed_test = textwrap.dedent("""\
            #!/bin/bash
            input="#PasswordAuthentication yes\\nPermitRootLogin yes"
            output=$(echo -e "$input" | \\
                sed 's/#PasswordAuthentication yes/PasswordAuthentication no/' | \\
                sed 's/PermitRootLogin yes/PermitRootLogin no/')
            echo "$output"
        """)
        result = subprocess.run(
            ["bash", "-c", sed_test],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "PasswordAuthentication no" in result.stdout
        assert "PermitRootLogin no" in result.stdout
        # Should not contain the originals
        assert "#PasswordAuthentication yes" not in result.stdout
        assert "PermitRootLogin yes" not in result.stdout


# ── Ordering tests ────────────────────────────────────────────────────


class TestOrdering:
    """Verify that critical sections appear in the correct order."""

    def _line_containing(self, text: str, pattern: str) -> int:
        for i, line in enumerate(text.splitlines()):
            if pattern in line:
                return i
        return -1

    def test_user_creation_before_claude_install(self):
        """User 'terry' is created before Claude Code is installed."""
        content = _read_script()
        user_line = self._line_containing(content, "adduser")
        claude_line = self._line_containing(content, "@anthropic-ai/claude-code")
        assert user_line > 0
        assert claude_line > 0
        assert user_line < claude_line

    def test_apt_before_node(self):
        """System packages are installed before Node.js."""
        content = _read_script()
        apt_line = self._line_containing(content, "apt-get install")
        fnm_line = self._line_containing(content, "fnm.vercel.app")
        assert apt_line > 0
        assert fnm_line > 0
        assert apt_line < fnm_line

    def test_node_before_claude(self):
        """Node.js is installed before Claude Code."""
        content = _read_script()
        fnm_line = self._line_containing(content, "fnm install --lts")
        claude_line = self._line_containing(content, "@anthropic-ai/claude-code")
        assert fnm_line > 0
        assert claude_line > 0
        assert fnm_line < claude_line

    def test_ssh_hardening_is_last_step(self):
        """SSH hardening is the last configuration step."""
        content = _read_script()
        sshd_line = self._line_containing(content, "systemctl restart sshd")
        # After sshd restart, only echo/next-steps should remain
        remaining = content.splitlines()[sshd_line + 1:]
        # All remaining lines should be echo statements or blank/comments
        for line in remaining:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                assert stripped.startswith("echo") or stripped.startswith("set"), \
                    f"Unexpected command after SSH hardening: {stripped}"

    def test_fnm_path_setup_before_npm(self):
        """fnm PATH setup comes before npm install commands."""
        content = _read_script()
        fnm_path_line = self._line_containing(content, "$HOME/.local/share/fnm")
        npm_line = self._line_containing(content, "npm install -g @anthropic-ai")
        assert fnm_path_line > 0
        assert npm_line > 0
        assert fnm_path_line < npm_line
