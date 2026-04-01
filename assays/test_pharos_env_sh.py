from __future__ import annotations

"""Tests for effectors/pharos-env.sh — bash script tested via subprocess."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-env.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run(
    *args: str, env: dict[str, str] | None = None
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


def _make_patched_script(tmp_path: Path) -> Path:
    """Create a copy of pharos-env.sh with HOME patched to tmp_path."""
    src = SCRIPT.read_text()
    # Replace the hardcoded HOME line so zshenv.local lookup uses tmp_path
    patched = src.replace(
        'export HOME="/home/terry"',
        f'export HOME="{tmp_path}"',
    )
    patched_path = tmp_path / "pharos-env-test.sh"
    patched_path.write_text(patched)
    patched_path.chmod(0o755)
    return patched_path


def _run_patched(
    tmp_path: Path, *args: str
) -> subprocess.CompletedProcess:
    """Run the HOME-patched copy of pharos-env.sh."""
    script = _make_patched_script(tmp_path)
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        timeout=10,
    )


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def test_help_exits_zero(self):
        r = _run("--help")
        assert r.returncode == 0

    def test_help_short_flag_exits_zero(self):
        r = _run("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_systemd(self):
        r = _run("--help")
        assert "systemd" in r.stdout

    def test_help_no_stderr(self):
        r = _run("--help")
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


# ── environment setup ──────────────────────────────────────────────────


class TestEnvironmentSetup:
    def test_sets_home(self):
        """HOME is hardcoded to /home/terry regardless of caller env."""
        env = os.environ.copy()
        env["HOME"] = "/tmp/somewhere_else"
        r = _run("printenv", "HOME", env=env)
        assert r.returncode == 0
        assert r.stdout.strip() == "/home/terry"

    def test_sets_path(self):
        """PATH contains all expected directories."""
        r = _run("printenv", "PATH")
        assert r.returncode == 0
        path = r.stdout.strip()
        for expected in [
            "/home/terry/.local/bin",
            "/home/terry/.cargo/bin",
            "/home/terry/.bun/bin",
            "/home/terry/go/bin",
            "/home/terry/.nix-profile/bin",
            "/nix/var/nix/profiles/default/bin",
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
        ]:
            assert expected in path, f"{expected} missing from PATH"

    def test_path_local_bin_first(self):
        """User-local bin directories come before system ones."""
        r = _run("printenv", "PATH")
        path = r.stdout.strip()
        local_idx = path.index("/home/terry/.local/bin")
        system_idx = path.index("/usr/bin")
        assert local_idx < system_idx, ".local/bin should precede /usr/bin"

    def test_executes_command(self):
        """Wrapper execs the given command successfully."""
        r = _run("echo", "hello from pharos-env")
        assert r.returncode == 0
        assert r.stdout.strip() == "hello from pharos-env"

    def test_passes_multiple_args(self):
        """All arguments are forwarded to the exec'd command."""
        r = _run("printf", "%s|%s|%s", "a", "b", "c")
        assert r.returncode == 0
        assert r.stdout == "a|b|c"

    def test_nonzero_exit_propagated(self):
        """Child exit code passes through."""
        r = _run("false")
        assert r.returncode != 0

    def test_stderr_passes_through(self):
        """stderr from child is not swallowed."""
        r = _run("bash", "-c", "echo err >&2")
        assert r.returncode == 0
        assert "err" in r.stderr

    def test_stdout_passes_through(self):
        """stdout from child is captured correctly."""
        r = _run("bash", "-c", "echo out")
        assert r.returncode == 0
        assert "out" in r.stdout


# ── zshenv.local sourcing ──────────────────────────────────────────────


class TestZshenvSourcing:
    def test_source_block_in_script(self):
        """Static check: script contains the sourcing block."""
        src = SCRIPT.read_text()
        assert 'if [ -f "$HOME/.zshenv.local" ]; then' in src
        assert "set -a" in src
        assert 'source "$HOME/.zshenv.local"' in src
        assert "set +a" in src

    def test_sources_zshenv_and_exports_vars(self, tmp_path):
        """When .zshenv.local exists, its exports are visible to the child."""
        zshenv = tmp_path / ".zshenv.local"
        zshenv.write_text('export PHAROS_TEST_SECRET="open sesame"\n')
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        r = _run("printenv", "PHAROS_TEST_SECRET", env=env)
        assert r.returncode == 0
        assert r.stdout.strip() == "open sesame"

    def test_missing_zshenv_no_error(self, tmp_path):
        """When .zshenv.local is absent, the script still works fine."""
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        # Ensure no .zshenv.local
        assert not (tmp_path / ".zshenv.local").exists()
        r = _run("true", env=env)
        assert r.returncode == 0

    def test_set_a_exports_without_explicit_export(self, tmp_path):
        """set -a auto-exports variables; no 'export' keyword needed in .zshenv.local."""
        zshenv = tmp_path / ".zshenv.local"
        zshenv.write_text('PHAROS_IMPLICIT_VAR="auto_exported"\n')
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        r = _run("printenv", "PHAROS_IMPLICIT_VAR", env=env)
        assert r.returncode == 0
        assert r.stdout.strip() == "auto_exported"

    def test_zshenv_error_causes_failure(self, tmp_path):
        """If .zshenv.local has a syntax error, the script fails (set -e)."""
        zshenv = tmp_path / ".zshenv.local"
        zshenv.write_text('this is not valid bash syntax !!!!\n')
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        r = _run("true", env=env)
        assert r.returncode != 0


# ── no-argument guard ──────────────────────────────────────────────────


class TestNoArgs:
    def test_no_args_exits_nonzero(self):
        """With no arguments, exec "$@" fails (set -e)."""
        r = _run()
        # exec with no args is a bash error
        assert r.returncode != 0
