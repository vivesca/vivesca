#!/usr/bin/env python3
"""Tests for search-guard effector."""

import sys
import os
import subprocess
from importlib.machinery import SourceFileLoader
import pytest
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import search-guard (no .py extension)
sg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'effectors', 'search-guard'))
search_guard = SourceFileLoader("search_guard", sg_path).load_module()

def test_blocks_root_search(capsys, monkeypatch):
    """Test search-guard blocks search on root directory."""
    monkeypatch.setattr(sys, "argv", ["rg", "pattern", "/"])
    monkeypatch.setattr(os, "basename", lambda _: "rg")
    monkeypatch.setattr(os, "expanduser", lambda x: x)
    monkeypatch.setattr(os, "abspath", lambda _: "/")
    
    with pytest.raises(SystemExit):
        search_guard.main()
    
    captured = capsys.readouterr()
    assert "SEARCH BLOCKED" in captured.out
    assert "Broad search on '/' is prohibited" in captured.out

def test_blocks_massive_directory(capsys, monkeypatch):
    """Test search-guard blocks search on massive directories."""
    monkeypatch.setattr(sys, "argv", ["rg", "pattern", "/Users/terry/Library"])
    monkeypatch.setattr(os, "basename", lambda _: "rg")
    monkeypatch.setattr(os, "expanduser", lambda x: x)
    monkeypatch.setattr(os, "abspath", lambda _: "/Users/terry/Library")
    
    with pytest.raises(SystemExit):
        search_guard.main()
    
    captured = capsys.readouterr()
    assert "SEARCH BLOCKED" in captured.out
    assert "too large" in captured.out

def test_allows_stdin_search_no_path(monkeypatch):
    """Test search-guard allows search when no path is provided (stdin)."""
    monkeypatch.setattr(sys, "argv", ["grep", "pattern"])
    monkeypatch.setattr(os, "basename", lambda _: "grep")
    
    called = False
    def mock_execv(path, args):
        nonlocal called
        called = True
        assert path == "/usr/bin/grep"
        raise SystemExit # Don't actually execute
    
    monkeypatch.setattr(os, "execv", mock_execv)
    
    try:
        search_guard.main()
    except SystemExit:
        pass
    
    assert called is True

def test_finds_rg_fallback(monkeypatch):
    """Test search-guard finds rg in alternative location."""
    monkeypatch.setattr(sys, "argv", ["rg", "pattern", "./test"])
    monkeypatch.setattr(os, "basename", lambda _: "rg")
    
    def mock_expanduser(x):
        return "/home/terry/germline/test"
    
    monkeypatch.setattr(os, "expanduser", mock_expanduser)
    monkeypatch.setattr(os, "abspath", lambda _: "/home/terry/germline/test")
    monkeypatch.setattr(os, "exists", lambda _: False)
    
    def mock_check_output(cmd, **kwargs):
        return b"/opt/homebrew/bin/rg\n"
    
    monkeypatch.setattr(subprocess, "check_output", mock_check_output)
    
    called_path = None
    def mock_execv(path, args):
        nonlocal called_path
        called_path = path
        raise SystemExit
    
    monkeypatch.setattr(os, "execv", mock_execv)
    
    try:
        search_guard.main()
    except SystemExit:
        pass
    
    assert "opt/homebrew/bin/rg" in called_path

def test_executes_allowed_search(monkeypatch):
    """Test search-guard executes search for allowed paths."""
    monkeypatch.setattr(sys, "argv", ["rg", "test", "~/germline"])
    monkeypatch.setattr(os, "basename", lambda _: "rg")
    
    def mock_expanduser(x):
        return "/Users/terry/germline"
    
    monkeypatch.setattr(os, "expanduser", mock_expanduser)
    monkeypatch.setattr(os, "abspath", lambda _: "/Users/terry/germline")
    
    called = False
    def mock_execv(path, args):
        nonlocal called
        called = True
        raise SystemExit
    
    monkeypatch.setattr(os, "execv", mock_execv)
    
    try:
        search_guard.main()
    except SystemExit:
        pass
    
    assert called is True
