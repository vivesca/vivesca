#!/usr/bin/env python3
"""Tests for pharos-sync.sh effector."""

import subprocess
import os
import tempfile
from pathlib import Path


EFFECTOR_PATH = Path(__file__).parent.parent / "effectors" / "pharos-sync.sh"


def test_script_is_executable():
    """Test that pharos-sync.sh is executable."""
    assert EFFECTOR_PATH.exists()
    assert os.access(EFFECTOR_PATH, os.X_OK)


def test_help_flag():
    """Test that --help prints usage and exits cleanly."""
    result = subprocess.run(
        [str(EFFECTOR_PATH), "--help"],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "Sync Claude config" in result.stdout
    assert "pharos-sync.sh" in result.stdout


def test_bash_syntax_is_valid():
    """Test that the bash script has no syntax errors."""
    result = subprocess.run(
        ["bash", "-n", str(EFFECTOR_PATH)],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 0
    assert result.stderr == ""


def test_sync_function_works_correctly():
    """Test the sync_file function behaves correctly."""
    # Create a test bash snippet that sources the script and tests sync_file
    test_script = f"""
source {EFFECTOR_PATH}

# Create temp dir
test_dir=$(mktemp -d)
src1="$test_dir/src1"
dst1="$test_dir/dst1"
echo "hello" > "$src1"

# Test syncing new file
sync_file "$src1" "$dst1"
ret=$?
if [ $ret -ne 0 ]; then
    echo "Failed: sync new file should return 0"
    exit 1
fi
if ! diff -q "$src1" "$dst1"; then
    echo "Failed: files don't match after sync"
    exit 1
fi

# Test syncing unchanged file
sync_file "$src1" "$dst1"
ret=$?
if [ $ret -ne 1 ]; then
    echo "Failed: unchanged file should return 1"
    exit 1
fi

# Test sync when source doesn't exist
sync_file "$test_dir/nonexistent" "$test_dir/dst2"
ret=$?
if [ $ret -ne 1 ]; then
    echo "Failed: nonexistent source should return 1"
    exit 1
fi

# Test sync updates changed file
echo "world" > "$src1"
sync_file "$src1" "$dst1"
ret=$?
if [ $ret -ne 0 ]; then
    echo "Failed: changed file should return 0"
    exit 1
fi
if ! diff -q "$src1" "$dst1"; then
    echo "Failed: files don't match after update"
    exit 1
fi

echo "All sync_file tests passed"
exit 0
"""
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        check=False
    )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0
    assert "All sync_file tests passed" in result.stdout


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
