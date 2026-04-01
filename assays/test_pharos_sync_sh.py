from __future__ import annotations

"""Tests for effectors/pharos-sync.sh — bash script tested via subprocess."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-sync.sh"


def _run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    """Run pharos-sync.sh with HOME=tmp_path."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
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

    def test_help_mentions_claude(self):
        r = self._run_help("--help")
        assert "Claude" in r.stdout or "claude" in r.stdout.lower()


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/usr/bin/env bash") or first.startswith("#!/bin/bash")

    def test_has_set_uo_pipefail(self):
        src = SCRIPT.read_text()
        assert "set -uo pipefail" in src


# ── script permissions ──────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()


# ── test sync_file function ─────────────────────────────────────────────


class TestSyncFile:
    def test_sync_file_function_exists(self):
        src = SCRIPT.read_text()
        assert "sync_file() {" in src

    def test_sync_file_succeeds_when_src_exists(self, tmp_path):
        src = tmp_path / "src.txt"
        src.write_text("test content")
        dst = tmp_path / "dst.txt"

        # Source the script and call sync_file
        script = f"""
        source "{SCRIPT}"
        sync_file "{src}" "{dst}"
        echo "returncode=$?"
        """
        r = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0
        assert dst.exists()
        assert dst.read_text() == "test content"
