from __future__ import annotations

"""Tests for effectors/perplexity.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "perplexity.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    tmp_path: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run perplexity.sh with optional args and environment overrides."""
    env = os.environ.copy()
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=30,
    )


# ── --help tests ────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_exits_zero(self):
        r = _run_script(["--help"])
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self):
        r = _run_script(["-h"])
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run_script(["--help"])
        assert "Usage:" in r.stdout

    def test_help_mentions_modes(self):
        r = _run_script(["--help"])
        assert "search" in r.stdout
        assert "ask" in r.stdout
        assert "research" in r.stdout
        assert "reason" in r.stdout


# ── file basics ─────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/usr/bin/env bash")

    def test_has_set_euo(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src


# ── script permissions ──────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()


# ── invalid usage tests ─────────────────────────────────────────────────


class TestInvalidUsage:
    def test_no_args_exits_1(self):
        r = _run_script([])
        assert r.returncode == 1

    def test_unknown_mode_exits_1(self):
        r = _run_script(["invalid-mode", "test query"], env_extra={"PERPLEXITY_API_KEY": "fake-key"})
        assert r.returncode == 1
        assert "Unknown mode" in r.stderr

    def test_missing_query_exits_1(self):
        r = _run_script(["search"], env_extra={"PERPLEXITY_API_KEY": "fake-key"})
        assert r.returncode == 1
