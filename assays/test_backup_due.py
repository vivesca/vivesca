#!/usr/bin/env python3
"""Test for backup-due.sh effector script."""

import subprocess
import pytest
from pathlib import Path


EFFECTOR_PATH = Path(__file__).parent.parent / "effectors" / "backup-due.sh"


def test_backup_due_script_exists():
    """Verify the script file exists."""
    assert EFFECTOR_PATH.exists()
    assert EFFECTOR_PATH.is_file()


def test_backup_due_help_flag():
    """Test that --help prints usage and exits cleanly."""
    result = subprocess.run(
        [str(EFFECTOR_PATH), "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Usage: backup-due.sh" in result.stdout
    assert "Nightly backup of Due app database" in result.stdout
    assert "Retains the last 30 backups" in result.stdout


def test_error_when_database_missing():
    """Test script exits with error when Due database is not found."""
    # This test will always fail on Linux (gemmule), since Due is macOS only.
    # That's actually what we expect - the error is correct behavior.
    result = subprocess.run(
        [str(EFFECTOR_PATH)],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
    assert "ERROR: Due database not found" in result.stderr
