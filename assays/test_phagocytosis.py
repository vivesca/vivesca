#!/usr/bin/env python3
"""Tests for phagocytosis.py — Obsidian lastOpenFiles logging tests."""

import pytest
import json
import io
from unittest.mock import patch, mock_open
from pathlib import Path

# Execute the phagocytosis file directly
phago_path = Path("/home/terry/germline/effectors/phagocytosis.py")
phago_code = phago_path.read_text()
namespace = {}
exec(phago_code, namespace)

# Extract all the functions/globals from the namespace
phagocytosis = type('phago_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(phagocytosis, key, value)

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

def test_paths_resolved():
    """Test all paths are correctly constructed."""
    assert str(phagocytosis.CHROMATIN).endswith("epigenome/chromatin")
    assert phagocytosis.WORKSPACE == phagocytosis.CHROMATIN / ".obsidian" / "workspace.json"
    assert phagocytosis.LOG_FILE == phagocytosis.CHROMATIN / ".consumption-log.jsonl"

# ---------------------------------------------------------------------------
# Test read_last_open_files
# ---------------------------------------------------------------------------

def test_read_last_open_files_extracts_correctly():
    """Test reads and extracts lastOpenFiles from workspace."""
    workspace_data = {
        "lastOpenFiles": [
            "/note1.md",
            "/note2.md",
            "/note3.md"
        ]
    }
    mock_text = json.dumps(workspace_data)
    
    with patch('pathlib.Path.read_text', return_value=mock_text):
        result = phagocytosis.read_last_open_files()
        assert len(result) == 3
        assert result[0] == "/note1.md"

def test_read_last_open_files_handles_empty():
    """Test when no lastOpenFiles key, returns empty list."""
    workspace_data = {}
    mock_text = json.dumps(workspace_data)
    
    with patch('pathlib.Path.read_text', return_value=mock_text):
        result = phagocytosis.read_last_open_files()
        assert result == []

# ---------------------------------------------------------------------------
# Test read_last_snapshot
# ---------------------------------------------------------------------------

def test_read_last_snapshot_returns_none_when_no_file():
    """Test returns None when log file doesn't exist."""
    with patch('pathlib.Path.exists', return_value=False):
        result = phagocytosis.read_last_snapshot()
        assert result is None

def test_read_last_snapshot_returns_none_when_empty():
    """Test returns None when log file is empty."""
    def mock_exists(self):
        if self == phagocytosis.LOG_FILE:
            return True
        return False

    mock_file = io.BytesIO()

    def mock_open(self, *args, **kwargs):
        if self == phagocytosis.LOG_FILE:
            return mock_file
        raise FileNotFoundError(f"{self} not found")

    with patch('pathlib.Path.exists', mock_exists):
        with patch('pathlib.Path.open', mock_open):
            result = phagocytosis.read_last_snapshot()
            assert result is None

def test_read_last_snapshot_reads_last_line():
    """Test correctly reads the last line from log file."""
    entry1 = json.dumps({"ts": 1234567890, "files": ["a.md", "b.md"]})
    entry2 = json.dumps({"ts": 1234567891, "files": ["b.md", "c.md"]})
    content = f"{entry1}\n{entry2}\n".encode('utf-8')

    mock_io = io.BytesIO(content)

    def mock_exists(self):
        if self == phagocytosis.LOG_FILE:
            return True
        return False

    def mock_open(self, *args, **kwargs):
        if self == phagocytosis.LOG_FILE:
            return mock_io
        raise FileNotFoundError(f"{self} not found")

    with patch('pathlib.Path.exists', mock_exists):
        with patch('pathlib.Path.open', mock_open):
            result = phagocytosis.read_last_snapshot()
            assert result == ["b.md", "c.md"]

# ---------------------------------------------------------------------------
# Test main function
# ---------------------------------------------------------------------------

def test_main_exits_if_workspace_missing():
    """Test main returns early when workspace file doesn't exist."""
    with patch('pathlib.Path.exists', return_value=False):
        # Should not throw
        phagocytosis.main()

def test_main_exits_if_no_current_files():
    """Test main returns early when empty file list."""
    def mock_exists(self):
        return str(self) == str(phagocytosis.WORKSPACE)
    
    with patch('pathlib.Path.exists', mock_exists):
        with patch('pathlib.Path.read_text', return_value='{"lastOpenFiles": []}'):
            # Should not throw
            phagocytosis.main()

def test_main_skips_if_same_as_last():
    """Test skips writing when files haven't changed."""
    file_list = ["/a.md", "/b.md"]

    # Track if open is called to ensure it isn't
    open_called = False

    def mock_open(self, *args, **kwargs):
        nonlocal open_called
        open_called = True
        raise FileNotFoundError(f"Should not open when skipping")

    def mock_exists(self):
        # Both workspace and log file exist
        return str(self) in (str(phagocytosis.WORKSPACE), str(phagocytosis.LOG_FILE))

    with patch('pathlib.Path.exists', mock_exists):
        with patch('pathlib.Path.read_text', return_value=json.dumps({"lastOpenFiles": file_list})):
            with patch.object(phagocytosis, 'read_last_snapshot', return_value=file_list):
                with patch('pathlib.Path.open', mock_open):
                    # Should exit early without writing
                    phagocytosis.main()
                    assert open_called is False, "Should not open file when no change"

def test_main_writes_entry_when_changed():
    """Test writes new entry when files changed."""
    last_files = ["/a.md", "/b.md"]
    current_files = ["/b.md", "/c.md"]

    written_content = []

    class MockFile:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def write(self, data): written_content.append(data)

    mock_file = MockFile()

    def mock_open(self, *args, **kwargs):
        if self == phagocytosis.LOG_FILE:
            return mock_file
        raise FileNotFoundError(f"{self} not found")

    def mock_exists(self):
        return str(self) in (str(phagocytosis.WORKSPACE), str(phagocytosis.LOG_FILE))

    with patch('pathlib.Path.exists', mock_exists):
        with patch('pathlib.Path.read_text', return_value=json.dumps({"lastOpenFiles": current_files})):
            with patch.object(phagocytosis, 'read_last_snapshot', return_value=last_files):
                with patch('pathlib.Path.open', mock_open):
                    with patch('time.time', return_value=1234567890.0):
                        phagocytosis.main()
                        # Should write new entry
                        assert len(written_content) == 1
                        written = written_content[0].strip()
                        # Should be valid JSON
                        data = json.loads(written.strip())
                        assert data['ts'] == 1234567890
                        assert data['files'] == current_files
