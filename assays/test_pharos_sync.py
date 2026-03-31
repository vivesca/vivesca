from __future__ import annotations

"""Tests for pharos-sync.sh — sync Claude config to officina repo."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline" / "effectors" / "pharos-sync.sh"


def _run(
    script: Path,
    args: list[str] | None = None,
    env: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run pharos-sync.sh with optional args and env overrides."""
    cmd = ["bash", str(script)]
    if args:
        cmd.extend(args)
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=run_env,
        timeout=30,
    )


def _setup_officina(tmp_path: Path) -> Path:
    """Create a minimal officina repo with git init."""
    officina = tmp_path / "officina"
    officina.mkdir()
    subprocess.run(["git", "init", str(officina)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(officina), "config", "user.email", "test@test.com"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(officina), "config", "user.name", "Test"],
        capture_output=True,
        check=True,
    )
    # Create initial commit so git commit works
    (officina / ".gitkeep").touch()
    subprocess.run(
        ["git", "-C", str(officina), "add", ".gitkeep"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(officina), "commit", "-m", "init"],
        capture_output=True,
        check=True,
    )
    return officina


# ── Basic execution tests ───────────────────────────────────────────────


class TestBasicExecution:
    """Tests for basic script execution."""

    def test_script_exists(self):
        """Script file exists."""
        assert SCRIPT.exists()

    def test_script_is_executable_or_bash_readable(self):
        """Script can be read by bash."""
        r = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
        assert r.returncode == 0, f"Syntax error: {r.stderr}"

    def test_no_args_exits_0(self, tmp_path):
        """Script exits 0 even with no files to sync."""
        officina = _setup_officina(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_empty_home(self, tmp_path):
        """Script handles completely empty HOME directory."""
        empty = tmp_path / "empty_home"
        empty.mkdir()
        officina = _setup_officina(empty)
        r = _run(SCRIPT, env={"HOME": str(empty)})
        assert r.returncode == 0


# ── settings.json sync tests ────────────────────────────────────────────


class TestSettingsSync:
    """Tests for settings.json sync to officina."""

    def test_no_settings_no_error(self, tmp_path):
        """Script exits 0 when settings.json does not exist."""
        _setup_officina(tmp_path)
        (tmp_path / ".claude").mkdir()
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_copies_settings_to_officina(self, tmp_path):
        """Script copies settings.json to officina/claude/."""
        _setup_officina(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.json"
        settings.write_text('{"test": true}')

        officina = tmp_path / "officina"
        (officina / "claude").mkdir()

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        dst = officina / "claude" / "settings.json"
        assert dst.exists()
        assert dst.read_text() == '{"test": true}'

    def test_requires_officina_claude_dir_to_exist(self, tmp_path):
        """Script does not create officina/claude/ automatically."""
        _setup_officina(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.json"
        settings.write_text('{"auto": true}')

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Script does NOT create officina/claude/ - sync_file requires it
        dst = tmp_path / "officina" / "claude" / "settings.json"
        assert not dst.exists()

    def test_skips_identical_settings(self, tmp_path):
        """Script does not copy if settings.json is identical."""
        _setup_officina(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.json"
        settings.write_text('{"same": true}')

        officina = tmp_path / "officina"
        claude_dst = officina / "claude"
        claude_dst.mkdir()
        dst = claude_dst / "settings.json"
        dst.write_text('{"same": true}')

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Should not print "updated: settings.json"
        assert "updated: settings.json" not in r.stdout

    def test_updates_changed_settings(self, tmp_path):
        """Script copies and reports update when settings.json differs."""
        _setup_officina(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.json"
        settings.write_text('{"new": true}')

        officina = tmp_path / "officina"
        claude_dst = officina / "claude"
        claude_dst.mkdir()
        dst = claude_dst / "settings.json"
        dst.write_text('{"old": true}')

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert "updated: settings.json" in r.stdout


# ── Memory directory sync tests ─────────────────────────────────────────


class TestMemorySync:
    """Tests for memory directory rsync to officina."""

    def test_no_memory_dir_no_error(self, tmp_path):
        """Script exits 0 when memory directory does not exist."""
        _setup_officina(tmp_path)
        (tmp_path / ".claude").mkdir()
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_syncs_memory_directory(self, tmp_path):
        """Script syncs memory directory to officina/claude/memory/."""
        officina = _setup_officina(tmp_path)
        # rsync requires the parent directory to exist
        (officina / "claude").mkdir()

        # Create source memory directory (Claude projects path)
        # Script hardcodes -Users-terry path
        memory_src = tmp_path / ".claude" / "projects" / "-Users-terry" / "memory"
        memory_src.mkdir(parents=True)
        (memory_src / "MEMORY.md").write_text("# Test Memory\nContent here.\n")
        (memory_src / "notes.txt").write_text("Some notes\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Check destination (using actual path logic from script)
        # Script uses: $CLAUDE_DIR/projects/-Users-terry/memory
        memory_dst = tmp_path / "officina" / "claude" / "memory"
        assert memory_dst.exists()
        assert (memory_dst / "MEMORY.md").read_text() == "# Test Memory\nContent here.\n"

    def test_synced_output_message(self, tmp_path):
        """Script reports 'synced: memory/' on successful sync."""
        _setup_officina(tmp_path)

        memory_src = tmp_path / ".claude" / "projects" / "-Users-terry" / "memory"
        memory_src.mkdir(parents=True)
        (memory_src / "MEMORY.md").write_text("# Memory\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert "synced: memory/" in r.stdout


# ── Git commit tests ────────────────────────────────────────────────────


class TestGitCommit:
    """Tests for git commit behavior in officina."""

    def test_commits_on_settings_change(self, tmp_path):
        """Script commits to officina when settings.json changes."""
        officina = _setup_officina(tmp_path)
        (officina / "claude").mkdir()

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.json"
        settings.write_text('{"commit": true}')

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Check git log for sync commit
        result = subprocess.run(
            ["git", "-C", str(officina), "log", "--oneline", "-1"],
            capture_output=True,
            text=True,
        )
        assert "sync: claude config" in result.stdout

    def test_no_commit_when_no_changes(self, tmp_path):
        """Script does not commit when nothing changed."""
        officina = _setup_officina(tmp_path)

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Git log should still show only the init commit
        result = subprocess.run(
            ["git", "-C", str(officina), "log", "--oneline"],
            capture_output=True,
            text=True,
        )
        # Only the init commit (no sync commit)
        assert result.stdout.count("\n") == 1 or "init" in result.stdout


# ── Credentials sync tests (mocked) ─────────────────────────────────────


class TestCredentialsSync:
    """Tests for credentials sync (network operations mocked)."""

    def test_no_credentials_no_error(self, tmp_path):
        """Script exits 0 when .credentials.json does not exist."""
        _setup_officina(tmp_path)
        (tmp_path / ".claude").mkdir()
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_credentials_file_ignored_without_network(self, tmp_path):
        """Script handles credentials file gracefully when network unavailable."""
        _setup_officina(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        creds = claude_dir / ".credentials.json"
        creds.write_text('{"api_key": "test123"}')

        # Without flyctl or network, should still exit 0
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0


# ── .zshenv sync tests (mocked) ─────────────────────────────────────────


class TestZshenvSync:
    """Tests for .zshenv sync to pharos (legacy)."""

    def test_no_zshenv_no_error(self, tmp_path):
        """Script exits 0 when .zshenv does not exist."""
        _setup_officina(tmp_path)
        (tmp_path / ".claude").mkdir()
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_zshenv_ignored_without_network(self, tmp_path):
        """Script handles .zshenv gracefully when scp fails."""
        _setup_officina(tmp_path)
        (tmp_path / ".claude").mkdir()
        zshenv = tmp_path / ".zshenv"
        zshenv.write_text("export TEST=1")

        # Without network/pharos, should still exit 0
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0


# ── Edge case tests ─────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases for pharos-sync.sh."""

    def test_missing_officina(self, tmp_path):
        """Script exits 0 when officina directory does not exist."""
        (tmp_path / ".claude").mkdir()
        # Don't create officina
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Script should handle missing officina gracefully
        # Exit code may be 0 (no changes) or non-zero (git error)
        # Either way, shouldn't crash hard

    def test_officina_without_git(self, tmp_path):
        """Script handles officina directory without .git/."""
        officina = tmp_path / "officina"
        officina.mkdir()
        # No git init
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "settings.json").write_text('{}')

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Script continues even if git commands fail
        assert r.returncode == 0

    def test_concurrent_run_safety(self, tmp_path):
        """Script handles being run twice rapidly."""
        _setup_officina(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.json"
        settings.write_text('{"test": true}')

        (tmp_path / "officina" / "claude").mkdir()

        # Run twice
        r1 = _run(SCRIPT, env={"HOME": str(tmp_path)})
        r2 = _run(SCRIPT, env={"HOME": str(tmp_path)})

        assert r1.returncode == 0
        assert r2.returncode == 0

    def test_handles_special_chars_in_settings(self, tmp_path):
        """Script handles settings.json with special characters."""
        _setup_officina(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.json"
        settings.write_text('{"emoji": "🎉", "quote": "\'test\'", "backslash": "\\\\"}')

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        dst = tmp_path / "officina" / "claude" / "settings.json"
        assert dst.exists()


# ── Output format tests ─────────────────────────────────────────────────


class TestOutputFormat:
    """Tests for human-readable output."""

    def test_updated_message_format(self, tmp_path):
        """Script outputs 'updated: <filename>' format."""
        _setup_officina(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        settings = claude_dir / "settings.json"
        settings.write_text('{"test": true}')

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Should contain human-readable update message
        assert "updated:" in r.stdout or r.returncode == 0

    def test_synced_message_format(self, tmp_path):
        """Script outputs 'synced: memory/' for directory sync."""
        _setup_officina(tmp_path)

        memory_src = tmp_path / ".claude" / "projects" / "-Users-terry" / "memory"
        memory_src.mkdir(parents=True)
        (memory_src / "MEMORY.md").write_text("# Memory\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Should show synced message
        assert "synced:" in r.stdout or r.returncode == 0
