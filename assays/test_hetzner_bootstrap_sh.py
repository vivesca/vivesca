from __future__ import annotations

"""Tests for effectors/hetzner-bootstrap.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "hetzner-bootstrap.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_help(*args: str) -> subprocess.CompletedProcess:
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

    def test_help_mentions_hetzner(self):
        r = _run_help("--help")
        assert "Hetzner" in r.stdout or "hetzner" in r.stdout.lower()

    def test_help_mentions_claude_code(self):
        r = _run_help("--help")
        assert "Claude Code" in r.stdout

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


# ── content checks ───────────────────────────────────────────────────────


class TestContentChecks:
    def test_mentions_user_terry(self):
        src = SCRIPT.read_text()
        assert "terry" in src

    def test_mentions_fnm(self):
        src = SCRIPT.read_text()
        assert "fnm" in src

    def test_mentions_tailscale(self):
        src = SCRIPT.read_text()
        assert "Tailscale" in src or "tailscale" in src.lower()

    def test_mentions_uv(self):
        src = SCRIPT.read_text()
        assert "uv" in src

    def test_mentions_pnpm(self):
        src = SCRIPT.read_text()
        assert "pnpm" in src

    def test_mentions_tmux_config(self):
        src = SCRIPT.read_text()
        assert ".tmux.conf" in src

