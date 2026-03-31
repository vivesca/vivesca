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


def _make_fake_tmux_dir(pane_output: str) -> tuple[str, str]:
    """Create a temp dir with a fake tmux script; return (tmpdir, tmux_path)."""
    tmpdir = tempfile.mkdtemp(prefix="osc52_test_")
    # Write pane output to a data file to avoid shell quoting issues
    data_path = os.path.join(tmpdir, "pane_data")
    with open(data_path, "wb") as f:
        f.write(pane_output.encode())
    tmux_path = os.path.join(tmpdir, "tmux")
    with open(tmux_path, "w") as f:
        f.write(f"#!/bin/bash\nif [[ \"$1\" == \"capture-pane\" ]]; then\ncat '{data_path}'\nfi\n")
    os.chmod(tmux_path, os.stat(tmux_path).st_mode | stat.S_IEXEC)
    return tmpdir, tmux_path


def _run_with_fake_tmux(pane_content: str, pane_id: str = "test-pane") -> tuple[int, bytes, str, str]:
    """Run the script with a fake tmux; return (returncode, tty_bytes, stdout, stderr)."""
    tmpdir, _ = _make_fake_tmux_dir(pane_content)
    try:
        tty_fd, tty_path = tempfile.mkstemp(suffix=".tty", dir=tmpdir)
        os.close(tty_fd)

        env = os.environ.copy()
        env["PATH"] = tmpdir + ":" + env.get("PATH", "")

        r = subprocess.run(
            ["bash", str(SCRIPT), pane_id, tty_path],
            capture_output=True,
            text=True,
            env=env,
        )

        with open(tty_path, "rb") as f:
            tty_bytes = f.read()

        return r.returncode, tty_bytes, r.stdout, r.stderr
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── help flag tests ───────────────────────────────────────────────────


def test_help_flag_short():
    """-h prints usage from the script header."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout


def test_help_flag_long():
    """--help prints usage from the script header."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout


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
    rc, written, _, stderr = _run_with_fake_tmux(pane_content)
    assert rc == 0, f"stderr: {stderr}"

    expected_b64 = base64.b64encode(pane_content.encode()).decode().replace("\n", "")
    expected = f"\033]52;c;{expected_b64}\007".encode()
    assert written == expected, f"got {written!r}, expected {expected!r}"


def test_osc52_multiline_content():
    """Multi-line pane content is properly base64'd and written."""
    pane_content = "line1\nline2\nline3"
    rc, written, _, stderr = _run_with_fake_tmux(pane_content)
    assert rc == 0, f"stderr: {stderr}"

    expected_b64 = base64.b64encode(pane_content.encode()).decode().replace("\n", "")
    expected = f"\033]52;c;{expected_b64}\007".encode()
    assert written == expected


def test_osc52_empty_pane():
    """Empty pane content still produces a valid OSC 52 sequence."""
    pane_content = ""
    rc, written, _, stderr = _run_with_fake_tmux(pane_content)
    assert rc == 0, f"stderr: {stderr}"

    expected_b64 = base64.b64encode(b"").decode().replace("\n", "")
    expected = f"\033]52;c;{expected_b64}\007".encode()
    assert written == expected


def test_osc52_special_characters():
    """Content with special shell characters is handled safely."""
    pane_content = "tab\there and 'quotes' and \"dquotes\""
    rc, written, _, stderr = _run_with_fake_tmux(pane_content)
    assert rc == 0, f"stderr: {stderr}"

    expected_b64 = base64.b64encode(pane_content.encode()).decode().replace("\n", "")
    expected = f"\033]52;c;{expected_b64}\007".encode()
    assert written == expected


# ── escape sequence structure tests ───────────────────────────────────


def test_output_starts_with_osc52_escape():
    """Output always begins with ESC ]52;c;."""
    rc, written, _, _ = _run_with_fake_tmux("abc")
    assert rc == 0
    assert written[:7] == b"\033]52;c;"
    assert written[-1:] == b"\007"


def test_base64_has_no_newlines():
    """The base64 payload should contain no newlines (tr -d '\n')."""
    # Use enough content that base64 would normally wrap lines
    pane_content = "A" * 200
    rc, written, _, _ = _run_with_fake_tmux(pane_content)
    assert rc == 0

    payload = written[7:-1].decode()  # between \033]52;c; and \007
    assert "\n" not in payload


def test_pane_id_passed_to_tmux():
    """The pane ID argument is passed through to tmux capture-pane."""
    tmpdir, _ = _make_fake_tmux_dir("x")
    try:
        # Replace fake tmux with one that logs its args
        tmux_path = os.path.join(tmpdir, "tmux")
        log_path = os.path.join(tmpdir, "args.log")
        with open(tmux_path, "w") as f:
            f.write(f"#!/bin/bash\necho \"$@\" > {log_path}\necho -n 'x'\n")
        os.chmod(tmux_path, os.stat(tmux_path).st_mode | stat.S_IEXEC)

        tty_fd, tty_path = tempfile.mkstemp(suffix=".tty", dir=tmpdir)
        os.close(tty_fd)

        env = os.environ.copy()
        env["PATH"] = tmpdir + ":" + env.get("PATH", "")

        subprocess.run(
            ["bash", str(SCRIPT), "my-special-pane", tty_path],
            capture_output=True,
            env=env,
        )

        with open(log_path) as f:
            logged_args = f.read().strip()
        assert "my-special-pane" in logged_args
        assert "capture-pane" in logged_args
        assert "-p" in logged_args
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
