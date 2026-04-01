from __future__ import annotations

"""Tests for effectors/pharos-env.sh — bash script tested via subprocess."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-env.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_command_with_env(
    tmp_path: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    """Run pharos-env.sh with given args and optional env overrides."""
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

    def test_help_mentions_systemd(self):
        r = self._run_help("--help")
        assert "systemd" in r.stdout

    def test_help_no_stderr(self):
        r = self._run_help("--help")
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


# ── environment setup tests ─────────────────────────────────────────────


class TestEnvironmentSetup:
    def test_sets_home(self, tmp_path):
        """Verify HOME is set to /home/terry."""
        # Use printenv to check environment variables
        r = _run_command_with_env(tmp_path, "printenv", "HOME")
        assert r.returncode == 0
        assert r.stdout.strip() == "/home/terry"

    def test_sets_path(self, tmp_path):
        """Verify PATH contains expected components."""
        r = _run_command_with_env(tmp_path, "printenv", "PATH")
        assert r.returncode == 0
        path = r.stdout.strip()
        assert "/home/terry/.local/bin" in path
        assert "/home/terry/.cargo/bin" in path
        assert "/home/terry/.bun/bin" in path
        assert "/home/terry/go/bin" in path
        assert "/home/terry/.nix-profile/bin" in path
        assert "/nix/var/nix/profiles/default/bin" in path
        assert "/usr/local/bin" in path
        assert "/usr/bin" in path
        assert "/bin" in path

    def test_executes_command(self, tmp_path):
        """Verify the wrapper execs the given command successfully."""
        r = _run_command_with_env(tmp_path, "echo", "hello from pharos-env")
        assert r.returncode == 0
        assert r.stdout.strip() == "hello from pharos-env"

    def test_sources_zshenv_local(self, tmp_path):
        """Verify .zshenv.local is sourced if present."""
        # For this test, verify the sourcing block exists
        src = SCRIPT.read_text()
        assert 'if [ -f "$HOME/.zshenv.local" ]; then' in src
        assert "set -a" in src
        assert 'source "$HOME/.zshenv.local"' in src
        assert "set +a" in src
