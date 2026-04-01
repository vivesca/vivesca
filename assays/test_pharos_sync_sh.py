from __future__ import annotations

"""Tests for effectors/pharos-sync.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-sync.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run(tmp_path: Path, args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run pharos-sync.sh with HOME=tmp_path."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    return subprocess.run(
        ["bash", str(SCRIPT)] + (args or []),
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


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


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/bin/bash")

    def test_has_set_uo_pipefail(self):
        src = SCRIPT.read_text()
        assert "set -uo pipefail" in src


# ── script permissions ──────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()


# ── sync_file function tests ────────────────────────────────────────────


class TestSyncFileFunction:
    def test_sync_file_function_exists(self):
        """Verify sync_file is defined in the script."""
        src = SCRIPT.read_text()
        assert "sync_file()" in src

    def test_script_exits_zero_with_minimal_setup(self, tmp_path):
        """With minimal structure, script exits 0 (even if no changes)."""
        r = _run(tmp_path)
        # Script has || true on most operations, so it should exit 0
        assert r.returncode == 0
