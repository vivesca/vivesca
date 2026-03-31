from __future__ import annotations

"""Tests for effectors/tmux-osc52.sh — OSC 52 clipboard copy via tmux."""

import base64
import os
import stat
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "effectors" / "tmux-osc52.sh"


def _run(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    """Run the script with given args, capturing output."""
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def _fake_tmux(output: str):
    """Return a function that simulates tmux capture-pane."""
    def fake_capture_pane(*args, **kwargs):
        r = subprocess.CompletedProcess(
            args=args, returncode=0, stdout=output, stderr=""
        )
        return r
    return fake_capture_pane


# ── Help flag tests ──────────────────────────────────────────────────


def test_help_flag_long():
    """--help prints usage and exits 0."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "tmux-osc52.sh" in r.stdout or "pane" in r.stdout.lower()


def test_help_flag_short():
    """-h prints usage and exits 0."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage" in r.stdout or "pane" in r.stdout.lower()


# ── Functional tests with fake tmux and temp TTY ─────────────────────


def test_writes_osc52_to_tty():
    """Script writes OSC 52 escape sequence to the given TTY file."""
    pane_content = "hello world"
    b64 = base64.b64encode(pane_content.encode()).decode().replace("\n", "")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False) as tty:
        tty_path = tty.name

    try:
        env = os.environ.copy()
        # Create a fake tmux script that outputs our content
        fake_tmux_dir = tempfile.mkdtemp()
        fake_tmux_path = os.path.join(fake_tmux_dir, "tmux")
        with open(fake_tmux_path, "w") as f:
            f.write(f'#!/bin/bash\nif [ "$1" = "capture-pane" ]; then\n  echo "{pane_content}"\nfi\n')
        os.chmod(fake_tmux_path, 0o755)

        env["PATH"] = fake_tmux_dir + ":" + env.get("PATH", "")

        r = _run(["%0", tty_path], env=env)
        assert r.returncode == 0, f"stderr: {r.stderr}"

        written = open(tty_path, "rb").read()
        expected = f"\033]52;c;{b64}\007".encode()
        assert written == expected, f"got {written!r}, expected {expected!r}"
    finally:
        os.unlink(tty_path)
        import shutil
        shutil.rmtree(fake_tmux_dir, ignore_errors=True)


def test_empty_pane_still_writes_osc52():
    """Empty tmux pane produces a valid (empty base64) OSC 52 sequence."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False) as tty:
        tty_path = tty.name

    try:
        fake_tmux_dir = tempfile.mkdtemp()
        fake_tmux_path = os.path.join(fake_tmux_dir, "tmux")
        with open(fake_tmux_path, "w") as f:
            f.write('#!/bin/bash\nif [ "$1" = "capture-pane" ]; then\n  echo ""\nfi\n')
        os.chmod(fake_tmux_path, 0o755)

        env = os.environ.copy()
        env["PATH"] = fake_tmux_dir + ":" + env.get("PATH", "")

        r = _run(["%0", tty_path], env=env)
        assert r.returncode == 0

        written = open(tty_path, "rb").read()
        # base64 of "\n" (what echo "" produces) = "Cg=="
        assert b"\033]52;c;" in written
        assert b"\007" in written
    finally:
        os.unlink(tty_path)
        import shutil
        shutil.rmtree(fake_tmux_dir, ignore_errors=True)


def test_multiline_pane_content():
    """Multi-line pane content is base64-encoded without newlines."""
    lines = "line1\nline2\nline3"
    # base64 of "line1\nline2\nline3\n" (echo adds trailing newline)
    raw = lines + "\n"
    b64 = base64.b64encode(raw.encode()).decode().replace("\n", "")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False) as tty:
        tty_path = tty.name

    try:
        fake_tmux_dir = tempfile.mkdtemp()
        fake_tmux_path = os.path.join(fake_tmux_dir, "tmux")
        with open(fake_tmux_path, "w") as f:
            f.write(f'#!/bin/bash\nif [ "$1" = "capture-pane" ]; then\n  printf "%s" "{lines}"\nfi\n')
        os.chmod(fake_tmux_path, 0o755)

        env = os.environ.copy()
        env["PATH"] = fake_tmux_dir + ":" + env.get("PATH", "")

        r = _run(["%0", tty_path], env=env)
        assert r.returncode == 0

        written = open(tty_path, "rb").read()
        expected = f"\033]52;c;{b64}\007".encode()
        assert written == expected
    finally:
        os.unlink(tty_path)
        import shutil
        shutil.rmtree(fake_tmux_dir, ignore_errors=True)


def test_special_characters_in_pane():
    """Unicode and special chars in pane content survive the round trip."""
    pane_content = "hello 🌍 café"
    b64 = base64.b64encode(pane_content.encode()).decode().replace("\n", "")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False) as tty:
        tty_path = tty.name

    try:
        fake_tmux_dir = tempfile.mkdtemp()
        fake_tmux_path = os.path.join(fake_tmux_dir, "tmux")
        with open(fake_tmux_path, "w") as f:
            f.write(f'#!/bin/bash\nif [ "$1" = "capture-pane" ]; then\n  printf "%s" "{pane_content}"\nfi\n')
        os.chmod(fake_tmux_path, 0o755)

        env = os.environ.copy()
        env["PATH"] = fake_tmux_dir + ":" + env.get("PATH", "")

        r = _run(["%0", tty_path], env=env)
        assert r.returncode == 0

        written = open(tty_path, "rb").read()
        expected = f"\033]52;c;{b64}\007".encode()
        assert written == expected
    finally:
        os.unlink(tty_path)
        import shutil
        shutil.rmtree(fake_tmux_dir, ignore_errors=True)


def test_base64_has_no_newlines():
    """The base64 output in OSC 52 sequence must not contain newlines."""
    long_content = "x" * 1000
    b64 = base64.b64encode(long_content.encode()).decode().replace("\n", "")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False) as tty:
        tty_path = tty.name

    try:
        fake_tmux_dir = tempfile.mkdtemp()
        fake_tmux_path = os.path.join(fake_tmux_dir, "tmux")
        with open(fake_tmux_path, "w") as f:
            f.write(f'#!/bin/bash\nif [ "$1" = "capture-pane" ]; then\n  printf "%s" "{long_content}"\nfi\n')
        os.chmod(fake_tmux_path, 0o755)

        env = os.environ.copy()
        env["PATH"] = fake_tmux_dir + ":" + env.get("PATH", "")

        r = _run(["%0", tty_path], env=env)
        assert r.returncode == 0

        written = open(tty_path, "rb").read()
        # Extract the base64 portion between the delimiters
        seq = written.decode()
        start = seq.index("52;c;") + 5
        end = seq.index("\007", start)
        b64_part = seq[start:end]
        assert "\n" not in b64_part
        assert b64_part == b64
    finally:
        os.unlink(tty_path)
        import shutil
        shutil.rmtree(fake_tmux_dir, ignore_errors=True)


def test_passes_pane_id_to_tmux():
    """Script passes the correct pane ID to tmux capture-pane."""
    fake_tmux_dir = tempfile.mkdtemp()
    log_path = os.path.join(fake_tmux_dir, "args.log")
    fake_tmux_path = os.path.join(fake_tmux_dir, "tmux")
    with open(fake_tmux_path, "w") as f:
        f.write(f'#!/bin/bash\necho "$@" > {log_path}\necho "output"')
    os.chmod(fake_tmux_path, 0o755)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False) as tty:
        tty_path = tty.name

    try:
        env = os.environ.copy()
        env["PATH"] = fake_tmux_dir + ":" + env.get("PATH", "")

        r = _run(["%42", tty_path], env=env)
        assert r.returncode == 0

        logged_args = open(log_path).read().strip()
        assert "capture-pane" in logged_args
        assert "-p" in logged_args
        assert "-t" in logged_args
        assert "%42" in logged_args
    finally:
        os.unlink(tty_path)
        import shutil
        shutil.rmtree(fake_tmux_dir, ignore_errors=True)
