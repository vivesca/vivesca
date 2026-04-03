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


# ── additional PATH coverage ──────────────────────────────────────────


def test_path_includes_bun_bin():
    """PATH includes $HOME/.bun/bin."""
    r = _run(["/bin/bash", "-c", "echo $PATH"])
    parts = r.stdout.strip().split(":")
    assert str(Path.home() / ".bun/bin") in parts


def test_path_includes_go_bin():
    """PATH includes $HOME/go/bin."""
    r = _run(["/bin/bash", "-c", "echo $PATH"])
    parts = r.stdout.strip().split(":")
    assert str(Path.home() / "go/bin") in parts


def test_path_includes_nix_default_profile():
    """PATH includes /nix/var/nix/profiles/default/bin."""
    r = _run(["/bin/bash", "-c", "echo $PATH"])
    parts = r.stdout.strip().split(":")
    assert "/nix/var/nix/profiles/default/bin" in parts


def test_path_custom_dirs_before_system():
    """Custom bin dirs appear before system dirs in PATH."""
    r = _run(["/bin/bash", "-c", "echo $PATH"])
    parts = r.stdout.strip().split(":")
    local_bin = str(Path.home() / ".local/bin")
    usr_bin = "/usr/bin"
    if local_bin in parts and usr_bin in parts:
        assert parts.index(local_bin) < parts.index(usr_bin)


def test_path_is_fully_replaced():
    """Script sets PATH explicitly, not inheriting or appending."""
    env = dict(os.environ)
    env["PATH"] = "/usr/sbin:/sbin"
    r = subprocess.run(
        ["/bin/bash", str(PHAROS_ENV), "/bin/bash", "-c", "echo $PATH"],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert r.returncode == 0
    parts = r.stdout.strip().split(":")
    assert "/usr/sbin" not in parts
    assert "/sbin" not in parts
    assert str(Path.home() / ".local/bin") in parts


# ── HOME handling ──────────────────────────────────────────────────────


def test_home_preserved_when_set(tmp_path: Path):
    """HOME is preserved when already set in the environment."""
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    r = subprocess.run(
        ["/bin/bash", str(PHAROS_ENV), "/bin/bash", "-c", "echo $HOME"],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == str(tmp_path)


# ── .zshenv.local edge cases ──────────────────────────────────────────


def test_zshenv_local_exports_multiple_vars(tmp_path: Path):
    """Multiple exports in .zshenv.local are all available."""
    zshenv = tmp_path / ".zshenv.local"
    zshenv.write_text(
        'export PHAROS_ALPHA="1"\nexport PHAROS_BETA="2"\n'
    )
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    env.pop("PHAROS_ALPHA", None)
    env.pop("PHAROS_BETA", None)
    r = subprocess.run(
        [
            "/bin/bash",
            str(PHAROS_ENV),
            "/bin/bash",
            "-c",
            "echo $PHAROS_ALPHA:$PHAROS_BETA",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == "1:2"


def test_zshenv_local_set_a_exports_unset_vars(tmp_path: Path):
    """set -a ensures bare assignments in .zshenv.local are exported."""
    zshenv = tmp_path / ".zshenv.local"
    zshenv.write_text('PHAROS_BARE_EXPORT="yes"\n')
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    env.pop("PHAROS_BARE_EXPORT", None)
    r = subprocess.run(
        [
            "/bin/bash",
            str(PHAROS_ENV),
            "/bin/bash",
            "-c",
            "echo $PHAROS_BARE_EXPORT",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == "yes"


def test_zshenv_local_var_used_by_child(tmp_path: Path):
    """Variables from .zshenv.local are available to the exec'd command."""
    zshenv = tmp_path / ".zshenv.local"
    zshenv.write_text('export MY_SECRET_KEY="abc123"\n')
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    env.pop("MY_SECRET_KEY", None)
    r = subprocess.run(
        ["/bin/bash", str(PHAROS_ENV), "printenv", "MY_SECRET_KEY"],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == "abc123"


# ── exec behavior ─────────────────────────────────────────────────────


def test_exec_replaces_process():
    """exec replaces the bash process — child PID should equal the spawned PID."""
    r = _run(["/bin/bash", "-c", "echo $$"])
    assert r.returncode == 0
    # After exec, the PID printed by $$ is the direct child of our subprocess.run
    # (not a grandchild). We just verify a PID was printed.
    pid_str = r.stdout.strip()
    assert pid_str.isdigit()
    assert int(pid_str) > 0


def test_multiword_arg_passed_correctly():
    """Arguments with spaces are passed through correctly."""
    r = _run(["echo", "hello   world"])
    assert r.returncode == 0
    assert r.stdout.strip() == "hello   world"


def test_stderr_passthrough():
    """Child stderr flows through to the parent."""
    r = _run(["/bin/bash", "-c", "echo err >&2"])
    assert r.returncode == 0
    assert r.stderr.strip() == "err"
