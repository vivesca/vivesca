from __future__ import annotations

"""Tests for effectors/start-chrome-debug.sh — argument parsing, help, error paths."""

import subprocess
from pathlib import Path

SCRIPT = Path.home() / "germline/effectors/start-chrome-debug.sh"


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run the script with given args and capture output."""
    return subprocess.run(
        [str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        timeout=5,
        **kwargs,
    )


# ── Help / usage ──────────────────────────────────────────────────────


def test_help_flag_short():
    """-h prints usage and exits 0."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "start-chrome-debug.sh" in r.stdout


def test_help_flag_long():
    """--help prints usage and exits 0."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "--port" in r.stdout
    assert "9222" in r.stdout


def test_help_mentions_all_options():
    """Help text documents both --help and --port."""
    r = _run(["--help"])
    assert "--help" in r.stdout
    assert "--port" in r.stdout


# ── Unknown options ───────────────────────────────────────────────────


def test_unknown_option_exits_2():
    """Unknown flag writes error to stderr and exits 2."""
    r = _run(["--bogus"])
    assert r.returncode == 2
    assert "Unknown option" in r.stderr


def test_unknown_short_option():
    """Single-char unknown flag also exits 2."""
    r = _run(["-Z"])
    assert r.returncode == 2
    assert "Unknown option" in r.stderr


def test_unknown_option_still_shows_usage():
    """Error output includes usage text on unknown option."""
    r = _run(["--nope"])
    assert r.returncode == 2
    assert "Usage:" in r.stderr


# ── Chrome detection (no Chrome on this machine) ─────────────────────


def test_chrome_not_found():
    """When no Chrome binary is on PATH, script exits 1 with error message."""
    r = _run([])
    # On this machine Chrome is not installed
    assert r.returncode == 1
    assert "not found" in r.stderr.lower() or "not executable" in r.stderr.lower()


def test_chrome_not_found_minimal_path():
    """PATH with only /usr/bin (no Chrome candidates) — exits 1."""
    r = _run([], env={"PATH": "/usr/bin", "HOME": str(Path.home())})
    assert r.returncode == 1
    assert "not found" in r.stderr.lower() or "chrome" in r.stderr.lower()


# ── Port flag validation ─────────────────────────────────────────────


def test_port_flag_changes_port_in_help_default():
    """Default port 9222 is documented in help output."""
    r = _run(["--help"])
    assert "9222" in r.stdout
