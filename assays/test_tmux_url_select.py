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


# ── Strict mode ────────────────────────────────────────────────────────────


def test_script_uses_strict_mode():
    """Script uses set -euo pipefail for safety."""
    content = SCRIPT.read_text()
    assert "set -euo pipefail" in content


# ── URL stops at single quote ──────────────────────────────────────────────


def test_stops_at_single_quote(tmp_path):
    """URL extraction stops at ' characters."""
    _write_buffer("link='https://example.com/page' next\n")
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\nhead -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        encoded = base64.b64encode(b"https://example.com/page").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()


# ── URL with complex characters ────────────────────────────────────────────


def test_url_with_query_params(tmp_path):
    """URLs with query strings (? and &) are fully captured."""
    url = "https://example.com/search?q=hello+world&page=2&lang=en"
    _write_buffer(f"visit {url} now\n")
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


def test_url_with_fragment(tmp_path):
    """URLs with fragments (#) are captured up to the delimiter."""
    url = "https://example.com/docs#section"
    _write_buffer(f"see {url} for details\n")
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


def test_url_with_port(tmp_path):
    """URLs with port numbers are fully captured."""
    url = "http://localhost:8080/api/v1/health"
    _write_buffer(f"check {url} endpoint\n")
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


def test_url_with_path_special_chars(tmp_path):
    """URLs with hyphens, underscores, dots in path are captured."""
    url = "https://my-site.example.com/path/to/my_resource-v2.0.html"
    _write_buffer(f"open {url} please\n")
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


# ── Multiple URLs on same line ─────────────────────────────────────────────


def test_multiple_urls_on_same_line(tmp_path):
    """Multiple URLs on a single line are all extracted."""
    _write_buffer("compare https://a.com and https://b.com for details\n")
    capture = tmp_path / "fzf_input.txt"
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text(f"#!/bin/bash\ntee {capture} | head -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        lines = capture.read_text().strip().splitlines()
        assert len(lines) == 2
        assert "https://a.com" in lines
        assert "https://b.com" in lines
    finally:
        _remove_buffer()


# ── Dedup preserves first occurrence order ──────────────────────────────────


def test_dedup_preserves_first_occurrence_order(tmp_path):
    """Deduplication keeps first occurrence and preserves order."""
    _write_buffer(
        "https://second.com\n"
        "https://first.com\n"
        "https://second.com\n"
        "https://first.com\n"
    )
    capture = tmp_path / "fzf_input.txt"
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text(f"#!/bin/bash\ntee {capture} | head -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        lines = capture.read_text().strip().splitlines()
        assert len(lines) == 2
        # first.com appeared first in original, but second.com was first
        assert lines[0] == "https://second.com"
        assert lines[1] == "https://first.com"
    finally:
        _remove_buffer()


# ── tmux display-message invoked ───────────────────────────────────────────


def test_tmux_display_message_called_on_selection(tmp_path):
    """When a URL is selected, tmux display-message is invoked."""
    url = "https://example.com/test"
    _write_buffer(f"{url}\n")
    # Create both fake fzf and fake tmux
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\nhead -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    tmux_capture = tmp_path / "tmux_args.txt"
    fake_tmux = tmp_path / "tmux"
    fake_tmux.write_text(f"#!/bin/bash\necho \"$@\" >> {tmux_capture}\n")
    fake_tmux.chmod(fake_tmux.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        tmux_calls = tmux_capture.read_text().strip().splitlines()
        assert len(tmux_calls) >= 1
        assert "display-message" in tmux_calls[0]
        assert url in tmux_calls[0]
    finally:
        _remove_buffer()


def test_tmux_not_called_when_nothing_selected(tmp_path):
    """When fzf returns nothing, tmux is not invoked."""
    _write_buffer("https://example.com\n")
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\nexit 0\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    tmux_capture = tmp_path / "tmux_args.txt"
    fake_tmux = tmp_path / "tmux"
    fake_tmux.write_text(f"#!/bin/bash\necho \"$@\" >> {tmux_capture}\n")
    fake_tmux.chmod(fake_tmux.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        assert not tmux_capture.exists()
    finally:
        _remove_buffer()


# ── Buffer with whitespace only ────────────────────────────────────────────


def test_buffer_whitespace_only():
    """Buffer with only whitespace produces 'No URLs found'."""
    _write_buffer("   \n  \n\t\n")
    try:
        p = _run([])
        assert p.returncode == 0
        assert "No URLs found" in p.stdout
    finally:
        _remove_buffer()


# ── URL at end of line without trailing delimiter ──────────────────────────


def test_url_at_end_of_line(tmp_path):
    """URL at very end of line (no trailing space/delim) is fully captured."""
    url = "https://example.com/end"
    _write_buffer(f"check {url}\n")
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


# ── Help content specifics ─────────────────────────────────────────────────


def test_help_mentions_osc52():
    """Help text mentions OSC 52."""
    p = _run(["--help"])
    assert "OSC 52" in p.stdout


def test_help_mentions_blink():
    """Help text mentions Blink."""
    p = _run(["--help"])
    assert "Blink" in p.stdout


def test_help_mentions_buffer_path():
    """Help text mentions the buffer file path."""
    p = _run(["--help"])
    assert "/tmp/tmux-url-buffer" in p.stdout


# ── Mixed content with URLs ────────────────────────────────────────────────


def test_extracts_url_from_mixed_content(tmp_path):
    """URLs are extracted from text mixed with other content."""
    _write_buffer(
        "Build log:\n"
        "  error at https://ci.example.com/build/1234#log\n"
        "  retry: https://ci.example.com/build/1234#log\n"
        "  docs https://docs.example.com/errors\n"
    )
    capture = tmp_path / "fzf_input.txt"
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text(f"#!/bin/bash\ntee {capture} | head -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        lines = capture.read_text().strip().splitlines()
        # Two unique URLs (build URL appears twice but deduped)
        assert len(lines) == 2
    finally:
        _remove_buffer()


# ── Only http/https schemes matched ────────────────────────────────────────


def test_ftp_scheme_not_matched():
    """Non-http(s) schemes like ftp:// are not extracted."""
    _write_buffer("download ftp://files.example.com/data.zip here\n")
    try:
        p = _run([])
        assert "No URLs found" in p.stdout
    finally:
        _remove_buffer()


def test_no_scheme_not_matched():
    """Bare domains without scheme are not extracted."""
    _write_buffer("visit www.example.com for info\n")
    try:
        p = _run([])
        assert "No URLs found" in p.stdout
    finally:
        _remove_buffer()


# ── OSC 52 exact format ────────────────────────────────────────────────────


def test_osc52_exact_format(tmp_path):
    """OSC 52 sequence uses exact format: ESC ] 52 ; c ; <base64> BEL."""
    url = "https://example.com"
    _write_buffer(f"{url}\n")
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\nhead -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        encoded = base64.b64encode(url.encode()).decode()
        expected = f"\x1b]52;c;{encoded}\x07"
        assert expected in p.stdout
        # Verify starts with ESC ]52;c; and ends with BEL
        assert "\x1b]52;c;" in p.stdout
        assert p.stdout.endswith("\x07") or "\x07" in p.stdout
    finally:
        _remove_buffer()


# ── Large URL ──────────────────────────────────────────────────────────────


def test_long_url(tmp_path):
    """Very long URLs are handled correctly (base64 may wrap on Linux)."""
    url = "https://example.com/" + "a" * 500
    _write_buffer(f"{url}\n")
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\nhead -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        encoded = base64.b64encode(url.encode()).decode()
        # Linux base64 wraps at 76 chars; strip newlines before comparing
        stdout_clean = p.stdout.replace("\n", "")
        assert f"\x1b]52;c;{encoded}\x07" in stdout_clean
    finally:
        _remove_buffer()


# ── Buffer with binary-like garbage and embedded URL ───────────────────────


def test_url_in_garbage_content(tmp_path):
    """URLs are extracted even when surrounded by non-URL text (no null bytes)."""
    _write_buffer("~~~garbage!!! https://example.com/clean ###more\n")
    fake_fzf = tmp_path / "fzf"
    fake_fzf.write_text("#!/bin/bash\nhead -1\n")
    fake_fzf.chmod(fake_fzf.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    try:
        p = _run([], env=env)
        encoded = base64.b64encode(b"https://example.com/clean").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()


# ── Unknown flags are not intercepted ──────────────────────────────────────


def test_unknown_flag_runs_normally():
    """Unknown flags are not intercepted — script runs the main path."""
    _remove_buffer()
    try:
        p = _run(["--version"])
        # Script won't show help for unknown flags; it'll try the main path
        # which prints "No URLs found" since buffer is missing
        assert p.returncode == 0
        assert "No URLs found" in p.stdout
    finally:
        pass
