from __future__ import annotations

"""Tests for effectors/pharos-sync.sh — sync Claude config to officina repo.

Uses subprocess.run with mocked network commands (flyctl, scp, git).
Uses tempfile.TemporaryDirectory instead of pytest tmp_path to avoid
tmp_path_retention_policy='none' race conditions in large test suites.
"""

import os
import stat
import subprocess
import tempfile
import uuid
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-sync.sh"


# ── helpers ─────────────────────────────────────────────────────────────


@pytest.fixture
def work_dir():
    """Isolated temp directory unaffected by pytest tmp_path retention policy."""
    with tempfile.TemporaryDirectory(prefix="pharos_sync_") as d:
        yield Path(d)


def _run(
    work_dir: Path,
    recordings: dict[str, Path] | None = None,
) -> subprocess.CompletedProcess:
    """Run pharos-sync.sh with HOME=work_dir and mocked network commands."""
    env = os.environ.copy()
    env["HOME"] = str(work_dir)

    mock_dir = work_dir / "mock-bin"
    mock_dir.mkdir(exist_ok=True)

    for name, rec_file in (recordings or {}).items():
        script = mock_dir / name
        script.write_text(
            "#!/bin/bash\n"
            f'printf "%s\\n" "$@" >> {rec_file}\n'
            '# Fail if source file (first non-flag arg) does not exist\n'
            'src=""\n'
            'for a in "$@"; do\n'
            '  case "$a" in\n'
            '    -*) continue ;;\n'
            '    *)\n'
            '      if [ -z "$src" ]; then src="$a"; fi ;;\n'
            '  esac\n'
            'done\n'
            'if [ -n "$src" ] && [ ! -f "$src" ]; then exit 1; fi\n'
            "exit 0\n"
        )
        script.chmod(script.stat().st_mode | stat.S_IEXEC)

    env["PATH"] = str(mock_dir) + os.pathsep + env.get("PATH", "")

    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )


def _setup(work_dir: Path) -> tuple[Path, Path]:
    """Create .claude and officina dirs. Returns (claude_dir, officina)."""
    claude = work_dir / ".claude"
    off = work_dir / "officina"
    claude.mkdir(exist_ok=True)
    off.mkdir(exist_ok=True)
    (off / "claude").mkdir(exist_ok=True)
    return claude, off


# ── sync_file behaviour (observed via settings.json) ────────────────────


class TestSyncFile:
    """Test sync_file() observed through settings.json sync."""

    def test_no_source_skips(self, work_dir):
        """No settings.json source -> no 'updated:' message."""
        _setup(work_dir)
        r = _run(work_dir)
        assert "updated: settings.json" not in r.stdout

    def test_dest_missing_copies(self, work_dir):
        """Source exists but dest missing -> copies and prints 'updated:'."""
        claude, _ = _setup(work_dir)
        (claude / "settings.json").write_text('{"key": "value"}')
        r = _run(work_dir)
        assert "updated: settings.json" in r.stdout

    def test_files_differ_copies(self, work_dir):
        """Source differs from dest -> copies and prints 'updated:'."""
        claude, off = _setup(work_dir)
        (claude / "settings.json").write_text('{"key": "new"}')
        (off / "claude" / "settings.json").write_text('{"key": "old"}')
        r = _run(work_dir)
        assert "updated: settings.json" in r.stdout

    def test_identical_files_skips(self, work_dir):
        """Source and dest identical -> no 'updated:' message."""
        claude, off = _setup(work_dir)
        content = '{"key": "same"}'
        (claude / "settings.json").write_text(content)
        (off / "claude" / "settings.json").write_text(content)
        r = _run(work_dir)
        assert "updated: settings.json" not in r.stdout


# ── memory directory sync ───────────────────────────────────────────────


class TestMemorySync:
    def test_no_memory_dir_skips(self, work_dir):
        """No memory source dir -> no 'synced: memory/' message."""
        _setup(work_dir)
        r = _run(work_dir)
        assert "synced: memory/" not in r.stdout

    def test_memory_dir_syncs(self, work_dir):
        """Memory dir exists -> rsync runs, 'synced: memory/' printed."""
        claude, _ = _setup(work_dir)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "test.md").write_text("hello")
        r = _run(work_dir)
        assert "synced: memory/" in r.stdout

    def test_memory_copies_files(self, work_dir):
        """rsync actually copies files into officina."""
        claude, off = _setup(work_dir)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "notes.md").write_text("world")
        _run(work_dir)
        mem_dst = off / "claude" / "memory"
        assert (mem_dst / "notes.md").read_text() == "world"

    def test_rsync_delete_removes_stale_files(self, work_dir):
        """rsync --delete removes files from dest that no longer exist in src."""
        claude, off = _setup(work_dir)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        mem_dst = off / "claude" / "memory"
        mem_dst.mkdir(parents=True)
        (mem_dst / "old.md").write_text("stale")
        _run(work_dir)
        assert not (mem_dst / "old.md").exists()

    def test_memory_preserves_subdirs(self, work_dir):
        """rsync copies nested directory structure."""
        claude, off = _setup(work_dir)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        sub = mem_src / "deep" / "nested"
        sub.mkdir(parents=True)
        (sub / "file.md").write_text("nested content")
        _run(work_dir)
        mem_dst = off / "claude" / "memory"
        assert (mem_dst / "deep" / "nested" / "file.md").read_text() == "nested content"

    def test_empty_memory_dir_syncs(self, work_dir):
        """Empty memory source dir -> synced message still printed."""
        claude, _ = _setup(work_dir)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        r = _run(work_dir)
        assert "synced: memory/" in r.stdout

    def test_syncs_multiple_memory_files(self, work_dir):
        """Multiple files in memory dir all get synced."""
        claude, off = _setup(work_dir)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "a.md").write_text("file a")
        (mem_src / "b.md").write_text("file b")
        (mem_src / "c.md").write_text("file c")
        _run(work_dir)
        mem_dst = off / "claude" / "memory"
        assert (mem_dst / "a.md").read_text() == "file a"
        assert (mem_dst / "b.md").read_text() == "file b"
        assert (mem_dst / "c.md").read_text() == "file c"


# ── credentials push ────────────────────────────────────────────────────


class TestCredentialsPush:
    def test_no_credentials_no_flyctl(self, work_dir):
        """No .credentials.json -> flyctl not called."""
        _setup(work_dir)
        rec = work_dir / "flyctl.log"
        _run(work_dir, recordings={"flyctl": rec})
        assert not rec.exists()

    def test_credentials_calls_flyctl(self, work_dir):
        """.credentials.json exists -> flyctl called with -a lucerna."""
        claude, _ = _setup(work_dir)
        (claude / ".credentials.json").write_text('{"creds": true}')
        rec = work_dir / "flyctl.log"
        _run(work_dir, recordings={"flyctl": rec})
        assert rec.exists()
        assert "lucerna" in rec.read_text()

    def test_no_credentials_no_scp_to_macbooks(self, work_dir):
        """No .credentials.json -> no 'updated: .credentials.json → m2/m3'."""
        _setup(work_dir)
        r = _run(work_dir)
        assert "updated: .credentials.json → m2" not in r.stdout
        assert "updated: .credentials.json → m3" not in r.stdout

    def test_credentials_scp_to_macbooks(self, work_dir):
        """.credentials.json exists -> scp called for m2 and m3."""
        claude, _ = _setup(work_dir)
        (claude / ".credentials.json").write_text('{"creds": true}')
        rec = work_dir / "scp.log"
        _run(work_dir, recordings={"scp": rec})
        assert rec.exists()
        text = rec.read_text()
        assert "m2" in text
        assert "m3" in text

    def test_flyctl_receives_credential_content(self, work_dir):
        """flyctl ssh console receives the credential file content."""
        claude, _ = _setup(work_dir)
        (claude / ".credentials.json").write_text('{"apikey": "secret123"}')
        rec = work_dir / "flyctl.log"
        _run(work_dir, recordings={"flyctl": rec})
        log = rec.read_text()
        assert "secret123" in log

    def test_scp_credential_path_correct(self, work_dir):
        """scp copies from .claude/.credentials.json to host:~/.claude/.credentials.json."""
        claude, _ = _setup(work_dir)
        (claude / ".credentials.json").write_text('{"creds": true}')
        rec = work_dir / "scp.log"
        _run(work_dir, recordings={"scp": rec})
        log = rec.read_text()
        assert "m2" in log
        assert "m3" in log
        assert ".credentials.json" in log


# ── .zshenv push ────────────────────────────────────────────────────────


class TestZshenvPush:
    def test_no_zshenv_no_scp(self, work_dir):
        """No .zshenv -> scp not called for .zshenv to pharos."""
        _setup(work_dir)
        rec = work_dir / "scp.log"
        _run(work_dir, recordings={"scp": rec})
        if rec.exists():
            assert ".zshenv" not in rec.read_text()

    def test_zshenv_scp_to_pharos(self, work_dir):
        """.zshenv exists -> scp called with pharos host."""
        _setup(work_dir)
        (work_dir / ".zshenv").write_text("export FOO=bar")
        rec = work_dir / "scp.log"
        _run(work_dir, recordings={"scp": rec})
        assert rec.exists()
        assert "pharos" in rec.read_text()

    def test_zshenv_tpl_scp_to_pharos(self, work_dir):
        """.zshenv.tpl exists -> scp called with pharos host."""
        _setup(work_dir)
        (work_dir / ".zshenv.tpl").write_text("export FOO={{BAR}}")
        rec = work_dir / "scp.log"
        _run(work_dir, recordings={"scp": rec})
        assert rec.exists()
        assert "pharos" in rec.read_text()

    def test_both_zshenv_files(self, work_dir):
        """Both .zshenv and .zshenv.tpl -> two scp calls to pharos."""
        _setup(work_dir)
        (work_dir / ".zshenv").write_text("export A=1")
        (work_dir / ".zshenv.tpl").write_text("export A={{B}}")
        rec = work_dir / "scp.log"
        _run(work_dir, recordings={"scp": rec})
        log = rec.read_text()
        pharos_lines = [l for l in log.splitlines() if "pharos" in l]
        assert len(pharos_lines) >= 2


# ── git commit / push ──────────────────────────────────────────────────


class TestGitCommit:
    def test_no_changes_no_git(self, work_dir):
        """Nothing changed -> git not called."""
        _setup(work_dir)
        rec = work_dir / "git.log"
        _run(work_dir, recordings={"git": rec})
        assert not rec.exists()

    def test_settings_changed_triggers_git(self, work_dir):
        """settings.json changed -> git add + commit + push called."""
        claude, _ = _setup(work_dir)
        (claude / "settings.json").write_text('{"key": "val"}')
        rec = work_dir / "git.log"
        _run(work_dir, recordings={"git": rec})
        assert rec.exists()
        text = rec.read_text()
        assert "add" in text
        assert "commit" in text
        assert "push" in text

    def test_memory_changed_triggers_git(self, work_dir):
        """Memory dir sync sets changed=true -> git called."""
        claude, _ = _setup(work_dir)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "test.md").write_text("content")
        rec = work_dir / "git.log"
        _run(work_dir, recordings={"git": rec})
        assert rec.exists()
        assert "add" in rec.read_text()


# ── changed flag logic ─────────────────────────────────────────────────


class TestChangedFlagLogic:
    def test_identical_settings_no_git(self, work_dir):
        """settings.json identical -> changed stays false -> no git."""
        claude, off = _setup(work_dir)
        content = '{"k": "v"}'
        (claude / "settings.json").write_text(content)
        (off / "claude" / "settings.json").write_text(content)
        rec = work_dir / "git.log"
        _run(work_dir, recordings={"git": rec})
        assert not rec.exists()

    def test_memory_only_triggers_git(self, work_dir):
        """Memory sync (without settings change) triggers git."""
        claude, _ = _setup(work_dir)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "data.md").write_text("data")
        rec = work_dir / "git.log"
        _run(work_dir, recordings={"git": rec})
        assert rec.exists()

    def test_both_changed_triggers_git(self, work_dir):
        """Both memory and settings changed -> git triggered."""
        claude, off = _setup(work_dir)
        (claude / "settings.json").write_text('{"k": "new"}')
        (off / "claude" / "settings.json").write_text('{"k": "old"}')
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "a.md").write_text("a")
        rec = work_dir / "git.log"
        _run(work_dir, recordings={"git": rec})
        assert rec.exists()
        log = rec.read_text()
        assert "add" in log
        assert "commit" in log
        assert "push" in log


# ── git commit message ─────────────────────────────────────────────────


class TestGitCommitMessage:
    def test_commit_message_contains_sync_prefix(self, work_dir):
        """git commit message starts with 'sync: claude config'."""
        claude, _ = _setup(work_dir)
        (claude / "settings.json").write_text('{"key": "val"}')
        rec = work_dir / "git.log"
        _run(work_dir, recordings={"git": rec})
        log = rec.read_text()
        assert "sync: claude config" in log

    def test_git_adds_correct_paths(self, work_dir):
        """git add targets claude/settings.json."""
        claude, _ = _setup(work_dir)
        (claude / "settings.json").write_text('{"key": "val"}')
        rec = work_dir / "git.log"
        _run(work_dir, recordings={"git": rec})
        log = rec.read_text()
        assert "claude/settings.json" in log


# ── set -u robustness ──────────────────────────────────────────────────


class TestSetU:
    def test_handles_empty_home_gracefully(self, work_dir):
        """Script handles missing directories without crash (set -u safe)."""
        _setup(work_dir)
        r = _run(work_dir)
        assert r.returncode == 0


# ── exit codes ──────────────────────────────────────────────────────────


class TestExitCode:
    def test_exits_zero_no_changes(self, work_dir):
        """Script exits 0 when nothing to sync."""
        _setup(work_dir)
        r = _run(work_dir)
        assert r.returncode == 0

    def test_exits_zero_with_changes(self, work_dir):
        """Script exits 0 even when changes are synced."""
        claude, _ = _setup(work_dir)
        (claude / "settings.json").write_text('{"key": "val"}')
        r = _run(work_dir)
        assert r.returncode == 0

    def test_stderr_empty_on_success(self, work_dir):
        """Successful run produces no stderr."""
        _setup(work_dir)
        r = _run(work_dir)
        assert r.stderr == ""
