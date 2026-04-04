from __future__ import annotations

"""Tests for effectors/plan-exec — deprecated stub tested via subprocess."""

import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "effectors" / "plan-exec"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_shell_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/bin/sh")


# ── help / -h flags ────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_exits_zero(self):
        r = _run("--help")
        assert r.returncode == 0

    def test_h_exits_zero(self):
        r = _run("-h")
        assert r.returncode == 0

    def test_help_prints_deprecation_to_stdout(self):
        r = _run("--help")
        assert "deprecated" in r.stdout.lower()

    def test_help_mentions_sortase(self):
        r = _run("--help")
        assert "sortase" in r.stdout

    def test_help_no_stderr(self):
        r = _run("--help")
        assert r.stderr == ""

    def test_h_no_stderr(self):
        r = _run("-h")
        assert r.stderr == ""


# ── default invocation (no flags) ─────────────────────────────────────


class TestDefaultInvocation:
    def test_no_args_exits_1(self):
        r = _run()
        assert r.returncode == 1

    def test_no_args_prints_deprecation_to_stderr(self):
        r = _run()
        assert "deprecated" in r.stderr.lower()

    def test_no_args_mentions_sortase(self):
        r = _run()
        assert "sortase" in r.stderr

    def test_no_args_no_stdout(self):
        r = _run()
        assert r.stdout == ""

    def test_random_arg_exits_1(self):
        r = _run("somefile.yaml")
        assert r.returncode == 1

    def test_random_arg_stderr_deprecation(self):
        r = _run("somefile.yaml")
        assert "deprecated" in r.stderr.lower()


# ── script permissions ─────────────────────────────────────────────────


class TestPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_is_file(self):
        assert SCRIPT.is_file()
