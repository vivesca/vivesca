from __future__ import annotations

"""Tests for effectors/update-coding-tools.sh — bash script tested via subprocess."""

import os
import re
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
) -> subprocess.CompletedProcess:
    """Run the script with an optional custom PATH and HOME."""
    env = os.environ.copy()
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if path_dirs is not None:
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
    script.write_text(f"#!/bin/bash\necho -n '{stdout}'\nexit {exit_code}\n")
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

    def test_help_does_not_create_log(self, tmp_path):
        _run_script(["--help"], tmp_path=tmp_path)
        assert not (tmp_path / ".coding-tools-update.log").exists()

    def test_help_mentions_log_file(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "log" in r.stdout.lower()
        assert ".coding-tools-update.log" in r.stdout


# ── homebrew check tests ────────────────────────────────────────────────


class TestHomebrewCheck:
    def test_no_brew_exits_1(self, tmp_path):
        """Script exits 1 when brew not found on PATH."""
        # Filter PATH to exclude any dir with brew
        filtered_path = []
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            if not (Path(dir_path) / "brew").exists():
                filtered_path.append(Path(dir_path))
        r = _run_script(path_dirs=filtered_path, tmp_path=tmp_path)
        assert r.returncode == 1

    def test_no_brew_writes_error(self, tmp_path):
        filtered_path = []
        for dir_path in os.environ.get("PATH", "").split(os.pathsep):
            if not dir_path:
                continue
            if not (Path(dir_path) / "brew").exists():
                filtered_path.append(Path(dir_path))
        r = _run_script(path_dirs=filtered_path, tmp_path=tmp_path)
        assert "Homebrew not found" in r.stderr


# ── logging tests ───────────────────────────────────────────────────────


class TestLogging:
    def test_creates_log_file(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "brew")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        assert (tmp_path / ".coding-tools-update.log").exists()

    def test_log_contains_date_marker(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "brew")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = (tmp_path / ".coding-tools-update.log").read_text()
        assert "===" in log_text

    def test_log_contains_year(self, tmp_path):
        bindir = _make_mock_bin(tmp_path, "brew")
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        log_text = (tmp_path / ".coding-tools-update.log").read_text()
        assert re.search(r"20\d{2}", log_text) is not None


# ── tool health tests ───────────────────────────────────────────────────


class TestToolHealth:
    def test_creates_health_file(self, tmp_path):
        # Make mocks for all required tools
        bindir = tmp_path / "bin"
        bindir.mkdir(exist_ok=True)
        for tool in ("brew", "claude", "opencode", "gemini", "codex", "agent-browser", "mas"):
            script = bindir / tool
            script.write_text("#!/bin/bash\nexit 0\n")
            script.chmod(script.stat().st_mode | stat.S_IEXEC)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        health_file = tmp_path / ".coding-tools-health.json"
        assert health_file.exists()

    def test_health_file_status_ok(self, tmp_path):
        bindir = tmp_path / "bin"
        bindir.mkdir(exist_ok=True)
        for tool in ("brew", "claude", "opencode", "gemini", "codex", "agent-browser", "mas"):
            script = bindir / tool
            script.write_text("#!/bin/bash\nexit 0\n")
            script.chmod(script.stat().st_mode | stat.S_IEXEC)
        _run_script(path_dirs=[bindir], tmp_path=tmp_path)
        import json
        health = json.loads((tmp_path / ".coding-tools-health.json").read_text())
        assert health["status"] == "ok"
        assert health["failures"] == []
