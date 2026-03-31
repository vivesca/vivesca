#!/usr/bin/env python3
"""Tests for safe_search effector."""

import sys
import os
import pytest
import subprocess
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import effectors.safe_search as safe_search

def test_safe_search_blocks_root(capsys, monkeypatch):
    """Test safe_search blocks search on root directory."""
    monkeypatch.setattr(sys, "argv", ["safe_search.py", "pattern", "/"])
    monkeypatch.setattr(os.path, "abspath", lambda x: x)
    
    with pytest.raises(SystemExit):
        safe_search.main()
    
    captured = capsys.readouterr()
    assert "PROHIBITED" in captured.out

def test_safe_search_blocks_massive_directory(capsys, monkeypatch):
    """Test safe_search blocks search on massive directories."""
    monkeypatch.setattr(sys, "argv", ["safe_search.py", "pattern", "/Users/terry/Library"])
    monkeypatch.setattr(os.path, "abspath", lambda x: x)
    
    with pytest.raises(SystemExit):
        safe_search.main()
    
    captured = capsys.readouterr()
    assert "too large for broad search" in captured.out

def test_safe_search_allows_valid_path(monkeypatch):
    """Test safe_search executes search for valid path."""
    monkeypatch.setattr(sys, "argv", ["safe_search.py", "pattern", "~/germline"])
    
    def mock_expanduser(x):
        return "/Users/terry/germline"
    
    monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
    monkeypatch.setattr(os.path, "abspath", lambda _: "/Users/terry/germline")
    
    called = False
    def mock_run(cmd, **kwargs):
        nonlocal called
        called = True
        assert "rg" in cmd[0]
        assert "pattern" in cmd
        assert "/Users/terry/germline" in cmd
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    safe_search.main()
    assert called is True

def test_safe_search_fallback_to_grep(monkeypatch):
    """Test safe_search falls back to grep when rg not found."""
    monkeypatch.setattr(sys, "argv", ["safe_search.py", "pattern", "~/germline"])
    
    def mock_expanduser(x):
        return "/Users/terry/germline"
    
    monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
    monkeypatch.setattr(os.path, "abspath", lambda _: "/Users/terry/germline")
    
    called_rg = False
    called_grep = False
    def mock_run(cmd, **kwargs):
        nonlocal called_rg, called_grep
        if not called_rg:
            called_rg = True
            raise FileNotFoundError
        else:
            called_grep = True
            assert cmd[0] == "grep"
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    safe_search.main()
    assert called_rg is True
    assert called_grep is True

def test_safe_search_timeout(capsys, monkeypatch):
    """Test safe_search handles timeout correctly."""
    monkeypatch.setattr(sys, "argv", ["safe_search.py", "pattern", "~/germline"])
    
    def mock_expanduser(x):
        return "/Users/terry/germline"
    
    monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
    monkeypatch.setattr(os.path, "abspath", lambda _: "/Users/terry/germline")
    
    def mock_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(15, None)
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    with pytest.raises(SystemExit):
        safe_search.main()
    
    captured = capsys.readouterr()
    assert "timed out after 15s" in captured.out
