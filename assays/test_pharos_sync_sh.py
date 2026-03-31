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

    # Create recording mocks for specified tools
    for name, rec_file in (recordings or {}).items():
        script = mock_dir / name
        script.write_text(
            "#!/bin/bash\n"
            f'printf "%s\\n" "$@" >> {rec_file}\n'
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
        """No .credentials.json -> scp not called for m2/m3."""
        _setup(tmp_path)
        rec = tmp_path / "scp.log"
        _run(tmp_path, recordings={"scp": rec})
        if rec.exists():
            text = rec.read_text()
            assert "m2" not in text
            assert "m3" not in text

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
