from __future__ import annotations
"""Tests for effectors/backup-due.sh — nightly backup of Due app database."""

import subprocess
import os
from datetime import date
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "effectors" / "backup-due.sh"

# Path components the script expects under $HOME
DUE_REL = Path("Library/Group Containers/5JMF32H3VU.com.phocusllp.duemac.shared/Compact.duecdb")
BACKUP_REL = Path("epigenome/oscillators/backups")


def _run_script(home: str, **kwargs: object) -> subprocess.CompletedProcess:
    """Run backup-due.sh with HOME overridden."""
    env = {**os.environ, "HOME": home}
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        **kwargs,
    )


def _make_due_db(home: Path) -> Path:
    """Create a fake Due database in the expected location."""
    db = home / DUE_REL
    db.parent.mkdir(parents=True, exist_ok=True)
    db.write_text("fake-due-data")
    return db


# ── File basics ──────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/bin/bash")

    def test_has_set_euo(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src


# ── Error: Due DB not found ──────────────────────────────────────────────


class TestDbNotFound:
    def test_exits_1_when_db_missing(self, tmp_path):
        result = _run_script(str(tmp_path))
        assert result.returncode == 1

    def test_stderr_mentions_error(self, tmp_path):
        result = _run_script(str(tmp_path))
        assert "ERROR" in result.stderr or "ERROR" in result.stdout

    def test_stderr_mentions_path(self, tmp_path):
        result = _run_script(str(tmp_path))
        combined = result.stderr + result.stdout
        assert "Compact.duecdb" in combined


# ── Happy path: successful backup ────────────────────────────────────────


class TestSuccessfulBackup:
    def test_exits_0(self, tmp_path):
        _make_due_db(tmp_path)
        result = _run_script(str(tmp_path))
        assert result.returncode == 0

    def test_creates_backup_dir(self, tmp_path):
        _make_due_db(tmp_path)
        backup_dir = tmp_path / BACKUP_REL
        assert not backup_dir.exists()
        _run_script(str(tmp_path))
        assert backup_dir.is_dir()

    def test_copies_db_with_datestamp(self, tmp_path):
        _make_due_db(tmp_path)
        _run_script(str(tmp_path))
        today = date.today().strftime("%Y-%m-%d")
        expected = tmp_path / BACKUP_REL / f"due-{today}.duecdb"
        assert expected.exists()
        assert expected.read_text() == "fake-due-data"

    def test_output_mentions_copied(self, tmp_path):
        _make_due_db(tmp_path)
        result = _run_script(str(tmp_path))
        assert "due-backup:" in result.stdout
        assert "copied" in result.stdout

    def test_output_mentions_retained(self, tmp_path):
        _make_due_db(tmp_path)
        result = _run_script(str(tmp_path))
        assert "retained" in result.stdout


# ── Idempotency: overwrites same-day backup ──────────────────────────────


class TestIdempotency:
    def test_second_run_overwrites(self, tmp_path):
        db = _make_due_db(tmp_path)
        _run_script(str(tmp_path))
        today = date.today().strftime("%Y-%m-%d")
        dest = tmp_path / BACKUP_REL / f"due-{today}.duecdb"
        # Modify source
        db.write_text("updated-data")
        _run_script(str(tmp_path))
        assert dest.read_text() == "updated-data"

    def test_second_run_still_exit_0(self, tmp_path):
        _make_due_db(tmp_path)
        _run_script(str(tmp_path))
        result = _run_script(str(tmp_path))
        assert result.returncode == 0


# ── Retention pruning ────────────────────────────────────────────────────


class TestRetention:
    def _seed_backups(self, backup_dir: Path, count: int) -> list[Path]:
        """Create count dated backup files with descending mtimes. Returns list newest-first."""
        import time
        from datetime import timedelta
        files = []
        today = date.today()
        for i in range(count):
            d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            f = backup_dir / f"due-{d}.duecdb"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"backup-{d}")
            # Set mtime so ls -t sorts newest-first correctly
            os.utime(f, (time.time() - i * 86400, time.time() - i * 86400))
            files.append(f)
        return files

    def test_keeps_at_most_30(self, tmp_path):
        _make_due_db(tmp_path)
        backup_dir = tmp_path / BACKUP_REL
        self._seed_backups(backup_dir, 35)
        result = _run_script(str(tmp_path))
        assert result.returncode == 0
        remaining = sorted(backup_dir.glob("due-*.duecdb"))
        assert len(remaining) <= 30

    def test_prunes_oldest(self, tmp_path):
        _make_due_db(tmp_path)
        backup_dir = tmp_path / BACKUP_REL
        files = self._seed_backups(backup_dir, 35)
        _run_script(str(tmp_path))
        # The oldest file should have been pruned
        assert not files[-1].exists()

    def test_keeps_recent(self, tmp_path):
        _make_due_db(tmp_path)
        backup_dir = tmp_path / BACKUP_REL
        files = self._seed_backups(backup_dir, 35)
        _run_script(str(tmp_path))
        # Most recent file should still exist
        assert files[0].exists()

    def test_output_shows_retained_count(self, tmp_path):
        _make_due_db(tmp_path)
        backup_dir = tmp_path / BACKUP_REL
        self._seed_backups(backup_dir, 35)
        result = _run_script(str(tmp_path))
        # Should report some number of retained backups
        assert "backups retained" in result.stdout

    def test_fewer_than_30_no_prune(self, tmp_path):
        _make_due_db(tmp_path)
        backup_dir = tmp_path / BACKUP_REL
        files = self._seed_backups(backup_dir, 5)
        _run_script(str(tmp_path))
        # All 5 pre-existing + today's overwrite = should still have 5
        remaining = list(backup_dir.glob("due-*.duecdb"))
        assert len(remaining) == 5


# ── Empty source DB ──────────────────────────────────────────────────────


class TestEmptySourceDb:
    def test_copies_empty_file(self, tmp_path):
        db = tmp_path / DUE_REL
        db.parent.mkdir(parents=True, exist_ok=True)
        db.write_text("")
        result = _run_script(str(tmp_path))
        assert result.returncode == 0
        today = date.today().strftime("%Y-%m-%d")
        dest = tmp_path / BACKUP_REL / f"due-{today}.duecdb"
        assert dest.exists()
        assert dest.read_text() == ""
