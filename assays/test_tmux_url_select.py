from __future__ import annotations

"""Tests for tmux-url-select.sh — interactive URL picker with OSC 52 copy.

Uses subprocess.run to invoke the script (effectors are scripts, not importable).
"""

import os
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "tmux-url-select.sh"
BUFFER = Path("/tmp/tmux-url-buffer")


def _run(args: list[str], *, env_extra: dict | None = None, input_data: str = "") -> subprocess.CompletedProcess[str]:
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


def _write_buffer(content: str) -> None:
    BUFFER.write_text(content)


def _remove_buffer() -> None:
    if BUFFER.exists():
        BUFFER.unlink()


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


class TestNoUrls:
    def test_empty_buffer(self):
        _write_buffer("no urls here just text\n")
        try:
            r = _run([])
            assert r.returncode == 0
            assert "No URLs found" in r.stdout
        finally:
            _remove_buffer()

    def test_buffer_with_no_http(self):
        _write_buffer("ftp://example.com\njust some words\n")
        try:
            r = _run([])
            assert r.returncode == 0
            assert "No URLs found" in r.stdout
        finally:
            _remove_buffer()

    def test_missing_buffer_file(self):
        _remove_buffer()
        r = _run([])
        # set -e causes non-zero exit when grep fails on missing file
        assert r.returncode != 0


class TestUrlExtraction:
    def _make_fzf_mock(self, tmpdir: str, selection: str) -> str:
        """Create a mock fzf that echoes the selection."""
        mock = os.path.join(tmpdir, "fzf")
        with open(mock, "w") as f:
            f.write(f"#!/bin/sh\necho '{selection}'\n")
        os.chmod(mock, 0o755)
        return tmpdir

    def test_single_url_selected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_fzf_mock(tmpdir, "https://example.com/page")
            _write_buffer("Visit https://example.com/page for details\n")
            try:
                r = _run([], env_extra={"PATH": f"{tmpdir}:{os.environ['PATH']}"})
                # Should emit OSC 52 sequence with base64-encoded URL
                assert r.returncode == 0
                assert "\\033]52;c;" in r.stdout or "]52;c;" in r.stdout
            finally:
                _remove_buffer()

    def test_deduplicates_urls(self):
        """URL extraction uses awk '!seen[$0]++' to deduplicate."""
        _write_buffer(
            "Visit https://example.com/a\n"
            "Also https://example.com/a\n"
            "And https://example.com/b\n"
        )
        try:
            # Run just the extraction part manually to check dedup
            r = subprocess.run(
                ["bash", "-c",
                 f"grep -oE 'https?://[^ >)\"'\\''']+' {BUFFER} | awk '!seen[$0]++'"],
                capture_output=True, text=True, timeout=5,
            )
            lines = r.stdout.strip().split("\n")
            assert lines == ["https://example.com/a", "https://example.com/b"]
        finally:
            _remove_buffer()

    def test_multiple_urls_in_buffer(self):
        _write_buffer(
            "Check https://foo.com and https://bar.org/baz?q=1\n"
            "Also https://foo.com repeated\n"
        )
        try:
            r = subprocess.run(
                ["bash", "-c",
                 f"grep -oE 'https?://[^ >)\"'\\''']+' {BUFFER} | awk '!seen[$0]++'"],
                capture_output=True, text=True, timeout=5,
            )
            lines = r.stdout.strip().split("\n")
            assert "https://foo.com" in lines
            assert "https://bar.org/baz?q=1" in lines
            assert len(lines) == 2  # deduped
        finally:
            _remove_buffer()

    def test_url_stops_at_space(self):
        _write_buffer("link: https://example.com/path next word\n")
        try:
            r = subprocess.run(
                ["bash", "-c",
                 f"grep -oE 'https?://[^ >)\"'\\''']+' {BUFFER}"],
                capture_output=True, text=True, timeout=5,
            )
            assert r.stdout.strip() == "https://example.com/path"
        finally:
            _remove_buffer()

    def test_url_stops_at_angle_bracket(self):
        _write_buffer("<https://example.com>click\n")
        try:
            r = subprocess.run(
                ["bash", "-c",
                 f"grep -oE 'https?://[^ >)\"'\\''']+' {BUFFER}"],
                capture_output=True, text=True, timeout=5,
            )
            assert r.stdout.strip() == "https://example.com"
        finally:
            _remove_buffer()

    def test_url_stops_at_double_quote(self):
        _write_buffer('href="https://example.com/x" class\n')
        try:
            r = subprocess.run(
                ["bash", "-c",
                 f"grep -oE 'https?://[^ >)\"'\\''']+' {BUFFER}"],
                capture_output=True, text=True, timeout=5,
            )
            assert r.stdout.strip() == "https://example.com/x"
        finally:
            _remove_buffer()

    def test_url_stops_at_paren(self):
        _write_buffer("(https://example.com/z)see\n")
        try:
            r = subprocess.run(
                ["bash", "-c",
                 f"grep -oE 'https?://[^ >)\"'\\''']+' {BUFFER}"],
                capture_output=True, text=True, timeout=5,
            )
            assert r.stdout.strip() == "https://example.com/z"
        finally:
            _remove_buffer()

    def test_url_stops_at_single_quote(self):
        _write_buffer("url='https://example.com/sq'more\n")
        try:
            r = subprocess.run(
                ["bash", "-c",
                 f"grep -oE 'https?://[^ >)\"'\\''']+' {BUFFER}"],
                capture_output=True, text=True, timeout=5,
            )
            assert r.stdout.strip() == "https://example.com/sq"
        finally:
            _remove_buffer()

    def test_http_url_extracted(self):
        _write_buffer("Visit http://insecure.com/page\n")
        try:
            r = subprocess.run(
                ["bash", "-c",
                 f"grep -oE 'https?://[^ >)\"'\\''']+' {BUFFER}"],
                capture_output=True, text=True, timeout=5,
            )
            assert r.stdout.strip() == "http://insecure.com/page"
        finally:
            _remove_buffer()

    def test_osc52_encoding(self):
        """Verify the OSC 52 sequence contains correct base64."""
        import base64
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_fzf_mock(tmpdir, "https://example.com/test")
            _write_buffer("https://example.com/test\n")
            try:
                r = _run([], env_extra={"PATH": f"{tmpdir}:{os.environ['PATH']}"})
                expected_b64 = base64.b64encode(b"https://example.com/test").decode()
                assert expected_b64 in r.stdout
            finally:
                _remove_buffer()

    def test_fzf_cancels_no_output(self):
        """When fzf returns nothing (user cancels), no OSC 52 is emitted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock fzf that returns empty (user pressed Esc)
            mock = os.path.join(tmpdir, "fzf")
            with open(mock, "w") as f:
                f.write("#!/bin/sh\nexit 1\n")
            os.chmod(mock, 0o755)
            _write_buffer("https://example.com\n")
            try:
                r = _run([], env_extra={"PATH": f"{tmpdir}:{os.environ['PATH']}"})
                # fzf exit 1 causes set -e to abort; no OSC 52 emitted
                assert r.returncode != 0
                assert "]52;c;" not in r.stdout
            finally:
                _remove_buffer()
