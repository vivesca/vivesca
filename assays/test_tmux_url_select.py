from __future__ import annotations

"""Tests for tmux-url-select.sh — interactive URL picker with OSC 52 copy.

Uses subprocess.run to invoke the script (effectors are scripts, not importable).
"""

import base64
import os
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "tmux-url-select.sh"
BUFFER = Path("/tmp/tmux-url-buffer")

# Regex from the script: https?://[^ >)"']+
# We extract the same pattern for standalone tests.
URL_PATTERN = r"https?://[^ >)\"']+"

# Helper script that runs just the extraction pipeline.
GREP_SCRIPT = """#!/usr/bin/env bash
grep -oE '{pattern}' "$1" | awk '!seen[$0]++'
"""


def _run(
    args: list[str],
    *,
    env_extra: dict | None = None,
    input_data: str = "",
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(env_extra or {})
    return subprocess.run(
        ["/usr/bin/env", "bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        input=input_data,
    )


def _run_extract(buffer_content: str) -> list[str]:
    """Write content to the buffer and run just the extraction pipeline."""
    _write_buffer(buffer_content)
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(GREP_SCRIPT.format(pattern=URL_PATTERN))
            f.flush()
            tmp_script = f.name
        os.chmod(tmp_script, 0o755)
        r = subprocess.run(
            ["bash", tmp_script, str(BUFFER)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        os.unlink(tmp_script)
        if r.returncode != 0:
            return []
        return r.stdout.strip().split("\n") if r.stdout.strip() else []
    finally:
        _remove_buffer()


def _write_buffer(content: str) -> None:
    BUFFER.write_text(content)


def _remove_buffer() -> None:
    if BUFFER.exists():
        BUFFER.unlink()


def _make_fzf_mock(tmpdir: str, selection: str) -> None:
    """Create a mock fzf that echoes the selection."""
    mock = os.path.join(tmpdir, "fzf")
    with open(mock, "w") as f:
        f.write(f"#!/bin/sh\necho '{selection}'\n")
    os.chmod(mock, 0o755)


def _make_tmux_mock(tmpdir: str) -> None:
    """Create a mock tmux that succeeds silently."""
    mock = os.path.join(tmpdir, "tmux")
    with open(mock, "w") as f:
        f.write("#!/bin/sh\nexit 0\n")
    os.chmod(mock, 0o755)


# ── Help tests ──────────────────────────────────────────────────────────


class TestHelp:
    def test_help_long_flag(self):
        r = _run(["--help"])
        assert r.returncode == 0
        assert "Usage" in r.stdout
        assert "tmux-url-select.sh" in r.stdout

    def test_help_short_flag(self):
        r = _run(["-h"])
        assert r.returncode == 0
        assert "Usage" in r.stdout

    def test_help_mentions_requirements(self):
        r = _run(["--help"])
        assert "fzf" in r.stdout
        assert "tmux" in r.stdout
        assert "OSC 52" in r.stdout


# ── No-URL / missing buffer tests ──────────────────────────────────────


class TestNoUrls:
    def test_empty_buffer_exits_nonzero(self):
        """grep returns 1 on no match; set -euo pipefail causes non-zero exit."""
        _write_buffer("no urls here just text\n")
        try:
            r = _run([])
            assert r.returncode != 0
        finally:
            _remove_buffer()

    def test_buffer_with_no_http_exits_nonzero(self):
        """ftp:// does not match the https?:// pattern."""
        _write_buffer("ftp://example.com\njust some words\n")
        try:
            r = _run([])
            assert r.returncode != 0
        finally:
            _remove_buffer()

    def test_missing_buffer_file(self):
        _remove_buffer()
        r = _run([])
        assert r.returncode != 0


# ── URL extraction tests ───────────────────────────────────────────────


class TestUrlExtraction:
    def test_deduplicates_urls(self):
        lines = _run_extract(
            "Visit https://example.com/a\n"
            "Also https://example.com/a\n"
            "And https://example.com/b\n"
        )
        assert lines == ["https://example.com/a", "https://example.com/b"]

    def test_multiple_urls_in_buffer(self):
        lines = _run_extract(
            "Check https://foo.com and https://bar.org/baz?q=1\n"
            "Also https://foo.com repeated\n"
        )
        assert "https://foo.com" in lines
        assert "https://bar.org/baz?q=1" in lines
        assert len(lines) == 2

    def test_url_stops_at_space(self):
        lines = _run_extract("link: https://example.com/path next word\n")
        assert lines == ["https://example.com/path"]

    def test_url_stops_at_angle_bracket(self):
        lines = _run_extract("<https://example.com>click\n")
        assert lines == ["https://example.com"]

    def test_url_stops_at_double_quote(self):
        lines = _run_extract('href="https://example.com/x" class\n')
        assert lines == ["https://example.com/x"]

    def test_url_stops_at_paren(self):
        lines = _run_extract("(https://example.com/z)see\n")
        assert lines == ["https://example.com/z"]

    def test_url_stops_at_single_quote(self):
        lines = _run_extract("url='https://example.com/sq'more\n")
        assert lines == ["https://example.com/sq"]

    def test_http_url_extracted(self):
        lines = _run_extract("Visit http://insecure.com/page\n")
        assert lines == ["http://insecure.com/page"]


# ── End-to-end with mock fzf/tmux ──────────────────────────────────────


class TestEndToEnd:
    def test_single_url_selected_emits_osc52(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_fzf_mock(tmpdir, "https://example.com/page")
            _make_tmux_mock(tmpdir)
            _write_buffer("Visit https://example.com/page for details\n")
            try:
                r = _run([], env_extra={"PATH": f"{tmpdir}:{os.environ['PATH']}"})
                assert r.returncode == 0
                # OSC 52 escape sequence should be in stdout
                assert "]52;c;" in r.stdout
            finally:
                _remove_buffer()

    def test_osc52_encoding_correct_base64(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_fzf_mock(tmpdir, "https://example.com/test")
            _make_tmux_mock(tmpdir)
            _write_buffer("https://example.com/test\n")
            try:
                r = _run([], env_extra={"PATH": f"{tmpdir}:{os.environ['PATH']}"})
                expected_b64 = base64.b64encode(b"https://example.com/test").decode()
                assert expected_b64 in r.stdout
            finally:
                _remove_buffer()

    def test_fzf_cancels_no_osc52(self):
        """When fzf exits 1 (user cancels), set -e aborts — no OSC 52."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock = os.path.join(tmpdir, "fzf")
            with open(mock, "w") as f:
                f.write("#!/bin/sh\nexit 1\n")
            os.chmod(mock, 0o755)
            _make_tmux_mock(tmpdir)
            _write_buffer("https://example.com\n")
            try:
                r = _run([], env_extra={"PATH": f"{tmpdir}:{os.environ['PATH']}"})
                assert r.returncode != 0
                assert "]52;c;" not in r.stdout
            finally:
                _remove_buffer()
