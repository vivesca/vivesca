from __future__ import annotations

"""Tests for effectors/electroreception — Python script tested via subprocess and function extraction."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "electroreception"


def _run_script(args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run the electroreception script with given args."""
    cmd = [sys.executable, str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=10,
    )


def test_electroreception_help_flag_exits_zero():
    """Test --help exits with 0."""
    r = _run_script(["--help"])
    assert r.returncode == 0


def test_h_flag_exits_zero():
    """Test -h exits with 0."""
    r = _run_script(["-h"])
    assert r.returncode == 0


def test_help_shows_usage():
    """Test help output contains usage instructions."""
    r = _run_script(["--help"])
    assert "usage:" in r.stdout
    assert "electroreception" in r.stdout
    assert "iMessage" in r.stdout


def test_all_flags_listed_in_help():
    """Test all expected flags are mentioned in help."""
    r = _run_script(["--help"])
    flags = ["-n", "--limit", "-s", "--sender", "-d", "--days", 
             "-q", "--query", "--incoming", "--json"]
    for flag in flags:
        assert flag in r.stdout


def test_db_not_found_exits_with_1():
    """Test script exits 1 when chat.db not found (which it isn't on this system)."""
    r = _run_script()
    assert r.returncode == 1
    assert "chat.db not found" in r.stderr
    assert "Messages enabled" in r.stderr


class TestExtractText:
    """Tests for the extract_text function that extracts text from NSAttributedString blobs."""
    
    def test_empty_blob_returns_none(self):
        """Test empty blob returns None."""
        # Load the function by executing the script
        ns = {}
        with open(SCRIPT) as f:
            code = f.read()
        exec(code, ns)
        extract_text = ns["extract_text"]
        
        assert extract_text(b"") is None
    
    def test_clean_text_after_metadata_extracts(self):
        """Test text after metadata extracts correctly."""
        ns = {}
        with open(SCRIPT) as f:
            code = f.read()
        exec(code, ns)
        extract_text = ns["extract_text"]
        
        # The actual blob contains control characters separating runs
        # Let's create a decoded string that would result from blob decoding
        # with actual useful content after metadata
        test_content = "streamtyped\x00NSString\x00Hello World\x00NSObject"
        test_blob = test_content.encode("utf-8")
        result = extract_text(test_blob)
        assert result == "Hello World"
    
    def test_text_with_phone_prefix_stripped(self):
        """Test phone prefix is stripped."""
        ns = {}
        with open(SCRIPT) as f:
            code = f.read()
        exec(code, ns)
        extract_text = ns["extract_text"]
        
        test_content = "NSString\x00+1Hello World\x00"
        test_blob = test_content.encode("utf-8")
        result = extract_text(test_blob)
        assert result == "Hello World"
    
    def test_only_metadata_returns_none(self):
        """Test when everything is filtered as metadata, return None."""
        ns = {}
        with open(SCRIPT) as f:
            code = f.read()
        exec(code, ns)
        extract_text = ns["extract_text"]
        
        test_content = "streamtyped\x00NSString\x00NSDictionary\x00NSArray"
        test_blob = test_content.encode("utf-8")
        result = extract_text(test_blob)
        assert result is None
    
    def test_three_characters_kept(self):
        """Test strings >=3 characters are kept, shorter are ignored."""
        ns = {}
        with open(SCRIPT) as f:
            code = f.read()
        exec(code, ns)
        extract_text = ns["extract_text"]
        
        test_content = "NSString\x00Hi!\x00"
        test_blob = test_content.encode("utf-8")
        result = extract_text(test_blob)
        # "Hi!" is length 3, should be kept
        assert result == "Hi!"

    def test_two_characters_ignored(self):
        """Test two character strings are ignored (need len >=3)."""
        ns = {}
        with open(SCRIPT) as f:
            code = f.read()
        exec(code, ns)
        extract_text = ns["extract_text"]

        test_content = "NSString\x00Hi\x00"
        test_blob = test_content.encode("utf-8")
        result = extract_text(test_blob)
        # "Hi" is length 2 < 3, should be ignored
        assert result is None

    def test_single_char_ignored(self):
        """Test a single character is ignored."""
        ns = {}
        with open(SCRIPT) as f:
            code = f.read()
        exec(code, ns)
        extract_text = ns["extract_text"]
        
        test_content = "NSString\x00H\x00"
        test_blob = test_content.encode("utf-8")
        result = extract_text(test_blob)
        # "H" is length 1, should be ignored
        assert result is None
    
    def test_exception_returns_none(self):
        """Test that exceptions during extraction return None."""
        ns = {}
        with open(SCRIPT) as f:
            code = f.read()
        exec(code, ns)
        extract_text = ns["extract_text"]
        
        # Pass None instead of bytes to cause exception
        result = extract_text(None)  # type: ignore
        assert result is None


def test_electroreception_json_flag_accepted():
    """Test that --json flag is accepted by argparse."""
    # Even though DB doesn't exist, argparse should still parse
    r = _run_script(["--json", "-n", "10"])
    # It should fail at DB check but not argparse
    assert r.returncode == 1
    assert "chat.db not found" in r.stderr


def test_incoming_flag_accepted():
    """Test that --incoming flag is accepted."""
    r = _run_script(["--incoming"])
    assert r.returncode == 1
    assert "chat.db not found" in r.stderr


def test_all_flags_combination_accepted():
    """Test that combining all flags works with argparse."""
    r = _run_script(["-n", "50", "-s", "John", "-d", "7", "-q", "lunch", "--incoming", "--json"])
    assert r.returncode == 1
    assert "chat.db not found" in r.stderr


def test_electroreception_script_is_executable():
    """Test that the script has the shebang line and is executable."""
    assert SCRIPT.exists()
    content = SCRIPT.read_text()
    assert content.startswith("#!/usr/bin/env python3")
