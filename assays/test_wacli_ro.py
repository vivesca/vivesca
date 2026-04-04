from __future__ import annotations

"""Tests for wacli-ro — read-only wacli wrapper that blocks send."""

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "wacli-ro"


def run_wacli_ro(
    *args: str, mock_wacli_dir: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run wacli-ro with optional PATH override pointing at mock wacli."""
    env = os.environ.copy()
    if mock_wacli_dir is not None:
        env["PATH"] = str(mock_wacli_dir) + ":" + env.get("PATH", "")
    return subprocess.run(
        [str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def _create_mock_wacli(tmp_path: Path, stdout: str = "wacli-ok", exit_code: int = 0) -> Path:
    """Create a mock wacli script in tmp_path and return the directory."""
    wacli = tmp_path / "wacli"
    wacli.write_text(f"#!/bin/bash\necho '{stdout}'\nexit {exit_code}\n")
    wacli.chmod(wacli.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return tmp_path


# ── Help flag tests ────────────────────────────────────────────────────


def test_wacli_ro_help_long_flag():
    """--help shows usage and exits 0."""
    r = run_wacli_ro("--help")
    assert r.returncode == 0
    assert "wacli-ro" in r.stdout
    assert "read-only" in r.stdout.lower()


def test_wacli_ro_help_short_flag():
    """-h shows usage and exits 0."""
    r = run_wacli_ro("-h")
    assert r.returncode == 0
    assert "wacli-ro" in r.stdout
    assert "Usage" in r.stdout


# ── Send blocking tests ────────────────────────────────────────────────


def test_send_as_first_arg_blocked():
    """'send' as first argument is blocked."""
    r = run_wacli_ro("send", "hello")
    assert r.returncode == 1
    assert "ERROR" in r.stdout
    assert "read-only" in r.stdout.lower() or "Send is disabled" in r.stdout


def test_send_anywhere_blocked():
    """Any argument containing 'send' is blocked."""
    r = run_wacli_ro("contact", "send")
    assert r.returncode == 1
    assert "ERROR" in r.stdout


def test_send_substring_blocked():
    """Word containing 'send' in arguments triggers block (e.g. 'resend')."""
    r = run_wacli_ro("resend")
    assert r.returncode == 1
    assert "ERROR" in r.stdout


def test_send_in_message_blocked():
    """'send' appearing inside a quoted string argument is blocked."""
    r = run_wacli_ro("message", "please send this")
    assert r.returncode == 1


# ── Passthrough tests (mock wacli) ─────────────────────────────────────


def test_passthrough_non_send_args(tmp_path):
    """Non-send args are forwarded to wacli."""
    mock_dir = _create_mock_wacli(tmp_path)
    r = run_wacli_ro("status", mock_wacli_dir=mock_dir)
    assert r.returncode == 0
    assert "wacli-ok" in r.stdout


def test_passthrough_multiple_args(tmp_path):
    """Multiple non-send args are forwarded correctly."""
    mock_dir = _create_mock_wacli(tmp_path)
    r = run_wacli_ro("contact", "list", "--format", "json", mock_wacli_dir=mock_dir)
    assert r.returncode == 0
    assert "wacli-ok" in r.stdout


def test_passthrough_empty_args(tmp_path):
    """Running with no args delegates to wacli."""
    mock_dir = _create_mock_wacli(tmp_path)
    r = run_wacli_ro(mock_wacli_dir=mock_dir)
    assert r.returncode == 0
    assert "wacli-ok" in r.stdout


def test_passthrough_preserves_wacli_exit_code(tmp_path):
    """wacli-ro exits with same code as wacli when wacli fails."""
    mock_dir = _create_mock_wacli(tmp_path, exit_code=42)
    r = run_wacli_ro("status", mock_wacli_dir=mock_dir)
    assert r.returncode == 42


# ── No wacli on PATH ───────────────────────────────────────────────────


def test_wacli_not_found():
    """wacli-ro fails if wacli is not on PATH (not a send command)."""
    # Use a PATH that definitely has no wacli
    env = os.environ.copy()
    env["PATH"] = "/usr/nonexistent"
    r = subprocess.run(
        [str(SCRIPT), "status"],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    # exec wacli should fail — exit code is typically 127
    assert r.returncode != 0
