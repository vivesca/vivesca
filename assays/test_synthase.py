#!/usr/bin/env python3
"""Tests for synthase effector."""

import sys
import os
from importlib.machinery import SourceFileLoader
import pytest
import subprocess
from unittest.mock import patch, mock_open

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

synthase_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'effectors', 'synthase'))
synthase = SourceFileLoader("synthase", synthase_path).load_module()

def test_load_config_exists():
    """Test _load_config when config exists."""
    mock_yaml = """
llm:
  default_model: "sonnet"
"""
    with patch("builtins.open", mock_open(read_data=mock_yaml)):
        with patch("yaml.safe_load", return_value={"llm": {"default_model": "sonnet"}}):
            cfg = synthase._load_config()
            assert cfg == {"default_model": "sonnet"}

def test_load_config_not_found():
    """Test _load_config when config not found."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        cfg = synthase._load_config()
        assert cfg == {}

def test_backend_channel_success(monkeypatch):
    """Test _backend_channel with successful execution."""
    def mock_run(args, **kwargs):
        return subprocess.CompletedProcess(
            args=[], returncode=0, stdout="test output", stderr=""
        )
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    monkeypatch.setattr(synthase, "_which", lambda _: "/usr/bin/channel")
    
    result = synthase._backend_channel("test prompt", "haiku", 60)
    assert result == "test output"

def test_backend_channel_error(monkeypatch):
    """Test _backend_channel when channel returns empty output."""
    def mock_run(args, **kwargs):
        return subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="something went wrong"
        )
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    monkeypatch.setattr(synthase, "_which", lambda _: "/usr/bin/channel")
    
    with pytest.raises(RuntimeError, match="channel error: something went wrong"):
        synthase._backend_channel("test prompt", "haiku", 60)

def test_backend_channel_not_found(monkeypatch):
    """Test _backend_channel when channel not found."""
    monkeypatch.setattr(synthase, "_which", lambda _: None)
    
    with pytest.raises(RuntimeError, match="channel not found on PATH"):
        synthase._backend_channel("test prompt", "haiku", 60)

def test_which_found(monkeypatch):
    """Test _which finds executable."""
    import shutil
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/test")
    result = synthase._which("test")
    assert result == "/usr/bin/test"
