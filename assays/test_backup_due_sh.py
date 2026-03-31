from __future__ import annotations

"""Tests for effectors/backup-due.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "backup-due.sh"
DUE_RELATIVE = "Library/Group Containers/5JMF32H3VU.com.phocusllp.duemac.shared/Compact.duecdb"
BACKUP_RELATIVE = "epigenome/oscillators/backups"


# ── helpers ─────────────────────────────────────────────────────────────


def _run(tmp_path: Path, binary: bool = False) -> subprocess.CompletedProcess:
    """Run backup-due.sh with HOME=tmp_path."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=not binary,
        env=env,
        timeout=10,
    )


def _make_db(tmp_path: Path, content: bytes | str = b"fake-due-data") -> Path:
    """Create the Due database file inside tmp_path HOME."""
    db = tmp_path / DUE_RELATIVE
    db.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        db.write_bytes(content)
    else:
        db.write_text(content)
    return db


def _backups(tmp_path: Path) -> list[str]:
    """Return sorted list of backup filenames."""
    bdir = tmp_path / BACKUP_RELATIVE
    if not bdir.exists():
        return []
    return sorted(p.name for p in bdir.glob("due-*.duecdb"))


def _today_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/bin/bash")

    def test_has_set_euo(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src


# ── missing database ────────────────────────────────────────────────────


class TestMissingDB:
    def test_exits_1(self, tmp_path):
        r = _run(tmp_path)
        assert r.returncode == 1

    def test_stderr_message(self, tmp_path):
        r = _run(tmp_path)
        assert "ERROR" in r.stderr
        assert "not found" in r.stderr

    def test_stderr_mentions_path(self, tmp_path):
        r = _run(tmp_path)
        assert "Compact.duecdb" in r.stderr

    def test_no_backup_created(self, tmp_path):
        _run(tmp_path)
        assert _backups(tmp_path) == []

    def test_directory_instead_of_file(self, tmp_path):
        """If the DB path is a directory, [ ! -f ] should trigger error."""
        db_dir = tmp_path / DUE_RELATIVE
        db_dir.mkdir(parents=True, exist_ok=True)
        r = _run(tmp_path)
        assert r.returncode == 1
        assert "ERROR" in r.stderr


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
        dest = tmp_path / BACKUP_RELATIVE / f"due-{_today_stamp()}.duecdb"
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

    def test_creates_backup_dir_when_already_exists(self, tmp_path):
        """mkdir -p is idempotent — pre-existing dir should not cause failure."""
        _make_db(tmp_path)
        (tmp_path / BACKUP_RELATIVE).mkdir(parents=True)
        r = _run(tmp_path)
        assert r.returncode == 0
        assert _backups(tmp_path) == [f"due-{_today_stamp()}.duecdb"]

    def test_timestamp_in_filename(self, tmp_path):
        _make_db(tmp_path)
        _run(tmp_path)
        assert _backups(tmp_path) == [f"due-{_today_stamp()}.duecdb"]

    def test_output_mentions_retained(self, tmp_path):
        _make_db(tmp_path)
        r = _run(tmp_path)
        assert "backups retained" in r.stdout


# ── empty and binary source ────────────────────────────────────────────


class TestSourceVariants:
    def test_copies_empty_file(self, tmp_path):
        _make_db(tmp_path, "")
        r = _run(tmp_path)
        assert r.returncode == 0
        dest = tmp_path / BACKUP_RELATIVE / f"due-{_today_stamp()}.duecdb"
        assert dest.exists()
        assert dest.read_text() == ""

    def test_copies_binary_content(self, tmp_path):
        """Binary data (e.g. a real SQLite DB) is preserved byte-for-byte."""
        payload = os.urandom(4096)
        _make_db(tmp_path, payload)
        r = _run(tmp_path)
        assert r.returncode == 0
        dest = tmp_path / BACKUP_RELATIVE / f"due-{_today_stamp()}.duecdb"
        assert dest.read_bytes() == payload


# ── retention pruning ──────────────────────────────────────────────────


class TestRetention:
    def _seed_backups(
        self, backup_dir: Path, count: int
    ) -> list[Path]:
        """Create count dated backup files with descending mtimes. Returns newest-first."""
        today = date.today()
        files = []
        for i in range(count):
            d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            f = backup_dir / f"due-{d}.duecdb"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"backup-{d}")
            os.utime(f, (time.time() - i * 86400, time.time() - i * 86400))
            files.append(f)
        return files

    def test_keeps_30_backups(self, tmp_path):
        """When 31+ backups exist, only 30 are kept after pruning."""
        _make_db(tmp_path)
        bdir = tmp_path / BACKUP_RELATIVE
        bdir.mkdir(parents=True, exist_ok=True)
        for i in range(35):
            (bdir / f"due-2025-01-{i:02d}.duecdb").write_text(f"old-{i}")
        _run(tmp_path)
        assert len(_backups(tmp_path)) <= 30

    def test_prunes_oldest(self, tmp_path):
        """Oldest backups by mtime are removed, total kept <= 30."""
        _make_db(tmp_path)
        bdir = tmp_path / BACKUP_RELATIVE
        bdir.mkdir(parents=True, exist_ok=True)
        for i in range(35):
            f = bdir / f"due-2025-02-{i:02d}.duecdb"
            f.write_text(f"old-{i}")
            os.utime(f, (1_000_000 + i * 100, 1_000_000 + i * 100))
        _run(tmp_path)
        remaining = _backups(tmp_path)
        assert len(remaining) <= 30
        assert f"due-{_today_stamp()}.duecdb" in remaining
        assert "due-2025-02-00.duecdb" not in remaining

    def test_prunes_with_real_dates(self, tmp_path):
        """Seed 35 backups with real descending dates, run script, verify <= 30."""
        _make_db(tmp_path)
        backup_dir = tmp_path / BACKUP_RELATIVE
        self._seed_backups(backup_dir, 35)
        r = _run(tmp_path)
        assert r.returncode == 0
        remaining = sorted(backup_dir.glob("due-*.duecdb"))
        assert len(remaining) <= 30

    def test_prunes_oldest_real_dates(self, tmp_path):
        """The oldest file (farthest date) gets pruned."""
        _make_db(tmp_path)
        backup_dir = tmp_path / BACKUP_RELATIVE
        files = self._seed_backups(backup_dir, 35)
        _run(tmp_path)
        assert not files[-1].exists()

    def test_keeps_recent_real_dates(self, tmp_path):
        """The most recent pre-existing backup survives pruning."""
        _make_db(tmp_path)
        backup_dir = tmp_path / BACKUP_RELATIVE
        files = self._seed_backups(backup_dir, 35)
        _run(tmp_path)
        assert files[0].exists()

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

    def test_fewer_than_30_exact_count(self, tmp_path):
        """Seeding 5 backups + today's copy = 5 retained (today overwrites matching seed)."""
        _make_db(tmp_path)
        backup_dir = tmp_path / BACKUP_RELATIVE
        self._seed_backups(backup_dir, 5)
        _run(tmp_path)
        remaining = list(backup_dir.glob("due-*.duecdb"))
        assert len(remaining) == 5

    def test_output_shows_retained_count(self, tmp_path):
        _make_db(tmp_path)
        backup_dir = tmp_path / BACKUP_RELATIVE
        self._seed_backups(backup_dir, 35)
        r = _run(tmp_path)
        assert "backups retained" in r.stdout


# ── overwrite behaviour ────────────────────────────────────────────────


class TestOverwrite:
    def test_overwrites_same_day_backup(self, tmp_path):
        """Running twice on the same day overwrites the earlier backup."""
        _make_db(tmp_path, "version-1")
        _run(tmp_path)
        _make_db(tmp_path, "version-2")
        _run(tmp_path)
        dest = tmp_path / BACKUP_RELATIVE / f"due-{_today_stamp()}.duecdb"
        assert dest.read_text() == "version-2"

    def test_second_run_still_exit_0(self, tmp_path):
        _make_db(tmp_path)
        _run(tmp_path)
        r = _run(tmp_path)
        assert r.returncode == 0


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
