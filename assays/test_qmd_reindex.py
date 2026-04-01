#!/usr/bin/env python3
"""Test for qmd-reindex.sh effector script"""

import subprocess
import pytest
from pathlib import Path


def test_script_exists_and_is_executable():
    """Test that the script exists and has executable permissions"""
    script_path = Path(__file__).parent.parent / "effectors" / "qmd-reindex.sh"
    assert script_path.exists()
    assert script_path.is_file()
    
    # Check executable bit
    assert (script_path.stat().st_mode & 0o111) != 0, "Script should be executable"


def test_help_flag_works():
    """Test that --help outputs usage information"""
    script_path = Path(__file__).parent.parent / "effectors" / "qmd-reindex.sh"
    result = subprocess.run(
        [str(script_path), "--help"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "Re-index vault notes" in result.stdout
    assert "qmd update && qmd embed" in result.stdout


def test_help_flag_short_works():
    """Test that -h outputs usage information"""
    script_path = Path(__file__).parent.parent / "effectors" / "qmd-reindex.sh"
    result = subprocess.run(
        [str(script_path), "-h"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "Usage:" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
