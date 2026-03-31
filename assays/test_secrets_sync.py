"""Tests for secrets-sync — Sync API keys, SSH keys, gitconfig to a target host."""
from __future__ import annotations

import subprocess
import textwrap
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Load effector via exec (it's a script, not an importable module) ──

_SCRIPT = Path(__file__).parent.parent / "effectors" / "secrets-sync"
_NS: dict = {"__name__": "secrets_sync"}
exec(open(_SCRIPT).read(), _NS)

parse_env_file = _NS["parse_env_file"]
ssh_key_files = _NS["ssh_key_files"]
run_remote = _NS["run_remote"]
sync_env = _NS["sync_env"]
sync_ssh_keys = _NS["sync_ssh_keys"]
sync_gitconfig = _NS["sync_gitconfig"]
main = _NS["main"]


@contextmanager
def _patch_ns(**kwargs):
    """Patch module-level constants in the exec'd namespace dict.

    patch.object fails on plain dicts, and patch("secrets_sync.KEY", ...)
    fails because secrets_sync is not in sys.modules. So we mutate and
    restore the dict directly.
    """
    old = {k: _NS[k] for k in kwargs}
    _NS.update(kwargs)
    try:
        yield
    finally:
        _NS.update(old)


# ── parse_env_file ──────────────────────────────────────────────────


class TestParseEnvFile:
    def test_double_quoted(self, tmp_path: Path):
        env = tmp_path / ".env.fly"
        env.write_text('export ANTHROPIC_API_KEY="sk-ant-abc123"\n')
        assert parse_env_file(env) == [("ANTHROPIC_API_KEY", "sk-ant-abc123")]

    def test_single_quoted(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("export KEY='val'\n")
        assert parse_env_file(env) == [("KEY", "val")]

    def test_unquoted(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("export TOKEN=gho_abc\n")
        assert parse_env_file(env) == [("TOKEN", "gho_abc")]

    def test_skips_comments_and_blanks(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("# comment\n\nexport A=1\n# x\nexport B=2\n")
        assert parse_env_file(env) == [("A", "1"), ("B", "2")]

    def test_nonexistent_returns_empty(self, tmp_path: Path):
        assert parse_env_file(tmp_path / "nope") == []

    def test_non_export_lines_skipped(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("PLAIN=value\nexport GOOD=yes\n")
        assert parse_env_file(env) == [("GOOD", "yes")]

    def test_multiple_keys(self, tmp_path: Path):
        env = tmp_path / ".env.fly"
        env.write_text('export K1="v1"\nexport K2="v2"\nexport K3="v3"\n')
        result = parse_env_file(env)
        assert len(result) == 3
        assert [k for k, _ in result] == ["K1", "K2", "K3"]


# ── ssh_key_files ───────────────────────────────────────────────────


class TestSshKeyFiles:
    def test_finds_both_keys(self, tmp_path: Path):
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        (ssh_dir / "id_ed25519.pub").write_text("pub")
        with _patch_ns(SSH_DIR=ssh_dir):
            files = ssh_key_files()
        names = {f.name for f in files}
        assert names == {"id_ed25519", "id_ed25519.pub"}

    def test_only_private_key(self, tmp_path: Path):
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        with _patch_ns(SSH_DIR=ssh_dir):
            files = ssh_key_files()
        assert len(files) == 1
        assert files[0].name == "id_ed25519"

    def test_no_keys_returns_empty(self, tmp_path: Path):
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        with _patch_ns(SSH_DIR=ssh_dir):
            assert ssh_key_files() == []


# ── run_remote ──────────────────────────────────────────────────────


class TestRunRemote:
    def test_dry_run_returns_success(self, capsys):
        result = run_remote(["ssh", "host", "echo hi"], dry_run=True)
        assert result.returncode == 0
        assert "[dry-run]" in capsys.readouterr().out

    def test_real_run_calls_subprocess(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
            run_remote(["ssh", "host", "echo hi"], dry_run=False)
            mock_run.assert_called_once_with(
                ["ssh", "host", "echo hi"], capture_output=True, text=True
            )


# ── sync_env ────────────────────────────────────────────────────────


class TestSyncEnv:
    def test_dry_run_no_subprocess(self, capsys):
        pairs = [("API_KEY", "secret123"), ("TOKEN", "tok456")]
        with patch("subprocess.run") as mock_run:
            result = sync_env("user@host", pairs, dry_run=True)
        assert result is True
        mock_run.assert_not_called()
        out = capsys.readouterr().out
        assert "API_KEY" in out
        assert "TOKEN" in out
        assert "secret123" not in out

    def test_writes_via_ssh_stdin(self):
        pairs = [("KEY1", "val1"), ("KEY2", "val2")]
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
            result = sync_env("user@host", pairs, dry_run=False)
        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["ssh", "user@host", "cat > ~/.env.fly"]
        stdin_content = call_args[1]["input"]
        assert 'export KEY1="val1"' in stdin_content
        assert 'export KEY2="val2"' in stdin_content

    def test_ssh_failure_returns_false(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 1, "", "connection refused")
            assert sync_env("user@host", [("K", "v")], dry_run=False) is False

    def test_empty_pairs_succeeds(self, capsys):
        assert sync_env("user@host", [], dry_run=False) is True
        assert "No env vars" in capsys.readouterr().out


# ── sync_ssh_keys ───────────────────────────────────────────────────


class TestSyncSshKeys:
    def test_dry_run_no_subprocess(self, capsys):
        keys = [Path("/home/terry/.ssh/id_ed25519")]
        with patch("subprocess.run") as mock_run:
            result = sync_ssh_keys("user@host", keys, dry_run=True)
        assert result is True
        mock_run.assert_not_called()
        assert "id_ed25519" in capsys.readouterr().out

    def test_copies_and_chmod(self):
        keys = [Path("/home/terry/.ssh/id_ed25519")]
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
            result = sync_ssh_keys("user@host", keys, dry_run=False)
        assert result is True
        # mkdir + scp + chmod = 3 calls
        assert mock_run.call_count == 3
        cmd_strs = [" ".join(c[0][0]) for c in mock_run.call_args_list]
        assert any("mkdir" in s for s in cmd_strs)
        assert any("scp" in s for s in cmd_strs)
        assert any("chmod" in s for s in cmd_strs)

    def test_scp_failure_returns_false(self):
        keys = [Path("/home/terry/.ssh/id_ed25519")]
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess([], 0, "", ""),
                subprocess.CompletedProcess([], 1, "", "scp failed"),
            ]
            assert sync_ssh_keys("user@host", keys, dry_run=False) is False

    def test_no_keys_succeeds(self, capsys):
        assert sync_ssh_keys("user@host", [], dry_run=False) is True
        assert "No SSH key" in capsys.readouterr().out


# ── sync_gitconfig ──────────────────────────────────────────────────


class TestSyncGitconfig:
    def test_dry_run(self, tmp_path: Path, capsys):
        cfg = tmp_path / ".gitconfig"
        cfg.write_text("[user]\n  name = Test\n")
        with _patch_ns(GITCONFIG=cfg):
            with patch("subprocess.run") as mock_run:
                result = sync_gitconfig("user@host", dry_run=True)
        assert result is True
        mock_run.assert_not_called()
        assert "dry-run" in capsys.readouterr().out

    def test_writes_via_ssh_stdin(self, tmp_path: Path):
        cfg = tmp_path / ".gitconfig"
        content = "[user]\n  name = Test\n"
        cfg.write_text(content)
        with _patch_ns(GITCONFIG=cfg):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
                result = sync_gitconfig("user@host", dry_run=False)
        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["ssh", "user@host", "cat > ~/.gitconfig"]
        assert call_args[1]["input"] == content

    def test_ssh_failure_returns_false(self, tmp_path: Path):
        cfg = tmp_path / ".gitconfig"
        cfg.write_text("[user]\n  name = T\n")
        with _patch_ns(GITCONFIG=cfg):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 1, "", "ssh error")
                assert sync_gitconfig("user@host", dry_run=False) is False

    def test_missing_file_succeeds(self, capsys):
        with _patch_ns(GITCONFIG=Path("/nonexistent/path/gitconfig")):
            assert sync_gitconfig("user@host", dry_run=False) is True
        assert "No ~/.gitconfig" in capsys.readouterr().out


# ── main integration ────────────────────────────────────────────────


class TestMain:
    def test_dry_run_exits_zero(self, tmp_path: Path, capsys):
        env = tmp_path / ".env.fly"
        env.write_text('export TEST_KEY="testval"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        cfg = tmp_path / ".gitconfig"
        cfg.write_text("[user]\n  name = T\n")

        with _patch_ns(ENV_FILE=env, SSH_DIR=ssh_dir, GITCONFIG=cfg):
            ret = main(["--target", "user@host", "--dry-run"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "TEST_KEY" in out
        assert "dry-run" in out
        assert "testval" not in out

    def test_full_sync(self, tmp_path: Path):
        env = tmp_path / ".env.fly"
        env.write_text('export API="secret"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_ed25519").write_text("key")
        (ssh_dir / "id_ed25519.pub").write_text("pub")
        cfg = tmp_path / ".gitconfig"
        cfg.write_text("[user]\n  name = T\n")

        with _patch_ns(ENV_FILE=env, SSH_DIR=ssh_dir, GITCONFIG=cfg):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
                ret = main(["--target", "user@host"])
        assert ret == 0
        assert mock_run.call_count >= 4

    def test_no_target_exits_error(self):
        with pytest.raises(SystemExit):
            main([])

    def test_never_logs_secret_values(self, tmp_path: Path, capsys):
        env = tmp_path / ".env.fly"
        env.write_text('export SUPER_SECRET="hunter2"\nexport ANOTHER="password123"\n')
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        cfg = tmp_path / ".gitconfig"
        cfg.write_text("[user]\n  name = T\n")

        with _patch_ns(ENV_FILE=env, SSH_DIR=ssh_dir, GITCONFIG=cfg):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
                main(["--target", "user@host"])
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "SUPER_SECRET" in output
        assert "ANOTHER" in output
        assert "hunter2" not in output
        assert "password123" not in output


# ── secret leakage guard ────────────────────────────────────────────


class TestNoSecretLeakage:
    def test_secret_not_in_command_args(self, tmp_path: Path):
        env = tmp_path / ".env.fly"
        env.write_text('export SUPER_SECRET="leaked_value_xyz"\n')

        with _patch_ns(ENV_FILE=env, SSH_DIR=tmp_path, GITCONFIG=tmp_path / "nope"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
                main(["--target", "t@h"])

        for call_args in mock_run.call_args_list:
            cmd = call_args[0][0]
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            assert "leaked_value_xyz" not in cmd_str, f"Secret leaked: {cmd_str}"

    def test_secret_only_in_stdin(self, tmp_path: Path):
        env = tmp_path / ".env.fly"
        env.write_text('export MY_TOKEN="token_abc_999"\n')

        with _patch_ns(ENV_FILE=env, SSH_DIR=tmp_path, GITCONFIG=tmp_path / "nope"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
                main(["--target", "t@h"])

        env_call = None
        for c in mock_run.call_args_list:
            cmd = c[0][0]
            if "cat > ~/.env.fly" in " ".join(cmd):
                env_call = c
                break
        assert env_call is not None, "No env write call found"
        stdin_input = env_call[1].get("input", "")
        assert "token_abc_999" in stdin_input
