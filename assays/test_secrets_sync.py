"""Tests for effectors/secrets-sync — mocked SSH, no real network."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "effectors" / "secrets-sync"

NS: dict = {}
exec(SCRIPT.read_text(), NS)  # load module into namespace

parse_env_file = NS["parse_env_file"]
local_ssh_keys = NS["local_ssh_keys"]
ssh_cmd = NS["ssh_cmd"]
scp_file = NS["scp_file"]
write_remote_env = NS["write_remote_env"]
sync = NS["sync"]


# ── parse_env_file ─────────────────────────────────────────────


class TestParseEnvFile:
    def test_extracts_export_lines(self, tmp_path: Path) -> None:
        env = tmp_path / ".env.fly"
        env.write_text(textwrap.dedent("""\
            export FOO="bar"
            export BAZ='qux'
            export PLAIN=value
        """))
        pairs = parse_env_file(env)
        assert pairs == [("FOO", "bar"), ("BAZ", "qux"), ("PLAIN", "value")]

    def test_skips_comments_and_blanks(self, tmp_path: Path) -> None:
        env = tmp_path / ".env.fly"
        env.write_text("# comment\n\nexport K=\"v\"\n")
        assert parse_env_file(env) == [("K", "v")]

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert parse_env_file(tmp_path / "nope") == []

    def test_strips_double_quotes(self, tmp_path: Path) -> None:
        env = tmp_path / ".env.fly"
        env.write_text('export KEY="val"\n')
        assert parse_env_file(env) == [("KEY", "val")]

    def test_strips_single_quotes(self, tmp_path: Path) -> None:
        env = tmp_path / ".env.fly"
        env.write_text("export KEY='val'\n")
        assert parse_env_file(env) == [("KEY", "val")]


# ── local_ssh_keys ─────────────────────────────────────────────


class TestLocalSshKeys:
    def test_finds_existing_keys(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        (ssh_dir / "id_ed25519.pub").write_text("pub")
        monkeypatch.setattr(NS["__builtins__"].get("HOME") if False else NS, "HOME", tmp_path)
        # Patch the HOME constant in the module namespace
        NS["HOME"] = tmp_path
        found = local_ssh_keys()
        names = {p.name for p in found}
        assert names == {"id_ed25519", "id_ed25519.pub"}
        NS["HOME"] = Path.home()  # restore

    def test_no_keys(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        NS["HOME"] = tmp_path
        found = local_ssh_keys()
        assert found == []
        NS["HOME"] = Path.home()


# ── ssh_cmd (mocked subprocess) ────────────────────────────────


class TestSshCmd:
    @patch("subprocess.run")
    def test_success(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="ok\n", stderr="")
        out = ssh_cmd("host", "echo hi")
        assert out == "ok\n"
        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        assert cmd_args == ["ssh", "host", "echo hi"]

    @patch("subprocess.run")
    def test_failure_raises(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="denied")
        with pytest.raises(RuntimeError, match="denied"):
            ssh_cmd("host", "bad")

    def test_dry_run_no_call(self, capsys: pytest.CaptureFixture) -> None:
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

    def test_dry_run_no_call(self, capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
        f = tmp_path / "testkey"
        f.write_text("data")
        scp_file("host", f, ".ssh/testkey", dry_run=True)
        assert "[dry-run]" in capsys.readouterr().out


# ── write_remote_env (mocked subprocess) ───────────────────────


class TestWriteRemoteEnv:
    @patch("subprocess.run")
    def test_writes_all_keys(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        pairs = [("FOO", "secret123"), ("BAR", "abc")]
        write_remote_env("host", pairs)
        # Check the input passed to ssh cat
        call_args = mock_run.call_args
        sent = call_args.kwargs.get("input") or call_args[1].get("input", "")
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


# ── full sync (mocked SSH + SCP) ───────────────────────────────


class TestSync:
    @patch("subprocess.run")
    def test_full_sync_dry_run(self, mock_run: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        # Set up fake home
        env_file = tmp_path / ".env.fly"
        env_file.write_text('export API_KEY="testval"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("privkey")
        (ssh_dir / "id_ed25519.pub").write_text("pubkey")
        gitconfig = tmp_path / ".gitconfig"
        gitconfig.write_text("[user]\n  name = Test\n")

        # Patch HOME in module
        NS["HOME"] = tmp_path
        NS["ENV_FILE"] = tmp_path / ".env.fly"
        NS["GITCONFIG"] = tmp_path / ".gitconfig"

        sync("user@host", dry_run=True)

        out = capsys.readouterr().out
        mock_run.assert_not_called()
        assert "API_KEY" in out
        assert "testval" not in out
        assert "id_ed25519" in out
        assert ".gitconfig" in out
        assert "[dry-run]" in out

        # Restore
        NS["HOME"] = Path.home()
        NS["ENV_FILE"] = Path.home() / ".env.fly"
        NS["GITCONFIG"] = Path.home() / ".gitconfig"

    @patch("subprocess.run")
    def test_sync_no_env_no_keys(self, mock_run: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        # No .env.fly, no ssh keys, no .gitconfig

        NS["HOME"] = tmp_path
        NS["ENV_FILE"] = tmp_path / ".env.fly"
        NS["GITCONFIG"] = tmp_path / ".gitconfig"

        sync("host", dry_run=True)
        out = capsys.readouterr().out
        assert "no keys found" in out
        assert "no ed25519 keys" in out
        assert "no .gitconfig" in out

        NS["HOME"] = Path.home()
        NS["ENV_FILE"] = Path.home() / ".env.fly"
        NS["GITCONFIG"] = Path.home() / ".gitconfig"
