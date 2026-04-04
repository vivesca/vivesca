from __future__ import annotations

"""Tests for effectors/update-coding-tools.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "effectors" / "update-coding-tools.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_help(*args: str) -> subprocess.CompletedProcess:
    """Run the script with --help/-h."""
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


def _run_with_fake_home(
    tmp_path: Path, extra_env: dict | None = None
) -> subprocess.CompletedProcess:
    """Run the script with HOME=tmp_path and optional extra env vars."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def _make_fake_command(name: str, work_dir: Path, output: str = "", exit_code: int = 0) -> Path:
    """Create a fake command that prints *output* and exits with *exit_code*."""
    bindir = work_dir / "bin"
    bindir.mkdir(exist_ok=True)
    fake = bindir / name
    echo_line = f'echo "{output}"' if output else ""
    fake.write_text(f"#!/bin/bash\n{echo_line}\nexit {exit_code}\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return bindir


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def test_help_exits_zero(self):
        r = _run_help("--help")
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self):
        r = _run_help("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run_help("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_brew(self):
        r = _run_help("--help")
        assert "brew" in r.stdout

    def test_help_mentions_macos(self):
        r = _run_help("--help")
        assert "macOS" in r.stdout


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/usr/bin/env bash")

    def test_has_set_e(self):
        src = SCRIPT.read_text()
        assert "set -e" in src


# ── no brew found ─────────────────────────────────────────────────────


class TestNoBrewFound:
    def test_exits_1_when_no_brew(self, tmp_path):
        """When brew is not on PATH, script exits 1 with error message."""
        # Create a bindir with no brew, but include /usr/bin for bash/date/etc
        bindir = tmp_path / "empty_bin"
        bindir.mkdir()
        env = os.environ.copy()
        env["PATH"] = str(bindir) + os.pathsep + "/usr/bin"
        env["HOME"] = str(tmp_path)
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.returncode == 1
        assert "Homebrew not found" in r.stderr


# ── script permissions ──────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()
