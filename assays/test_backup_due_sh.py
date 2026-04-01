from __future__ import annotations

"""Tests for effectors/backup-due.sh — bash script tested via subprocess."""

import os
import shutil
import stat
import subprocess
import tempfile
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "backup-due.sh"
DUE_RELATIVE = "Library/Group Containers/5JMF32H3VU.com.phocusllp.duemac.shared/Compact.duecdb"
BACKUP_RELATIVE = "epigenome/oscillators/backups"


# ── fixture override ─────────────────────────────────────────────────────
# Override pytest's tmp_path to avoid pytest-asyncio auto-mode +
# tmp_path_retention_policy="none" cleaning up the directory between tests.


@pytest.fixture()
def tmp_path():
    d = Path(tempfile.mkdtemp(prefix="backup-due-test-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


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


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def _run_help(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_help_exits_zero(self):
        r = self._run_help("--help")
        assert r.returncode == 0

    def test_help_short_flag_exits_zero(self):
        r = self._run_help("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = self._run_help("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_due(self):
        r = self._run_help("--help")
        assert "Due" in r.stdout

    def test_help_mentions_nightly(self):
        r = self._run_help("--help")
        assert "nightly" in r.stdout.lower() or "Nightly" in r.stdout

    def test_help_shows_retention_policy(self):
        r = self._run_help("--help")
        assert "30" in r.stdout

    def test_help_no_stderr(self):
        r = self._run_help("--help")
        assert r.stderr == ""

    def test_help_no_backup_created(self, tmp_path):
        """--help must not trigger any backup operations."""
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        r = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.returncode == 0
        assert not (tmp_path / BACKUP_RELATIVE).exists()


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


# ── script permissions ──────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()


# ── success message details ─────────────────────────────────────────────


class TestSuccessMessageDetails:
    def test_stdout_mentions_source_basename(self, tmp_path):
        _make_db(tmp_path)
        r = _run(tmp_path)
        assert "Compact.duecdb" in r.stdout

    def test_stdout_mentions_dest_path(self, tmp_path):
        _make_db(tmp_path)
        r = _run(tmp_path)
        assert "due-" in r.stdout
        assert ".duecdb" in r.stdout

    def test_no_stderr_on_success(self, tmp_path):
        _make_db(tmp_path)
        r = _run(tmp_path)
        assert r.stderr == ""

    def test_success_output_two_lines(self, tmp_path):
        """Successful run prints exactly 2 lines: copy + retention."""
        _make_db(tmp_path)
        r = _run(tmp_path)
        lines = [l for l in r.stdout.strip().split("\n") if l]
        assert len(lines) == 2


# ── non-backup files in backup dir ──────────────────────────────────────


class TestNonBackupFiles:
    def test_pruning_ignores_non_duecdb_files(self, tmp_path):
        """Files not matching due-*.duecdb pattern are never pruned."""
        _make_db(tmp_path)
        bdir = tmp_path / BACKUP_RELATIVE
        bdir.mkdir(parents=True, exist_ok=True)
        # Create a non-matching file
        other = bdir / "other-file.txt"
        other.write_text("keep me")
        # Seed 35 backups so pruning happens
        today = date.today()
        for i in range(35):
            d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            (bdir / f"due-{d}.duecdb").write_text(f"backup-{d}")
        r = _run(tmp_path)
        assert r.returncode == 0
        assert other.exists()
        assert other.read_text() == "keep me"

    def test_pruning_ignores_partial_name_match(self, tmp_path):
        """Files like 'due-notes.txt' are not matched by due-*.duecdb glob."""
        _make_db(tmp_path)
        bdir = tmp_path / BACKUP_RELATIVE
        bdir.mkdir(parents=True, exist_ok=True)
        notes = bdir / "due-notes.txt"
        notes.write_text("notes")
        r = _run(tmp_path)
        assert r.returncode == 0
        assert notes.exists()


# ── exact boundary tests ────────────────────────────────────────────────


class TestExactBoundary:
    def test_exactly_30_backups_no_pruning(self, tmp_path):
        """With exactly 30 pre-existing backups, none are removed (today's makes 31 but prunes to 30)."""
        _make_db(tmp_path)
        bdir = tmp_path / BACKUP_RELATIVE
        bdir.mkdir(parents=True, exist_ok=True)
        today = date.today()
        seeded = []
        for i in range(30):
            d = (today - timedelta(days=i + 1)).strftime("%Y-%m-%d")
            f = bdir / f"due-{d}.duecdb"
            f.write_text(f"backup-{d}")
            os.utime(f, (time.time() - (i + 1) * 86400, time.time() - (i + 1) * 86400))
            seeded.append(f.name)
        r = _run(tmp_path)
        assert r.returncode == 0
        remaining = _backups(tmp_path)
        # Today's backup + 29 oldest = 30 (1 seed pruned since 30+1=31, prune to 30)
        assert len(remaining) == 30
        assert f"due-{_today_stamp()}.duecdb" in remaining

    def test_exactly_31_backups_prunes_to_30(self, tmp_path):
        """With exactly 31 pre-existing backups, after run we have 30."""
        _make_db(tmp_path)
        bdir = tmp_path / BACKUP_RELATIVE
        bdir.mkdir(parents=True, exist_ok=True)
        today = date.today()
        for i in range(31):
            d = (today - timedelta(days=i + 1)).strftime("%Y-%m-%d")
            f = bdir / f"due-{d}.duecdb"
            f.write_text(f"backup-{d}")
            os.utime(f, (time.time() - (i + 1) * 86400, time.time() - (i + 1) * 86400))
        r = _run(tmp_path)
        assert r.returncode == 0
        remaining = _backups(tmp_path)
        assert len(remaining) == 30


# ── source file permissions ─────────────────────────────────────────────


class TestCopyIntegrity:
    def test_preserves_content_not_permissions(self, tmp_path):
        """cp preserves content (permissions may differ, content must match)."""
        content = b"\x00\xff\x80\x7f" * 100
        db = _make_db(tmp_path, content)
        _run(tmp_path)
        dest = tmp_path / BACKUP_RELATIVE / f"due-{_today_stamp()}.duecdb"
        assert dest.read_bytes() == content

    def test_large_file_backup(self, tmp_path):
        """Backup works with a large file (10 MB)."""
        _make_db(tmp_path, b"X" * (10 * 1024 * 1024))
        r = _run(tmp_path)
        assert r.returncode == 0
        dest = tmp_path / BACKUP_RELATIVE / f"due-{_today_stamp()}.duecdb"
        assert dest.stat().st_size == 10 * 1024 * 1024


# ── retention count output with many backups ────────────────────────────


class TestRetentionCountOutput:
    def test_count_matches_actual_after_pruning(self, tmp_path):
        """The 'N backups retained' count matches actual file count."""
        _make_db(tmp_path)
        bdir = tmp_path / BACKUP_RELATIVE
        bdir.mkdir(parents=True, exist_ok=True)
        today = date.today()
        for i in range(40):
            d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            (bdir / f"due-{d}.duecdb").write_text(f"b-{d}")
        r = _run(tmp_path)
        assert r.returncode == 0
        actual = len(_backups(tmp_path))
        # Extract count from output: "due-backup: retention pruned, N backups retained"
        for line in r.stdout.strip().split("\n"):
            if "backups retained" in line:
                reported = int(line.split()[-3].strip(","))
                assert reported == actual
                break
        else:
            pytest.fail("No 'backups retained' line found in output")


# ── symlink source ───────────────────────────────────────────────────────


class TestSymlinkSource:
    def test_follows_symlink_to_real_file(self, tmp_path):
        """Script follows a symlink source to the real database."""
        real = tmp_path / "actual-data" / "Compact.duecdb"
        real.parent.mkdir(parents=True)
        real.write_text("symlinked-content")
        link = tmp_path / DUE_RELATIVE
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(real)
        r = _run(tmp_path)
        assert r.returncode == 0
        dest = tmp_path / BACKUP_RELATIVE / f"due-{_today_stamp()}.duecdb"
        assert dest.read_text() == "symlinked-content"

    def test_broken_symlink_treated_as_missing(self, tmp_path):
        """A broken symlink is treated as a missing database."""
        link = tmp_path / DUE_RELATIVE
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(tmp_path / "nonexistent-target")
        r = _run(tmp_path)
        assert r.returncode == 1
        assert "ERROR" in r.stderr


# ── HOME not set (set -u) ────────────────────────────────────────────────


class TestHomeUnset:
    def test_fails_when_home_unset(self, tmp_path):
        """With set -u, unset HOME causes the script to fail immediately."""
        env = os.environ.copy()
        env.pop("HOME", None)
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.returncode != 0

    def test_fails_when_home_empty(self, tmp_path):
        """Empty HOME results in an invalid path, triggering the missing-DB check."""
        env = os.environ.copy()
        env["HOME"] = ""
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.returncode == 1


# ── read-only backup directory ────────────────────────────────────────────


class TestReadOnlyBackupDir:
    def test_fails_when_backup_dir_readonly(self, tmp_path):
        """cp fails into a read-only directory; set -e causes script exit."""
        _make_db(tmp_path)
        bdir = tmp_path / BACKUP_RELATIVE
        bdir.mkdir(parents=True)
        bdir.chmod(0o555)
        r = _run(tmp_path)
        try:
            assert r.returncode != 0
        finally:
            bdir.chmod(0o755)


# ── unicode content ──────────────────────────────────────────────────────


class TestUnicodeContent:
    def test_copies_unicode_content(self, tmp_path):
        """Database with unicode characters is copied faithfully."""
        content = " café résumé naïve こんにちは 🧬 "
        _make_db(tmp_path, content)
        r = _run(tmp_path)
        assert r.returncode == 0
        dest = tmp_path / BACKUP_RELATIVE / f"due-{_today_stamp()}.duecdb"
        assert dest.read_text() == content


# ── destination filename format ───────────────────────────────────────────


class TestDestinationFormat:
    def test_dest_has_due_prefix(self, tmp_path):
        """Backup filename starts with 'due-'."""
        _make_db(tmp_path)
        _run(tmp_path)
        backups = _backups(tmp_path)
        assert all(b.startswith("due-") for b in backups)

    def test_dest_has_duecdb_extension(self, tmp_path):
        """Backup filename ends with '.duecdb'."""
        _make_db(tmp_path)
        _run(tmp_path)
        backups = _backups(tmp_path)
        assert all(b.endswith(".duecdb") for b in backups)

    def test_dest_date_is_valid_iso(self, tmp_path):
        """Date portion of filename is a valid ISO date (YYYY-MM-DD)."""
        _make_db(tmp_path)
        _run(tmp_path)
        backups = _backups(tmp_path)
        stamp = _today_stamp()
        assert backups == [f"due-{stamp}.duecdb"]
        # Verify it parses as a real date
        datetime.strptime(stamp, "%Y-%m-%d")
