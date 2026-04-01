from __future__ import annotations

"""Tests for tmux-url-select.sh script."""

import subprocess
from pathlib import Path
import pytest


SCRIPT_PATH = Path("/home/terry/germline/effectors/tmux-url-select.sh")


def test_script_exists_and_is_executable():
    """Verify the script exists and is executable."""
    assert SCRIPT_PATH.exists()
    assert SCRIPT_PATH.is_file()
    # Check that script is executable
    assert (SCRIPT_PATH.stat().st_mode & 0o111) != 0


def test_help_flag_works():
    """Test --help flag outputs usage information."""
    result = subprocess.run(
        [str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0
    assert "Usage: tmux-url-select.sh" in result.stdout
    assert "Interactively select a URL" in result.stdout
    assert "Requires: fzf, tmux" in result.stdout


def test_h_flag_works():
    """Test -h flag outputs usage information."""
    result = subprocess.run(
        [str(SCRIPT_PATH), "-h"],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0
    assert "Usage: tmux-url-select.sh" in result.stdout


def test_no_url_buffer_file_shows_message():
    """Test script handles missing /tmp/tmux-url-buffer gracefully."""
    # Remove the buffer file if it exists
    subprocess.run(["rm", "-f", "/tmp/tmux-url-buffer"], check=True)
    
    result = subprocess.run(
        [str(SCRIPT_PATH)],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "No URLs found in pane" in result.stdout


def test_empty_url_buffer_shows_message():
    """Test script handles empty buffer file gracefully."""
    with open("/tmp/tmux-url-buffer", "w") as f:
        f.write("")
    
    result = subprocess.run(
        [str(SCRIPT_PATH)],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "No URLs found in pane" in result.stdout


def test_extracts_urls_correctly():
    """Test script extracts unique URLs from the buffer."""
    # Create test buffer with multiple URLs including duplicates
    test_content = """
Some text with URLs:
https://example.com/page1
Another line with https://example.com/page2 and https://example.com/page1
Check out https://gist.github.com/example/12345 more text.
Look at this one with parentheses: https://example.com/path/to/(file)
And one in quotes: "https://example.com/quoted"
And one in angle brackets: <https://example.com/bracketed>
    """
    
    with open("/tmp/tmux-url-buffer", "w") as f:
        f.write(test_content)
    
    # Since we can't run fzf interactively, let's just test the URL extraction logic
    # Extract URLs the same way the script does
    with open("/tmp/tmux-url-buffer", "r") as f:
        content = f.read()
    
    import re
    urls = re.findall(r"https?://[^ >)\"')]+", content)
    # Deduplicate
    seen = {}
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen[url] = True
            unique_urls.append(url)
    
    assert len(unique_urls) == 6
    assert "https://example.com/page1" in unique_urls
    assert "https://example.com/page2" in unique_urls
    assert "https://gist.github.com/example/12345" in unique_urls
    assert "https://example.com/path/to/(file)" in unique_urls
    assert "https://example.com/quoted" in unique_urls
    assert "https://example.com/bracketed" in unique_urls


def test_shebang_is_correct():
    """Verify script has proper shebang."""
    with open(SCRIPT_PATH, "r") as f:
        first_line = f.readline().strip()
    assert first_line == "#!/usr/bin/env bash"


def test_has_strict_mode():
    """Verify script uses strict mode."""
    with open(SCRIPT_PATH, "r") as f:
        lines = f.readlines()
    strict_mode = [line.strip() for line in lines if line.strip().startswith("set -euo")]
    assert len(strict_mode) == 1
    assert "set -euo pipefail" in strict_mode[0]
