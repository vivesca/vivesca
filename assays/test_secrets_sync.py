"""Tests for effectors/secrets-sync — mocked SSH, no real network."""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load the effector via exec (it's a script, not an importable module).
_SCRIPT = Path(__file__).parent.parent / "effectors" / "secrets-sync"
_NS: dict = {"__name__": "secrets_sync"}
exec(open(_SCRIPT).read(), _NS)

parse_env_file = _NS["parse_env_file"]
ssh_key_files = _NS["ssh_key_files"]
sync_env = _NS["sync_env"]
sync_ssh_keys = _NS["sync_ssh_keys"]
sync_gitconfig = _NS["sync_gitconfig"]
main = _NS["main"]


class TestParseEnvFile:
    def test_extracts_double_quoted_values(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text('export ANTHROPIC_API_KEY="sk-ant-abc123"\n')
        result = parse_env_file(env)
        assert result == [("ANTHROPIC_API_KEY", "sk-ant-abc123")]

    def test_extracts_single_quoted_values(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text("export ZHIPU_API_KEY='zhipu-key'\n")
        result = parse_env_file(env)
        assert result == [("ZHIPU_API_KEY", "zhipu-key")]

    def test_extracts_unquoted_values(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text("export GITHUB_TOKEN=gho_token\n")
        result = parse_env_file(env)
        assert result == [("GITHUB_TOKEN", "gho_token")]

    def test_skips_blank_and_comment_lines(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text("# comment\n\nexport FOO=bar\n")
        result = parse_env_file(env)
        assert result == [("FOO", "bar")]

    def test_missing_file_returns_empty(self, tmp_path):
        result = parse_env_file(tmp_path / "nonexistent")
        assert result == []

    def test_multiple_keys(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text(textwrap.dedent("""\
            export KEY_A="val_a"
            export KEY_B="val_b"
            export KEY_C="val_c"
        """))
        result = parse_env_file(env)
        assert len(result) == 3
        assert [k for k, _ in result] == ["KEY_A", "KEY_B", "KEY_C"]


class TestSshKeyFiles:
    def test_finds_existing_keys(self, tmp_path):
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        (ssh_dir / "id_ed25519.pub").write_text("pub")
        _NS["SSH_DIR"] = ssh_dir
        keys = ssh_key_files()
        _NS["SSH_DIR"] = Path.home() / ".ssh"  # restore
        assert len(keys) == 2
        names = {k.name for k in keys}
        assert names == {"id_ed25519", "id_ed25519.pub"}

    def test_returns_empty_when_no_keys(self, tmp_path):
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        _NS["SSH_DIR"] = ssh_dir
        keys = ssh_key_files()
        _NS["SSH_DIR"] = Path.home() / ".ssh"
        assert keys == []

    def test_returns_only_existing(self, tmp_path):
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        _NS["SSH_DIR"] = ssh_dir
        keys = ssh_key_files()
        _NS["SSH_DIR"] = Path.home() / ".ssh"
        assert len(keys) == 1
        assert keys[0].name == "id_ed25519"


class TestSyncEnv:
    def test_dry_run_does_not_call_subprocess(self):
        with patch("subprocess.run") as mock_run:
            result = sync_env("user@host", [("KEY", "val")], dry_run=True)
        assert result is True
        mock_run.assert_not_called()

    def test_writes_via_ssh_stdin(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = sync_env("user@host", [("API_KEY", "secret123")], dry_run=False)
        assert result is True
        call_args = mock_run.call_args_list[0]
        cmd = call_args[0][0]
        # Secrets must go via stdin, not in command args
        assert "secret123" not in " ".join(cmd)
        # stdin (input=) should contain the secret
        stdin_input = call_args.kwargs.get("input", "")
        assert "secret123" in stdin_input

    def test_returns_false_on_error(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="connection refused")
            result = sync_env("user@host", [("K", "v")], dry_run=False)
        assert result is False

    def test_no_pairs_is_ok(self):
        with patch("subprocess.run") as mock_run:
            result = sync_env("user@host", [], dry_run=False)
        assert result is True
        mock_run.assert_not_called()


class TestSyncSshKeys:
    def test_dry_run_does_not_call_subprocess(self, tmp_path):
        key = tmp_path / "id_ed25519"
        key.write_text("key")
        with patch("subprocess.run") as mock_run:
            result = sync_ssh_keys("user@host", [key], dry_run=True)
        assert result is True
        mock_run.assert_not_called()

    def test_syncs_keys_via_scp(self, tmp_path):
        priv = tmp_path / "id_ed25519"
        priv.write_text("private-key")
        pub = tmp_path / "id_ed25519.pub"
        pub.write_text("public-key")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = sync_ssh_keys("user@host", [priv, pub], dry_run=False)
        assert result is True

        all_cmds = [c[0][0] for c in mock_run.call_args_list]
        cmd_strs = [" ".join(c) for c in all_cmds]
        # mkdir .ssh on remote
        assert any("mkdir -p ~/.ssh" in s for s in cmd_strs)
        # scp both keys
        assert any("scp" in s and "id_ed25519 " in s for s in cmd_strs)
        assert any("scp" in s and "id_ed25519.pub" in s for s in cmd_strs)
        # chmod on private key
        assert any("chmod 600" in s and "id_ed25519" in s for s in cmd_strs)

    def test_no_keys_is_ok(self):
        with patch("subprocess.run") as mock_run:
            result = sync_ssh_keys("user@host", [], dry_run=False)
        assert result is True
        mock_run.assert_not_called()


class TestSyncGitconfig:
    def test_dry_run_does_not_call_subprocess(self, tmp_path):
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\nname=T\n")
        _NS["GITCONFIG"] = gitconfig
        with patch("subprocess.run") as mock_run:
            result = sync_gitconfig("user@host", dry_run=True)
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"
        assert result is True
        mock_run.assert_not_called()

    def test_writes_gitconfig_via_ssh_stdin(self, tmp_path):
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\nname=Terry\n")
        _NS["GITCONFIG"] = gitconfig
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = sync_gitconfig("user@host", dry_run=False)
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"
        assert result is True
        call_args = mock_run.call_args_list[0]
        cmd = call_args[0][0]
        assert "cat > ~/.gitconfig" in " ".join(cmd)
        stdin_input = call_args.kwargs.get("input", "")
        assert "Terry" in stdin_input

    def test_no_gitconfig_is_ok(self, tmp_path):
        _NS["GITCONFIG"] = tmp_path / "nope"
        with patch("subprocess.run") as mock_run:
            result = sync_gitconfig("user@host", dry_run=False)
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"
        assert result is True
        mock_run.assert_not_called()


class TestMainIntegration:
    def test_dry_run_full_flow(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text('export API_KEY="secret"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        (ssh_dir / "id_ed25519.pub").write_text("pub")
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\nname=T\n")

        _NS["HOME"] = tmp_path
        _NS["ENV_FILE"] = env
        _NS["SSH_DIR"] = ssh_dir
        _NS["GITCONFIG"] = gitconfig

        with patch("subprocess.run") as mock_run:
            ret = main(["--target", "user@host", "--dry-run"])

        _NS["HOME"] = Path.home()
        _NS["ENV_FILE"] = Path.home() / ".env.fly"
        _NS["SSH_DIR"] = Path.home() / ".ssh"
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"

        assert ret == 0
        mock_run.assert_not_called()

    def test_real_flow_success(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text('export API_KEY="val"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\nname=T\n")

        _NS["HOME"] = tmp_path
        _NS["ENV_FILE"] = env
        _NS["SSH_DIR"] = ssh_dir
        _NS["GITCONFIG"] = gitconfig

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            ret = main(["--target", "user@host"])

        _NS["HOME"] = Path.home()
        _NS["ENV_FILE"] = Path.home() / ".env.fly"
        _NS["SSH_DIR"] = Path.home() / ".ssh"
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"

        assert ret == 0
        assert mock_run.call_count > 0


class TestNoSecretLeakage:
    """Verify no secret values appear in any subprocess command-line arguments."""

    def test_secret_not_in_command_args(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text('export SUPER_SECRET="leaked_value_xyz"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\nname=T\n")

        _NS["HOME"] = tmp_path
        _NS["ENV_FILE"] = env
        _NS["SSH_DIR"] = ssh_dir
        _NS["GITCONFIG"] = gitconfig

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            main(["--target", "t@h"])

        _NS["HOME"] = Path.home()
        _NS["ENV_FILE"] = Path.home() / ".env.fly"
        _NS["SSH_DIR"] = Path.home() / ".ssh"
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"

        for call_args in mock_run.call_args_list:
            cmd = call_args[0][0]
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            assert "leaked_value_xyz" not in cmd_str, f"Secret leaked in command: {cmd_str}"

    def test_secret_only_in_stdin(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text('export MY_TOKEN="token_abc_999"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\nname=T\n")

        _NS["HOME"] = tmp_path
        _NS["ENV_FILE"] = env
        _NS["SSH_DIR"] = ssh_dir
        _NS["GITCONFIG"] = gitconfig

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            main(["--target", "t@h"])

        _NS["HOME"] = Path.home()
        _NS["ENV_FILE"] = Path.home() / ".env.fly"
        _NS["SSH_DIR"] = Path.home() / ".ssh"
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"

        # Find the env-write call and verify input contains the secret
        env_call = None
        for c in mock_run.call_args_list:
            cmd = c[0][0]
            if "cat > ~/.env.fly" in " ".join(cmd):
                env_call = c
                break
        assert env_call is not None, "No env-write SSH call found"
        stdin_input = env_call.kwargs.get("input", "")
        assert "token_abc_999" in stdin_input
