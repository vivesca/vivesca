from __future__ import annotations

"""Tests for com.vivesca.soma-pull.plist — macOS LaunchAgent for soma-pull."""

import plistlib
from pathlib import Path

import pytest

PLIST_PATH = Path(__file__).resolve().parent.parent / "effectors" / "com.vivesca.soma-pull.plist"


@pytest.fixture()
def plist() -> dict:
    """Load and parse the plist file."""
    with open(PLIST_PATH, "rb") as f:
        return plistlib.load(f)


# ── Structural validity ──────────────────────────────────────────────


def test_plist_file_exists():
    """Plist file exists on disk."""
    assert PLIST_PATH.exists()


def test_plist_parseable(plist):
    """Plist file is valid XML plist parseable by plistlib."""
    assert isinstance(plist, dict)


# ── Label ─────────────────────────────────────────────────────────────


def test_label(plist):
    """Label matches expected LaunchAgent identifier."""
    assert plist["Label"] == "com.vivesca.soma-pull"


# ── ProgramArguments ──────────────────────────────────────────────────


def test_program_arguments_is_list(plist):
    """ProgramArguments is a list with at least one entry."""
    assert isinstance(plist["ProgramArguments"], list)
    assert len(plist["ProgramArguments"]) >= 1


def test_program_arguments_python_executable(plist):
    """First argument points to a python3 binary."""
    assert "python3" in plist["ProgramArguments"][0]


def test_program_arguments_soma_pull_script(plist):
    """Second argument points to the soma-pull script."""
    assert plist["ProgramArguments"][1].endswith("soma-pull")


# ── StartInterval ─────────────────────────────────────────────────────


def test_start_interval(plist):
    """StartInterval is 900 seconds (15 minutes)."""
    assert plist["StartInterval"] == 900


# ── Log paths ─────────────────────────────────────────────────────────


def test_standard_out_path(plist):
    """StandardOutPath is set to a .log file."""
    assert plist["StandardOutPath"].endswith("soma-pull-stdout.log")


def test_standard_error_path(plist):
    """StandardErrorPath is set to a .log file."""
    assert plist["StandardErrorPath"].endswith("soma-pull-stderr.log")


# ── RunAtLoad ─────────────────────────────────────────────────────────


def test_run_at_load(plist):
    """RunAtLoad is true so the agent runs immediately on load."""
    assert plist["RunAtLoad"] is True


# ── No unexpected keys ────────────────────────────────────────────────


def test_no_extra_keys(plist):
    """Plist contains only the expected keys."""
    expected = {
        "Label",
        "ProgramArguments",
        "StartInterval",
        "StandardOutPath",
        "StandardErrorPath",
        "RunAtLoad",
    }
    assert set(plist.keys()) == expected


# ── Referenced script exists ──────────────────────────────────────────


def test_soma_pull_script_exists():
    """The soma-pull effector script referenced by the plist exists."""
    script_path = PLIST_PATH.parent / "soma-pull"
    assert script_path.exists()


def test_soma_pull_script_is_python():
    """The soma-pull script has a Python shebang."""
    script_path = PLIST_PATH.parent / "soma-pull"
    first_line = script_path.read_text().splitlines()[0]
    assert "python" in first_line
