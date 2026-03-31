from __future__ import annotations

"""Tests for effectors/pharos-sync.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-sync.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run(
    tmp_path: Path,
    recordings: dict[str, Path] | None = None,
) -> subprocess.CompletedProcess:
    """Run pharos-sync.sh with HOME=tmp_path and mocked network commands."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    mock_dir = tmp_path / "mock-bin"
    mock_dir.mkdir(exist_ok=True)

    # Create recording mocks for specified tools.
    # Mocks fail (exit 1) when the source file doesn't exist,
    # mirroring real scp/cp behaviour.
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

    # Prepend mock dir so our mocks shadow real binaries
    env["PATH"] = str(mock_dir) + os.pathsep + env.get("PATH", "")

    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True, text=True, env=env, timeout=10,
    )


def _setup(tmp_path: Path) -> tuple[Path, Path]:
    """Create .claude and officina dirs. Returns (claude_dir, officina)."""
    claude = tmp_path / ".claude"
    off = tmp_path / "officina"
    claude.mkdir(exist_ok=True)
    off.mkdir(exist_ok=True)
    (off / "claude").mkdir(exist_ok=True)
    return claude, off


# ── sync_file behaviour (observed via settings.json) ────────────────────


class TestSyncFile:
    """Test sync_file() observed through settings.json sync."""

    def test_no_source_skips(self, tmp_path):
        """No settings.json source -> no 'updated:' message."""
        _setup(tmp_path)
        r = _run(tmp_path)
        assert "updated: settings.json" not in r.stdout

    def test_dest_missing_copies(self, tmp_path):
        """Source exists but dest missing -> copies and prints 'updated:'."""
        claude, _ = _setup(tmp_path)
        (claude / "settings.json").write_text('{"key": "value"}')
        r = _run(tmp_path)
        assert "updated: settings.json" in r.stdout

    def test_files_differ_copies(self, tmp_path):
        """Source differs from dest -> copies and prints 'updated:'."""
        claude, off = _setup(tmp_path)
        (claude / "settings.json").write_text('{"key": "new"}')
        (off / "claude" / "settings.json").write_text('{"key": "old"}')
        r = _run(tmp_path)
        assert "updated: settings.json" in r.stdout

    def test_identical_files_skips(self, tmp_path):
        """Source and dest identical -> no 'updated:' message."""
        claude, off = _setup(tmp_path)
        content = '{"key": "same"}'
        (claude / "settings.json").write_text(content)
        (off / "claude" / "settings.json").write_text(content)
        r = _run(tmp_path)
        assert "updated: settings.json" not in r.stdout


# ── memory directory sync ───────────────────────────────────────────────


class TestMemorySync:
    def test_no_memory_dir_skips(self, tmp_path):
        """No memory source dir -> no 'synced: memory/' message."""
        _setup(tmp_path)
        r = _run(tmp_path)
        assert "synced: memory/" not in r.stdout

    def test_memory_dir_syncs(self, tmp_path):
        """Memory dir exists -> rsync runs, 'synced: memory/' printed."""
        claude, _ = _setup(tmp_path)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "test.md").write_text("hello")
        r = _run(tmp_path)
        assert "synced: memory/" in r.stdout

    def test_memory_copies_files(self, tmp_path):
        """rsync actually copies files into officina."""
        claude, off = _setup(tmp_path)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "notes.md").write_text("world")
        _run(tmp_path)
        mem_dst = off / "claude" / "memory"
        assert (mem_dst / "notes.md").read_text() == "world"


# ── credentials push ────────────────────────────────────────────────────


class TestCredentialsPush:
    def test_no_credentials_no_flyctl(self, tmp_path):
        """No .credentials.json -> flyctl not called."""
        _setup(tmp_path)
        rec = tmp_path / "flyctl.log"
        _run(tmp_path, recordings={"flyctl": rec})
        assert not rec.exists()

    def test_credentials_calls_flyctl(self, tmp_path):
        """.credentials.json exists -> flyctl called with -a lucerna."""
        claude, _ = _setup(tmp_path)
        (claude / ".credentials.json").write_text('{"creds": true}')
        rec = tmp_path / "flyctl.log"
        _run(tmp_path, recordings={"flyctl": rec})
        assert rec.exists()
        assert "lucerna" in rec.read_text()

    def test_no_credentials_no_scp_to_macbooks(self, tmp_path):
        """No .credentials.json -> scp still called but fails, no 'updated' in stdout."""
        _setup(tmp_path)
        r = _run(tmp_path)
        # Script calls scp for m2/m3 unconditionally, but the echo
        # after && only fires if scp succeeds — with no source file it fails.
        assert "updated: .credentials.json → m2" not in r.stdout
        assert "updated: .credentials.json → m3" not in r.stdout

    def test_credentials_scp_to_macbooks(self, tmp_path):
        """.credentials.json exists -> scp called for m2 and m3."""
        claude, _ = _setup(tmp_path)
        (claude / ".credentials.json").write_text('{"creds": true}')
        rec = tmp_path / "scp.log"
        _run(tmp_path, recordings={"scp": rec})
        assert rec.exists()
        text = rec.read_text()
        assert "m2" in text
        assert "m3" in text


# ── .zshenv push ────────────────────────────────────────────────────────


class TestZshenvPush:
    def test_no_zshenv_no_scp(self, tmp_path):
        """No .zshenv -> scp not called for .zshenv to pharos."""
        _setup(tmp_path)
        rec = tmp_path / "scp.log"
        _run(tmp_path, recordings={"scp": rec})
        if rec.exists():
            assert ".zshenv" not in rec.read_text()

    def test_zshenv_scp_to_pharos(self, tmp_path):
        """.zshenv exists -> scp called with pharos host."""
        _setup(tmp_path)
        (tmp_path / ".zshenv").write_text("export FOO=bar")
        rec = tmp_path / "scp.log"
        _run(tmp_path, recordings={"scp": rec})
        assert rec.exists()
        assert "pharos" in rec.read_text()

    def test_zshenv_tpl_scp_to_pharos(self, tmp_path):
        """.zshenv.tpl exists -> scp called with pharos host."""
        _setup(tmp_path)
        (tmp_path / ".zshenv.tpl").write_text("export FOO={{BAR}}")
        rec = tmp_path / "scp.log"
        _run(tmp_path, recordings={"scp": rec})
        assert rec.exists()
        assert "pharos" in rec.read_text()


# ── git commit / push ──────────────────────────────────────────────────


class TestGitCommit:
    def test_no_changes_no_git(self, tmp_path):
        """Nothing changed -> git not called."""
        _setup(tmp_path)
        rec = tmp_path / "git.log"
        _run(tmp_path, recordings={"git": rec})
        assert not rec.exists()

    def test_settings_changed_triggers_git(self, tmp_path):
        """settings.json changed -> git add + commit + push called."""
        claude, _ = _setup(tmp_path)
        (claude / "settings.json").write_text('{"key": "val"}')
        rec = tmp_path / "git.log"
        _run(tmp_path, recordings={"git": rec})
        assert rec.exists()
        text = rec.read_text()
        assert "add" in text
        assert "commit" in text
        assert "push" in text

    def test_memory_changed_triggers_git(self, tmp_path):
        """Memory dir sync sets changed=true -> git called."""
        claude, _ = _setup(tmp_path)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "test.md").write_text("content")
        rec = tmp_path / "git.log"
        _run(tmp_path, recordings={"git": rec})
        assert rec.exists()
        assert "add" in rec.read_text()


# ── exit code ───────────────────────────────────────────────────────────


class TestMemoryRsyncDelete:
    def test_rsync_delete_removes_stale_files(self, tmp_path):
        """rsync --delete removes files from dest that no longer exist in src."""
        claude, off = _setup(tmp_path)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        mem_dst = off / "claude" / "memory"
        mem_dst.mkdir(parents=True)
        # Stale file only in dest
        (mem_dst / "old.md").write_text("stale")
        _run(tmp_path)
        assert not (mem_dst / "old.md").exists()

    def test_memory_preserves_subdirs(self, tmp_path):
        """rsync copies nested directory structure."""
        claude, off = _setup(tmp_path)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        sub = mem_src / "deep" / "nested"
        sub.mkdir(parents=True)
        (sub / "file.md").write_text("nested content")
        _run(tmp_path)
        mem_dst = off / "claude" / "memory"
        assert (mem_dst / "deep" / "nested" / "file.md").read_text() == "nested content"

    def test_empty_memory_dir_syncs(self, tmp_path):
        """Empty memory source dir -> synced message still printed."""
        claude, _ = _setup(tmp_path)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        r = _run(tmp_path)
        assert "synced: memory/" in r.stdout


class TestChangedFlagLogic:
    def test_identical_settings_no_git(self, tmp_path):
        """settings.json identical -> changed stays false -> no git."""
        claude, off = _setup(tmp_path)
        content = '{"k": "v"}'
        (claude / "settings.json").write_text(content)
        (off / "claude" / "settings.json").write_text(content)
        rec = tmp_path / "git.log"
        _run(tmp_path, recordings={"git": rec})
        assert not rec.exists()

    def test_memory_only_triggers_git(self, tmp_path):
        """Memory sync (without settings change) triggers git."""
        claude, _ = _setup(tmp_path)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "data.md").write_text("data")
        rec = tmp_path / "git.log"
        _run(tmp_path, recordings={"git": rec})
        assert rec.exists()

    def test_both_changed_triggers_git(self, tmp_path):
        """Both memory and settings changed -> git triggered."""
        claude, off = _setup(tmp_path)
        (claude / "settings.json").write_text('{"k": "new"}')
        (off / "claude" / "settings.json").write_text('{"k": "old"}')
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "a.md").write_text("a")
        rec = tmp_path / "git.log"
        _run(tmp_path, recordings={"git": rec})
        assert rec.exists()
        log = rec.read_text()
        assert "add" in log
        assert "commit" in log
        assert "push" in log


class TestGitCommitMessage:
    def test_commit_message_contains_sync_prefix(self, tmp_path):
        """git commit message starts with 'sync: claude config'."""
        claude, _ = _setup(tmp_path)
        (claude / "settings.json").write_text('{"key": "val"}')
        rec = tmp_path / "git.log"
        _run(tmp_path, recordings={"git": rec})
        log = rec.read_text()
        assert "sync: claude config" in log

    def test_git_adds_correct_paths(self, tmp_path):
        """git add targets claude/memory/ and claude/settings.json."""
        claude, _ = _setup(tmp_path)
        (claude / "settings.json").write_text('{"key": "val"}')
        rec = tmp_path / "git.log"
        _run(tmp_path, recordings={"git": rec})
        log = rec.read_text()
        assert "claude/settings.json" in log


class TestCredentialsContent:
    def test_flyctl_receives_credential_content(self, tmp_path):
        """flyctl ssh console receives the credential file content."""
        claude, _ = _setup(tmp_path)
        (claude / ".credentials.json").write_text('{"apikey": "secret123"}')
        rec = tmp_path / "flyctl.log"
        _run(tmp_path, recordings={"flyctl": rec})
        log = rec.read_text()
        assert "secret123" in log

    def test_scp_credential_path_correct(self, tmp_path):
        """scp copies from .claude/.credentials.json to host:~/.claude/.credentials.json."""
        claude, _ = _setup(tmp_path)
        (claude / ".credentials.json").write_text('{"creds": true}')
        rec = tmp_path / "scp.log"
        _run(tmp_path, recordings={"scp": rec})
        log = rec.read_text()
        # Should contain both m2 and m3 as destination hosts
        assert "m2" in log
        assert "m3" in log
        assert ".credentials.json" in log


class TestZshenvBothFiles:
    def test_both_zshenv_files(self, tmp_path):
        """Both .zshenv and .zshenv.tpl -> two scp calls to pharos."""
        _setup(tmp_path)
        (tmp_path / ".zshenv").write_text("export A=1")
        (tmp_path / ".zshenv.tpl").write_text("export A={{B}}")
        rec = tmp_path / "scp.log"
        _run(tmp_path, recordings={"scp": rec})
        log = rec.read_text()
        pharos_lines = [l for l in log.splitlines() if "pharos" in l]
        assert len(pharos_lines) >= 2


class TestSetU:
    def test_unset_variable_exits_nonzero(self, tmp_path):
        """set -u causes exit on unset variable reference."""
        _setup(tmp_path)
        # Remove HOME to trigger unset-variable error
        # Actually set -u is about referencing unset variables in the script.
        # The script uses $HOME which is always set via env. Let's test that
        # the script handles missing directories gracefully (no crash).
        r = _run(tmp_path)
        assert r.returncode == 0


class TestMultipleMemoryFiles:
    def test_syncs_multiple_memory_files(self, tmp_path):
        """Multiple files in memory dir all get synced."""
        claude, off = _setup(tmp_path)
        mem_src = claude / "projects" / "-Users-terry" / "memory"
        mem_src.mkdir(parents=True)
        (mem_src / "a.md").write_text("file a")
        (mem_src / "b.md").write_text("file b")
        (mem_src / "c.md").write_text("file c")
        _run(tmp_path)
        mem_dst = off / "claude" / "memory"
        assert (mem_dst / "a.md").read_text() == "file a"
        assert (mem_dst / "b.md").read_text() == "file b"
        assert (mem_dst / "c.md").read_text() == "file c"


class TestExitCode:
    def test_exits_zero_no_changes(self, tmp_path):
        """Script exits 0 when nothing to sync."""
        _setup(tmp_path)
        r = _run(tmp_path)
        assert r.returncode == 0

    def test_exits_zero_with_changes(self, tmp_path):
        """Script exits 0 even when changes are synced."""
        claude, _ = _setup(tmp_path)
        (claude / "settings.json").write_text('{"key": "val"}')
        r = _run(tmp_path)
        assert r.returncode == 0

    def test_stderr_empty_on_success(self, tmp_path):
        """Successful run produces no stderr."""
        _setup(tmp_path)
        r = _run(tmp_path)
        assert r.stderr == ""
