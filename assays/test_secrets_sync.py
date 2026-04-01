from __future__ import annotations

"""Tests for effectors/secrets-sync -- mocked SSH, no real network."""

import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_secrets_sync():
    """Load secrets-sync by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/secrets-sync")).read()
    ns: dict = {"__name__": "secrets_sync"}
    exec(source, ns)
    return ns


_mod = _load_secrets_sync()
parse_env_file = _mod["parse_env_file"]
ssh_key_files = _mod["ssh_key_files"]
run_remote = _mod["run_remote"]
sync_env = _mod["sync_env"]
sync_ssh_keys = _mod["sync_ssh_keys"]
sync_gitconfig = _mod["sync_gitconfig"]
main = _mod["main"]


# -- parse_env_file tests --


def test_parse_env_extracts_export_lines(tmp_path: Path):
    env = tmp_path / ".env.fly"
    env.write_text('export FOO="bar"\nexport BAZ="qux"\n')
    assert parse_env_file(env) == [("FOO", "bar"), ("BAZ", "qux")]


def test_parse_env_strips_single_quotes(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("export KEY='val'\n")
    assert parse_env_file(env) == [("KEY", "val")]


def test_parse_env_unquoted_value(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("export NUM=42\n")
    assert parse_env_file(env) == [("NUM", "42")]


def test_parse_env_skips_comments_and_blanks(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("# comment\n\nexport X=\"y\"\n# another\n")
    assert parse_env_file(env) == [("X", "y")]


def test_parse_env_nonexistent_returns_empty(tmp_path: Path):
    assert parse_env_file(tmp_path / "nope") == []


def test_parse_env_skips_non_export_lines(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("PLAIN=value\nexport GOOD=yes\n")
    assert parse_env_file(env) == [("GOOD", "yes")]


# -- ssh_key_files tests --


def test_ssh_key_files_finds_existing(tmp_path: Path):
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "id_ed25519").write_text("key")
    (ssh_dir / "id_ed25519.pub").write_text("pub-key")
    old = _mod["SSH_DIR"]
    try:
        _mod["SSH_DIR"] = ssh_dir
        files = ssh_key_files()
    finally:
        _mod["SSH_DIR"] = old
    names = {f.name for f in files}
    assert names == {"id_ed25519", "id_ed25519.pub"}


def test_ssh_key_files_only_private(tmp_path: Path):
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "id_ed25519").write_text("key")
    old = _mod["SSH_DIR"]
    try:
        _mod["SSH_DIR"] = ssh_dir
        files = ssh_key_files()
    finally:
        _mod["SSH_DIR"] = old
    assert len(files) == 1
    assert files[0].name == "id_ed25519"


def test_ssh_key_files_none_exist(tmp_path: Path):
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    old = _mod["SSH_DIR"]
    try:
        _mod["SSH_DIR"] = ssh_dir
        files = ssh_key_files()
    finally:
        _mod["SSH_DIR"] = old
    assert files == []


# -- run_remote tests --


def test_run_remote_dry_run(capsys):
    result = run_remote(["ssh", "host", "echo hi"], dry_run=True)
    assert result.returncode == 0
    assert "[dry-run]" in capsys.readouterr().out


def test_run_remote_executes():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
        run_remote(["ssh", "host", "echo hi"], dry_run=False)
        mock_run.assert_called_once_with(
            ["ssh", "host", "echo hi"], capture_output=True, text=True
        )


# -- sync_env tests --


def test_sync_env_dry_run_no_subprocess(capsys):
    pairs = [("API_KEY", "secret123"), ("TOKEN", "tok456")]
    with patch("subprocess.run") as mock_run:
        ok = sync_env("user@host", pairs, dry_run=True)
    assert ok is True
    mock_run.assert_not_called()
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "TOKEN" in out
    assert "secret123" not in out


def test_sync_env_writes_via_ssh():
    pairs = [("KEY1", "val1")]
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        ok = sync_env("user@host", pairs, dry_run=False)
    assert ok is True
    call_args = mock_run.call_args
    assert call_args[0][0] == ["ssh", "user@host", "cat > ~/.env.fly"]
    assert 'export KEY1="val1"' in call_args[1]["input"]


def test_sync_env_ssh_failure():
    pairs = [("KEY", "val")]
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="connection refused")
        ok = sync_env("user@host", pairs, dry_run=False)
    assert ok is False


def test_sync_env_empty_pairs(capsys):
    ok = sync_env("user@host", [], dry_run=False)
    assert ok is True
    assert "No env vars" in capsys.readouterr().out


# -- sync_ssh_keys tests --


def test_sync_ssh_keys_dry_run(capsys):
    keys = [Path(str(Path.home() / ".ssh/id_ed25519"))]
    with patch("subprocess.run") as mock_run:
        ok = sync_ssh_keys("user@host", keys, dry_run=True)
    assert ok is True
    mock_run.assert_not_called()
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "id_ed25519" in out


def test_sync_ssh_keys_copies_and_chmods():
    keys = [Path(str(Path.home() / ".ssh/id_ed25519"))]
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        ok = sync_ssh_keys("user@host", keys, dry_run=False)
    assert ok is True
    # mkdir + scp + chmod = 3 calls to subprocess.run
    assert mock_run.call_count == 3
    first_cmd = mock_run.call_args_list[0][0][0]
    assert "mkdir" in " ".join(first_cmd)


def test_sync_ssh_keys_scp_failure():
    keys = [Path(str(Path.home() / ".ssh/id_ed25519"))]
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stderr=""),  # mkdir via run_remote
            MagicMock(returncode=1, stderr="scp failed"),  # scp
        ]
        ok = sync_ssh_keys("user@host", keys, dry_run=False)
    assert ok is False


def test_sync_ssh_keys_no_keys(capsys):
    ok = sync_ssh_keys("user@host", [], dry_run=False)
    assert ok is True
    assert "No SSH key" in capsys.readouterr().out


# -- sync_gitconfig tests --


def test_sync_gitconfig_dry_run(capsys, tmp_path: Path):
    tmp = tmp_path / ".gitconfig"
    tmp.write_text("[user]\n  name = Test\n")
    old = _mod["GITCONFIG"]
    try:
        _mod["GITCONFIG"] = tmp
        with patch("subprocess.run") as mock_run:
            ok = sync_gitconfig("user@host", dry_run=True)
    finally:
        _mod["GITCONFIG"] = old
    assert ok is True
    mock_run.assert_not_called()
    assert "dry-run" in capsys.readouterr().out


def test_sync_gitconfig_writes_via_ssh(tmp_path: Path):
    tmp = tmp_path / ".gitconfig"
    content = "[user]\n  name = Test\n"
    tmp.write_text(content)
    old = _mod["GITCONFIG"]
    try:
        _mod["GITCONFIG"] = tmp
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            ok = sync_gitconfig("user@host", dry_run=False)
    finally:
        _mod["GITCONFIG"] = old
    assert ok is True
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][0] == ["ssh", "user@host", "cat > ~/.gitconfig"]
    assert "[user]" in call_args[1]["input"]


def test_sync_gitconfig_ssh_failure(tmp_path: Path):
    tmp = tmp_path / ".gitconfig"
    tmp.write_text("[user]\n  name = T\n")
    old = _mod["GITCONFIG"]
    try:
        _mod["GITCONFIG"] = tmp
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="ssh error")
            ok = sync_gitconfig("user@host", dry_run=False)
    finally:
        _mod["GITCONFIG"] = old
    assert ok is False


def test_sync_gitconfig_no_file(capsys):
    old = _mod["GITCONFIG"]
    try:
        _mod["GITCONFIG"] = Path("/nonexistent/path/.gitconfig")
        ok = sync_gitconfig("user@host", dry_run=False)
    finally:
        _mod["GITCONFIG"] = old
    assert ok is True
    assert "No ~/.gitconfig" in capsys.readouterr().out


# -- main integration tests --


def test_main_dry_run(capsys, tmp_path: Path):
    tmp_env = tmp_path / ".env.fly"
    tmp_env.write_text('export TEST_KEY="testval"\n')
    tmp_git = tmp_path / ".gitconfig"
    tmp_git.write_text("[user]\n  name = T\n")
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "id_ed25519").write_text("key")

    saved = (_mod["ENV_FILE"], _mod["GITCONFIG"], _mod["SSH_DIR"])
    try:
        _mod["ENV_FILE"] = tmp_env
        _mod["GITCONFIG"] = tmp_git
        _mod["SSH_DIR"] = ssh_dir
        rc = main(["--target", "user@host", "--dry-run"])
    finally:
        _mod["ENV_FILE"], _mod["GITCONFIG"], _mod["SSH_DIR"] = saved

    assert rc == 0
    out = capsys.readouterr().out
    assert "TEST_KEY" in out
    assert "dry-run" in out
    assert "testval" not in out


def test_main_full_sync(tmp_path: Path):
    tmp_env = tmp_path / ".env.fly"
    tmp_env.write_text('export API="secret"\n')
    tmp_git = tmp_path / ".gitconfig"
    tmp_git.write_text("[user]\n  name = T\n")
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "id_ed25519").write_text("key")
    (ssh_dir / "id_ed25519.pub").write_text("pub")

    saved = (_mod["ENV_FILE"], _mod["GITCONFIG"], _mod["SSH_DIR"])
    try:
        _mod["ENV_FILE"] = tmp_env
        _mod["GITCONFIG"] = tmp_git
        _mod["SSH_DIR"] = ssh_dir
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            rc = main(["--target", "user@host"])
    finally:
        _mod["ENV_FILE"], _mod["GITCONFIG"], _mod["SSH_DIR"] = saved

    assert rc == 0
    assert mock_run.call_count >= 4


def test_main_no_target_exits_error():
    with pytest.raises(SystemExit):
        main([])


def test_main_never_logs_secret_values(capsys, tmp_path: Path):
    tmp_env = tmp_path / ".env.fly"
    tmp_env.write_text('export SUPER_SECRET="hunter2"\nexport ANOTHER="password123"\n')
    tmp_git = tmp_path / ".gitconfig"
    tmp_git.write_text("[user]\n  name = T\n")
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()

    saved = (_mod["ENV_FILE"], _mod["GITCONFIG"], _mod["SSH_DIR"])
    try:
        _mod["ENV_FILE"] = tmp_env
        _mod["GITCONFIG"] = tmp_git
        _mod["SSH_DIR"] = ssh_dir
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            rc = main(["--target", "user@host"])
    finally:
        _mod["ENV_FILE"], _mod["GITCONFIG"], _mod["SSH_DIR"] = saved

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "SUPER_SECRET" in output
    assert "ANOTHER" in output
    assert "hunter2" not in output
    assert "password123" not in output

