"""Tests for metabolon.pinocytosis.ecdysis."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from metabolon.pinocytosis.ecdysis import intake, main


# ---------------------------------------------------------------------------
# intake()
# ---------------------------------------------------------------------------

def test_intake_raises_not_implemented():
    """intake() is a stub and must raise NotImplementedError."""
    with pytest.raises(NotImplementedError, match="not yet implemented"):
        intake()


def test_intake_default_is_json_true():
    """Default as_json=True still raises — parameter is accepted but not used."""
    with pytest.raises(NotImplementedError):
        intake(as_json=True)


def test_intake_json_false_also_raises():
    """Explicit as_json=False also raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        intake(as_json=False)


def test_intake_error_message_mentions_migration():
    """The error message should mention the migration source."""
    with pytest.raises(NotImplementedError, match="migrate from weekly"):
        intake()


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------

def test_main_propagates_not_implemented(capsys):
    """main() calls intake() which raises, so the error propagates."""
    sys.argv = ["ecdysis"]
    try:
        with pytest.raises(NotImplementedError):
            main()
    finally:
        sys.argv = sys.argv[:0]
    # Nothing should be printed since intake() raises before returning.
    captured = capsys.readouterr()
    assert captured.out == ""


def test_main_json_flag_propagates_error(capsys):
    """main --json still hits the NotImplementedError from intake."""
    sys.argv = ["ecdysis", "--json"]
    try:
        with pytest.raises(NotImplementedError):
            main()
    finally:
        sys.argv = sys.argv[:0]  # restore


def test_cli_entrypoint_runs():
    """Running the module as a script via subprocess exits with non-zero
    due to NotImplementedError (printed as traceback)."""
    mod = Path(__file__).resolve().parent.parent / "metabolon" / "pinocytosis" / "ecdysis.py"
    result = subprocess.run(
        [sys.executable, str(mod)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "NotImplementedError" in result.stderr
