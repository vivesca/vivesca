from __future__ import annotations

"""Tests for effectors/pharos-env.sh — environment wrapper for systemd services."""

import os
import stat
import subprocess
import tempfile
from pathlib import Path

PHAROS_ENV = Path.home() / "germline/effectors/pharos-env.sh"


def _run(args: list[str], env: dict | None = None, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run pharos-env.sh and return CompletedProcess."""
    return subprocess.run(
        ["/bin/bash", str(PHAROS_ENV), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
        timeout=10,
    )


# ── help flag tests ──────────────────────────────────────────────────


def test_help_long_flag():
    """--help prints usage and exits 0."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage: pharos-env.sh" in r.stdout
    assert "Environment wrapper" in r.stdout


def test_help_short_flag():
    """-h prints usage and exits 0."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage: pharos-env.sh" in r.stdout


# ── command execution tests ──────────────────────────────────────────


def test_exec_command():
    """Runs the given command via exec."""
    r = _run(["echo", "hello world"])
    assert r.returncode == 0
    assert r.stdout.strip() == "hello world"


def test_exec_command_with_args():
    """Passes arguments through to the exec'd command."""
    r = _run(["printf", "%s-%s", "foo", "bar"])
    assert r.returncode == 0
    assert r.stdout == "foo-bar"


def test_propagates_exit_code():
    """Forwards the child process exit code."""
    r = _run(["/bin/bash", "-c", "exit 42"])
    assert r.returncode == 42


# ── PATH tests ────────────────────────────────────────────────────────


def test_path_includes_local_bin():
    """PATH includes $HOME/.local/bin."""
    r = _run(["/bin/bash", "-c", "echo $PATH"])
    assert r.returncode == 0
    parts = r.stdout.strip().split(":")
    assert str(Path.home() / ".local/bin") in parts


def test_path_includes_cargo_bin():
    """PATH includes $HOME/.cargo/bin."""
    r = _run(["/bin/bash", "-c", "echo $PATH"])
    parts = r.stdout.strip().split(":")
    assert str(Path.home() / ".cargo/bin") in parts


def test_path_includes_nix_profile():
    """PATH includes $HOME/.nix-profile/bin."""
    r = _run(["/bin/bash", "-c", "echo $PATH"])
    parts = r.stdout.strip().split(":")
    assert str(Path.home() / ".nix-profile/bin") in parts


def test_path_includes_system_dirs():
    """PATH includes standard system directories."""
    r = _run(["/bin/bash", "-c", "echo $PATH"])
    parts = r.stdout.strip().split(":")
    for expected in ("/usr/local/bin", "/usr/bin", "/bin"):
        assert expected in parts


# ── HOME default tests ────────────────────────────────────────────────


def test_home_falls_back_to_expanded_tilde():
    """When HOME is unset, script sets it to expanded ~."""
    env = dict(os.environ)
    env.pop("HOME", None)
    r = subprocess.run(
        ["/bin/bash", str(PHAROS_ENV), "/bin/bash", "-c", "echo $HOME"],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == str(Path.home())


# ── .zshenv.local sourcing tests ──────────────────────────────────────


def test_sources_zshenv_local(tmp_path: Path):
    """Sources $HOME/.zshenv.local when it exists, exporting variables."""
    zshenv = tmp_path / ".zshenv.local"
    zshenv.write_text('export PHAROS_TEST_VAR="from_local"\n')

    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    env.pop("PHAROS_TEST_VAR", None)

    r = subprocess.run(
        ["/bin/bash", str(PHAROS_ENV), "/bin/bash", "-c", "echo $PHAROS_TEST_VAR"],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == "from_local"


def test_no_zshenv_local_no_error(tmp_path: Path):
    """Does not fail when .zshenv.local is absent."""
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)

    r = subprocess.run(
        ["/bin/bash", str(PHAROS_ENV), "echo", "ok"],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == "ok"


# ── error cases ───────────────────────────────────────────────────────


def test_no_args_exits_clean():
    """Running with no arguments: exec with no args is a no-op, exits 0."""
    r = subprocess.run(
        ["/bin/bash", str(PHAROS_ENV)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert r.returncode == 0
    assert r.stdout == ""
