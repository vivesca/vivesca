from __future__ import annotations

"""Tests for tmux-osc52.sh — OSC 52 clipboard via tmux pane capture."""

import base64
import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "tmux-osc52.sh"


# ── helpers ─────────────────────────────────────────────────────────────


@pytest.fixture()
def work_dir():
    """Isolated temp dir using tempfile, avoiding pytest basetemp conflicts."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def _run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run the script with subprocess.run and return the result."""
    kw: dict = {}
    if env is not None:
        kw["env"] = env
    return subprocess.run(
        [str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=5,
        **kw,
    )


def _make_fake_tmux(output: str, work_dir: Path) -> Path:
    """Create a fake tmux binary that prints *output* to stdout.

    Returns the bindir containing the fake tmux.
    """
    bindir = work_dir / "bin"
    bindir.mkdir(exist_ok=True)
    payload = work_dir / "tmux_output.bin"
    payload.write_bytes(output.encode())
    fake = bindir / "tmux"
    fake.write_text(f"#!/bin/bash\ncat '{payload}'\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_logging_tmux(work_dir: Path, log_file: Path) -> Path:
    """Create a fake tmux that logs its args and prints 'captured'."""
    bindir = work_dir / "bin"
    bindir.mkdir(exist_ok=True)
    fake = bindir / "tmux"
    fake.write_text(f"#!/bin/bash\necho \"$@\" > {log_file}\necho 'captured'\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return bindir


def _env_with_bindir(bindir: Path) -> dict:
    """Return env dict with bindir prepended to PATH."""
    return {**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}"}


def _run_with_fake_tmux(pane: str, tty_file: Path, bindir: Path) -> subprocess.CompletedProcess:
    """Run the script with a fake tmux on PATH, return result."""
    return _run(pane, str(tty_file), env=_env_with_bindir(bindir))


def _extract_payload(tty_file: Path) -> str:
    """Read the TTY file and return the base64 payload (no wrapper)."""
    content = tty_file.read_text()
    payload = content[len("\033]52;c;") :]
    payload = payload.removesuffix("\007")
    return payload


# ── help / usage ──────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_exits_zero(self):
        r = _run("--help")
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self):
        r = _run("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run("--help")
        assert "Usage" in r.stdout or "tmux-osc52.sh" in r.stdout

    def test_help_mentions_pane_and_tty(self):
        r = _run("--help")
        assert "pane" in r.stdout.lower() or "tty" in r.stdout.lower()


# ── missing / bad arguments ───────────────────────────────────────────


class TestBadArguments:
    def test_no_args_exits_nonzero(self):
        r = _run()
        assert r.returncode != 0

    def test_one_arg_exits_nonzero(self):
        r = _run("0")
        assert r.returncode != 0


# ── OSC 52 sequence structure ─────────────────────────────────────────


class TestOsc52Sequence:
    def test_writes_osc52_wrapper(self, work_dir):
        tty_file = work_dir / "fake_tty"
        bindir = _make_fake_tmux("hello world", work_dir)
        r = _run_with_fake_tmux("0", tty_file, bindir)
        assert r.returncode == 0, f"stderr: {r.stderr}"
        content = tty_file.read_text()
        assert content.startswith("\033]52;c;")
        assert content.endswith("\007")

    def test_base64_decodes_correctly(self, work_dir):
        tty_file = work_dir / "fake_tty"
        bindir = _make_fake_tmux("hello world", work_dir)
        _run_with_fake_tmux("0", tty_file, bindir)
        payload = _extract_payload(tty_file)
        assert base64.b64decode(payload).decode() == "hello world"

    def test_no_newlines_in_payload(self, work_dir):
        """base64 output is stripped of line breaks (tr -d '\\n')."""
        tty_file = work_dir / "fake_tty"
        bindir = _make_fake_tmux("x" * 200, work_dir)
        _run_with_fake_tmux("0", tty_file, bindir)
        payload = _extract_payload(tty_file)
        assert "\n" not in payload
        assert "\r" not in payload

    def test_empty_pane_produces_valid_sequence(self, work_dir):
        tty_file = work_dir / "fake_tty"
        bindir = _make_fake_tmux("", work_dir)
        r = _run_with_fake_tmux("0", tty_file, bindir)
        assert r.returncode == 0
        content = tty_file.read_text()
        assert content.startswith("\033]52;c;")
        assert content.endswith("\007")


# ── pane id forwarding ────────────────────────────────────────────────


class TestPaneForwarding:
    def test_passes_pane_id_to_tmux(self, work_dir):
        tty_file = work_dir / "fake_tty"
        log_file = work_dir / "tmux_args.log"
        bindir = _make_logging_tmux(work_dir, log_file)
        r = _run_with_fake_tmux("mypane.42", tty_file, bindir)
        assert r.returncode == 0, f"stderr: {r.stderr}"
        logged = log_file.read_text().strip()
        assert "mypane.42" in logged
        assert "capture-pane" in logged
        assert "-p" in logged
        assert "-t" in logged

    def test_numeric_pane_id(self, work_dir):
        tty_file = work_dir / "fake_tty"
        log_file = work_dir / "tmux_args.log"
        bindir = _make_logging_tmux(work_dir, log_file)
        r = _run_with_fake_tmux("0", tty_file, bindir)
        assert r.returncode == 0
        logged = log_file.read_text().strip()
        assert "-t 0" in logged


# ── content edge cases ────────────────────────────────────────────────


class TestContentEncoding:
    def test_multiline_content(self, work_dir):
        tty_file = work_dir / "fake_tty"
        multiline = "line1\nline2\nline3"
        bindir = _make_fake_tmux(multiline, work_dir)
        _run_with_fake_tmux("0", tty_file, bindir)
        payload = _extract_payload(tty_file)
        assert base64.b64decode(payload).decode() == multiline

    def test_special_characters(self, work_dir):
        tty_file = work_dir / "fake_tty"
        special = "hello $USER `whoami` \t 'quoted' \"double\""
        bindir = _make_fake_tmux(special, work_dir)
        _run_with_fake_tmux("0", tty_file, bindir)
        payload = _extract_payload(tty_file)
        assert base64.b64decode(payload).decode() == special

    def test_unicode_content(self, work_dir):
        tty_file = work_dir / "fake_tty"
        bindir = _make_fake_tmux("hello 日本語 🌍", work_dir)
        _run_with_fake_tmux("0", tty_file, bindir)
        payload = _extract_payload(tty_file)
        assert base64.b64decode(payload).decode() == "hello 日本語 🌍"

    def test_large_content(self, work_dir):
        """10 KB payload — ensures no truncation."""
        big = "A" * 10_000
        tty_file = work_dir / "fake_tty"
        bindir = _make_fake_tmux(big, work_dir)
        _run_with_fake_tmux("0", tty_file, bindir)
        payload = _extract_payload(tty_file)
        assert base64.b64decode(payload).decode() == big


# ── TTY file behaviour ────────────────────────────────────────────────


class TestTtyFile:
    def test_tty_file_overwritten(self, work_dir):
        tty_file = work_dir / "fake_tty"
        tty_file.write_text("old content that should be gone")
        bindir = _make_fake_tmux("new", work_dir)
        _run_with_fake_tmux("0", tty_file, bindir)
        content = tty_file.read_text()
        assert "old content" not in content
        assert content.startswith("\033]52;c;")

    def test_nonexistent_tty_dir_fails(self, work_dir):
        """Writing to a TTY path in a missing directory should fail."""
        bindir = _make_fake_tmux("data", work_dir)
        bad_tty = work_dir / "nonexistent" / "dir" / "tty"
        r = _run_with_fake_tmux("0", bad_tty, bindir)
        assert r.returncode != 0
