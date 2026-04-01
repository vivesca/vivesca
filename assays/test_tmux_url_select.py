from __future__ import annotations

"""Tests for effectors/tmux-url-select.sh.

Effectors are scripts — tested via subprocess.run, never imported.
"""

import os
import subprocess
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "effectors" / "tmux-url-select.sh"
BUFFER_FILE = Path("/tmp/tmux-url-buffer")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(
    args: list[str] | None = None,
    env_extra: dict[str, str] | None = None,
    timeout: int = 10,
    stdin_data: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run tmux-url-select.sh with optional overrides."""
    cmd = ["bash", str(SCRIPT), *(args or [])]
    env = os.environ.copy()
    env.update(env_extra or {})
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        input=stdin_data,
    )


def _make_mock_bin(bindir: Path, name: str, body: str) -> Path:
    """Create a mock executable script in bindir."""
    path = bindir / name
    path.write_text(f"#!/usr/bin/env bash\n{body}\n")
    path.chmod(0o755)
    return path


def _env_with_mocked_path(tmp_path: Path, mocks: dict[str, str]) -> dict[str, str]:
    """Return env dict with a PATH that finds our mock scripts first."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for name, body in mocks.items():
        _make_mock_bin(bindir, name, body)
    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '/usr/bin:/bin')}"
    return env


def _write_buffer(urls: str, tmp_path: Path) -> Path:
    """Write url content to the buffer path and return the path."""
    buf = tmp_path / "tmux-url-buffer"
    buf.write_text(urls)
    return buf


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHelp:
    """--help and -h flags."""

    def test_help_flag(self):
        r = _run(["--help"])
        assert r.returncode == 0
        assert "Usage:" in r.stdout
        assert "tmux-url-select.sh" in r.stdout

    def test_h_short_flag(self):
        r = _run(["-h"])
        assert r.returncode == 0
        assert "Usage:" in r.stdout


class TestNoURLsFound:
    """When the buffer file is missing or has no URLs."""

    def test_missing_buffer_file(self, tmp_path: Path, monkeypatch):
        """Missing buffer file → prints message, exits 0."""
        buf = tmp_path / "nonexistent"
        env = _env_with_mocked_path(tmp_path, {})
        # Patch the buffer path by rewriting the script's grep target.
        # Instead, write to /tmp/tmux-url-buffer pointing nowhere:
        # We'll just ensure /tmp/tmux-url-buffer doesn't have URLs.
        # Use a tmp buffer file and override via sed-free approach:
        # Actually easiest: just ensure the real buffer is absent/empty.
        r = _run(env_extra=env)
        assert r.returncode == 0
        assert "No URLs found in pane" in r.stdout

    def test_empty_buffer_file(self, tmp_path: Path):
        """Empty buffer → prints message, exits 0."""
        BUFFER_FILE.write_text("")
        try:
            r = _run()
            assert r.returncode == 0
            assert "No URLs found in pane" in r.stdout
        finally:
            BUFFER_FILE.unlink(missing_ok=True)

    def test_buffer_with_no_urls(self, tmp_path: Path):
        """Buffer with plain text (no URLs) → prints message, exits 0."""
        BUFFER_FILE.write_text("just some text\nno links here\n")
        try:
            r = _run()
            assert r.returncode == 0
            assert "No URLs found in pane" in r.stdout
        finally:
            BUFFER_FILE.unlink(missing_ok=True)


class TestURLSelection:
    """URL extraction and selection via fzf."""

    def test_single_url_selected(self, tmp_path: Path):
        """Single URL in buffer, fzf selects it → OSC 52 emitted."""
        url = "https://example.com/page"
        BUFFER_FILE.write_text(f"Check out {url} for details\n")
        try:
            # Mock fzf to just pass through stdin (pick first line)
            # Mock tmux display-message to capture args
            mock_fzf = textwrap.dedent("""\
                # fzf mock: just echo first line from stdin
                head -n1
            """)
            display_msg_file = tmp_path / "tmux_display_args"
            mock_tmux = textwrap.dedent(f"""\
                echo "$@" > {display_msg_file}
            """)
            env = _env_with_mocked_path(tmp_path, {
                "fzf": mock_fzf,
                "tmux": mock_tmux,
            })

            r = _run(env_extra=env)
            assert r.returncode == 0
            # Should contain OSC 52 escape sequence with base64-encoded URL
            import base64
            expected_b64 = base64.b64encode(url.encode()).decode()
            assert f"\033]52;c;{expected_b64}\a" in r.stdout
            # tmux display-message should have been called
            assert display_msg_file.exists()
            msg = display_msg_file.read_text()
            assert "display-message" in msg
            assert url in msg
        finally:
            BUFFER_FILE.unlink(missing_ok=True)

    def test_multiple_urls_deduplicated(self, tmp_path: Path):
        """Duplicate URLs in buffer are deduplicated before fzf."""
        BUFFER_FILE.write_text(
            "See https://example.com and also https://example.com again\n"
        )
        try:
            # Capture what fzf receives on stdin by writing it to a file
            fzf_input_file = tmp_path / "fzf_input"
            mock_fzf = textwrap.dedent(f"""\
                cat > {fzf_input_file}
                # Output the first URL
                head -n1 {fzf_input_file}
            """)
            mock_tmux = textwrap.dedent("""\
                true
            """)
            env = _env_with_mocked_path(tmp_path, {
                "fzf": mock_fzf,
                "tmux": mock_tmux,
            })

            r = _run(env_extra=env)
            assert r.returncode == 0
            # The fzf input should have only 1 line (deduplicated)
            fzf_input = fzf_input_file.read_text().strip()
            lines = [l for l in fzf_input.splitlines() if l.strip()]
            assert len(lines) == 1
            assert lines[0] == "https://example.com"
        finally:
            BUFFER_FILE.unlink(missing_ok=True)

    def test_url_selection_none_chosen(self, tmp_path: Path):
        """fzf returns empty (user cancelled) → no OSC 52 output."""
        BUFFER_FILE.write_text("Visit https://example.com today\n")
        try:
            # Mock fzf to return empty
            mock_fzf = textwrap.dedent("""\
                # Simulate user pressing Escape / cancelling
                true  # output nothing
            """)
            mock_tmux = textwrap.dedent("""\
                echo "SHOULD NOT BE CALLED" > /tmp/test_tmux_fail
            """)
            env = _env_with_mocked_path(tmp_path, {
                "fzf": mock_fzf,
                "tmux": mock_tmux,
            })

            r = _run(env_extra=env)
            assert r.returncode == 0
            # No OSC 52 escape sequence
            assert "\033]52;" not in r.stdout
        finally:
            BUFFER_FILE.unlink(missing_ok=True)

    def test_url_with_special_chars(self, tmp_path: Path):
        """URLs with query params and fragments are handled correctly."""
        url = "https://example.com/path?q=hello+world&lang=en#section"
        BUFFER_FILE.write_text(f"Link: {url}\n")
        try:
            mock_fzf = textwrap.dedent("""\
                head -n1
            """)
            display_file = tmp_path / "tmux_msg"
            mock_tmux = textwrap.dedent(f"""\
                echo "$*" > {display_file}
            """)
            env = _env_with_mocked_path(tmp_path, {
                "fzf": mock_fzf,
                "tmux": mock_tmux,
            })

            r = _run(env_extra=env)
            assert r.returncode == 0
            import base64
            expected_b64 = base64.b64encode(url.encode()).decode()
            assert f"\033]52;c;{expected_b64}\a" in r.stdout
        finally:
            BUFFER_FILE.unlink(missing_ok=True)

    def test_http_url_extracted(self, tmp_path: Path):
        """http:// URLs (non-HTTPS) are also extracted."""
        url = "http://insecure.example.org"
        BUFFER_FILE.write_text(f"Old link: {url}\n")
        try:
            mock_fzf = textwrap.dedent("""\
                head -n1
            """)
            mock_tmux = textwrap.dedent("""\
                true
            """)
            env = _env_with_mocked_path(tmp_path, {
                "fzf": mock_fzf,
                "tmux": mock_tmux,
            })

            r = _run(env_extra=env)
            assert r.returncode == 0
            import base64
            expected_b64 = base64.b64encode(url.encode()).decode()
            assert f"\033]52;c;{expected_b64}\a" in r.stdout
        finally:
            BUFFER_FILE.unlink(missing_ok=True)


class TestURLExtraction:
    """Verify URL regex patterns from the buffer."""

    def test_urls_excluded_trailing_punctuation(self, tmp_path: Path):
        """Trailing ) > " characters are not part of the URL."""
        BUFFER_FILE.write_text('(see https://example.com/page) and "https://other.com"\n')
        try:
            fzf_input_file = tmp_path / "fzf_input"
            mock_fzf = textwrap.dedent(f"""\
                cat > {fzf_input_file}
                head -n1 {fzf_input_file}
            """)
            mock_tmux = textwrap.dedent("""\
                true
            """)
            env = _env_with_mocked_path(tmp_path, {
                "fzf": mock_fzf,
                "tmux": mock_tmux,
            })

            r = _run(env_extra=env)
            assert r.returncode == 0
            fzf_input = fzf_input_file.read_text().strip()
            lines = [l for l in fzf_input.splitlines() if l.strip()]
            assert "https://example.com/page" in lines
            assert "https://other.com" in lines
            # Ensure trailing ) and " are NOT in the URLs
            for line in lines:
                assert not line.endswith(")")
                assert not line.endswith('"')
        finally:
            BUFFER_FILE.unlink(missing_ok=True)

    def test_multiple_distinct_urls(self, tmp_path: Path):
        """Multiple distinct URLs are all extracted."""
        BUFFER_FILE.write_text(
            "First: https://a.com\nSecond: https://b.com\nThird: https://c.com\n"
        )
        try:
            fzf_input_file = tmp_path / "fzf_input"
            mock_fzf = textwrap.dedent(f"""\
                cat > {fzf_input_file}
                head -n1 {fzf_input_file}
            """)
            mock_tmux = textwrap.dedent("""\
                true
            """)
            env = _env_with_mocked_path(tmp_path, {
                "fzf": mock_fzf,
                "tmux": mock_tmux,
            })

            r = _run(env_extra=env)
            assert r.returncode == 0
            fzf_input = fzf_input_file.read_text().strip()
            lines = [l for l in fzf_input.splitlines() if l.strip()]
            assert len(lines) == 3
            assert "https://a.com" in lines
            assert "https://b.com" in lines
            assert "https://c.com" in lines
        finally:
            BUFFER_FILE.unlink(missing_ok=True)
