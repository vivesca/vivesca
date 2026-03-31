"""Tests for effectors/backup-due.sh — Due app database backup script.

Effectors are scripts: tested via subprocess.run, never imported.
"""
import os
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "effectors" / "backup-due.sh"

DUE_RELATIVE = (
    "Library/Group Containers"
    "/5JMF32H3VU.com.phocusllp.duemac.shared/Compact.duecdb"
)
BACKUP_RELATIVE = "epigenome/oscillators/backups"


def _run(home: str) -> subprocess.CompletedProcess:
    """Run backup-due.sh with HOME overridden to a temp dir."""
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": home},
    )


def _make_due_db(home: Path, content: str = "fake-due-db") -> Path:
    """Create a fake Due database file inside a temp HOME."""
    db = home / DUE_RELATIVE
    db.parent.mkdir(parents=True, exist_ok=True)
    db.write_text(content)
    return db


def test_missing_due_db_exits_nonzero():
    """When Due DB is absent, script exits 1 with an error message."""
    with tempfile.TemporaryDirectory() as td:
        result = _run(td)
        assert result.returncode == 1
        assert "Due database not found" in result.stderr


def test_successful_backup():
    """When Due DB exists, script copies it to backups dir and exits 0."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        _make_due_db(home, content="due-data-v1")

        result = _run(td)
        assert result.returncode == 0
        assert "due-backup: copied" in result.stdout

        backup_dir = home / BACKUP_RELATIVE
        assert backup_dir.is_dir()

        backups = sorted(backup_dir.glob("due-*.duecdb"))
        assert len(backups) == 1
        assert backups[0].read_text() == "due-data-v1"


def test_backup_includes_today_datestamp():
    """Backup filename contains today's date in YYYY-MM-DD format."""
    from datetime import date

    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        _make_due_db(home)

        result = _run(td)
        assert result.returncode == 0

        today = date.today().isoformat()
        backup_dir = home / BACKUP_RELATIVE
        expected = backup_dir / f"due-{today}.duecdb"
        assert expected.exists(), f"Expected backup at {expected}"


def test_retention_prunes_old_backups():
    """Script keeps only the last 30 backups, deleting older ones."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        _make_due_db(home)

        backup_dir = home / BACKUP_RELATIVE
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create 35 pre-existing backups with older dates
        for i in range(35):
            older = backup_dir / f"due-2025-01-{i + 1:02d}.duecdb"
            older.write_text(f"old-backup-{i}")

        result = _run(td)
        assert result.returncode == 0

        remaining = sorted(backup_dir.glob("due-*.duecdb"))
        # ls -t | tail -n +31 keeps the first 30 (newest first), so total = 30
        assert len(remaining) == 30, (
            f"Expected 30 backups after pruning 35+1 to 30, got {len(remaining)}"
        )


def test_idempotent_same_day_rerun():
    """Running the script twice on the same day overwrites the same file."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        _make_due_db(home, content="version-1")

        result1 = _run(td)
        assert result1.returncode == 0

        _make_due_db(home, content="version-2")
        result2 = _run(td)
        assert result2.returncode == 0

        backup_dir = home / BACKUP_RELATIVE
        backups = sorted(backup_dir.glob("due-*.duecdb"))
        assert len(backups) == 1
        assert backups[0].read_text() == "version-2"


def test_creates_backup_dir_if_missing():
    """Script creates the backup directory tree if it doesn't exist."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        _make_due_db(home)

        backup_dir = home / BACKUP_RELATIVE
        assert not backup_dir.exists()

        result = _run(td)
        assert result.returncode == 0
        assert backup_dir.is_dir()


def test_stdout_reports_retained_count():
    """Script prints how many backups were retained after pruning."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        _make_due_db(home)

        result = _run(td)
        assert result.returncode == 0
        assert "backups retained" in result.stdout
