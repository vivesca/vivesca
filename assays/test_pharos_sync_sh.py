from __future__ import annotations

"""Tests for pharos-sync.sh — syncs Claude config to officina repo and remote machines."""

import subprocess
from pathlib import Path
import tempfile
import os

SCRIPT_PATH = Path.home() / "germline/effectors/pharos-sync.sh"


def run_script(args: list[str] = None, env: dict = None) -> subprocess.CompletedProcess:
    """Run pharos-sync.sh with optional args and custom env."""
    cmd = [str(SCRIPT_PATH)] + (args or [])
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, env=run_env)


# ── Help flag tests ─────────────────────────────────────────────────


def test_help_flag_exits_zero():
    """--help flag should exit with code 0."""
    result = run_script(["--help"])
    assert result.returncode == 0


def test_help_flag_shows_usage():
    """--help should show usage information."""
    result = run_script(["--help"])
    assert "Usage:" in result.stdout
    assert "pharos-sync" in result.stdout


def test_help_flag_short():
    """-h should work the same as --help."""
    result = run_script(["-h"])
    assert result.returncode == 0
    assert "Usage:" in result.stdout


# ── Default run (no args) tests ────────────────────────────────────────


def test_no_args_exits_zero(tmp_path):
    """Running with no arguments should exit 0 even with missing directories."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0


def test_no_args_no_stdout(tmp_path):
    """Default run with empty home produces no stdout."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    result = run_script(env={"HOME": str(fake_home)})
    assert result.stdout.strip() == ""


def test_script_is_executable():
    """pharos-sync.sh must have execute permission."""
    assert SCRIPT_PATH.exists()
    assert os.access(str(SCRIPT_PATH), os.X_OK)


# ── sync_file function tests ─────────────────────────────────────────────


def test_sync_file_creates_directory_structure(tmp_path):
    """sync_file should create destination directories if they don't exist."""
    # Let's test by sourcing the script and calling sync_file directly
    test_script = f"""
    source {SCRIPT_PATH}
    src="{tmp_path / 'src.txt'}"
    dst="{tmp_path / 'deep' / 'nested' / 'dst.txt'}"
    echo "test content" > "$src"
    sync_file "$src" "$dst"
    """
    result = subprocess.run(["bash", "-c", test_script], capture_output=True, text=True)
    assert result.returncode == 0
    assert (tmp_path / "deep" / "nested" / "dst.txt").exists()
    assert (tmp_path / "deep" / "nested" / "dst.txt").read_text() == "test content\n"


def test_sync_file_updates_changed_file(tmp_path):
    """sync_file should update destination if source has changed."""
    test_script = f"""
    source {SCRIPT_PATH}
    src="{tmp_path / 'src.txt'}"
    dst="{tmp_path / 'dst.txt'}"
    echo "old" > "$src"
    echo "old" > "$dst"
    # First sync - no change
    sync_file "$src" "$dst"
    # Now change source
    echo "new" > "$src"
    sync_file "$src" "$dst"
    """
    result = subprocess.run(["bash", "-c", test_script], capture_output=True, text=True)
    assert result.returncode == 0
    assert (tmp_path / "dst.txt").read_text() == "new\n"


def test_sync_file_returns_correct_exit_codes(tmp_path):
    """sync_file should return 0 when file updated, 1 otherwise."""
    test_script = f"""
    source {SCRIPT_PATH}
    src="{tmp_path / 'src.txt'}"
    dst="{tmp_path / 'dst.txt'}"

    # Test 1: src doesn't exist → should return 1
    sync_file "$src" "$dst" >/dev/null 2>&1
    echo "test1: $?"

    # Test 2: create src, dst doesn't exist → should return 0
    echo "content" > "$src"
    sync_file "$src" "$dst" >/dev/null 2>&1
    echo "test2: $?"

    # Test 3: src and dst same → should return 1
    sync_file "$src" "$dst" >/dev/null 2>&1
    echo "test3: $?"

    # Test4: src changed → should return 0
    echo "new content" > "$src"
    sync_file "$src" "$dst" >/dev/null 2>&1
    echo "test4: $?"
    """
    result = subprocess.run(["bash", "-c", test_script], capture_output=True, text=True)
    assert result.returncode == 0
    lines = result.stdout.strip().split("\n")
    assert lines[0] == "test1: 1"
    assert lines[1] == "test2: 0"
    assert lines[2] == "test3: 1"
    assert lines[3] == "test4: 0"
