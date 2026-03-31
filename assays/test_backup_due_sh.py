from __future__ import annotations
"""Tests for effectors/backup-due.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "backup-due.sh"
DUE_RELATIVE = "Library/Group Containers/5JMF32H3VU.com.phocusllp.duemac.shared/Compact.duecdb"
BACKUP_RELATIVE = "epigenome/oscillators/backups"


# ── helpers ─────────────────────────────────────────────────────────────


def _run(tmp_path: Path) -> subprocess.CompletedProcess:
    """Run backup-due.sh with HOME=tmp_path."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True, text=True, env=env, timeout=10,
    )


def _make_db(tmp_path: Path, content: str = "fake-due-data") -> Path:
    """Create the Due database file inside tmp_path HOME."""
    db = tmp_path / DUE_RELATIVE
    db.parent.mkdir(parents=True, exist_ok=True)
    db.write_text(content)
    return db


def _backups(tmp_path: Path) -> list[str]:
    """Return sorted list of backup filenames."""
    bdir = tmp_path / BACKUP_RELATIVE
    if not bdir.exists():
        return []
    return sorted(p.name for p in bdir.glob("due-*.duecdb"))


# ── missing database ────────────────────────────────────────────────────


class TestMissingDB:
    def test_exits_1(self, tmp_path):
        r = _run(tmp_path)
        assert r.returncode == 1

    def test_stderr_message(self, tmp_path):
        r = _run(tmp_path)
        assert "ERROR" in r.stderr
        assert "not found" in r.stderr

    def test_no_backup_created(self, tmp_path):
        _run(tmp_path)
        assert _backups(tmp_path) == []


# ── successful backup ───────────────────────────────────────────────────


class TestSuccessfulBackup:
    def test_exits_zero(self, tmp_path):
        _make_db(tmp_path)
        r = _run(tmp_path)
        assert r.returncode == 0

    def test_copies_file(self, tmp_path):
        content = "my-reminders"
        _make_db(tmp_path, content)
        _run(tmp_path)
        today = datetime.now().strftime("%Y-%m-%d")
        dest = tmp_path / BACKUP_RELATIVE / f"due-{today}.duecdb"
        assert dest.exists()
        assert dest.read_text() == content

    def test_prints_success(self, tmp_path):
        _make_db(tmp_path)
        r = _run(tmp_path)
        assert "due-backup: copied" in r.stdout

    def test_creates_backup_dir(self, tmp_path):
        _make_db(tmp_path)
        assert not (tmp_path / BACKUP_RELATIVE).exists()
        _run(tmp_path)
        assert (tmp_path / BACKUP_RELATIVE).is_dir()

    def test_timestamp_in_filename(self, tmp_path):
        _make_db(tmp_path)
        _run(tmp_path)
        today = datetime.now().strftime("%Y-%m-%d")
        assert _backups(tmp_path) == [f"due-{today}.duecdb"]


# ── retention pruning ──────────────────────────────────────────────────


class TestRetention:
    def test_keeps_30_backups(self, tmp_path):
        """When 31+ backups exist, only 30 are kept after pruning."""
        _make_db(tmp_path)
        bdir = tmp_path / BACKUP_RELATIVE
        bdir.mkdir(parents=True, exist_ok=True)
        # Create 35 old backups (ls -t sorts newest first, so old ones get pruned)
        for i in range(35):
            (bdir / f"due-2025-01-{i:02d}.duecdb").write_text(f"old-{i}")
        _run(tmp_path)
        assert len(_backups(tmp_path)) <= 30

    def test_prunes_oldest(self, tmp_path):
        """Oldest backups by mtime are removed, total kept <= 30."""
        _make_db(tmp_path)
        bdir = tmp_path / BACKUP_RELATIVE
        bdir.mkdir(parents=True, exist_ok=True)
        # Create 35 old backups with distinct mtimes so ls -t is stable
        for i in range(35):
            f = bdir / f"due-2025-02-{i:02d}.duecdb"
            f.write_text(f"old-{i}")
            # Lower mtime = "older" file; ls -t puts newest first
            os.utime(f, (1_000_000 + i * 100, 1_000_000 + i * 100))
        _run(tmp_path)
        remaining = _backups(tmp_path)
        # 35 old + 1 new = 36 total; after pruning <= 30
        assert len(remaining) <= 30
        # Today's backup must survive
        today = datetime.now().strftime("%Y-%m-%d")
        assert f"due-{today}.duecdb" in remaining
        # The very oldest file (lowest mtime) should be pruned
        assert "due-2025-02-00.duecdb" not in remaining

    def test_no_prune_under_30(self, tmp_path):
        """With fewer than 30 backups, none are pruned."""
        _make_db(tmp_path)
        bdir = tmp_path / BACKUP_RELATIVE
        bdir.mkdir(parents=True, exist_ok=True)
        for i in range(5):
            (bdir / f"due-2025-03-{i:02d}.duecdb").write_text(f"keep-{i}")
        _run(tmp_path)
        remaining = _backups(tmp_path)
        for i in range(5):
            assert f"due-2025-03-{i:02d}.duecdb" in remaining


# ── overwrite behaviour ────────────────────────────────────────────────


class TestOverwrite:
    def test_overwrites_same_day_backup(self, tmp_path):
        """Running twice on the same day overwrites the earlier backup."""
        _make_db(tmp_path, "version-1")
        _run(tmp_path)
        _make_db(tmp_path, "version-2")
        _run(tmp_path)
        today = datetime.now().strftime("%Y-%m-%d")
        dest = tmp_path / BACKUP_RELATIVE / f"due-{today}.duecdb"
        assert dest.read_text() == "version-2"


# ── retention message ──────────────────────────────────────────────────


class TestRetentionPolicy:
    def test_retention_message(self, tmp_path):
        _make_db(tmp_path)
        r = _run(tmp_path)
        assert "retention pruned" in r.stdout

    def test_retention_count(self, tmp_path):
        _make_db(tmp_path)
        r = _run(tmp_path)
        assert "1 backups retained" in r.stdout
