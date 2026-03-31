from __future__ import annotations

"""Tests for effectors/tmux-url-select.sh — tmux URL selector for Blink.

Tests operate by:
  1. Validating script structure (shebang, error flags, help text).
  2. Running the script via subprocess with mocked commands (fzf, tmux)
     via PATH overrides.
  3. Verifying URL extraction logic and OSC 52 encoding.
"""

import base64
import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "tmux-url-select.sh"
BUFFER_PATH = Path("/tmp/tmux-url-buffer")


def _read_script() -> str:
    return SCRIPT.read_text()


# ── Structural tests ────────────────────────────────────────────────────


class TestScriptStructure:
    """Verify the script has required structural elements."""

    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_executable(self):
        mode = SCRIPT.stat().st_mode
        assert mode & stat.S_IEXEC, "tmux-url-select.sh should be executable"

    def test_shebang(self):
        lines = _read_script().splitlines()
        assert lines[0] == "#!/usr/bin/env bash"

    def test_strict_mode(self):
        content = _read_script()
        assert "set -euo pipefail" in content

    def test_no_todo_or_fixme(self):
        content = _read_script()
        for line in content.splitlines():
            upper = line.upper()
            assert "TODO" not in upper, f"Found TODO: {line.strip()}"
            assert "FIXME" not in upper, f"Found FIXME: {line.strip()}"

    def test_script_ends_with_newline(self):
        content = _read_script()
        assert content.endswith("\n"), "Script should end with a newline"


# ── Help flag tests ─────────────────────────────────────────────────────


class TestHelpFlag:
    """Verify --help and -h produce expected output."""

    def test_help_flag(self):
        r = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "Usage:" in r.stdout
        assert "tmux-url-select.sh" in r.stdout

    def test_short_help_flag(self):
        r = subprocess.run(
            ["bash", str(SCRIPT), "-h"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "Usage:" in r.stdout

    def test_help_mentions_requirements(self):
        r = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert "fzf" in r.stdout
        assert "tmux" in r.stdout

    def test_help_exits_zero(self):
        r = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0


# ── URL extraction logic ────────────────────────────────────────────────


class TestURLExtraction:
    """Test the grep pattern used to extract URLs from the buffer."""

    def test_extracts_http_url(self, tmp_path):
        buf = tmp_path / "buffer"
        buf.write_text("See http://example.com for details\n")
        r = subprocess.run(
            ["bash", "-c",
             f'grep -oE \'https?://[^ >)"\\x27\\x27]+\' {buf} | awk \'!seen[$0]++\''],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "http://example.com" in r.stdout

    def test_extracts_https_url(self, tmp_path):
        buf = tmp_path / "buffer"
        buf.write_text("Visit https://example.com/path?q=1\n")
        r = subprocess.run(
            ["bash", "-c",
             f'grep -oE \'https?://[^ >)"\\x27\\x27]+\' {buf} | awk \'!seen[$0]++\''],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "https://example.com/path?q=1" in r.stdout

    def test_deduplicates_urls(self, tmp_path):
        buf = tmp_path / "buffer"
        buf.write_text(
            "See https://example.com and also https://example.com again\n"
        )
        r = subprocess.run(
            ["bash", "-c",
             f'grep -oE \'https?://[^ >)"\\x27\\x27]+\' {buf} | awk \'!seen[$0]++\''],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        urls = r.stdout.strip().splitlines()
        assert urls.count("https://example.com") == 1

    def test_extracts_multiple_unique_urls(self, tmp_path):
        buf = tmp_path / "buffer"
        buf.write_text(
            "https://foo.com and https://bar.com and https://baz.com\n"
        )
        r = subprocess.run(
            ["bash", "-c",
             f'grep -oE \'https?://[^ >)"\\x27\\x27]+\' {buf} | awk \'!seen[$0]++\''],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        urls = r.stdout.strip().splitlines()
        assert len(urls) == 3

    def test_stops_at_space(self, tmp_path):
        buf = tmp_path / "buffer"
        buf.write_text("https://example.com/path other text\n")
        r = subprocess.run(
            ["bash", "-c",
             f'grep -oE \'https?://[^ >)"\\x27\\x27]+\' {buf} | awk \'!seen[$0]++\''],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == "https://example.com/path"

    def test_stops_at_closing_paren(self, tmp_path):
        buf = tmp_path / "buffer"
        buf.write_text("link (https://example.com) here\n")
        r = subprocess.run(
            ["bash", "-c",
             f'grep -oE \'https?://[^ >)"\\x27\\x27]+\' {buf} | awk \'!seen[$0]++\''],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == "https://example.com"

    def test_stops_at_double_quote(self, tmp_path):
        buf = tmp_path / "buffer"
        buf.write_text('href="https://example.com/page" target\n')
        r = subprocess.run(
            ["bash", "-c",
             f'grep -oE \'https?://[^ >)"\\x27\\x27]+\' {buf} | awk \'!seen[$0]++\''],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == "https://example.com/page"

    def test_stops_at_single_quote(self, tmp_path):
        buf = tmp_path / "buffer"
        buf.write_text("url='https://example.com/x' next\n")
        r = subprocess.run(
            ["bash", "-c",
             f'grep -oE \'https?://[^ >)"\\x27\\x27]+\' {buf} | awk \'!seen[$0]++\''],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == "https://example.com/x"

    def test_no_urls_in_plain_text(self, tmp_path):
        buf = tmp_path / "buffer"
        buf.write_text("just some plain text without any links\n")
        r = subprocess.run(
            ["bash", "-c",
             f'grep -oE \'https?://[^ >)"\\x27\\x27]+\' {buf}'],
            capture_output=True, text=True, timeout=10,
        )
        assert r.stdout.strip() == ""


# ── No URLs found ───────────────────────────────────────────────────────


class TestNoURLs:
    """Verify behavior when the buffer has no URLs."""

    def test_no_urls_message(self, tmp_path):
        buf = tmp_path / "tmux-url-buffer"
        buf.write_text("no urls here\n")
        # Rewrite the script to use our tmp buffer path
        script_text = _read_script().replace("/tmp/tmux-url-buffer", str(buf))

        r = subprocess.run(
            ["bash", "-c", script_text],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "No URLs found in pane" in r.stdout

    def test_empty_buffer(self, tmp_path):
        buf = tmp_path / "tmux-url-buffer"
        buf.write_text("")
        script_text = _read_script().replace("/tmp/tmux-url-buffer", str(buf))

        r = subprocess.run(
            ["bash", "-c", script_text],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "No URLs found in pane" in r.stdout

    def test_nonexistent_buffer(self, tmp_path):
        fake_buf = tmp_path / "nonexistent-buffer"
        script_text = _read_script().replace("/tmp/tmux-url-buffer", str(fake_buf))

        # grep on nonexistent file → script should fail (set -e) or handle it
        r = subprocess.run(
            ["bash", "-c", script_text],
            capture_output=True, text=True, timeout=10,
        )
        # The script uses set -e, so grep failing on nonexistent file
        # will cause non-zero exit. That's acceptable behavior.
        # Just verify it doesn't hang.
        assert r.returncode != 0 or "No URLs" in r.stdout


# ── URL selected (mocked fzf + tmux) ───────────────────────────────────


class TestURLSelected:
    """Test the selection path with mocked fzf and tmux."""

    def _make_mock_env(self, tmp_path, fzf_output: str) -> dict:
        """Create a PATH-override env with mocked fzf and tmux."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        # Mock fzf: just echo the predetermined output
        (bin_dir / "fzf").write_text(
            f"#!/bin/bash\necho '{fzf_output}'\n"
        )
        (bin_dir / "fzf").chmod(0o755)

        # Mock tmux: record calls
        tmux_log = tmp_path / "tmux.log"
        (bin_dir / "tmux").write_text(
            f"#!/bin/bash\necho \"$@\" >> {tmux_log}\n"
        )
        (bin_dir / "tmux").chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        return env

    def test_selected_url_emits_osc52(self, tmp_path):
        buf = tmp_path / "tmux-url-buffer"
        buf.write_text("https://example.com\n")
        script_text = _read_script().replace("/tmp/tmux-url-buffer", str(buf))

        env = self._make_mock_env(tmp_path, "https://example.com")

        r = subprocess.run(
            ["bash", "-c", script_text],
            capture_output=True, text=True, timeout=10,
            env=env,
        )
        assert r.returncode == 0

        # Verify OSC 52 escape sequence was emitted
        expected_b64 = base64.b64encode(b"https://example.com").decode()
        osc52 = f"\x1b]52;c;{expected_b64}\x07"
        assert osc52 in r.stdout, f"OSC 52 not found in stdout. Got: {repr(r.stdout)}"

    def test_selected_url_calls_tmux_display_message(self, tmp_path):
        buf = tmp_path / "tmux-url-buffer"
        buf.write_text("https://example.com\n")
        script_text = _read_script().replace("/tmp/tmux-url-buffer", str(buf))

        env = self._make_mock_env(tmp_path, "https://example.com")

        subprocess.run(
            ["bash", "-c", script_text],
            capture_output=True, text=True, timeout=10,
            env=env,
        )

        tmux_log = (tmp_path / "tmux.log").read_text()
        assert "display-message" in tmux_log
        assert "Copied:" in tmux_log
        assert "https://example.com" in tmux_log

    def test_base64_encoding_correct(self, tmp_path):
        url = "https://github.com/anthropics/claude-code"
        buf = tmp_path / "tmux-url-buffer"
        buf.write_text(url + "\n")
        script_text = _read_script().replace("/tmp/tmux-url-buffer", str(buf))

        env = self._make_mock_env(tmp_path, url)

        r = subprocess.run(
            ["bash", "-c", script_text],
            capture_output=True, text=True, timeout=10,
            env=env,
        )
        assert r.returncode == 0

        expected_b64 = base64.b64encode(url.encode()).decode()
        assert expected_b64 in r.stdout

    def test_url_with_query_params(self, tmp_path):
        url = "https://example.com/search?q=hello+world&lang=en"
        buf = tmp_path / "tmux-url-buffer"
        buf.write_text(url + "\n")
        script_text = _read_script().replace("/tmp/tmux-url-buffer", str(buf))

        env = self._make_mock_env(tmp_path, url)

        r = subprocess.run(
            ["bash", "-c", script_text],
            capture_output=True, text=True, timeout=10,
            env=env,
        )
        assert r.returncode == 0

        expected_b64 = base64.b64encode(url.encode()).decode()
        assert expected_b64 in r.stdout


# ── No selection (fzf returns empty) ───────────────────────────────────


class TestNoSelection:
    """Test behavior when fzf is cancelled / returns empty."""

    def _make_mock_env(self, tmp_path) -> dict:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        # Mock fzf: returns nothing (user cancelled)
        (bin_dir / "fzf").write_text("#!/bin/bash\nexit 1\n")
        (bin_dir / "fzf").chmod(0o755)

        # Mock tmux: should NOT be called
        tmux_log = tmp_path / "tmux.log"
        (bin_dir / "tmux").write_text(
            f"#!/bin/bash\necho \"$@\" >> {tmux_log}\n"
        )
        (bin_dir / "tmux").chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
        return env

    def test_no_tmux_call_on_cancel(self, tmp_path):
        buf = tmp_path / "tmux-url-buffer"
        buf.write_text("https://example.com\n")
        script_text = _read_script().replace("/tmp/tmux-url-buffer", str(buf))

        env = self._make_mock_env(tmp_path)

        r = subprocess.run(
            ["bash", "-c", script_text],
            capture_output=True, text=True, timeout=10,
            env=env,
        )
        # Script may exit non-zero due to set -e + fzf returning 1,
        # but the key thing is no OSC 52 and no tmux display-message.
        tmux_log_path = tmp_path / "tmux.log"
        if tmux_log_path.exists():
            assert tmux_log_path.read_text() == "", "tmux should not be called on cancel"

        # No OSC 52 sequence emitted
        assert "\x1b]52;" not in r.stdout


# ── OSC 52 encoding verification ───────────────────────────────────────


class TestOSC52Encoding:
    """Verify OSC 52 escape sequence format directly."""

    def test_osc52_format(self):
        """OSC 52 should follow the format ESC]52;c;<base64>BEL."""
        url = "https://example.com"
        encoded = base64.b64encode(url.encode()).decode()
        osc52 = f"\x1b]52;c;{encoded}\x07"
        assert osc52.startswith("\x1b]52;c;")
        assert osc52.endswith("\x07")

    def test_encoding_matches_script(self, tmp_path):
        """The script's base64 encoding should match Python's."""
        url = "https://test.org/path"
        buf = tmp_path / "tmux-url-buffer"
        buf.write_text(url + "\n")

        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        (bin_dir / "fzf").write_text(f"#!/bin/bash\necho '{url}'\n")
        (bin_dir / "fzf").chmod(0o755)
        (bin_dir / "tmux").write_text("#!/bin/bash\n")
        (bin_dir / "tmux").chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

        script_text = _read_script().replace("/tmp/tmux-url-buffer", str(buf))
        r = subprocess.run(
            ["bash", "-c", script_text],
            capture_output=True, text=True, timeout=10,
            env=env,
        )

        python_b64 = base64.b64encode(url.encode()).decode()
        assert python_b64 in r.stdout


# ── Syntax check ────────────────────────────────────────────────────────


class TestSyntaxCheck:
    """Verify the script is syntactically valid bash."""

    def test_bash_syntax_valid(self):
        r = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0, f"Syntax error:\n{r.stderr}"
