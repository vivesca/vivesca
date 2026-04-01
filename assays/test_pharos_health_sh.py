from __future__ import annotations

"""Tests for effectors/pharos-health.sh — bash script tested via subprocess."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-health.sh"


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

    def test_help_shows_usage(self):
        r = self._run_help("--help")
        assert "Usage:" in r.stdout


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/bin/bash")
