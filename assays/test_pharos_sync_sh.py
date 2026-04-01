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


# ── sync_file output tests ────────────────────────────────────────────────


def test_sync_file_prints_updated_on_change(tmp_path):
    """sync_file should print 'updated: <basename>' when it copies."""
    test_script = f"""
    source {SCRIPT_PATH}
    src="{tmp_path / 'config.json'}"
    dst="{tmp_path / 'out' / 'config.json'}"
    echo '{{"key": "val"}}' > "$src"
    sync_file "$src" "$dst"
    """
    result = subprocess.run(["bash", "-c", test_script], capture_output=True, text=True)
    assert result.returncode == 0
    assert "updated: config.json" in result.stdout


def test_sync_file_no_output_when_identical(tmp_path):
    """sync_file should produce no output when src and dst are identical."""
    src = tmp_path / "same.txt"
    dst = tmp_path / "same_out.txt"
    src.write_text("identical\n")
    dst.write_text("identical\n")
    test_script = f"""
    source {SCRIPT_PATH}
    sync_file "{src}" "{dst}"
    """
    result = subprocess.run(["bash", "-c", test_script], capture_output=True, text=True)
    assert result.returncode == 1  # returns 1 (no change)
    assert result.stdout.strip() == ""


# ── Main block guard tests ────────────────────────────────────────────────


def test_main_block_not_run_when_sourced(tmp_path):
    """Sourcing the script should not trigger rsync/git operations."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    fake_claude.mkdir(parents=True)
    (fake_claude / "settings.json").write_text("{}")
    # Create a memory directory to potentially rsync
    mem_dir = fake_claude / "projects" / "-Users-terry" / "memory"
    mem_dir.mkdir(parents=True)
    (mem_dir / "test.md").write_text("hello")

    test_script = f"""
    export HOME="{fake_home}"
    source {SCRIPT_PATH}
    # If main block ran, it would have tried rsync/git
    echo "sourced_ok"
    """
    result = subprocess.run(["bash", "-c", test_script], capture_output=True, text=True)
    assert result.returncode == 0
    assert "sourced_ok" in result.stdout
    # Should NOT have synced memory or tried git
    assert "synced:" not in result.stdout


# ── Main block: settings sync + git commit tests ──────────────────────────


def test_main_syncs_settings_json(tmp_path):
    """Main block should sync settings.json to officina/claude/."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    # Init officina as git repo so git commands don't fail
    subprocess.run(["git", "init", str(officina)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(officina), "config", "user.email", "test@test.com"],
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(officina), "config", "user.name", "Test"],
        capture_output=True,
    )
    (fake_claude / "settings.json").write_text('{"theme": "dark"}')

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0
    synced = officina / "claude" / "settings.json"
    assert synced.exists()
    assert synced.read_text() == '{"theme": "dark"}'


def test_main_syncs_memory_directory(tmp_path):
    """Main block should rsync memory/ directory to officina/claude/memory/."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    mem_src = fake_claude / "projects" / "-Users-terry" / "memory"
    mem_src.mkdir(parents=True)
    (mem_src / "MEMORY.md").write_text("# Memory\nTest content")
    subprocess.run(["git", "init", str(officina)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(officina), "config", "user.email", "test@test.com"],
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(officina), "config", "user.name", "Test"],
        capture_output=True,
    )

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0
    mem_dst = officina / "claude" / "memory" / "MEMORY.md"
    assert mem_dst.exists()
    assert mem_dst.read_text() == "# Memory\nTest content"


def test_main_git_commits_on_change(tmp_path):
    """Main block should git commit in officina when files change."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    subprocess.run(["git", "init", str(officina)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(officina), "config", "user.email", "test@test.com"],
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(officina), "config", "user.name", "Test"],
        capture_output=True,
    )
    # Provide both memory dir and settings so git add can find both paths
    mem_src = fake_claude / "projects" / "-Users-terry" / "memory"
    mem_src.mkdir(parents=True)
    (mem_src / "MEMORY.md").write_text("# Memory")
    (fake_claude / "settings.json").write_text('{"first": true}')

    run_script(env={"HOME": str(fake_home)})
    # Check that a commit was created
    log = subprocess.run(
        ["git", "-C", str(officina), "log", "--oneline"],
        capture_output=True, text=True,
    )
    assert "sync: claude config" in log.stdout


def test_main_no_error_when_officina_missing(tmp_path):
    """Main block should not error if officina directory doesn't exist."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    fake_claude.mkdir(parents=True)
    (fake_claude / "settings.json").write_text("{}")

    result = run_script(env={"HOME": str(fake_home)})
    # Script should still exit 0 (set -uo pipefail but all commands have || true)
    assert result.returncode == 0


def test_main_no_error_when_claude_dir_missing(tmp_path):
    """Main block should not error if .claude directory doesn't exist."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / "officina").mkdir()

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0
