from __future__ import annotations

"""Tests for backup-due.sh — nightly backup of Due app database."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline/effectors/backup-due.sh"


@pytest.fixture
def fake_env(tmp_path):
    """Create a fake HOME with Due DB and backup dir structure."""
    # Build the macOS-style Due DB path inside tmp_path
    due_dir = tmp_path / "Library" / "Group Containers" / "5JMF32H3VU.com.phocusllp.duemac.shared"
    due_dir.mkdir(parents=True)
    due_db = due_dir / "Compact.duecdb"
    due_db.write_text("fake-due-data")

    backup_dir = tmp_path / "epigenome" / "oscillators" / "backups"

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    return {
        "home": tmp_path,
        "due_db": due_db,
        "backup_dir": backup_dir,
        "env": env,
    }


def run_script(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run backup-due.sh and return CompletedProcess."""
    cmd = [str(SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)


# ── --help / -h ──────────────────────────────────────────────────────


def test_help_flag_exits_zero():
    r = run_script("--help")
    assert r.returncode == 0


def test_help_flag_prints_usage():
    r = run_script("--help")
    assert "Usage: backup-due.sh" in r.stdout
    assert "Nightly backup" in r.stdout


def test_h_short_flag_exits_zero():
    r = run_script("-h")
    assert r.returncode == 0
    assert "Usage: backup-due.sh" in r.stdout


# ── missing Due DB ───────────────────────────────────────────────────


def test_missing_db_exits_nonzero(tmp_path):
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    r = run_script(env=env)
    assert r.returncode == 1


def test_missing_db_prints_error_to_stderr(tmp_path):
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    r = run_script(env=env)
    assert "ERROR" in r.stderr
    assert "Due database not found" in r.stderr


# ── successful backup ────────────────────────────────────────────────


def test_successful_backup_creates_copy(fake_env):
    r = run_script(env=fake_env["env"])
    assert r.returncode == 0

    # A dated backup file should exist
    backups = sorted(fake_env["backup_dir"].glob("due-*.duecdb"))
    assert len(backups) == 1
    assert backups[0].read_text() == "fake-due-data"


def test_successful_backup_prints_copied_message(fake_env):
    r = run_script(env=fake_env["env"])
    assert r.returncode == 0
    assert "due-backup: copied" in r.stdout


def test_successful_backup_prints_retention_message(fake_env):
    r = run_script(env=fake_env["env"])
    assert r.returncode == 0
    assert "retention pruned" in r.stdout


# ── retention pruning ────────────────────────────────────────────────


def test_retention_keeps_last_30(fake_env):
    # Pre-create 35 dated backup files (oldest first via naming)
    for i in range(1, 36):
        day = f"2026-03-{i:02d}"
        f = fake_env["backup_dir"] / f"due-{day}.duecdb"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"old-data-{i}")

    # Create the "today" backup by running the script
    r = run_script(env=fake_env["env"])
    assert r.returncode == 0

    backups = sorted(fake_env["backup_dir"].glob("due-*.duecdb"))
    # Should have at most 30 files (pruned the oldest 5 + added today = 30 total)
    assert len(backups) == 30
    # The newest file should exist
    assert (fake_env["backup_dir"] / "due-2026-04-02.duecdb").exists()


def test_retention_no_files_no_error(fake_env):
    # backup_dir doesn't exist yet — script creates it and reports 0 retained
    r = run_script(env=fake_env["env"])
    assert r.returncode == 0
    assert "backups retained" in r.stdout


# ── idempotency ──────────────────────────────────────────────────────


def test_same_day_backup_overwrites(fake_env):
    r1 = run_script(env=fake_env["env"])
    assert r1.returncode == 0
    r2 = run_script(env=fake_env["env"])
    assert r2.returncode == 0

    backups = sorted(fake_env["backup_dir"].glob("due-*.duecdb"))
    # Same timestamp → only one file
    assert len(backups) == 1
