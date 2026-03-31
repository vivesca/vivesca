from __future__ import annotations

"""Tests for tmux-osc52.sh — copy tmux pane to clipboard via OSC 52."""

import base64
import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "tmux-osc52.sh"


# ── helpers ───────────────────────────────────────────────────────────


def _run(args: list[str], **kw) -> subprocess.CompletedProcess:
    """Run the script with given args."""
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        **kw,
    )


def _fake_tmux(output: str) -> str:
    """Create a fake tmux script that prints the given output and return its path."""
    fd, path = tempfile.mkstemp(suffix=".sh")
    os.write(fd, f"#!/bin/bash\nif [[ \"$1\" == \"capture-pane\" ]]; then\necho -n '{output}'\nfi\n".encode())
    os.close(fd)
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
    return path


# ── help flag tests ───────────────────────────────────────────────────


def test_help_flag_short():
    """-h prints usage from the script header."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout or "tmux-osc52.sh" in r.stdout


def test_help_flag_long():
    """--help prints usage from the script header."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout or "tmux-osc52.sh" in r.stdout


def test_help_prints_lines_2_and_3():
    """Help extracts exactly lines 2-3 of the script."""
    r = _run(["-h"])
    lines = r.stdout.strip().splitlines()
    assert len(lines) == 2
    assert "Copy current tmux pane" in lines[0]
    assert "Usage:" in lines[1]


# ── normal operation tests ────────────────────────────────────────────


def test_writes_osc52_to_tty():
    """Script writes OSC 52 escape sequence with base64'd pane content to TTY."""
    pane_content = "hello world"
    fake_tmux = _fake_tmux(pane_content)
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False) as f:
            tty_path = f.name

        env = os.environ.copy()
        # Put fake tmux first on PATH
        fake_dir = os.path.dirname(fake_tmux)
        fake_name = os.path.basename(fake_tmux)
        # Create a symlink named 'tmux' pointing to our fake
        tmux_link = os.path.join(fake_dir, "tmux")
        if os.path.exists(tmux_link):
            os.remove(tmux_link)
        os.symlink(fake_tmux, tmux_link)
        env["PATH"] = fake_dir + ":" + env.get("PATH", "")

        r = subprocess.run(
            ["bash", str(SCRIPT), "test-pane", tty_path],
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"

        with open(tty_path, "rb") as f:
            written = f.read()

        # Should be OSC 52: \033]52;c;<base64>\007
        expected_b64 = base64.b64encode(pane_content.encode()).decode().replace("\n", "")
        expected = f"\033]52;c;{expected_b64}\007".encode()
        assert written == expected, f"got {written!r}, expected {expected!r}"
    finally:
        os.unlink(fake_tmux)
        tmux_link = os.path.join(os.path.dirname(fake_tmux), "tmux")
        if os.path.exists(tmux_link):
            os.remove(tmux_link)
        if os.path.exists(tty_path):
            os.unlink(tty_path)


def test_osc52_multiline_content():
    """Multi-line pane content is properly base64'd and written."""
    pane_content = "line1\nline2\nline3"
    fake_tmux = _fake_tmux(pane_content)
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False) as f:
            tty_path = f.name

        env = os.environ.copy()
        fake_dir = os.path.dirname(fake_tmux)
        tmux_link = os.path.join(fake_dir, "tmux")
        if os.path.exists(tmux_link):
            os.remove(tmux_link)
        os.symlink(fake_tmux, tmux_link)
        env["PATH"] = fake_dir + ":" + env.get("PATH", "")

        r = subprocess.run(
            ["bash", str(SCRIPT), "my-pane", tty_path],
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"

        with open(tty_path, "rb") as f:
            written = f.read()

        expected_b64 = base64.b64encode(pane_content.encode()).decode().replace("\n", "")
        expected = f"\033]52;c;{expected_b64}\007".encode()
        assert written == expected
    finally:
        os.unlink(fake_tmux)
        tmux_link = os.path.join(os.path.dirname(fake_tmux), "tmux")
        if os.path.exists(tmux_link):
            os.remove(tmux_link)
        if os.path.exists(tty_path):
            os.unlink(tty_path)


def test_osc52_empty_pane():
    """Empty pane content still produces a valid OSC 52 sequence."""
    pane_content = ""
    fake_tmux = _fake_tmux(pane_content)
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False) as f:
            tty_path = f.name

        env = os.environ.copy()
        fake_dir = os.path.dirname(fake_tmux)
        tmux_link = os.path.join(fake_dir, "tmux")
        if os.path.exists(tmux_link):
            os.remove(tmux_link)
        os.symlink(fake_tmux, tmux_link)
        env["PATH"] = fake_dir + ":" + env.get("PATH", "")

        r = subprocess.run(
            ["bash", str(SCRIPT), "pane0", tty_path],
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"

        with open(tty_path, "rb") as f:
            written = f.read()

        expected_b64 = base64.b64encode(b"").decode().replace("\n", "")
        expected = f"\033]52;c;{expected_b64}\007".encode()
        assert written == expected
    finally:
        os.unlink(fake_tmux)
        tmux_link = os.path.join(os.path.dirname(fake_tmux), "tmux")
        if os.path.exists(tmux_link):
            os.remove(tmux_link)
        if os.path.exists(tty_path):
            os.unlink(tty_path)


# ── escape sequence structure tests ───────────────────────────────────


def test_output_starts_with_osc52_escape():
    """Output always begins with ESC ]52;c;."""
    fake_tmux = _fake_tmux("abc")
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False) as f:
            tty_path = f.name

        env = os.environ.copy()
        fake_dir = os.path.dirname(fake_tmux)
        tmux_link = os.path.join(fake_dir, "tmux")
        if os.path.exists(tmux_link):
            os.remove(tmux_link)
        os.symlink(fake_tmux, tmux_link)
        env["PATH"] = fake_dir + ":" + env.get("PATH", "")

        subprocess.run(
            ["bash", str(SCRIPT), "p", tty_path],
            capture_output=True,
            env=env,
        )

        with open(tty_path, "rb") as f:
            written = f.read()

        assert written[:7] == b"\033]52;c;"
        assert written[-1:] == b"\007"
    finally:
        os.unlink(fake_tmux)
        tmux_link = os.path.join(os.path.dirname(fake_tmux), "tmux")
        if os.path.exists(tmux_link):
            os.remove(tmux_link)
        if os.path.exists(tty_path):
            os.unlink(tty_path)


def test_base64_has_no_newlines():
    """The base64 payload should contain no newlines (tr -d '\n')."""
    # Use enough content that base64 would normally wrap
    pane_content = "A" * 200
    fake_tmux = _fake_tmux(pane_content)
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False) as f:
            tty_path = f.name

        env = os.environ.copy()
        fake_dir = os.path.dirname(fake_tmux)
        tmux_link = os.path.join(fake_dir, "tmux")
        if os.path.exists(tmux_link):
            os.remove(tmux_link)
        os.symlink(fake_tmux, tmux_link)
        env["PATH"] = fake_dir + ":" + env.get("PATH", "")

        subprocess.run(
            ["bash", str(SCRIPT), "p", tty_path],
            capture_output=True,
            env=env,
        )

        with open(tty_path, "rb") as f:
            written = f.read()

        # Strip the OSC 52 framing to get just the base64 payload
        payload = written[7:-1].decode()  # between \033]52;c; and \007
        assert "\n" not in payload
    finally:
        os.unlink(fake_tmux)
        tmux_link = os.path.join(os.path.dirname(fake_tmux), "tmux")
        if os.path.exists(tmux_link):
            os.remove(tmux_link)
        if os.path.exists(tty_path):
            os.unlink(tty_path)
