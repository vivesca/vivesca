from __future__ import annotations

"""Tests for tmux-osc52.sh — OSC 52 clipboard via tmux pane capture."""

import os
import stat
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "tmux-osc52.sh"


def _run(*args: str, **kw) -> subprocess.CompletedProcess:
    """Run the script with subprocess.run and return the result."""
    return subprocess.run(
        [str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=5,
        **kw,
    )


def _make_fake_tmux(output: str, tmpdir: Path) -> str:
    """Create a fake tmux binary that prints *output* to stdout."""
    payload = tmpdir / "tmux_output.bin"
    payload.write_bytes(output.encode())
    fake = tmpdir / "tmux"
    fake.write_text(f"#!/bin/bash\ncat '{payload}'\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return str(tmpdir)


# ── help / usage ──────────────────────────────────────────────────────


def test_help_flag_long():
    """--help prints usage and exits 0."""
    r = _run("--help")
    assert r.returncode == 0
    assert "Usage" in r.stdout or "tmux-osc52.sh" in r.stdout


def test_tmux_osc52_help_flag_short():
    """'-h' prints usage and exits 0."""
    r = _run("-h")
    assert r.returncode == 0
    assert "Usage" in r.stdout or "tmux-osc52.sh" in r.stdout


def test_help_output_contains_pane_and_tty():
    """Help text mentions the two required arguments."""
    r = _run("--help")
    assert "pane" in r.stdout.lower() or "tty" in r.stdout.lower()


# ── missing arguments ─────────────────────────────────────────────────


def test_no_args_exits_nonzero():
    """Running without arguments should fail (empty pane/tty)."""
    r = _run()
    assert r.returncode != 0


def test_one_arg_exits_nonzero():
    """Only pane_id without tty should fail."""
    r = _run("0")
    assert r.returncode != 0


# ── normal operation with fake tmux ───────────────────────────────────


def test_writes_osc52_sequence():
    """Script writes a valid OSC 52 escape sequence to the tty file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tty_file = tmpdir_path / "fake_tty"
        tty_file.write_text("")

        fake_tmux_dir = _make_fake_tmux("hello world", tmpdir_path)
        env = {**os.environ, "PATH": f"{fake_tmux_dir}:{os.environ['PATH']}"}

        r = subprocess.run(
            [str(SCRIPT), "0", str(tty_file)],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"

        content = tty_file.read_text()
        # OSC 52 format: ESC ] 52 ; c ; <base64> BEL
        assert content.startswith("\033]52;c;")
        assert content.endswith("\007")


def test_base64_content_is_valid():
    """The base64 payload in the OSC 52 sequence decodes to the captured text."""
    import base64

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tty_file = tmpdir_path / "fake_tty"
        tty_file.write_text("")

        fake_tmux_dir = _make_fake_tmux("hello world", tmpdir_path)
        env = {**os.environ, "PATH": f"{fake_tmux_dir}:{os.environ['PATH']}"}

        subprocess.run(
            [str(SCRIPT), "0", str(tty_file)],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )

        content = tty_file.read_text()
        # Strip the OSC 52 wrapper
        payload = content[len("\033]52;c;"):]
        if payload.endswith("\007"):
            payload = payload[:-1]

        decoded = base64.b64decode(payload).decode()
        assert decoded == "hello world"


def test_no_newlines_in_base64_payload():
    """The base64 payload must not contain newline characters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tty_file = tmpdir_path / "fake_tty"
        tty_file.write_text("")

        # Long output that base64 would normally wrap at 76 chars
        fake_tmux_dir = _make_fake_tmux("x" * 200, tmpdir_path)
        env = {**os.environ, "PATH": f"{fake_tmux_dir}:{os.environ['PATH']}"}

        subprocess.run(
            [str(SCRIPT), "0", str(tty_file)],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )

        content = tty_file.read_text()
        payload = content[len("\033]52;c;"):]
        if payload.endswith("\007"):
            payload = payload[:-1]

        assert "\n" not in payload
        assert "\r" not in payload


def test_passes_correct_pane_id():
    """The pane id argument is forwarded to tmux capture-pane."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tty_file = tmpdir_path / "fake_tty"
        tty_file.write_text("")

        # Fake tmux that logs its arguments
        fake_tmux = tmpdir_path / "tmux"
        log_file = tmpdir_path / "tmux_args.log"
        fake_tmux.write_text(
            f"#!/bin/bash\necho \"$@\" > {log_file}\necho 'captured'\n"
        )
        fake_tmux.chmod(fake_tmux.stat().st_mode | stat.S_IEXEC)

        env = {
            **os.environ,
            "PATH": f"{tmpdir_path}:{os.environ['PATH']}",
        }

        r = subprocess.run(
            [str(SCRIPT), "mypane.42", str(tty_file)],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"

        logged_args = log_file.read_text().strip()
        assert "mypane.42" in logged_args
        assert "capture-pane" in logged_args
        assert "-p" in logged_args
        assert "-t" in logged_args


def test_multiline_pane_content():
    """Multi-line pane content is captured and encoded correctly."""
    import base64

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tty_file = tmpdir_path / "fake_tty"
        tty_file.write_text("")

        multiline = "line1\nline2\nline3"
        fake_tmux_dir = _make_fake_tmux(multiline, tmpdir_path)
        env = {**os.environ, "PATH": f"{fake_tmux_dir}:{os.environ['PATH']}"}

        r = subprocess.run(
            [str(SCRIPT), "0", str(tty_file)],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        assert r.returncode == 0

        content = tty_file.read_text()
        payload = content[len("\033]52;c;"):]
        if payload.endswith("\007"):
            payload = payload[:-1]

        decoded = base64.b64decode(payload).decode()
        assert decoded == multiline


def test_empty_pane_content():
    """Empty pane content produces a valid (empty) OSC 52 sequence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tty_file = tmpdir_path / "fake_tty"
        tty_file.write_text("")

        fake_tmux_dir = _make_fake_tmux("", tmpdir_path)
        env = {**os.environ, "PATH": f"{fake_tmux_dir}:{os.environ['PATH']}"}

        r = subprocess.run(
            [str(SCRIPT), "0", str(tty_file)],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        assert r.returncode == 0

        content = tty_file.read_text()
        # Should still be a valid OSC 52 sequence even with empty content
        assert content.startswith("\033]52;c;")
        assert content.endswith("\007")


def test_special_characters_in_pane():
    """Special characters in pane content are handled correctly."""
    import base64

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tty_file = tmpdir_path / "fake_tty"
        tty_file.write_text("")

        special = "hello $USER `whoami` \t 'quoted' \"double\""
        fake_tmux_dir = _make_fake_tmux(special, tmpdir_path)
        env = {**os.environ, "PATH": f"{fake_tmux_dir}:{os.environ['PATH']}"}

        r = subprocess.run(
            [str(SCRIPT), "0", str(tty_file)],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        assert r.returncode == 0

        content = tty_file.read_text()
        payload = content[len("\033]52;c;"):]
        if payload.endswith("\007"):
            payload = payload[:-1]

        decoded = base64.b64decode(payload).decode()
        assert decoded == special


def test_unicode_content():
    """Unicode content in pane is encoded correctly."""
    import base64

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tty_file = tmpdir_path / "fake_tty"
        tty_file.write_text("")

        fake_tmux_dir = _make_fake_tmux("hello 日本語 🌍", tmpdir_path)
        env = {**os.environ, "PATH": f"{fake_tmux_dir}:{os.environ['PATH']}"}

        r = subprocess.run(
            [str(SCRIPT), "0", str(tty_file)],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        assert r.returncode == 0

        content = tty_file.read_text()
        payload = content[len("\033]52;c;"):]
        if payload.endswith("\007"):
            payload = payload[:-1]

        decoded = base64.b64decode(payload).decode()
        assert decoded == "hello 日本語 🌍"


def test_tty_file_overwritten():
    """Script overwrites (not appends to) the tty file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tty_file = tmpdir_path / "fake_tty"
        tty_file.write_text("old content that should be gone")

        fake_tmux_dir = _make_fake_tmux("new", tmpdir_path)
        env = {**os.environ, "PATH": f"{fake_tmux_dir}:{os.environ['PATH']}"}

        r = subprocess.run(
            [str(SCRIPT), "0", str(tty_file)],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        assert r.returncode == 0

        content = tty_file.read_text()
        assert "old content" not in content
        assert content.startswith("\033]52;c;")
