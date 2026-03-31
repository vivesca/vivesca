"""Tests for secrets-sync — env/SSH/gitconfig sync effector."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


def _load_module():
    """Load secrets-sync by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/secrets-sync").read()
    ns: dict = {"__name__": "secrets_sync"}
    exec(source, ns)
    return ns


_mod = _load_module()
parse_env_file = _mod["parse_env_file"]
ssh_key_files = _mod["ssh_key_files"]
sync_env = _mod["sync_env"]
sync_ssh_keys = _mod["sync_ssh_keys"]
sync_gitconfig = _mod["sync_gitconfig"]
main = _mod["main"]
ENV_FLY = _mod["ENV_FLY"]
SSH_DIR = _mod["SSH_DIR"]
GITCONFIG = _mod["GITCONFIG"]


# ── parse_env_file ──────────────────────────────────────────────


class TestParseEnvFile:
    def test_extracts_export_lines(self, tmp_path: Path):
        env = tmp_path / ".env.fly"
        env.write_text(textwrap.dedent("""\
            export FOO="bar"
            export BAZ='qux'
            export NUM=42
        """))
        pairs = parse_env_file(env)
        assert pairs == [("FOO", "bar"), ("BAZ", "qux"), ("NUM", "42")]

    def test_strips_double_quotes(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text('export KEY="val with spaces"\n')
        pairs = parse_env_file(env)
        assert pairs == [("KEY", "val with spaces")]

    def test_strips_single_quotes(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("export KEY='val'\n")
        pairs = parse_env_file(env)
        assert pairs == [("KEY", "val")]

    def test_skips_comments_and_blanks(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("# comment\n\nexport A=1\n# another\nexport B=2\n")
        pairs = parse_env_file(env)
        assert pairs == [("A", "1"), ("B", "2")]

    def test_nonexistent_file_returns_empty(self, tmp_path: Path):
        pairs = parse_env_file(tmp_path / "nope")
        assert pairs == []

    def test_no_export_prefix_skipped(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("PLAIN_VAR=value\nexport GOOD=yes\n")
        pairs = parse_env_file(env)
        assert pairs == [("GOOD", "yes")]


# ── ssh_key_files ───────────────────────────────────────────────


class TestSshKeyFiles:
    def test_returns_existing_keys(self, tmp_path: Path):
        priv = tmp_path / "id_ed25519"
        pub = tmp_path / "id_ed25519.pub"
        priv.write_text("keydata")
        pub.write_text("keydata pub")
        with patch.object(_mod, "SSH_DIR", tmp_path):
            files = ssh_key_files()
        assert len(files) == 2
        names = [f.name for f in files]
        assert "id_ed25519" in names
        assert "id_ed25519.pub" in names

    def test_returns_empty_when_no_keys(self, tmp_path: Path):
        with patch.object(_mod, "SSH_DIR", tmp_path):
            files = ssh_key_files()
        assert files == []


# ── sync_env (mocked SSH) ───────────────────────────────────────


class TestSyncEnv:
    def test_dry_run_prints_no_ssh(self, capsys):
        pairs = [("API_KEY", "secret123"), ("TOKEN", "tok456")]
        ok = sync_env("user@host", pairs, dry_run=True)
        assert ok is True
        out = capsys.readouterr().out
        assert "API_KEY" in out
        assert "TOKEN" in out
        assert "secret123" not in out

    def test_calls_ssh_with_content(self):
        pairs = [("KEY1", "val1")]
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            ok = sync_env("user@host", pairs, dry_run=False)
        assert ok is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["ssh", "user@host", "cat > ~/.env.fly"]
        assert "export KEY1=\"val1\"" in call_args[1]["input"]

    def test_returns_false_on_ssh_failure(self):
        pairs = [("KEY1", "val1")]
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Connection refused")
            ok = sync_env("user@host", pairs, dry_run=False)
        assert ok is False

    def test_empty_pairs_succeeds(self, capsys):
        ok = sync_env("user@host", [], dry_run=False)
        assert ok is True


# ── sync_ssh_keys (mocked SSH/SCP) ─────────────────────────────


class TestSyncSshKeys:
    def test_dry_run_no_scp(self, capsys):
        keys = [Path("/home/terry/.ssh/id_ed25519")]
        ok = sync_ssh_keys("user@host", keys, dry_run=True)
        assert ok is True
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert "scp" in out

    def test_copies_keys_and_chmods(self, tmp_path: Path):
        priv = tmp_path / "id_ed25519"
        pub = tmp_path / "id_ed25519.pub"
        priv.write_text("privkey")
        pub.write_text("pubkey")
        keys = [priv, pub]

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            ok = sync_ssh_keys("user@host", keys, dry_run=False)
        assert ok is True

        # Should have calls: mkdir, scp priv, scp pub, chmod priv
        calls = mock_run.call_args_list
        # First call: mkdir -p ~/.ssh
        assert "mkdir" in " ".join(str(c) for c in calls[0][0][0])
        # SCP calls for each key
        scp_calls = [c for c in calls if c[0][0][0] == "scp"]
        assert len(scp_calls) == 2

    def test_empty_keys_succeeds(self, capsys):
        ok = sync_ssh_keys("user@host", [], dry_run=False)
        assert ok is True


# ── sync_gitconfig (mocked SSH) ─────────────────────────────────


class TestSyncGitconfig:
    def test_dry_run(self, capsys):
        with patch.object(_mod, "GITCONFIG", Path("/nonexistent")):
            ok = sync_gitconfig("user@host", dry_run=True)
        # No gitconfig = still ok
        assert ok is True

    def test_copies_gitconfig(self):
        with patch.object(_mod, "GITCONFIG", Path("/tmp/fake_gitconfig")):
            Path("/tmp/fake_gitconfig").write_text("[user]\n  name = Test\n")
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")
                ok = sync_gitconfig("user@host", dry_run=False)
            assert ok is True
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == ["ssh", "user@host", "cat > ~/.gitconfig"]
            assert "[user]" in call_args[1]["input"]
            Path("/tmp/fake_gitconfig").unlink(missing_ok=True)

    def test_returns_false_on_failure(self):
        with patch.object(_mod, "GITCONFIG", Path("/tmp/fake_gitconfig2")):
            Path("/tmp/fake_gitconfig2").write_text("[user]\n  name = T\n")
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="fail")
                ok = sync_gitconfig("user@host", dry_run=False)
            assert ok is False
            Path("/tmp/fake_gitconfig2").unlink(missing_ok=True)


# ── main integration ────────────────────────────────────────────


class TestMain:
    def test_dry_run_exits_zero(self, capsys):
        with patch.object(_mod, "ENV_FLY", Path("/nonexistent")), \
             patch.object(_mod, "SSH_DIR", Path("/nonexistent")), \
             patch.object(_mod, "GITCONFIG", Path("/nonexistent")):
            rc = main(["--target", "user@host", "--dry-run"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "dry-run" in out

    def test_missing_target_exits_error(self):
        with pytest.raises(SystemExit):
            main([])

    def test_full_sync_success(self, tmp_path: Path):
        env = tmp_path / ".env.fly"
        env.write_text('export MYKEY="myval"\n')
        priv = tmp_path / "id_ed25519"
        priv.write_text("key")
        gitcfg = tmp_path / ".gitconfig"
        gitcfg.write_text("[user]\nname=T\n")

        with patch.object(_mod, "ENV_FLY", env), \
             patch.object(_mod, "SSH_DIR", tmp_path), \
             patch.object(_mod, "GITCONFIG", gitcfg), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            rc = main(["--target", "user@host"])
        assert rc == 0

    def test_never_logs_secret_values(self, tmp_path: Path, capsys):
        env = tmp_path / ".env.fly"
        env.write_text('export SUPER_SECRET="hunter2"\n')
        with patch.object(_mod, "ENV_FLY", env), \
             patch.object(_mod, "SSH_DIR", tmp_path), \
             patch.object(_mod, "GITCONFIG", Path("/nonexistent")):
            rc = main(["--target", "user@host", "--dry-run"])
        out = capsys.readouterr().out
        assert "SUPER_SECRET" in out
        assert "hunter2" not in out
