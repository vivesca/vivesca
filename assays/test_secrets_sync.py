"""Tests for secrets-sync — Sync API keys and secrets to a target host."""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_secrets_sync():
    """Load the secrets-sync module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/secrets-sync").read()
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


# ── parse_env_file tests ─────────────────────────────────────────────


def test_parse_env_file_extracts_export_lines(tmp_path: Path):
    """parse_env_file extracts export KEY=VALUE pairs."""
    env = tmp_path / ".env.fly"
    env.write_text('export FOO="bar"\nexport BAZ="qux"\n')
    pairs = parse_env_file(env)
    assert pairs == [("FOO", "bar"), ("BAZ", "qux")]


def test_parse_env_file_strips_quotes(tmp_path: Path):
    """parse_env_file strips surrounding double and single quotes."""
    env = tmp_path / ".env.fly"
    env.write_text('export A="val1"\nexport B=\'val2\'\nexport C=val3\n')
    pairs = parse_env_file(env)
    assert pairs == [("A", "val1"), ("B", "val2"), ("C", "val3")]


def test_parse_env_file_skips_comments_and_blanks(tmp_path: Path):
    """parse_env_file skips blank lines and comments."""
    env = tmp_path / ".env.fly"
    env.write_text("# comment\n\nexport X=\"y\"\n# another\n")
    pairs = parse_env_file(env)
    assert pairs == [("X", "y")]


def test_parse_env_file_nonexistent_returns_empty(tmp_path: Path):
    """parse_env_file returns empty list for nonexistent file."""
    pairs = parse_env_file(tmp_path / "nope")
    assert pairs == []


def test_parse_env_file_multiple_keys(tmp_path: Path):
    """parse_env_file handles realistic multi-key env file."""
    env = tmp_path / ".env.fly"
    env.write_text(textwrap.dedent("""\
        export ANTHROPIC_API_KEY="sk-ant-test123"
        export ZHIPU_API_KEY="abc.def"
        export GITHUB_TOKEN="gho_test"
    """))
    pairs = parse_env_file(env)
    assert len(pairs) == 3
    keys = [k for k, _ in pairs]
    assert "ANTHROPIC_API_KEY" in keys
    assert "ZHIPU_API_KEY" in keys
    assert "GITHUB_TOKEN" in keys


# ── ssh_key_files tests ──────────────────────────────────────────────


def test_ssh_key_files_finds_existing(tmp_path: Path):
    """ssh_key_files returns paths for existing ed25519 keys."""
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "id_ed25519").write_text("key")
    (ssh_dir / "id_ed25519.pub").write_text("pub-key")
    saved = _mod["SSH_DIR"]
    try:
        _mod["SSH_DIR"] = ssh_dir
        files = ssh_key_files()
    finally:
        _mod["SSH_DIR"] = saved
    names = {f.name for f in files}
    assert names == {"id_ed25519", "id_ed25519.pub"}


def test_ssh_key_files_missing_pub(tmp_path: Path):
    """ssh_key_files works with only private key present."""
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "id_ed25519").write_text("key")
    saved = _mod["SSH_DIR"]
    try:
        _mod["SSH_DIR"] = ssh_dir
        files = ssh_key_files()
    finally:
        _mod["SSH_DIR"] = saved
    assert len(files) == 1
    assert files[0].name == "id_ed25519"


def test_ssh_key_files_none_exist(tmp_path: Path):
    """ssh_key_files returns empty when no keys found."""
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    saved = _mod["SSH_DIR"]
    try:
        _mod["SSH_DIR"] = ssh_dir
        files = ssh_key_files()
    finally:
        _mod["SSH_DIR"] = saved
    assert files == []


# ── run_remote tests ─────────────────────────────────────────────────


def test_run_remote_dry_run(capsys):
    """run_remote in dry-run prints command and returns mock success."""
    result = run_remote(["ssh", "host", "echo hi"], dry_run=True)
    assert result.returncode == 0
    captured = capsys.readouterr()
    assert "[dry-run]" in captured.out
    assert "ssh" in captured.out


def test_run_remote_executes():
    """run_remote calls subprocess.run when not dry-run."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
        run_remote(["ssh", "host", "echo hi"], dry_run=False)
        mock_run.assert_called_once_with(
            ["ssh", "host", "echo hi"], capture_output=True, text=True
        )


# ── sync_env tests ───────────────────────────────────────────────────


def test_sync_env_dry_run(capsys):
    """sync_env in dry-run does not call subprocess."""
    pairs = [("API_KEY", "secret123"), ("TOKEN", "tok456")]
    with patch("subprocess.run") as mock_run:
        result = sync_env("user@host", pairs, dry_run=True)
    assert result is True
    mock_run.assert_not_called()
    captured = capsys.readouterr()
    assert "API_KEY" in captured.out
    assert "TOKEN" in captured.out
    # Never log values
    assert "secret123" not in captured.out
    assert "tok456" not in captured.out


def test_sync_env_writes_via_ssh():
    """sync_env writes env content via ssh stdin."""
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


def test_sync_env_ssh_failure():
    """sync_env returns False on SSH failure."""
    pairs = [("KEY", "val")]
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess([], 1, "", "connection refused")
        result = sync_env("user@host", pairs, dry_run=False)
    assert result is False


def test_sync_env_empty_pairs(capsys):
    """sync_env with no pairs returns True and prints message."""
    result = sync_env("user@host", [], dry_run=False)
    assert result is True
    captured = capsys.readouterr()
    assert "No env vars" in captured.out


# ── sync_ssh_keys tests ──────────────────────────────────────────────


def test_sync_ssh_keys_dry_run(capsys):
    """sync_ssh_keys in dry-run prints scp commands without executing."""
    key_files = [Path("/home/terry/.ssh/id_ed25519"), Path("/home/terry/.ssh/id_ed25519.pub")]
    with patch("subprocess.run") as mock_run:
        result = sync_ssh_keys("user@host", key_files, dry_run=True)
    assert result is True
    mock_run.assert_not_called()
    captured = capsys.readouterr()
    assert "id_ed25519" in captured.out


def test_sync_ssh_keys_copies_files():
    """sync_ssh_keys creates remote .ssh dir and copies keys via scp."""
    key_files = [Path("/home/terry/.ssh/id_ed25519")]
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
        result = sync_ssh_keys("user@host", key_files, dry_run=False)
    assert result is True
    # Should have: mkdir + scp + chmod (3 calls)
    assert mock_run.call_count == 3
    calls = mock_run.call_args_list
    # First call: mkdir
    assert "mkdir" in " ".join(str(c) for c in calls[0][0])
    # Second call: scp
    assert "scp" in calls[1][0][0][0]


def test_sync_ssh_keys_scp_failure():
    """sync_ssh_keys returns False when scp fails."""
    key_files = [Path("/home/terry/.ssh/id_ed25519")]
    with patch("subprocess.run") as mock_run:
        # First call (mkdir) succeeds, second (scp) fails
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 1, "", "scp failed"),
        ]
        result = sync_ssh_keys("user@host", key_files, dry_run=False)
    assert result is False


def test_sync_ssh_keys_no_keys(capsys):
    """sync_ssh_keys with empty list returns True."""
    result = sync_ssh_keys("user@host", [], dry_run=False)
    assert result is True
    captured = capsys.readouterr()
    assert "No SSH key" in captured.out


# ── sync_gitconfig tests ─────────────────────────────────────────────


def test_sync_gitconfig_dry_run(capsys, tmp_path: Path):
    """sync_gitconfig in dry-run prints action without executing."""
    tmp = tmp_path / "gitconfig"
    tmp.write_text("[user]\n  name = Test\n  email = test@test.com\n")
    saved = _mod["GITCONFIG"]
    try:
        _mod["GITCONFIG"] = tmp
        with patch("subprocess.run") as mock_run:
            result = sync_gitconfig("user@host", dry_run=True)
    finally:
        _mod["GITCONFIG"] = saved
    assert result is True
    mock_run.assert_not_called()
    captured = capsys.readouterr()
    assert "dry-run" in captured.out


def test_sync_gitconfig_writes_via_ssh(tmp_path: Path):
    """sync_gitconfig writes gitconfig content via ssh stdin."""
    tmp = tmp_path / "gitconfig"
    content = "[user]\n  name = Test\n"
    tmp.write_text(content)
    saved = _mod["GITCONFIG"]
    try:
        _mod["GITCONFIG"] = tmp
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
            result = sync_gitconfig("user@host", dry_run=False)
    finally:
        _mod["GITCONFIG"] = saved
    assert result is True
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][0] == ["ssh", "user@host", "cat > ~/.gitconfig"]
    assert call_args[1]["input"] == content


def test_sync_gitconfig_ssh_failure(tmp_path: Path):
    """sync_gitconfig returns False on SSH failure."""
    tmp = tmp_path / "gitconfig"
    tmp.write_text("[user]\n  name = T\n")
    saved = _mod["GITCONFIG"]
    try:
        _mod["GITCONFIG"] = tmp
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 1, "", "ssh error")
            result = sync_gitconfig("user@host", dry_run=False)
    finally:
        _mod["GITCONFIG"] = saved
    assert result is False


def test_sync_gitconfig_no_file(capsys):
    """sync_gitconfig returns True when no .gitconfig exists."""
    saved = _mod["GITCONFIG"]
    try:
        _mod["GITCONFIG"] = Path("/nonexistent/path/gitconfig")
        result = sync_gitconfig("user@host", dry_run=False)
    finally:
        _mod["GITCONFIG"] = saved
    assert result is True
    captured = capsys.readouterr()
    assert "No ~/.gitconfig" in captured.out


# ── main integration tests ───────────────────────────────────────────


def _patch_paths(env_content: str, gitconfig_content: str, ssh_keys: list[str] | None = None):
    """Context manager that patches ENV_FLY, GITCONFIG, SSH_DIR in _mod dict."""
    import contextlib, tempfile
    # We'll use a fixture-style approach with manual setup
    pass


def test_main_dry_run(capsys, tmp_path: Path):
    """main with --dry-run prints all actions, exits 0."""
    tmp_env = tmp_path / ".env.fly"
    tmp_env.write_text('export TEST_KEY="testval"\n')
    tmp_git = tmp_path / ".gitconfig"
    tmp_git.write_text("[user]\n  name = T\n")
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "id_ed25519").write_text("key")

    saved_env = _mod["ENV_FLY"]
    saved_git = _mod["GITCONFIG"]
    saved_ssh = _mod["SSH_DIR"]
    try:
        _mod["ENV_FLY"] = tmp_env
        _mod["GITCONFIG"] = tmp_git
        _mod["SSH_DIR"] = ssh_dir
        ret = main(["--target", "user@host", "--dry-run"])
    finally:
        _mod["ENV_FLY"] = saved_env
        _mod["GITCONFIG"] = saved_git
        _mod["SSH_DIR"] = saved_ssh

    assert ret == 0
    captured = capsys.readouterr()
    assert "TEST_KEY" in captured.out
    assert "dry-run" in captured.out
    assert "sync complete" in captured.out
    # Never log values
    assert "testval" not in captured.out


def test_main_full_sync(tmp_path: Path):
    """main performs full sync: env + ssh keys + gitconfig."""
    tmp_env = tmp_path / ".env.fly"
    tmp_env.write_text('export API="secret"\n')
    tmp_git = tmp_path / ".gitconfig"
    tmp_git.write_text("[user]\n  name = T\n")
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "id_ed25519").write_text("key")
    (ssh_dir / "id_ed25519.pub").write_text("pub")

    saved_env = _mod["ENV_FLY"]
    saved_git = _mod["GITCONFIG"]
    saved_ssh = _mod["SSH_DIR"]
    try:
        _mod["ENV_FLY"] = tmp_env
        _mod["GITCONFIG"] = tmp_git
        _mod["SSH_DIR"] = ssh_dir
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
            ret = main(["--target", "user@host"])
    finally:
        _mod["ENV_FLY"] = saved_env
        _mod["GITCONFIG"] = saved_git
        _mod["SSH_DIR"] = saved_ssh

    assert ret == 0
    # subprocess.run called: env write + mkdir + scp(priv) + scp(pub) + chmod(priv) + gitconfig
    assert mock_run.call_count >= 4


def test_main_no_target_exits_error():
    """main without --target exits with error."""
    with pytest.raises(SystemExit):
        main([])


def test_main_never_logs_secret_values(capsys, tmp_path: Path):
    """main never prints secret values to stdout/stderr."""
    tmp_env = tmp_path / ".env.fly"
    tmp_env.write_text('export SUPER_SECRET="hunter2"\nexport ANOTHER="password123"\n')
    tmp_git = tmp_path / ".gitconfig"
    tmp_git.write_text("[user]\n  name = T\n")
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()

    saved_env = _mod["ENV_FLY"]
    saved_git = _mod["GITCONFIG"]
    saved_ssh = _mod["SSH_DIR"]
    try:
        _mod["ENV_FLY"] = tmp_env
        _mod["GITCONFIG"] = tmp_git
        _mod["SSH_DIR"] = ssh_dir
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
            ret = main(["--target", "user@host"])
    finally:
        _mod["ENV_FLY"] = saved_env
        _mod["GITCONFIG"] = saved_git
        _mod["SSH_DIR"] = saved_ssh

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "SUPER_SECRET" in output
    assert "ANOTHER" in output
    assert "hunter2" not in output
    assert "password123" not in output
