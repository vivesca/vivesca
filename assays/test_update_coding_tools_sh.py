from __future__ import annotations

"""Tests for effectors/update-coding-tools.sh — bash script tested via subprocess."""

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "update-coding-tools.sh"


# ── script structure tests ──────────────────────────────────────────────


class TestScriptStructure:
    def test_script_exists(self):
        assert SCRIPT.exists()

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_has_shebang(self):
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line == "#!/usr/bin/env bash"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    path_dirs: list[Path] | None = None,
    tmp_path: Path | None = None,
    replace_path: bool = False,
) -> subprocess.CompletedProcess:
    """Run the script with an optional custom PATH.

    If replace_path=False (default) and path_dirs provided, prepend them to PATH
    keep system entries so essential commands like bash are still found.
    If replace_path=True, use exactly path_dirs as the new PATH (for filtered tests).
    """
    env = os.environ.copy()
    # Unset HOME override if present so script uses tmp_path as HOME
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if path_dirs is not None:
        if replace_path:
            # Use exactly the provided path dirs (already filtered)
            env["PATH"] = os.pathsep.join(str(p) for p in path_dirs)
        else:
            # Prepend custom path dirs, keep system PATH after
            # This ensures bash is still found but any system-level
            # commands come AFTER our mocks and only gets used if
            # we don't provide a mock
            env["PATH"] = os.pathsep.join(str(p) for p in path_dirs) + os.pathsep + env.get("PATH", "")
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=10,
    )


def _make_mock_bin(tmp_path: Path, name: str, stdout: str = "", exit_code: int = 0) -> Path:
    """Create a mock executable script in tmp_path/bin/<name>."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(f"#!/bin/bash\necho {stdout}\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_recording_bin(tmp_path: Path, name: str, record_file: Path, exit_code: int = 0) -> Path:
    """Create a mock bin that records all args to record_file."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(
        "#!/bin/bash\n"
        f'echo "$@" >> {record_file}\n'
        f"exit {exit_code}\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _log_file(tmp_path: Path) -> Path:
    return tmp_path / ".coding-tools-update.log"


def _health_file(tmp_path: Path) -> Path:
    return tmp_path / ".coding-tools-health.json"


# ── --help tests ────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_exits_zero(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self, tmp_path):
        r = _run_script(["-h"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_help_shows_usage(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "Usage:" in r.stdout

    def test_help_mentions_homebrew(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "Homebrew" in r.stdout


# ── homebrew check tests ────────────────────────────────────────────────


class TestHomebrewCheck:
    def test_no_brew_exits_1(self, tmp_path):
        """Script exits 1 when Homebrew not found on PATH."""
        # Create a minimal PATH with bash but no brew
        safe_bin = tmp_path / "safe-bin"
        safe_bin.mkdir()
        bash_path = shutil.which("bash")
        if bash_path:
            os.symlink(bash_path, safe_bin / "bash")
        # Build filtered PATH without brew
        filtered = []
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            if not (Path(dir_path) / "brew").exists():
                filtered.append(dir_path)
        r = _run_script(
            env_extra={"PATH": str(safe_bin) + os.pathsep + os.pathsep.join(filtered)},
            tmp_path=tmp_path,
        )
        assert r.returncode == 1


# ── basic execution tests ───────────────────────────────────────────────


class TestBasicExecution:
    def test_creates_log_file(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "brew")
        # Add other required mocks too
        _make_mock_bin(tmp_path, "npm")
        _make_mock_bin(tmp_path, "pnpm")
        _make_mock_bin(tmp_path, "uv")
        _make_mock_bin(tmp_path, "cargo")
        _make_mock_bin(tmp_path, "mas")
        _make_mock_bin(tmp_path, "date")
        # And mocks for the health check commands
        for cmd in ("claude", "opencode", "gemini", "codex", "agent-browser"):
            _make_mock_bin(tmp_path, cmd)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert _log_file(tmp_path).exists()

    def test_creates_health_file(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "brew")
        # Add other required mocks
        _make_mock_bin(tmp_path, "npm")
        _make_mock_bin(tmp_path, "pnpm")
        _make_mock_bin(tmp_path, "uv")
        _make_mock_bin(tmp_path, "cargo")
        _make_mock_bin(tmp_path, "mas")
        _make_mock_bin(tmp_path, "date")
        # And mocks for the health check commands
        for cmd in ("claude", "opencode", "gemini", "codex", "agent-browser"):
            _make_mock_bin(tmp_path, cmd)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert _health_file(tmp_path).exists()
