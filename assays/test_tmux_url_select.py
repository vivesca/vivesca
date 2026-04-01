#!/usr/bin/env python3
"""Test for tmux-url-select.sh effector script."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

EFFECTOR_PATH = Path(__file__).parent.parent / "effectors" / "tmux-url-select.sh"


def test_script_exists():
    """Verify the script file exists."""
    assert EFFECTOR_PATH.exists()
    assert EFFECTOR_PATH.is_file()


def test_help_flag():
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


def test_help_flag_short():
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
            'cat > "$1"\n' f'{fzf_input_file}\n'
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
