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
# Passed directly to grep (no shell quoting needed when using exec form).
URL_PATTERN = r"""https?://[^ >)"']+"""


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
    """Write content to the buffer and run just the grep+dedup pipeline.

    Uses subprocess list form (no shell) so the regex pattern with single
    quotes is passed directly to grep without bash quoting issues.
    Deduplication is done in Python to match the awk ``!seen[$0]++`` logic.
    """
    _write_buffer(buffer_content)
    try:
        r = subprocess.run(
            ["grep", "-oE", URL_PATTERN, str(BUFFER)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return []
        urls: list[str] = []
        seen: set[str] = set()
        for line in r.stdout.strip().split("\n"):
            if line not in seen:
                seen.add(line)
                urls.append(line)
        return urls
    finally:
        _remove_buffer()


def _write_buffer(content: str) -> None:
    BUFFER.write_text(content)


def _remove_buffer() -> None:
    if BUFFER.exists():
        BUFFER.unlink()


def _make_fzf_mock(tmpdir: str, selection: str) -> None:
    """Create a mock fzf that consumes stdin (avoids SIGPIPE) then echoes the selection."""
    mock = os.path.join(tmpdir, "fzf")
    with open(mock, "w") as f:
        f.write(f"#!/bin/sh\ncat >/dev/null\necho '{selection}'\n")
    os.chmod(mock, 0o755)


def _make_tmux_mock(tmpdir: str) -> None:
    """Create a mock tmux that succeeds silently."""
    mock = os.path.join(tmpdir, "tmux")
    with open(mock, "w") as f:
        f.write("#!/bin/sh\nexit 0\n")
    os.chmod(mock, 0o755)


def _make_tmux_log_mock(tmpdir: str, log_path: str) -> None:
    """Create a mock tmux that logs its arguments to a file."""
    mock = os.path.join(tmpdir, "tmux")
    with open(mock, "w") as f:
        f.write(f"#!/bin/sh\necho \"$@\" > '{log_path}'\n")
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
                assert r.returncode == 0
                expected_b64 = base64.b64encode(b"https://example.com/test").decode()
                assert expected_b64 in r.stdout
            finally:
                _remove_buffer()

    def test_osc52_escape_sequence_format(self):
        """OSC 52 uses format ESC]52;c;<base64>BEL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            url = "https://example.com/escape-test"
            _make_fzf_mock(tmpdir, url)
            _make_tmux_mock(tmpdir)
            _write_buffer(f"{url}\n")
            try:
                r = _run([], env_extra={"PATH": f"{tmpdir}:{os.environ['PATH']}"})
                assert r.returncode == 0
                expected_b64 = base64.b64encode(url.encode()).decode()
                assert f"\033]52;c;{expected_b64}\a" in r.stdout
            finally:
                _remove_buffer()

    def test_fzf_cancels_no_osc52(self):
        """When fzf exits 1 (user cancels), set -e aborts — no OSC 52."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock = os.path.join(tmpdir, "fzf")
            with open(mock, "w") as f:
                f.write("#!/bin/sh\ncat >/dev/null\nexit 1\n")
            os.chmod(mock, 0o755)
            _make_tmux_mock(tmpdir)
            _write_buffer("https://example.com\n")
            try:
                r = _run([], env_extra={"PATH": f"{tmpdir}:{os.environ['PATH']}"})
                assert r.returncode != 0
                assert "]52;c;" not in r.stdout
            finally:
                _remove_buffer()

    def test_fzf_empty_output_no_osc52(self):
        """When fzf outputs nothing (empty selection), no OSC 52 is emitted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock = os.path.join(tmpdir, "fzf")
            with open(mock, "w") as f:
                # Consume stdin, output nothing, exit 0
                f.write("#!/bin/sh\ncat >/dev/null\nexit 0\n")
            os.chmod(mock, 0o755)
            _make_tmux_mock(tmpdir)
            _write_buffer("https://example.com\n")
            try:
                r = _run([], env_extra={"PATH": f"{tmpdir}:{os.environ['PATH']}"})
                assert r.returncode == 0
                assert "]52;c;" not in r.stdout
            finally:
                _remove_buffer()

    def test_tmux_display_message_called(self):
        """After selecting, tmux display-message is called with the URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "tmux.log")
            _make_fzf_mock(tmpdir, "https://example.com/msg")
            _make_tmux_log_mock(tmpdir, log_file)
            _write_buffer("https://example.com/msg\n")
            try:
                r = _run([], env_extra={"PATH": f"{tmpdir}:{os.environ['PATH']}"})
                assert r.returncode == 0
                log = open(log_file).read()
                assert "display-message" in log
                assert "https://example.com/msg" in log
            finally:
                _remove_buffer()

    def test_url_with_query_and_fragment(self):
        """URLs with query strings and fragments are handled correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            url = "https://example.com/path?q=hello&lang=en#section"
            _make_fzf_mock(tmpdir, url)
            _make_tmux_mock(tmpdir)
            _write_buffer(f"link: {url} end\n")
            try:
                r = _run([], env_extra={"PATH": f"{tmpdir}:{os.environ['PATH']}"})
                assert r.returncode == 0
                expected_b64 = base64.b64encode(url.encode()).decode()
                assert expected_b64 in r.stdout
            finally:
                _remove_buffer()


# ── Full pipeline test (grep+awk in bash) ──────────────────────────────


class TestPipeline:
    """Test the full grep+awk pipeline as the script actually runs it."""

    def _run_pipeline(self, buffer_content: str) -> tuple[int, str]:
        """Run the exact grep+awk pipeline from the script via bash -c.

        Includes ``set -o pipefail`` to match the script's ``set -euo pipefail``.
        """
        _write_buffer(buffer_content)
        try:
            # Use the same quoting trick as the original script: '...'"'"'...'
            grep_part = """grep -oE 'https?://[^ >)"'"'"']+' /tmp/tmux-url-buffer"""
            awk_part = """awk '!seen[$0]++'"""
            cmd = f"set -o pipefail; {grep_part} | {awk_part}"
            r = subprocess.run(
                ["bash", "-c", cmd],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return r.returncode, r.stdout.strip()
        finally:
            _remove_buffer()

    def test_pipeline_extracts_single_url(self):
        rc, out = self._run_pipeline("Visit https://example.com/here\n")
        assert rc == 0
        assert out == "https://example.com/here"

    def test_pipeline_deduplicates(self):
        rc, out = self._run_pipeline(
            "https://a.com\nhttps://a.com\nhttps://b.com\n"
        )
        assert rc == 0
        lines = out.split("\n")
        assert lines == ["https://a.com", "https://b.com"]

    def test_pipeline_no_urls_returns_1(self):
        rc, out = self._run_pipeline("just text no urls\n")
        assert rc != 0

    def test_pipeline_url_with_path_and_query(self):
        rc, out = self._run_pipeline(
            "check https://example.com/api/v1?q=test&limit=10 here\n"
        )
        assert rc == 0
        assert out == "https://example.com/api/v1?q=test&limit=10"
