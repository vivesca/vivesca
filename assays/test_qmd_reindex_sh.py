from __future__ import annotations

"""Tests for effectors/qmd-reindex.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "qmd-reindex.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_help(*args: str) -> subprocess.CompletedProcess:
    """Run qmd-reindex.sh with help flags."""
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def test_help_exits_zero(self):
        r = _run_help("--help")
        assert r.returncode == 0

    def test_help_short_flag_exits_zero(self):
        r = _run_help("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run_help("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_qmd(self):
        r = _run_help("--help")
        assert "qmd" in r.stdout

    def test_help_no_stderr(self):
        r = _run_help("--help")
        assert r.stderr == ""


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


# ── script permissions ──────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()
