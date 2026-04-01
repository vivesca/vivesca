from __future__ import annotations

"""Tests for effectors/golem-daemon-wrapper.sh — bash wrapper that sources env and execs golem-daemon."""

import os
import stat
import subprocess
import tempfile
from pathlib import Path

WRAPPER = Path.home() / "germline" / "effectors" / "golem-daemon-wrapper.sh"
DAEMON = Path.home() / "germline" / "effectors" / "golem-daemon"


# ── help flags ────────────────────────────────────────────────────────


def test_golem_daemon_wrapper_help_flag_exits_zero():
    """--help prints usage and exits 0."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0


def test_help_flag_outputs_usage():
    """--help output contains description and usage."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    out = r.stdout
    assert "golem-daemon-wrapper" in out
    assert "Usage:" in out


def test_help_flag_outputs_description():
    """--help output mentions its purpose."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    assert "sources API keys" in r.stdout


def test_help_flag_no_stderr():
    """--help produces no stderr."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    assert r.stderr == ""


def test_short_help_flag():
    """-h works the same as --help."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "-h"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "golem-daemon-wrapper" in r.stdout


def test_help_outputs_no_user_options():
    """--help mentions managed by supervisor."""
    r = subprocess.run(
        ["bash", str(WRAPPER), "--help"],
        capture_output=True,
        text=True,
    )
    assert "Managed by" in r.stdout


# ── file attributes ───────────────────────────────────────────────────


def test_wrapper_is_executable():
    """Wrapper script has execute permission."""
    st = WRAPPER.stat()
    assert st.st_mode & stat.S_IXUSR


def test_wrapper_is_bash_script():
    """Wrapper starts with a bash shebang."""
    first_line = WRAPPER.read_text().splitlines()[0]
    assert first_line.startswith("#!/usr/bin/env bash") or first_line.startswith("#!/bin/bash")


def test_wrapper_uses_set_strict():
    """Wrapper uses strict mode (set -euo pipefail)."""
    content = WRAPPER.read_text()
    assert "set -euo pipefail" in content


# ── env sourcing ──────────────────────────────────────────────────────


def test_env_file_sourced_when_present():
    """If ~/.env.fly exists, its exported vars reach the exec'd process."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text("TEST_GOLEM_WRAPPER_VAR=hello123\n")

        # Create a shim python3 that prints the var and exits
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text("#!/bin/bash\necho \"VAR=$TEST_GOLEM_WRAPPER_VAR\"\nexit 0\n")
        shim.chmod(0o755)

        # Also need a fake germline dir so the path resolves
        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "VAR=hello123" in r.stdout, f"Expected sourced var in output, got: {r.stdout!r} stderr: {r.stderr!r}"


def test_no_env_file_still_works():
    """If ~/.env.fly is absent, the script still proceeds to exec."""
    with tempfile.TemporaryDirectory() as td:
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text("#!/bin/bash\necho \"LAUNCHED\"\nexit 0\n")
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "LAUNCHED" in r.stdout, f"Expected LAUNCHED in output, got: {r.stdout!r} stderr: {r.stderr!r}"


# ── exec target ───────────────────────────────────────────────────────


def test_exec_calls_daemon_with_start_foreground():
    """The wrapper execs python3 on golem-daemon with start --foreground."""
    with tempfile.TemporaryDirectory() as td:
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        # Print all args so we can verify the command line
        shim.write_text('#!/bin/bash\necho "ARGS: $@"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "start" in r.stdout
        assert "--foreground" in r.stdout


def test_exec_uses_correct_daemon_path():
    """The wrapper execs the daemon from $HOME/germline/effectors/golem-daemon."""
    content = WRAPPER.read_text()
    assert '$HOME/germline/effectors/golem-daemon' in content


def test_uses_exec_not_just_run():
    """The wrapper uses exec to replace the shell process."""
    content = WRAPPER.read_text()
    assert "exec python3" in content


# ── env.fly export behavior ──────────────────────────────────────────


def test_env_vars_are_exported():
    """set -a ensures vars from .env.fly are exported to child process."""
    with tempfile.TemporaryDirectory() as td:
        env_file = Path(td) / ".env.fly"
        env_file.write_text("MY_SECRET_KEY=abc123\nMY_OTHER_VAR=xyz\n")

        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        # Use env to show exported vars
        shim.write_text('#!/bin/bash\nenv\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "MY_SECRET_KEY=abc123" in r.stdout
        assert "MY_OTHER_VAR=xyz" in r.stdout


# ── edge cases ────────────────────────────────────────────────────────


def test_no_args_proceeds_to_exec():
    """Running with no arguments proceeds to exec (not --help)."""
    with tempfile.TemporaryDirectory() as td:
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "RAN"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}"',
            ],
            capture_output=True,
            text=True,
        )
        assert "RAN" in r.stdout


def test_unknown_arg_still_execs():
    """Unknown flags (not --help/-h) pass through and exec runs."""
    with tempfile.TemporaryDirectory() as td:
        shim_dir = Path(td) / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text('#!/bin/bash\necho "RAN_WITH_ARGS: $@"\nexit 0\n')
        shim.chmod(0o755)

        fake_germline = Path(td) / "germline" / "effectors"
        fake_germline.mkdir(parents=True)
        fake_daemon = fake_germline / "golem-daemon"
        fake_daemon.write_text("# dummy\n")

        r = subprocess.run(
            [
                "bash", "-c",
                f'HOME={td} PATH={shim_dir}:$PATH bash "{WRAPPER}" --unknown',
            ],
            capture_output=True,
            text=True,
        )
        # The wrapper doesn't pass unknown args to exec; it always execs
        # the daemon with fixed args. But it should still run.
        assert "RAN_WITH_ARGS" in r.stdout
