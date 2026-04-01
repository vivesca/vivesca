from __future__ import annotations

"""Tests for effectors/tmux-url-select.sh — tmux URL extractor + OSC 52 copier.

Effectors are scripts, so we test via subprocess.run only.
Uses tempfile.mkdtemp() instead of tmp_path to avoid basetemp race conditions
with tmp_path_retention_policy = "none".
"""

import base64
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "tmux-url-select.sh"
BUFFER = Path("/tmp/tmux-url-buffer")


def _run(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )


def _write_buffer(content: str) -> None:
    BUFFER.write_text(content)


def _remove_buffer() -> None:
    if BUFFER.exists():
        BUFFER.unlink()


def _make_fakedir() -> Path:
    """Create a temp dir for fake binaries; caller must clean up via shutil.rmtree."""
    return Path(tempfile.mkdtemp(prefix="tmux_url_test_"))


def _cleanup_fakedir(d: Path) -> None:
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


def _install_fake_fzf(d: Path, script_body: str) -> None:
    fzf = d / "fzf"
    fzf.write_text(f"#!/bin/bash\n{script_body}\n")
    fzf.chmod(fzf.stat().st_mode | stat.S_IEXEC)


def _install_fake_tmux(d: Path, capture_file: Path) -> None:
    tmux = d / "tmux"
    tmux.write_text(f'#!/bin/bash\necho "$@" >> {capture_file}\n')
    tmux.chmod(tmux.stat().st_mode | stat.S_IEXEC)


def _env_with_fakedir(d: Path) -> dict[str, str]:
    return {**os.environ, "PATH": f"{d}:{os.environ['PATH']}"}


# ── Script metadata ────────────────────────────────────────────────────────


def test_script_exists_and_is_executable():
    assert SCRIPT.exists()
    assert SCRIPT.is_file()
    assert os.access(SCRIPT, os.X_OK)


def test_shebang_is_correct():
    first_line = SCRIPT.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env bash"


def test_uses_strict_mode():
    content = SCRIPT.read_text()
    assert "set -euo pipefail" in content


# ── --help / -h ────────────────────────────────────────────────────────────


def test_help_flag():
    p = _run(["--help"])
    assert p.returncode == 0
    assert "Usage:" in p.stdout
    assert "tmux-url-select" in p.stdout


def test_h_short_flag():
    p = _run(["-h"])
    assert p.returncode == 0
    assert "Usage:" in p.stdout


def test_help_mentions_requirements():
    p = _run(["--help"])
    assert "fzf" in p.stdout
    assert "tmux" in p.stdout


def test_help_mentions_osc52():
    p = _run(["--help"])
    assert "OSC 52" in p.stdout


def test_help_mentions_blink():
    p = _run(["--help"])
    assert "Blink" in p.stdout


def test_help_mentions_buffer_path():
    p = _run(["--help"])
    assert "/tmp/tmux-url-buffer" in p.stdout


# ── Buffer states — no URLs found ──────────────────────────────────────────


def test_no_buffer_file():
    _remove_buffer()
    p = _run([])
    assert p.returncode == 0
    assert "No URLs found" in p.stdout


def test_empty_buffer():
    _write_buffer("")
    try:
        p = _run([])
        assert p.returncode == 0
        assert "No URLs found" in p.stdout
    finally:
        _remove_buffer()


def test_buffer_whitespace_only():
    _write_buffer("   \n  \n\t\n")
    try:
        p = _run([])
        assert p.returncode == 0
        assert "No URLs found" in p.stdout
    finally:
        _remove_buffer()


def test_buffer_with_no_urls():
    _write_buffer("just some plain text\nno links here\n")
    try:
        p = _run([])
        assert p.returncode == 0
        assert "No URLs found" in p.stdout
    finally:
        _remove_buffer()


def test_ftp_scheme_not_matched():
    _write_buffer("download ftp://files.example.com/data.zip here\n")
    try:
        p = _run([])
        assert "No URLs found" in p.stdout
    finally:
        _remove_buffer()


def test_no_scheme_not_matched():
    _write_buffer("visit www.example.com for info\n")
    try:
        p = _run([])
        assert "No URLs found" in p.stdout
    finally:
        _remove_buffer()


# ── URL extraction with fake fzf ───────────────────────────────────────────


def test_extracts_http_url():
    d = _make_fakedir()
    try:
        _write_buffer("see http://example.com for details\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(b"http://example.com").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_extracts_https_url():
    d = _make_fakedir()
    try:
        _write_buffer("visit https://secure.example.org/path?q=1\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(b"https://secure.example.org/path?q=1").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_stops_at_space():
    d = _make_fakedir()
    try:
        _write_buffer("link https://example.com/path other text\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(b"https://example.com/path").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_stops_at_angle_bracket():
    d = _make_fakedir()
    try:
        _write_buffer("<a href=https://example.com>click</a>\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(b"https://example.com").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_stops_at_parenthesis():
    d = _make_fakedir()
    try:
        _write_buffer("text (https://example.com/page) more\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(b"https://example.com/page").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_stops_at_double_quote():
    d = _make_fakedir()
    try:
        _write_buffer('href="https://example.com/res" class="x"\n')
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(b"https://example.com/res").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_stops_at_single_quote():
    d = _make_fakedir()
    try:
        _write_buffer("link='https://example.com/page' next\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(b"https://example.com/page").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_url_with_query_params():
    d = _make_fakedir()
    try:
        url = "https://example.com/search?q=hello+world&page=2&lang=en"
        _write_buffer(f"visit {url} now\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(url.encode()).decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_url_with_fragment():
    d = _make_fakedir()
    try:
        url = "https://example.com/docs#section"
        _write_buffer(f"see {url} for details\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(url.encode()).decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_url_with_port():
    d = _make_fakedir()
    try:
        url = "http://localhost:8080/api/v1/health"
        _write_buffer(f"check {url} endpoint\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(url.encode()).decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_url_with_path_special_chars():
    d = _make_fakedir()
    try:
        url = "https://my-site.example.com/path/to/my_resource-v2.0.html"
        _write_buffer(f"open {url} please\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(url.encode()).decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_url_at_end_of_line():
    d = _make_fakedir()
    try:
        url = "https://example.com/end"
        _write_buffer(f"check {url}\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(url.encode()).decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_url_in_garbage_content():
    d = _make_fakedir()
    try:
        _write_buffer("~~~garbage!!! https://example.com/clean ###more\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(b"https://example.com/clean").decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


# ── Deduplication ──────────────────────────────────────────────────────────


def test_deduplicates_urls():
    d = _make_fakedir()
    try:
        _write_buffer(
            "check https://example.com\n"
            "and https://example.com again\n"
            "also https://other.com\n"
        )
        capture = d / "fzf_input.txt"
        _install_fake_fzf(d, f"tee {capture} | head -1")
        p = _run([], env=_env_with_fakedir(d))
        lines = capture.read_text().strip().splitlines()
        assert len(lines) == 2
        assert "https://example.com" in lines
        assert "https://other.com" in lines
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_dedup_preserves_first_occurrence_order():
    d = _make_fakedir()
    try:
        _write_buffer(
            "https://second.com\n"
            "https://first.com\n"
            "https://second.com\n"
            "https://first.com\n"
        )
        capture = d / "fzf_input.txt"
        _install_fake_fzf(d, f"tee {capture} | head -1")
        p = _run([], env=_env_with_fakedir(d))
        lines = capture.read_text().strip().splitlines()
        assert len(lines) == 2
        assert lines[0] == "https://second.com"
        assert lines[1] == "https://first.com"
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_multiple_urls_on_same_line():
    d = _make_fakedir()
    try:
        _write_buffer("compare https://a.com and https://b.com for details\n")
        capture = d / "fzf_input.txt"
        _install_fake_fzf(d, f"tee {capture} | head -1")
        p = _run([], env=_env_with_fakedir(d))
        lines = capture.read_text().strip().splitlines()
        assert len(lines) == 2
        assert "https://a.com" in lines
        assert "https://b.com" in lines
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_multiple_urls_on_separate_lines():
    d = _make_fakedir()
    try:
        _write_buffer(
            "https://first.com\n"
            "https://second.com\n"
            "https://third.com\n"
        )
        capture = d / "fzf_input.txt"
        _install_fake_fzf(d, f"tee {capture} | head -1")
        p = _run([], env=_env_with_fakedir(d))
        lines = capture.read_text().strip().splitlines()
        assert len(lines) == 3
        assert "https://first.com" in lines
        assert "https://second.com" in lines
        assert "https://third.com" in lines
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_extracts_urls_from_mixed_content():
    d = _make_fakedir()
    try:
        _write_buffer(
            "Build log:\n"
            "  error at https://ci.example.com/build/1234#log\n"
            "  retry: https://ci.example.com/build/1234#log\n"
            "  docs https://docs.example.com/errors\n"
        )
        capture = d / "fzf_input.txt"
        _install_fake_fzf(d, f"tee {capture} | head -1")
        p = _run([], env=_env_with_fakedir(d))
        lines = capture.read_text().strip().splitlines()
        assert len(lines) == 2  # build URL deduped
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


# ── OSC 52 encoding ────────────────────────────────────────────────────────


def test_osc52_encoding():
    d = _make_fakedir()
    try:
        url = "https://example.com/test/path?a=1&b=2"
        _write_buffer(f"link: {url}\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(url.encode()).decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_osc52_exact_format():
    d = _make_fakedir()
    try:
        url = "https://example.com"
        _write_buffer(f"{url}\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(url.encode()).decode()
        assert f"\x1b]52;c;{encoded}\x07" in p.stdout
        assert "\x1b]52;c;" in p.stdout
        assert "\x07" in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_no_osc52_when_nothing_selected():
    d = _make_fakedir()
    try:
        _write_buffer("https://example.com\n")
        _install_fake_fzf(d, "exit 0")  # outputs nothing
        p = _run([], env=_env_with_fakedir(d))
        assert "\x1b]52" not in p.stdout
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_long_url():
    d = _make_fakedir()
    try:
        url = "https://example.com/" + "a" * 500
        _write_buffer(f"{url}\n")
        _install_fake_fzf(d, "head -1")
        p = _run([], env=_env_with_fakedir(d))
        encoded = base64.b64encode(url.encode()).decode()
        # Linux base64 may wrap at 76 chars; strip newlines before comparing
        stdout_clean = p.stdout.replace("\n", "")
        assert f"\x1b]52;c;{encoded}\x07" in stdout_clean
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


# ── fzf flags ──────────────────────────────────────────────────────────────


def test_fzf_receives_correct_flags():
    d = _make_fakedir()
    try:
        _write_buffer("https://example.com\n")
        args_capture = d / "fzf_args.txt"
        _install_fake_fzf(d, f'echo "$@" > {args_capture}\nhead -1')
        p = _run([], env=_env_with_fakedir(d))
        args = args_capture.read_text().strip()
        assert "--reverse" in args
        assert "--prompt" in args
        assert "Copy URL" in args
        assert "--no-info" in args
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


# ── tmux display-message ──────────────────────────────────────────────────


def test_tmux_display_message_called_on_selection():
    d = _make_fakedir()
    try:
        url = "https://example.com/test"
        _write_buffer(f"{url}\n")
        _install_fake_fzf(d, "head -1")
        tmux_capture = d / "tmux_args.txt"
        _install_fake_tmux(d, tmux_capture)
        p = _run([], env=_env_with_fakedir(d))
        tmux_calls = tmux_capture.read_text().strip().splitlines()
        assert len(tmux_calls) >= 1
        assert "display-message" in tmux_calls[0]
        assert url in tmux_calls[0]
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


def test_tmux_not_called_when_nothing_selected():
    d = _make_fakedir()
    try:
        _write_buffer("https://example.com\n")
        _install_fake_fzf(d, "exit 0")
        tmux_capture = d / "tmux_args.txt"
        _install_fake_tmux(d, tmux_capture)
        p = _run([], env=_env_with_fakedir(d))
        assert not tmux_capture.exists()
    finally:
        _remove_buffer()
        _cleanup_fakedir(d)


# ── Unknown flags fall through ─────────────────────────────────────────────


def test_unknown_flag_runs_normally():
    _remove_buffer()
    p = _run(["--version"])
    assert p.returncode == 0
    assert "No URLs found" in p.stdout
