from __future__ import annotations

"""Tests for effectors/tmux-osc52.sh — OSC 52 clipboard copy via tmux."""

import base64
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

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


class FakeTmux:
    """Context manager that installs a fake tmux on PATH and cleans up."""

    def __init__(self, stdout: str, use_printf: bool = False):
        self._stdout = stdout
        self._use_printf = use_printf
        self.dir: str = ""
        self.path: str = ""

    def __enter__(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "tmux")
        cmd = f'printf "%s" "{self._stdout}"' if self._use_printf else f'echo "{self._stdout}"'
        with open(self.path, "w") as f:
            f.write(f'#!/bin/bash\nif [ "$1" = "capture-pane" ]; then\n  {cmd}\nfi\n')
        os.chmod(self.path, 0o755)
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)

    def env(self, base: dict | None = None) -> dict:
        e = (base or os.environ).copy()
        e["PATH"] = self.dir + ":" + e.get("PATH", "")
        return e


class TtyFile:
    """Context manager that provides a temp file as a fake TTY device."""

    def __init__(self):
        self.path: str = ""

    def __enter__(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".tty", delete=False)
        f.close()
        self.path = f.name
        return self

    def __exit__(self, *exc):
        if self.path:
            os.unlink(self.path)

    def read_bytes(self) -> bytes:
        return open(self.path, "rb").read()


def _expected_osc52(raw_bytes: bytes) -> bytes:
    """Build the expected OSC 52 escape sequence for given raw content."""
    b64 = base64.b64encode(raw_bytes).decode().replace("\n", "")
    return f"\033]52;c;{b64}\007".encode()


def _extract_b64(osc_bytes: bytes) -> str:
    """Extract the base64 portion from an OSC 52 sequence."""
    seq = osc_bytes.decode()
    start = seq.index("52;c;") + 5
    end = seq.index("\007", start)
    return seq[start:end]


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
    # echo adds trailing newline, so actual raw output is "hello world\n"
    raw_expected = pane_content.encode() + b"\n"

    with FakeTmux(pane_content) as tmux, TtyFile() as tty:
        r = _run(["%0", tty.path], env=tmux.env())
        assert r.returncode == 0, f"stderr: {r.stderr}"

        written = tty.read_bytes()
        expected = _expected_osc52(raw_expected)
        assert written == expected, f"got {written!r}, expected {expected!r}"


def test_empty_pane_still_writes_osc52():
    """Empty tmux pane produces a valid OSC 52 sequence."""
    # echo "" outputs just a newline
    raw_expected = b"\n"

    with FakeTmux("") as tmux, TtyFile() as tty:
        r = _run(["%0", tty.path], env=tmux.env())
        assert r.returncode == 0

        written = tty.read_bytes()
        expected = _expected_osc52(raw_expected)
        assert written == expected


def test_multiline_pane_content():
    """Multi-line pane content is base64-encoded without newlines."""
    lines = "line1\nline2\nline3"
    # printf does NOT add trailing newline
    raw_expected = lines.encode()

    with FakeTmux(lines, use_printf=True) as tmux, TtyFile() as tty:
        r = _run(["%0", tty.path], env=tmux.env())
        assert r.returncode == 0

        written = tty.read_bytes()
        expected = _expected_osc52(raw_expected)
        assert written == expected


def test_special_characters_in_pane():
    """Unicode and special chars in pane content survive the round trip."""
    pane_content = "hello 🌍 café"
    # printf does NOT add trailing newline
    raw_expected = pane_content.encode()

    with FakeTmux(pane_content, use_printf=True) as tmux, TtyFile() as tty:
        r = _run(["%0", tty.path], env=tmux.env())
        assert r.returncode == 0

        written = tty.read_bytes()
        expected = _expected_osc52(raw_expected)
        assert written == expected


def test_base64_has_no_newlines():
    """The base64 output in OSC 52 sequence must not embedded newlines."""
    long_content = "x" * 1000

    with FakeTmux(long_content, use_printf=True) as tmux, TtyFile() as tty:
        r = _run(["%0", tty.path], env=tmux.env())
        assert r.returncode == 0

        written = tty.read_bytes()
        b64_part = _extract_b64(written)
        assert "\n" not in b64_part
        # Verify it decodes back to the original
        assert base64.b64decode(b64_part) == long_content.encode()


def test_passes_pane_id_to_tmux():
    """Script passes the correct pane ID to tmux capture-pane."""
    fake_tmux_dir = tempfile.mkdtemp()
    log_path = os.path.join(fake_tmux_dir, "args.log")
    fake_tmux_path = os.path.join(fake_tmux_dir, "tmux")
    with open(fake_tmux_path, "w") as f:
        f.write(f'#!/bin/bash\necho "$@" > {log_path}\necho "output"')
    os.chmod(fake_tmux_path, 0o755)

    with TtyFile() as tty:
        env = os.environ.copy()
        env["PATH"] = fake_tmux_dir + ":" + env.get("PATH", "")

        r = _run(["%42", tty.path], env=env)
        assert r.returncode == 0

        logged_args = open(log_path).read().strip()
        assert "capture-pane" in logged_args
        assert "-p" in logged_args
        assert "-t" in logged_args
        assert "%42" in logged_args

    shutil.rmtree(fake_tmux_dir, ignore_errors=True)


def test_osc52_escape_sequence_format():
    """Output strictly follows \\033]52;c;<b64>\\007 format."""
    with FakeTmux("test", use_printf=True) as tmux, TtyFile() as tty:
        r = _run(["%0", tty.path], env=tmux.env())
        assert r.returncode == 0

        written = tty.read_bytes()
        prefix = b"\033]52;c;"
        assert written[: len(prefix)] == prefix
        assert written[-1:] == b"\007"
        # Middle portion should be pure base64 chars
        b64_part = written[len(prefix) : -1].decode()
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in b64_part)
