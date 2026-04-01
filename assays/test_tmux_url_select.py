from __future__ import annotations

"""Tests for effectors/tmux-url-select.sh — tmux URL extractor + OSC 52 copier.

Effectors are scripts, so we test via subprocess.run only.
"""

import base64
import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "tmux-url-select.sh"
BUFFER = Path("/tmp/tmux-url-buffer")


def _run(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    """Run the script with given args and return CompletedProcess."""
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )


def _write_buffer(content: str) -> None:
    """Write content to the URL buffer file."""
    BUFFER.write_text(content)


def _remove_buffer() -> None:
    """Remove the URL buffer file if it exists."""
    if BUFFER.exists():
        BUFFER.unlink()


# ── --help flag ────────────────────────────────────────────────────────────


def test_help_flag():
    """--help prints usage and exits 0."""
    p = _run(["--help"])
    assert p.returncode == 0
    assert "Usage:" in p.stdout
    assert "tmux-url-select" in p.stdout


def test_h_short_flag():
    """Short -h flag prints usage and exits 0."""
    p = _run(["-h"])
    assert p.returncode == 0
    assert "Usage:" in p.stdout


def test_help_mentions_requirements():
    """Help text mentions required tools."""
    p = _run(["--help"])
    assert "fzf" in p.stdout
    assert "tmux" in p.stdout


# ── No buffer file ─────────────────────────────────────────────────────────


def test_no_buffer_file():
    """When buffer file is missing, prints 'No URLs found' and exits 0."""
    _remove_buffer()
    try:
        p = _run([])
        assert p.returncode == 0
        assert "No URLs found" in p.stdout
    finally:
        pass  # already removed


# ── Empty buffer ───────────────────────────────────────────────────────────


def test_empty_buffer():
    """Empty buffer file produces 'No URLs found'."""
    _write_buffer("")
    try:
        p = _run([])
        assert p.returncode == 0
        assert "No URLs found" in p.stdout
    finally:
        _remove_buffer()


def test_buffer_with_no_urls():
    """Buffer with text but no URLs produces 'No URLs found'."""
    _write_buffer("just some plain text\nno links here\n")
    try:
        p = _run([])
        assert p.returncode == 0
        assert "No URLs found" in p.stdout
    finally:
        _remove_buffer()


# ── URL extraction (grep pattern) ──────────────────────────────────────────


def test_extracts_http_url(tmp_path):
    """Script finds http:// URLs from buffer."""
    _write_buffer("see http://example.com for details\n")
    # Replace fzf with a script that echoes the first line it gets
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\ncat | head -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        # fzf returned a URL, so script should emit OSC 52
        encoded = base64.b64encode(b"http://example.com").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()


def test_extracts_https_url(tmp_path):
    """Script finds https:// URLs from buffer."""
    _write_buffer("visit https://secure.example.org/path?q=1\n")
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\ncat | head -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        encoded = base64.b64encode(b"https://secure.example.org/path?q=1").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()


def test_stops_at_space(tmp_path):
    """URL extraction stops at space characters."""
    _write_buffer("link https://example.com/path other text\n")
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\ncat | head -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        encoded = base64.b64encode(b"https://example.com/path").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
        # Should NOT include "other"
        assert "other" not in p.stdout or "No URLs found" in p.stdout or "\x1b]52" in p.stdout
    finally:
        _remove_buffer()


def test_stops_at_angle_bracket(tmp_path):
    """URL extraction stops at > characters."""
    _write_buffer("<a href=https://example.com>click</a>\n")
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\ncat | head -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        encoded = base64.b64encode(b"https://example.com").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()


def test_stops_at_parenthesis(tmp_path):
    """URL extraction stops at ) characters."""
    _write_buffer("text (https://example.com/page) more\n")
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\ncat | head -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        encoded = base64.b64encode(b"https://example.com/page").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()


def test_stops_at_double_quote(tmp_path):
    """URL extraction stops at \" characters."""
    _write_buffer('href="https://example.com/res" class="x"\n')
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\ncat | head -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        encoded = base64.b64encode(b"https://example.com/res").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()


# ── Deduplication ──────────────────────────────────────────────────────────


def test_deduplicates_urls(tmp_path):
    """Duplicate URLs are deduplicated before fzf."""
    _write_buffer(
        "check https://example.com\n"
        "and https://example.com again\n"
        "also https://other.com\n"
    )
    # Capture what fzf receives (its stdin)
    capture = tmp_path / "fzf_input.txt"
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text(f"#!/bin/bash\ntee {capture} | head -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        lines = capture.read_text().strip().splitlines()
        # Should have exactly 2 unique URLs, not 3
        assert len(lines) == 2
        assert "https://example.com" in lines
        assert "https://other.com" in lines
    finally:
        _remove_buffer()


# ── OSC 52 encoding ────────────────────────────────────────────────────────


def test_osc52_encoding(tmp_path):
    """Selected URL is base64-encoded and emitted as OSC 52 escape."""
    url = "https://example.com/test/path?a=1&b=2"
    _write_buffer(f"link: {url}\n")
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\nhead -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        encoded = base64.b64encode(url.encode()).decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()


def test_no_osc52_when_nothing_selected(tmp_path):
    """When fzf returns empty, no OSC 52 is emitted."""
    _write_buffer("https://example.com\n")
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\nexit 0\n")  # outputs nothing
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        assert "\x1b]52" not in p.stdout
    finally:
        _remove_buffer()


# ── Multiple URLs in buffer ───────────────────────────────────────────────


def test_multiple_urls_extracted(tmp_path):
    """Multiple different URLs are all passed to fzf."""
    _write_buffer(
        "https://first.com\n"
        "https://second.com\n"
        "https://third.com\n"
    )
    capture = tmp_path / "fzf_input.txt"
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text(f"#!/bin/bash\ntee {capture} | head -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        lines = capture.read_text().strip().splitlines()
        assert len(lines) == 3
        assert "https://first.com" in lines
        assert "https://second.com" in lines
        assert "https://third.com" in lines
    finally:
        _remove_buffer()


# ── fzf receives --reverse --prompt flags ──────────────────────────────────


def test_fzf_receives_correct_flags(tmp_path):
    """fzf is invoked with --reverse and --prompt flags."""
    _write_buffer("https://example.com\n")
    capture = tmp_path / "fzf_args.txt"
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text(f"#!/bin/bash\necho \"$@\" > {capture}\nhead -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        args = capture.read_text().strip()
        assert "--reverse" in args
        assert "--prompt" in args
        assert "Copy URL" in args
        assert "--no-info" in args
    finally:
        _remove_buffer()


# ── Script is executable ──────────────────────────────────────────────────


def test_script_is_executable():
    """The script file has execute permission."""
    assert SCRIPT.exists()
    assert os.access(SCRIPT, os.X_OK)


def test_script_has_shebang():
    """The script starts with a bash shebang."""
    first_line = SCRIPT.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env bash"
