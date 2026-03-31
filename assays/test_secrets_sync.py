"""Tests for secrets-sync effector — all SSH/subprocess calls are mocked."""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


# Load the effector via exec (it's a script, not an importable module).
_SCRIPT = Path(__file__).parent.parent / "effectors" / "secrets-sync"
_NS: dict = {}
exec(open(_SCRIPT).read(), _NS)

parse_env_exports = _NS["parse_env_exports"]
find_ssh_keys = _NS["find_ssh_keys"]
read_gitconfig = _NS["read_gitconfig"]
sync = _NS["sync"]


class TestParseEnvExports:
    def test_extracts_key_value_pairs(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text(textwrap.dedent("""\
            export ANTHROPIC_API_KEY="sk-ant-abc123"
            export ZHIPU_API_KEY='zhipu-key'
            export GITHUB_TOKEN=gho_token
        """))
        result = parse_env_exports(env)
        assert len(result) == 3
        assert result[0] == ("ANTHROPIC_API_KEY", "sk-ant-abc123")
        assert result[1] == ("ZHIPU_API_KEY", "zhipu-key")
        assert result[2] == ("GITHUB_TOKEN", "gho_token")

    def test_skips_blank_and_comment_lines(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text("# comment\n\nexport FOO=bar\n")
        result = parse_env_exports(env)
        assert result == [("FOO", "bar")]

    def test_missing_file_returns_empty(self, tmp_path):
        result = parse_env_exports(tmp_path / "nonexistent")
        assert result == []

    def test_never_includes_values_in_key_names(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text('export MY_KEY="secret_value_123"\n')
        result = parse_env_exports(env)
        keys = [k for k, _ in result]
        assert "secret_value_123" not in keys
        assert "MY_KEY" in keys


class TestFindSshKeys:
    def test_finds_existing_keys(self, tmp_path):
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        (ssh_dir / "id_ed25519.pub").write_text("pub")
        with patch.object(_NS["__builtins__"] if isinstance(_NS["__builtins__"], dict) else type(_NS), "__dict__", {}):
            # Patch HOME so it finds our tmp keys
            with patch(_NS["__name__"] + ".HOME", tmp_path):
                keys = find_ssh_keys()
        assert len(keys) == 2
        names = {k.name for k in keys}
        assert names == {"id_ed25519", "id_ed25519.pub"}

    def test_returns_empty_when_no_keys(self, tmp_path):
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        with patch(_NS["__name__"] + ".HOME", tmp_path):
            keys = find_ssh_keys()
        assert keys == []


class TestReadGitconfig:
    def test_reads_existing(self, tmp_path):
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\n  name = Terry\n")
        with patch(_NS["__name__"] + ".GITCONFIG", gitconfig):
            content = read_gitconfig()
        assert "Terry" in content

    def test_returns_none_when_missing(self, tmp_path):
        with patch(_NS["__name__"] + ".GITCONFIG", tmp_path / "nope"):
            assert read_gitconfig() is None


class TestSyncDryRun:
    """Dry-run should never call subprocess.run with real commands."""

    def test_dry_run_does_not_call_subprocess(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text('export FOO_KEY="val"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("keydata")
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\nname=T\n")

        with (
            patch(_NS["__name__"] + ".HOME", tmp_path),
            patch(_NS["__name__"] + ".ENV_FILE", env),
            patch(_NS["__name__"] + ".GITCONFIG", gitconfig),
            patch("subprocess.run") as mock_run,
        ):
            sync("user@target", dry_run=True)

        mock_run.assert_not_called()


class TestSyncRealRun:
    """Real run calls subprocess with correct SSH commands."""

    def test_writes_env_file_via_ssh_stdin(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text('export API_KEY="secret123"\nexport OTHER="val"\n')

        with (
            patch(_NS["__name__"] + ".HOME", tmp_path),
            patch(_NS["__name__"] + ".ENV_FILE", env),
            patch(_NS["__name__"] + ".GITCONFIG", tmp_path / "nope"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            sync("user@host", dry_run=False)

        # First call should be the env-file write via ssh cat > ~/.env.fly
        calls = mock_run.call_args_list
        env_calls = [c for c in calls if "cat > ~/.env.fly" in str(c)]
        assert len(env_calls) == 1
        # Verify secrets passed via stdin, NOT in the command args
        env_call = env_calls[0]
        cmd_args = env_call[0][0]  # positional: the command list
        assert "secret123" not in " ".join(cmd_args)
        # Verify stdin contains the actual values
        assert "secret123" in env_call.kwargs.get("input", "") or "secret123" in (env_call[1].get("input", "") if len(env_call) > 1 else "")

    def test_syncs_ssh_keys_and_gitconfig(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text('export K="v"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("priv")
        (ssh_dir / "id_ed25519.pub").write_text("pub")
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\nname=T\n")

        with (
            patch(_NS["__name__"] + ".HOME", tmp_path),
            patch(_NS["__name__"] + ".ENV_FILE", env),
            patch(_NS["__name__"] + ".GITCONFIG", gitconfig),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            sync("user@host", dry_run=False)

        all_cmds = [c[0][0] for c in mock_run.call_args_list]
        cmd_strs = [" ".join(c) for c in all_cmds]

        # Should have: mkdir .ssh, scp private key, scp pub key, chmod, gitconfig write
        assert any("mkdir -p ~/.ssh" in s for s in cmd_strs), f"Missing mkdir: {cmd_strs}"
        assert any("scp" in s and "id_ed25519 " in s for s in cmd_strs), f"Missing scp private: {cmd_strs}"
        assert any("scp" in s and "id_ed25519.pub" in s for s in cmd_strs), f"Missing scp pub: {cmd_strs}"
        assert any("chmod" in s for s in cmd_strs), f"Missing chmod: {cmd_strs}"
        assert any(".gitconfig" in s for s in cmd_strs), f"Missing gitconfig: {cmd_strs}"


class TestNoSecretLeakage:
    """Verify no secret values appear in any logged command args."""

    def test_secret_not_in_command_args(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text('export SUPER_SECRET="leaked_value_xyz"\n')

        with (
            patch(_NS["__name__"] + ".HOME", tmp_path),
            patch(_NS["__name__"] + ".ENV_FILE", env),
            patch(_NS["__name__"] + ".GITCONFIG", tmp_path / "nope"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            sync("t@h", dry_run=False)

        for call_args in mock_run.call_args_list:
            cmd = call_args[0][0]
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            assert "leaked_value_xyz" not in cmd_str, f"Secret leaked in command: {cmd_str}"

    def test_secret_only_in_stdin(self, tmp_path):
        env = tmp_path / ".env.fly"
        env.write_text('export MY_TOKEN="token_abc_999"\n')

        with (
            patch(_NS["__name__"] + ".HOME", tmp_path),
            patch(_NS["__name__"] + ".ENV_FILE", env),
            patch(_NS["__name__"] + ".GITCONFIG", tmp_path / "nope"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            sync("t@h", dry_run=False)

        # Find the env-write call and verify input contains the secret
        env_call = None
        for c in mock_run.call_args_list:
            cmd = c[0][0]
            if "cat > ~/.env.fly" in " ".join(cmd):
                env_call = c
                break
        assert env_call is not None
        stdin_input = env_call.kwargs.get("input") or (env_call[1].get("input") if len(env_call) > 1 else None)
        assert "token_abc_999" in stdin_input
