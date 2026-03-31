"""Tests for effectors/secrets-sync — mocked SSH, no real network."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load the effector via exec (it's a script, not an importable module).
_SCRIPT = Path(__file__).resolve().parent.parent / "effectors" / "secrets-sync"
_NS: dict = {"__name__": "secrets_sync"}
exec(_SCRIPT.read_text(), _NS)

parse_env_file = _NS["parse_env_file"]
local_ssh_keys = _NS["local_ssh_keys"]
ssh_cmd = _NS["ssh_cmd"]
scp_file = _NS["scp_file"]
write_remote_env = _NS["write_remote_env"]
sync = _NS["sync"]
main = _NS["main"]


# ── parse_env_file ─────────────────────────────────────────────


class TestParseEnvFile:
    def test_extracts_double_quoted(self, tmp_path: Path) -> None:
        env = tmp_path / ".env.fly"
        env.write_text('export ANTHROPIC_API_KEY="sk-ant-abc123"\n')
        assert parse_env_file(env) == [("ANTHROPIC_API_KEY", "sk-ant-abc123")]

    def test_extracts_single_quoted(self, tmp_path: Path) -> None:
        env = tmp_path / ".env.fly"
        env.write_text("export ZHIPU_API_KEY='zhipu-key'\n")
        assert parse_env_file(env) == [("ZHIPU_API_KEY", "zhipu-key")]

    def test_extracts_unquoted(self, tmp_path: Path) -> None:
        env = tmp_path / ".env.fly"
        env.write_text("export GITHUB_TOKEN=gho_token\n")
        assert parse_env_file(env) == [("GITHUB_TOKEN", "gho_token")]

    def test_skips_blanks_and_comments(self, tmp_path: Path) -> None:
        env = tmp_path / ".env.fly"
        env.write_text("# comment\n\nexport FOO=bar\n")
        assert parse_env_file(env) == [("FOO", "bar")]

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert parse_env_file(tmp_path / "nope") == []

    def test_multiple_keys(self, tmp_path: Path) -> None:
        env = tmp_path / ".env.fly"
        env.write_text(textwrap.dedent("""\
            export KEY_A="val_a"
            export KEY_B="val_b"
            export KEY_C="val_c"
        """))
        result = parse_env_file(env)
        assert len(result) == 3
        assert [k for k, _ in result] == ["KEY_A", "KEY_B", "KEY_C"]


# ── local_ssh_keys ─────────────────────────────────────────────


class TestLocalSshKeys:
    def test_finds_existing_keys(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        (ssh_dir / "id_ed25519.pub").write_text("pub")
        _NS["HOME"] = tmp_path
        found = local_ssh_keys()
        _NS["HOME"] = Path.home()  # restore
        names = {p.name for p in found}
        assert names == {"id_ed25519", "id_ed25519.pub"}

    def test_returns_empty_when_no_keys(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        _NS["HOME"] = tmp_path
        assert local_ssh_keys() == []
        _NS["HOME"] = Path.home()

    def test_returns_only_existing(self, tmp_path: Path) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        _NS["HOME"] = tmp_path
        found = local_ssh_keys()
        _NS["HOME"] = Path.home()
        assert len(found) == 1
        assert found[0].name == "id_ed25519"


# ── ssh_cmd (mocked subprocess) ────────────────────────────────


class TestSshCmd:
    @patch("subprocess.run")
    def test_success(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="ok\n", stderr="")
        out = ssh_cmd("host", "echo hi")
        assert out == "ok\n"
        cmd_args = mock_run.call_args[0][0]
        assert cmd_args == ["ssh", "host", "echo hi"]

    @patch("subprocess.run")
    def test_failure_raises(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="denied")
        with pytest.raises(RuntimeError, match="denied"):
            ssh_cmd("host", "bad")

    def test_dry_run_no_subprocess(self, capsys: pytest.CaptureFixture) -> None:
        out = ssh_cmd("host", "echo hi", dry_run=True)
        assert out == ""
        assert "[dry-run]" in capsys.readouterr().out


# ── scp_file (mocked subprocess) ───────────────────────────────


class TestScpFile:
    @patch("subprocess.run")
    def test_success(self, mock_run: MagicMock, tmp_path: Path) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        f = tmp_path / "testkey"
        f.write_text("data")
        scp_file("host", f, ".ssh/testkey")
        cmd_args = mock_run.call_args[0][0]
        assert cmd_args[0] == "scp"
        assert "host:.ssh/testkey" in cmd_args

    @patch("subprocess.run")
    def test_failure_raises(self, mock_run: MagicMock, tmp_path: Path) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr="nope")
        f = tmp_path / "testkey"
        f.write_text("data")
        with pytest.raises(RuntimeError, match="nope"):
            scp_file("host", f, ".ssh/testkey")

    def test_dry_run_no_subprocess(self, capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
        f = tmp_path / "testkey"
        f.write_text("data")
        scp_file("host", f, ".ssh/testkey", dry_run=True)
        assert "[dry-run]" in capsys.readouterr().out


# ── write_remote_env (mocked subprocess) ───────────────────────


class TestWriteRemoteEnv:
    @patch("subprocess.run")
    def test_writes_all_keys_via_stdin(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        pairs = [("FOO", "secret123"), ("BAR", "abc")]
        write_remote_env("host", pairs)
        call_args = mock_run.call_args
        sent = call_args.kwargs.get("input", "")
        assert 'export FOO="secret123"' in sent
        assert 'export BAR="abc"' in sent

    @patch("subprocess.run")
    def test_logs_key_names_not_values(self, mock_run: MagicMock, capsys: pytest.CaptureFixture) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        write_remote_env("host", [("SECRET_KEY", "supersecret")])
        out = capsys.readouterr().out
        assert "SECRET_KEY" in out
        assert "supersecret" not in out

    def test_dry_run_no_ssh(self, capsys: pytest.CaptureFixture) -> None:
        pairs = [("KEY1", "v1")]
        write_remote_env("host", pairs, dry_run=True)
        out = capsys.readouterr().out
        assert "[dry-run]" in out
        assert "KEY1" in out
        assert "v1" not in out

    @patch("subprocess.run")
    def test_failure_raises(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr="conn refused")
        with pytest.raises(RuntimeError, match="conn refused"):
            write_remote_env("host", [("K", "v")])


# ── full sync integration (mocked) ─────────────────────────────


class TestSync:
    @patch("subprocess.run")
    def test_full_sync_dry_run(self, mock_run: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        env_file = tmp_path / ".env.fly"
        env_file.write_text('export API_KEY="testval"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("privkey")
        (ssh_dir / "id_ed25519.pub").write_text("pubkey")
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\n  name = Test\n")

        _NS["HOME"] = tmp_path
        _NS["ENV_FILE"] = env_file
        _NS["GITCONFIG"] = gitconfig

        sync("user@host", dry_run=True)
        out = capsys.readouterr().out

        mock_run.assert_not_called()
        assert "API_KEY" in out
        assert "testval" not in out
        assert "id_ed25519" in out
        assert ".gitconfig" in out
        assert "[dry-run]" in out

        _NS["HOME"] = Path.home()
        _NS["ENV_FILE"] = Path.home() / ".env.fly"
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"

    @patch("subprocess.run")
    def test_full_sync_real(self, mock_run: MagicMock, tmp_path: Path) -> None:
        env_file = tmp_path / ".env.fly"
        env_file.write_text('export API_KEY="val"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\nname=T\n")

        _NS["HOME"] = tmp_path
        _NS["ENV_FILE"] = env_file
        _NS["GITCONFIG"] = gitconfig

        mock_run.return_value = MagicMock(returncode=0, stderr="")
        sync("user@host")

        assert mock_run.call_count > 0

        _NS["HOME"] = Path.home()
        _NS["ENV_FILE"] = Path.home() / ".env.fly"
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"

    @patch("subprocess.run")
    def test_sync_no_env_no_keys(self, mock_run: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()

        _NS["HOME"] = tmp_path
        _NS["ENV_FILE"] = tmp_path / ".env.fly"
        _NS["GITCONFIG"] = tmp_path / ".gitconfig"

        sync("host", dry_run=True)
        out = capsys.readouterr().out
        assert "no keys found" in out
        assert "no ed25519 keys" in out
        assert "no .gitconfig" in out

        _NS["HOME"] = Path.home()
        _NS["ENV_FILE"] = Path.home() / ".env.fly"
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"


# ── No secret leakage in command args ──────────────────────────


class TestNoSecretLeakage:
    """Verify secret values never appear in subprocess command-line arguments."""

    @patch("subprocess.run")
    def test_secret_not_in_command_args(self, mock_run: MagicMock, tmp_path: Path) -> None:
        env = tmp_path / ".env.fly"
        env.write_text('export SUPER_SECRET="leaked_value_xyz"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\nname=T\n")

        _NS["HOME"] = tmp_path
        _NS["ENV_FILE"] = env
        _NS["GITCONFIG"] = gitconfig

        mock_run.return_value = MagicMock(returncode=0, stderr="")
        sync("t@h")

        for call_args in mock_run.call_args_list:
            cmd = call_args[0][0]
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            assert "leaked_value_xyz" not in cmd_str, f"Secret leaked in command: {cmd_str}"

        _NS["HOME"] = Path.home()
        _NS["ENV_FILE"] = Path.home() / ".env.fly"
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"

    @patch("subprocess.run")
    def test_secret_only_in_stdin(self, mock_run: MagicMock, tmp_path: Path) -> None:
        env = tmp_path / ".env.fly"
        env.write_text('export MY_TOKEN="token_abc_999"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\nname=T\n")

        _NS["HOME"] = tmp_path
        _NS["ENV_FILE"] = env
        _NS["GITCONFIG"] = gitconfig

        mock_run.return_value = MagicMock(returncode=0, stderr="")
        sync("t@h")

        # Find the env-write call and verify input contains the secret
        env_call = None
        for c in mock_run.call_args_list:
            cmd = c[0][0]
            if "cat > .env.fly" in " ".join(cmd):
                env_call = c
                break
        assert env_call is not None, "No env-write SSH call found"
        stdin_input = env_call.kwargs.get("input", "")
        assert "token_abc_999" in stdin_input

        _NS["HOME"] = Path.home()
        _NS["ENV_FILE"] = Path.home() / ".env.fly"
        _NS["GITCONFIG"] = Path.home() / ".gitconfig"
