from __future__ import annotations

"""Tests for effectors/start-chrome-debug.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "start-chrome-debug.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run start-chrome-debug.sh with given args and env."""
    if env is None:
        env = os.environ.copy()
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def test_help_exits_zero(self):
        r = _run_script("--help")
        assert r.returncode == 0

    def test_help_short_flag_exits_zero(self):
        r = _run_script("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run_script("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_chrome(self):
        r = _run_script("--help")
        assert "Chrome" in r.stdout

    def test_help_mentions_port(self):
        r = _run_script("--help")
        assert "port" in r.stdout

    def test_help_no_stderr(self):
        r = _run_script("--help")
        assert r.stderr == ""


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/") and "bash" in first

    def test_has_set_euo(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src


# ── script permissions ──────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()


# ── unknown option ─────────────────────────────────────────────────────


class TestUnknownOption:
    def test_unknown_option_exits_2(self):
        r = _run_script("--unknown-option")
        assert r.returncode == 2

    def test_unknown_option_shows_usage(self):
        r = _run_script("--unknown-option")
        assert "Usage:" in r.stderr
