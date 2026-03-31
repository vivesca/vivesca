#!/usr/bin/env python3
"""Tests for importin effector."""

import pytest
import os
import subprocess
from unittest.mock import MagicMock, patch
from pathlib import Path

# Execute the importin file directly
importin_path = Path("/home/terry/germline/effectors/importin")
importin_code = importin_path.read_text()
namespace = {}
exec(importin_code, namespace)

# Extract module
importin = type('importin_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(importin, key, value)


def test_credentials_have_correct_mapping():
    """Test that all credentials have non-empty mappings."""
    for env_var, service in importin.CREDENTIALS.items():
        assert env_var, "Env var name should not be empty"
        assert service, "Service name should not be empty"
        assert isinstance(env_var, str)
        assert isinstance(service, str)


def test_get_keychain_value_handles_timeout():
    """Test that get_keychain_value returns None on timeout."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(None, 5)
        result = importin.get_keychain_value("test-service")
        assert result is None


def test_get_keychain_value_handles_not_found():
    """Test that get_keychain_value returns None when security not found."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = importin.get_keychain_value("test-service")
        assert result is None


def test_get_keychain_value_returns_value_on_success():
    """Test returns stripped value on success."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test-key-value\n"
        mock_run.return_value = mock_result
        result = importin.get_keychain_value("test-service")
        assert result == "test-key-value"
        assert mock_run.called
        assert "security" in mock_run.call_args[0][0]


def test_load_keychain_env_skips_already_set():
    """Test that load_keychain_env doesn't overwrite existing env vars."""
    original_env = os.environ.copy()
    os.environ["ANTHROPIC_API_KEY"] = "already-set"

    with patch.object(importin, 'get_keychain_value') as mock_get:
        mock_get.return_value = "should-not-overwrite"
        loaded = importin.load_keychain_env()
        assert "ANTHROPIC_API_KEY" not in loaded
        assert os.environ["ANTHROPIC_API_KEY"] == "already-set"

    # Restore env
    os.environ.clear()
    os.environ.update(original_env)


def test_load_keychain_env_adds_values_not_set():
    """Test that load_keychain_env adds credentials not already in env."""
    original_env = os.environ.copy()
    if "TEST_KEY" in os.environ:
        del os.environ["TEST_KEY"]
    # Add to CREDENTIALS temporarily for test
    original_creds = importin.CREDENTIALS.copy()
    importin.CREDENTIALS["TEST_KEY"] = "test-service"

    with patch.object(importin, 'get_keychain_value') as mock_get:
        mock_get.return_value = "test-value"
        loaded = importin.load_keychain_env()
        assert "TEST_KEY" in loaded
        assert loaded["TEST_KEY"] == "test-value"
        assert os.environ["TEST_KEY"] == "test-value"

    # Restore
    importin.CREDENTIALS.pop("TEST_KEY", None)
    os.environ.clear()
    os.environ.update(original_env)


def test_main_prints_exports_for_values():
    """Test main prints export statements."""
    with patch.object(importin, 'get_keychain_value') as mock_get:
        mock_get.side_effect = lambda s: "fake-key" if s == "anthropic-api-key" else None

        with patch('builtins.print') as mock_print:
            importin.main()
            # Should have printed export for ANTHROPIC_API_KEY
            printed_calls = [str(call[0][0]) for call in mock_print.call_args_list]
            assert any("export ANTHROPIC_API_KEY='fake-key'" in line for line in printed_calls)
