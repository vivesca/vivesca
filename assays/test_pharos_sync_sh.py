from __future__ import annotations

"""Tests for pharos-sync.sh — syncs Claude config to officina repo and remote machines."""

import os
import subprocess
from pathlib import Path

SCRIPT_PATH = Path.home() / "germline/effectors/pharos-sync.sh"


def run_script(
    args: list[str] | None = None, env: dict | None = None
) -> subprocess.CompletedProcess:
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
    src="{tmp_path / "src.txt"}"
    dst="{tmp_path / "deep" / "nested" / "dst.txt"}"
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
    src="{tmp_path / "src.txt"}"
    dst="{tmp_path / "dst.txt"}"
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
    src="{tmp_path / "src.txt"}"
    dst="{tmp_path / "dst.txt"}"

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
    src="{tmp_path / "config.json"}"
    dst="{tmp_path / "out" / "config.json"}"
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
        capture_output=True,
        text=True,
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


# ── sync_file edge cases ────────────────────────────────────────────────


def test_sync_file_missing_src(tmp_path):
    """sync_file returns 1 when source file doesn't exist."""
    src = tmp_path / "nonexistent.txt"
    dst = tmp_path / "dst.txt"
    test_script = f"""
    source {SCRIPT_PATH}
    sync_file "{src}" "{dst}"
    echo "exit: $?"
    """
    result = subprocess.run(["bash", "-c", test_script], capture_output=True, text=True)
    assert result.returncode == 0
    assert "exit: 1" in result.stdout
    assert not dst.exists()


def test_sync_file_overwrites_different_content(tmp_path):
    """sync_file should overwrite dst when src differs."""
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    src.write_text("version 1\n")
    dst.write_text("version 0\n")
    test_script = f"""
    source {SCRIPT_PATH}
    sync_file "{src}" "{dst}"
    """
    result = subprocess.run(["bash", "-c", test_script], capture_output=True, text=True)
    assert result.returncode == 0
    assert dst.read_text() == "version 1\n"


def test_sync_file_nested_dest_preserves_sibling(tmp_path):
    """sync_file creating a new file in a dir shouldn't disturb siblings."""
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()
    sibling = dst_dir / "other.txt"
    sibling.write_text("keep me\n")
    src = tmp_path / "new.txt"
    src.write_text("new file\n")
    test_script = f"""
    source {SCRIPT_PATH}
    sync_file "{src}" "{dst_dir / "new.txt"}"
    """
    result = subprocess.run(["bash", "-c", test_script], capture_output=True, text=True)
    assert result.returncode == 0
    assert sibling.read_text() == "keep me\n"
    assert (dst_dir / "new.txt").read_text() == "new file\n"


# ── Memory directory rsync tests ────────────────────────────────────────


def _init_officina(officina: Path) -> None:
    """Set up a minimal git repo in officina for commit tests."""
    subprocess.run(["git", "init", str(officina)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(officina), "config", "user.email", "test@test.com"],
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(officina), "config", "user.name", "Test"],
        capture_output=True,
    )


def test_memory_rsync_deletes_removed_files(tmp_path):
    """rsync --delete should remove files from dst that no longer exist in src."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    mem_src = fake_claude / "projects" / "-Users-terry" / "memory"
    mem_src.mkdir(parents=True)
    (mem_src / "keep.md").write_text("keep")
    (mem_src / "remove.md").write_text("remove")

    # First sync — rsync populates destination
    run_script(env={"HOME": str(fake_home)})
    mem_dst = officina / "claude" / "memory"
    assert (mem_dst / "keep.md").exists()
    assert (mem_dst / "remove.md").exists()

    # Commit first sync so second run starts clean
    subprocess.run(["git", "-C", str(officina), "add", "."], capture_output=True)
    subprocess.run(
        ["git", "-C", str(officina), "commit", "-m", "first sync"],
        capture_output=True,
    )

    # Remove file from source, re-sync
    (mem_src / "remove.md").unlink()
    run_script(env={"HOME": str(fake_home)})
    assert not (mem_dst / "remove.md").exists()
    assert (mem_dst / "keep.md").exists()


def test_memory_rsync_preserves_subdirs(tmp_path):
    """rsync -a should preserve directory structure inside memory/."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    mem_src = fake_claude / "projects" / "-Users-terry" / "memory"
    subdir = mem_src / "subdir"
    subdir.mkdir(parents=True)
    (subdir / "nested.md").write_text("nested content")
    (mem_src / "top.md").write_text("top level")

    run_script(env={"HOME": str(fake_home)})
    assert (officina / "claude" / "memory" / "subdir" / "nested.md").exists()
    assert (officina / "claude" / "memory" / "top.md").exists()


def test_memory_sync_prints_synced_message(tmp_path):
    """Memory directory sync should print 'synced: memory/'."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    mem_src = fake_claude / "projects" / "-Users-terry" / "memory"
    mem_src.mkdir(parents=True)
    (mem_src / "MEMORY.md").write_text("data")

    result = run_script(env={"HOME": str(fake_home)})
    assert "synced: memory/" in result.stdout


def test_empty_memory_dir_no_crash(tmp_path):
    """Empty memory directory (exists but no files) should not crash."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    mem_src = fake_claude / "projects" / "-Users-terry" / "memory"
    mem_src.mkdir(parents=True)

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0


# ── changed guard / git tests ──────────────────────────────────────────


def test_no_git_commit_when_nothing_changed(tmp_path):
    """If no files changed, no git commit should be made."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    # Settings exist but already synced
    settings_content = '{"unchanged": true}'
    (fake_claude / "settings.json").write_text(settings_content)
    (officina / "claude").mkdir()
    (officina / "claude" / "settings.json").write_text(settings_content)
    # Make initial commit so git log isn't empty
    subprocess.run(["git", "-C", str(officina), "add", "."], capture_output=True)
    subprocess.run(
        ["git", "-C", str(officina), "commit", "-m", "initial"],
        capture_output=True,
    )

    run_script(env={"HOME": str(fake_home)})
    log = subprocess.run(
        ["git", "-C", str(officina), "log", "--oneline"],
        capture_output=True,
        text=True,
    )
    # Only the initial commit should exist, no "sync:" commit
    assert "sync:" not in log.stdout


def test_git_commit_message_includes_date(tmp_path):
    """Commit message should contain today's date in YYYY-MM-DD format."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    # Provide memory dir so changed=true is set (sync_file alone may not
    # trigger the changed flag since it uses a separate variable path).
    mem_src = fake_claude / "projects" / "-Users-terry" / "memory"
    mem_src.mkdir(parents=True)
    (mem_src / "MEMORY.md").write_text("test")
    (fake_claude / "settings.json").write_text('{"new": true}')

    run_script(env={"HOME": str(fake_home)})
    log = subprocess.run(
        ["git", "-C", str(officina), "log", "--format=%s"],
        capture_output=True,
        text=True,
    )
    from datetime import date

    today = date.today().isoformat()[:10]  # YYYY-MM-DD
    assert today in log.stdout


def test_settings_not_copied_when_identical(tmp_path):
    """settings.json already matching in officina should not trigger changed."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    content = '{"already": "synced"}'
    (fake_claude / "settings.json").write_text(content)
    (officina / "claude").mkdir()
    (officina / "claude" / "settings.json").write_text(content)
    # Make initial commit
    subprocess.run(["git", "-C", str(officina), "add", "."], capture_output=True)
    subprocess.run(
        ["git", "-C", str(officina), "commit", "-m", "initial"],
        capture_output=True,
    )

    result = run_script(env={"HOME": str(fake_home)})
    assert "updated: settings.json" not in result.stdout


def test_changed_accumulates_across_syncs(tmp_path):
    """Both memory and settings changes should set changed=true."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    # Use the full memory path that the script expects
    mem_src = fake_claude / "projects" / "-Users-terry" / "memory"
    mem_src.mkdir(parents=True)
    (mem_src / "MEMORY.md").write_text("data")
    (fake_claude / "settings.json").write_text('{"x": 1}')

    result = run_script(env={"HOME": str(fake_home)})
    assert "synced: memory/" in result.stdout
    assert "updated: settings.json" in result.stdout


def test_no_memory_dir_no_synced_output(tmp_path):
    """If memory source dir doesn't exist, no 'synced: memory/' output."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)
    (fake_claude / "settings.json").write_text('{"only": "settings"}')

    result = run_script(env={"HOME": str(fake_home)})
    assert "synced: memory/" not in result.stdout


# ── Remote sync graceful-failure tests ─────────────────────────────────


def test_credentials_json_no_crash_when_present(tmp_path):
    """Script should not crash when .credentials.json exists but remotes are unreachable."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    (fake_claude / "settings.json").write_text("{}")
    (fake_claude / ".credentials.json").write_text('{"key": "val"}')

    result = run_script(env={"HOME": str(fake_home)})
    # flyctl/scp will fail (no remotes) but script should exit 0
    assert result.returncode == 0


def test_zshenv_no_crash_when_present(tmp_path):
    """Script should not crash when .zshenv exists but pharos is unreachable."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    (fake_claude / "settings.json").write_text("{}")
    (fake_home / ".zshenv").write_text("export FOO=bar\n")

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0


def test_zshenv_tpl_no_crash_when_present(tmp_path):
    """Script should not crash when .zshenv.tpl exists but pharos is unreachable."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    (fake_claude / "settings.json").write_text("{}")
    (fake_home / ".zshenv.tpl").write_text("export FOO={{BAR}}\n")

    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0


# ── git push graceful-failure tests ────────────────────────────────────


def test_git_push_failure_no_crash(tmp_path):
    """git push to a bare/missing remote should not crash the script."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    mem_src = fake_claude / "projects" / "-Users-terry" / "memory"
    mem_src.mkdir(parents=True)
    (mem_src / "MEMORY.md").write_text("data")
    (fake_claude / "settings.json").write_text('{"push": true}')

    # No remote configured → git push will fail, but script should exit 0
    result = run_script(env={"HOME": str(fake_home)})
    assert result.returncode == 0


# ── sync_file with special content ─────────────────────────────────────


def test_sync_file_handles_binary_content(tmp_path):
    """sync_file should correctly copy files with binary/null content."""
    src = tmp_path / "binary.bin"
    dst = tmp_path / "out" / "binary.bin"
    src.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
    test_script = f"""
    source {SCRIPT_PATH}
    sync_file "{src}" "{dst}"
    """
    result = subprocess.run(["bash", "-c", test_script], capture_output=True, text=True)
    assert result.returncode == 0
    assert dst.read_bytes() == b"\x00\x01\x02\xff\xfe\xfd"


def test_sync_file_handles_empty_file(tmp_path):
    """sync_file should handle empty source files correctly."""
    src = tmp_path / "empty.txt"
    dst = tmp_path / "out" / "empty.txt"
    src.write_bytes(b"")
    test_script = f"""
    source {SCRIPT_PATH}
    sync_file "{src}" "{dst}"
    """
    result = subprocess.run(["bash", "-c", test_script], capture_output=True, text=True)
    assert result.returncode == 0
    assert dst.read_bytes() == b""
    assert "updated: empty.txt" in result.stdout


# ── Multiple memory files ──────────────────────────────────────────────


def test_multiple_memory_files_all_synced(tmp_path):
    """All files in memory directory should be synced, not just one."""
    fake_home = tmp_path / "home"
    fake_claude = fake_home / ".claude"
    officina = fake_home / "officina"
    fake_claude.mkdir(parents=True)
    officina.mkdir(parents=True)
    _init_officina(officina)

    mem_src = fake_claude / "projects" / "-Users-terry" / "memory"
    mem_src.mkdir(parents=True)
    (mem_src / "MEMORY.md").write_text("mem")
    (mem_src / "NOTES.md").write_text("notes")
    (mem_src / "TODO.md").write_text("todos")

    run_script(env={"HOME": str(fake_home)})
    mem_dst = officina / "claude" / "memory"
    assert (mem_dst / "MEMORY.md").exists()
    assert (mem_dst / "NOTES.md").exists()
    assert (mem_dst / "TODO.md").exists()
    assert (mem_dst / "MEMORY.md").read_text() == "mem"
    assert (mem_dst / "NOTES.md").read_text() == "notes"
    assert (mem_dst / "TODO.md").read_text() == "todos"
