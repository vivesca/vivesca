#!/usr/bin/env python3
"""Tests for rg (search-guard alias)."""

import sys
import os
from importlib.machinery import SourceFileLoader
import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Get the actual search-guard path from symlink
rg_full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'effectors', 'rg'))
assert os.path.islink(rg_full_path)
target = os.readlink(rg_full_path)
sg_full_path = os.path.join(os.path.dirname(rg_full_path), target)
search_guard = SourceFileLoader("search_guard", sg_full_path).load_module()

def test_rg_is_search_guard():
    """Test rg is symlink to search-guard and behaves same way."""
    assert target == "search-guard"

def test_rg_blocks_root(capsys, monkeypatch):
    """Test rg blocks root search same as search-guard."""
    monkeypatch.setattr(sys, "argv", ["rg", "pattern", "/"])
    
    monkeypatch.setattr(os.path, "abspath", lambda _: "/")
    monkeypatch.setattr(os.path, "expanduser", lambda x: x)
    
    with pytest.raises(SystemExit):
        search_guard.main()
    
    captured = capsys.readouterr()
    assert "SEARCH BLOCKED" in captured.out

def test_rg_allows_valid_path(monkeypatch):
    """Test rg allows search on valid paths."""
    monkeypatch.setattr(sys, "argv", ["rg", "pattern", "~/germline"])
    
    called = False
    def mock_execv(path, args):
        nonlocal called
        called = True
        raise SystemExit
    
    monkeypatch.setattr(os, "execv", mock_execv)
    
    def mock_expanduser(x):
        return "/Users/terry/germline"
    
    monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
    monkeypatch.setattr(os.path, "abspath", lambda _: "/Users/terry/germline")
    
    try:
        search_guard.main()
    except SystemExit:
        pass
    
    assert called is True
