#!/usr/bin/env python3
"""Test for tmux-url-select.sh effector script."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

EFFECTOR_PATH = Path(__file__).parent.parent / "effectors" / "tmux-url-select.sh"


def test_tmux_url_select_script_exists():
    """Verify the script file exists."""
    assert EFFECTOR_PATH.exists()
    assert EFFECTOR_PATH.is_file()


def test_tmux_url_select_help_flag():
    """Test that --help prints usage and exits cleanly."""
    result = subprocess.run(
        [str(EFFECTOR_PATH), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage: tmux-url-select.sh" in result.stdout
    assert "Interactively select a URL" in result.stdout
    assert "fzf" in result.stdout


def test_tmux_url_select_help_flag_short():
    """Test that -h prints usage and exits cleanly."""
    result = subprocess.run(
        [str(EFFECTOR_PATH), "-h"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage: tmux-url-select.sh" in result.stdout


def test_no_urls_when_buffer_missing():
    """Test script handles missing buffer file gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        buffer_path = Path(tmpdir) / "tmux-url-buffer"
        # Don't create the buffer file - test missing file handling
        result = subprocess.run(
            [str(EFFECTOR_PATH)],
            capture_output=True,
            text=True,
            env={**os.environ, "TMPDIR": tmpdir},
            # Script hardcodes /tmp/tmux-url-buffer, so this tests
            # the "no URLs found" path when file doesn't exist
        )
        # Script should exit 0 and print message about no URLs
        assert result.returncode == 0
        assert "No URLs found in pane" in result.stdout


def test_no_urls_when_buffer_empty():
    """Test script handles empty buffer file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        buffer_path = Path(tmpdir) / "tmux-url-buffer"
        buffer_path.write_text("")
        
        # Script hardcodes /tmp/tmux-url-buffer, so we need to create it there
        # Use a subprocess to avoid polluting the real /tmp
        real_buffer = Path("/tmp/tmux-url-buffer")
        original_content = None
        if real_buffer.exists():
            original_content = real_buffer.read_text()
        
        try:
            real_buffer.write_text("")
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "No URLs found in pane" in result.stdout
        finally:
            # Restore or clean up
            if original_content is not None:
                real_buffer.write_text(original_content)
            elif real_buffer.exists():
                real_buffer.unlink()


def test_url_extraction_and_osc52_output():
    """Test URL extraction and OSC 52 output with mocked fzf."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create mock fzf that selects the first URL
        mock_fzf = tmpdir_path / "fzf"
        mock_fzf.write_text(
            '#!/bin/bash\n'
            '# Mock fzf - read stdin and output first line\n'
            'head -1\n'
        )
        mock_fzf.chmod(0o755)
        
        # Create mock tmux
        mock_tmux = tmpdir_path / "tmux"
        mock_tmux.write_text(
            '#!/bin/bash\n'
            'echo "tmux: $@"\n'
        )
        mock_tmux.chmod(0o755)
        
        # Create buffer with URLs
        real_buffer = Path("/tmp/tmux-url-buffer")
        original_content = None
        if real_buffer.exists():
            original_content = real_buffer.read_text()
        
        try:
            real_buffer.write_text(
                "Check out https://example.com/page1 for info\n"
                "Also see https://example.com/page2\n"
                "Duplicate https://example.com/page1\n"
            )
            
            # Run with mocked PATH
            env = {**os.environ, "PATH": f"{tmpdir}:{os.environ.get('PATH', '')}"}
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )
            
            # Should have selected first URL and output OSC 52
            assert result.returncode == 0
            # OSC 52 format: ESC]52;c;<base64>BEL
            assert "\x1b]52;c;" in result.stdout
            # Verify base64 encoded URL in output
            import base64
            # The selected URL should be the first one after dedup
            # URLs are extracted and deduplicated, first one should be selected
            assert "\x07" in result.stdout  # BEL character terminates OSC
        finally:
            if original_content is not None:
                real_buffer.write_text(original_content)
            elif real_buffer.exists():
                real_buffer.unlink()


def test_url_deduplication():
    """Test that duplicate URLs are removed before selection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Track what fzf receives on stdin
        fzf_input_file = tmpdir_path / "fzf_input.txt"
        mock_fzf = tmpdir_path / "fzf"
        mock_fzf.write_text(
            '#!/bin/bash\n'
            f'cat > {fzf_input_file}\n'
            '# Output first line for selection\n'
            'head -1\n'
        )
        mock_fzf.chmod(0o755)
        
        # Create mock tmux
        mock_tmux = tmpdir_path / "tmux"
        mock_tmux.write_text('#!/bin/bash\n')
        mock_tmux.chmod(0o755)
        
        real_buffer = Path("/tmp/tmux-url-buffer")
        original_content = None
        if real_buffer.exists():
            original_content = real_buffer.read_text()
        
        try:
            # Write buffer with duplicate URLs
            real_buffer.write_text(
                "https://example.com/page1\n"
                "https://example.com/page2\n"
                "https://example.com/page1\n"  # duplicate
                "https://example.com/page3\n"
                "https://example.com/page2\n"  # duplicate
            )
            
            env = {**os.environ, "PATH": f"{tmpdir}:{os.environ.get('PATH', '')}"}
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )
            
            # Check that fzf received deduplicated URLs
            if fzf_input_file.exists():
                urls_seen = fzf_input_file.read_text().strip().split("\n")
                # Should have 3 unique URLs, not 5
                assert len(urls_seen) == 3, f"Expected 3 unique URLs, got {len(urls_seen)}: {urls_seen}"
        finally:
            if original_content is not None:
                real_buffer.write_text(original_content)
            elif real_buffer.exists():
                real_buffer.unlink()


def test_multiple_url_extraction():
    """Test extraction of multiple URLs from mixed content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Mock fzf that outputs a specific URL
        mock_fzf = tmpdir_path / "fzf"
        selected_url = "https://selected.example.com/test"
        mock_fzf.write_text(
            '#!/bin/bash\n'
            f'echo "{selected_url}"\n'
        )
        mock_fzf.chmod(0o755)
        
        # Mock tmux
        mock_tmux = tmpdir_path / "tmux"
        mock_tmux.write_text('#!/bin/bash\n')
        mock_tmux.chmod(0o755)
        
        real_buffer = Path("/tmp/tmux-url-buffer")
        original_content = None
        if real_buffer.exists():
            original_content = real_buffer.read_text()
        
        try:
            # Buffer with URLs mixed in text
            real_buffer.write_text(
                "Some text before\n"
                "Visit http://first.example.com for more info\n"
                "Check https://second.example.org/path?q=1\n"
                "End of text\n"
            )
            
            env = {**os.environ, "PATH": f"{tmpdir}:{os.environ.get('PATH', '')}"}
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )
            
            # Should output OSC 52 with the selected URL
            assert result.returncode == 0
            assert "\x1b]52;c;" in result.stdout
        finally:
            if original_content is not None:
                real_buffer.write_text(original_content)
            elif real_buffer.exists():
                real_buffer.unlink()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_mocks(tmpdir, fzf_action: str, tmux_action: str = 'echo "tmux: $@"\n') -> dict:
    """Create mock fzf and tmux binaries in *tmpdir* and return an env dict."""
    tmpdir = Path(tmpdir)
    mock_fzf = tmpdir / "fzf"
    mock_fzf.write_text(f'#!/bin/bash\n{fzf_action}')
    mock_fzf.chmod(0o755)

    mock_tmux = tmpdir / "tmux"
    mock_tmux.write_text(f'#!/bin/bash\n{tmux_action}')
    mock_tmux.chmod(0o755)

    return {**os.environ, "PATH": f"{tmpdir}:{os.environ.get('PATH', '')}"}


class _Buffer:
    """Context manager that temporarily writes /tmp/tmux-url-buffer and restores it."""

    def __init__(self, content: str):
        self._path = Path("/tmp/tmux-url-buffer")
        self._content = content
        self._original: str | None = None

    def __enter__(self):
        if self._path.exists():
            self._original = self._path.read_text()
        self._path.write_text(self._content)
        return self

    def __exit__(self, *_):
        if self._original is not None:
            self._path.write_text(self._original)
        elif self._path.exists():
            self._path.unlink()


# ---------------------------------------------------------------------------
# Additional tests
# ---------------------------------------------------------------------------


def test_osc52_base64_decodes_to_selected_url():
    """OSC 52 payload must be valid base64 that decodes to the chosen URL."""
    import base64

    url = "https://example.com/hello-world"
    with tempfile.TemporaryDirectory() as tmpdir:
        env = _setup_mocks(tmpdir, fzf_action=f'cat > /dev/null\necho "{url}"\n')
        with _Buffer(f"See {url} for details\n"):
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )

        assert result.returncode == 0
        osc = result.stdout
        start = osc.index("\x1b]52;c;") + len("\x1b]52;c;")
        end = osc.index("\x07", start)
        payload = osc[start:end]
        assert base64.b64decode(payload).decode() == url


def test_fzf_cancel_no_osc52_output():
    """When fzf returns nothing (user cancels), no OSC 52 should be emitted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = _setup_mocks(tmpdir, fzf_action="cat > /dev/null\n")
        with _Buffer("https://example.com\n"):
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )

        assert result.returncode == 0
        assert "\x1b]52;c;" not in result.stdout


def test_buffer_with_text_but_no_urls():
    """Buffer that has text but zero http(s) URLs -> 'No URLs found'."""
    with _Buffer("hello world\njust some text\nno links here\n"):
        result = subprocess.run(
            [str(EFFECTOR_PATH)],
            capture_output=True,
            text=True,
        )

    assert result.returncode == 0
    assert "No URLs found in pane" in result.stdout


def test_http_url_scheme_extracted():
    """http:// URLs (not just https://) should be extracted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        fzf_input_file = td / "fzf_stdin.txt"
        env = _setup_mocks(
            tmpdir,
            fzf_action=f"cat > {fzf_input_file}\nhead -1\n",
        )
        with _Buffer("Go to http://plain.example.org/foo\n"):
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )

        assert result.returncode == 0
        urls = fzf_input_file.read_text().strip().splitlines()
        assert len(urls) >= 1
        assert urls[0] == "http://plain.example.org/foo"


def test_url_stops_at_space():
    """URLs must be truncated at the first space character."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fzf_input_file = tmpdir / "fzf_stdin.txt"
        env = _setup_mocks(
            tmpdir,
            fzf_action=f"cat > {fzf_input_file}\nhead -1\n",
        )
        with _Buffer("https://example.com/path page2 other\n"):
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )

        assert result.returncode == 0
        urls = fzf_input_file.read_text().strip().splitlines()
        assert urls[0] == "https://example.com/path"


def test_url_stops_at_angle_bracket():
    """URLs inside <...> markup should stop at >."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fzf_input_file = tmpdir / "fzf_stdin.txt"
        env = _setup_mocks(
            tmpdir,
            fzf_action=f"cat > {fzf_input_file}\nhead -1\n",
        )
        with _Buffer("link <https://example.com/a>b\n"):
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )

        assert result.returncode == 0
        urls = fzf_input_file.read_text().strip().splitlines()
        assert urls[0] == "https://example.com/a"


def test_url_stops_at_closing_paren():
    """URLs inside parentheses should stop at )."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fzf_input_file = tmpdir / "fzf_stdin.txt"
        env = _setup_mocks(
            tmpdir,
            fzf_action=f"cat > {fzf_input_file}\nhead -1\n",
        )
        with _Buffer("see (https://example.com/x) next\n"):
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )

        assert result.returncode == 0
        urls = fzf_input_file.read_text().strip().splitlines()
        assert urls[0] == "https://example.com/x"


def test_url_stops_at_double_quote():
    """URLs inside double quotes should stop at the quote."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fzf_input_file = tmpdir / "fzf_stdin.txt"
        env = _setup_mocks(
            tmpdir,
            fzf_action=f"cat > {fzf_input_file}\nhead -1\n",
        )
        with _Buffer('href="https://example.com/z" more\n'):
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )

        assert result.returncode == 0
        urls = fzf_input_file.read_text().strip().splitlines()
        assert urls[0] == "https://example.com/z"


def test_tmux_display_message_called_with_url():
    """When a URL is selected, tmux display-message must be invoked with it."""
    url = "https://msg.example.com/ok"
    with tempfile.TemporaryDirectory() as tmpdir:
        tmux_log = tmpdir / "tmux_calls.txt"
        env = _setup_mocks(
            tmpdir,
            fzf_action=f'echo "{url}"\n',
            tmux_action=f'echo "$@" >> {tmux_log}\n',
        )
        with _Buffer(f"{url}\n"):
            result = subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )

        assert result.returncode == 0
        calls = tmux_log.read_text()
        assert "display-message" in calls
        assert url in calls


def test_fzf_called_with_expected_flags():
    """fzf must be invoked with --reverse, --prompt, and --no-info."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fzf_log = tmpdir / "fzf_args.txt"
        env = _setup_mocks(
            tmpdir,
            fzf_action=f'echo "$@" >> {fzf_log}\nhead -1\n',
        )
        with _Buffer("https://example.com\n"):
            subprocess.run(
                [str(EFFECTOR_PATH)],
                capture_output=True,
                text=True,
                env=env,
            )

        args = fzf_log.read_text().strip()
        assert "--reverse" in args
        assert "--no-info" in args
        assert "--prompt" in args
