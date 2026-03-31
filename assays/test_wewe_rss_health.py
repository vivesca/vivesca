#!/usr/bin/env python3
"""Tests for wewe-rss-health effector."""

import sys
import os
from importlib.machinery import SourceFileLoader
import json
from unittest.mock import MagicMock
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import despite hyphen in name
wewe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'effectors', 'wewe-rss-health.py'))
wewe = SourceFileLoader("wewe_rss_health", wewe_path).load_module()

def test_load_state_exists(monkeypatch):
    """Test load_state when state file exists."""
    mock_data = json.dumps({"last_status": "failing"})
    state_file_mock = MagicMock()
    state_file_mock.exists.return_value = True
    state_file_mock.read_text.return_value = mock_data
    
    monkeypatch.setattr(wewe, "STATE_FILE", state_file_mock)
    
    state = wewe.load_state()
    assert state == {"last_status": "failing"}

def test_load_state_not_exists(monkeypatch):
    """Test load_state when state file does not exist."""
    state_file_mock = MagicMock()
    state_file_mock.exists.return_value = False
    
    monkeypatch.setattr(wewe, "STATE_FILE", state_file_mock)
    
    state = wewe.load_state()
    assert state == {"last_status": "ok"}

def test_save_state(monkeypatch):
    """Test save_state writes correctly."""
    state_file_mock = MagicMock()
    monkeypatch.setattr(wewe, "STATE_FILE", state_file_mock)
    
    wewe.save_state({"last_status": "ok"})
    state_file_mock.write_text.assert_called_with('{"last_status": "ok"}')

def test_check_service_success(monkeypatch):
    """Test check_service when everything is healthy."""
    mock_response = b'{"err": null, "data": [{"paused": false}, {"paused": false}]}'
    
    mock_urlopen = MagicMock()
    mock_urlopen.read.return_value = mock_response
    
    def mock_urlopen_func(req):
        return mock_urlopen
    
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_func)
    
    healthy, detail = wewe.check_service()
    
    assert healthy is True
    assert "2 feed(s) active" in detail

def test_check_service_api_unreachable(monkeypatch):
    """Test check_service when API is unreachable."""
    def mock_urlopen(req, **kwargs):
        raise Exception("Connection refused")
    
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)
    
    healthy, detail = wewe.check_service()
    
    assert healthy is False
    assert "API unreachable: Connection refused" in detail

def test_check_service_api_error(monkeypatch):
    """Test check_service when API returns error."""
    mock_response = b'{"err": "invalid key", "data": []}'
    
    mock_urlopen = MagicMock()
    mock_urlopen.read.return_value = mock_response
    
    def mock_urlopen_func(req):
        return mock_urlopen
    
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_func)
    
    healthy, detail = wewe.check_service()
    
    assert healthy is False
    assert "API error: invalid key" in detail

def test_check_service_no_feeds(monkeypatch):
    """Test check_service when no feeds configured."""
    mock_response = b'{"err": null, "data": []}'
    
    mock_urlopen = MagicMock()
    mock_urlopen.read.return_value = mock_response
    
    def mock_urlopen_func(req):
        return mock_urlopen
    
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_func)
    
    healthy, detail = wewe.check_service()
    
    assert healthy is False
    assert "no feeds configured" in detail

def test_check_service_some_paused(monkeypatch):
    """Test check_service when some feeds are paused."""
    mock_response = b'{"err": null, "data": [{"paused": true}, {"paused": false}]}'
    
    mock_urlopen = MagicMock()
    mock_urlopen.read.return_value = mock_response
    
    def mock_urlopen_func(req):
        return mock_urlopen
    
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_func)
    
    healthy, detail = wewe.check_service()
    
    assert healthy is False
    assert "1/2 feeds paused" in detail

def test_send_alert_prints_when_no_tg_script(capsys, monkeypatch):
    """Test send_alert prints when tg-notify.sh not found."""
    tg_mock = MagicMock()
    tg_mock.exists.return_value = False
    
    monkeypatch.setattr(wewe, "TG_SCRIPT", tg_mock)
    
    wewe.send_alert("test alert")
    
    captured = capsys.readouterr()
    assert "test alert" in captured.err
