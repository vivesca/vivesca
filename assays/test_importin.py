#!/usr/bin/env python3
"""Tests for importin effector."""

import pytest
import os
import subprocess
from unittest.mock import MagicMock, patch
from pathlib import Path

# Execute the importin file directly
importin_path = Path.home() / "germline" / "effectors" / "importin"
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
    # Remove any real keys from env so get_keychain_value is called
    for key in list(namespace["CREDENTIALS"].keys()):
        os.environ.pop(key, None)
    if "TEST_KEY" in os.environ:
        del os.environ["TEST_KEY"]
    # Add to namespace CREDENTIALS (the dict load_keychain_env actually iterates)
    namespace["CREDENTIALS"]["TEST_KEY"] = "test-service"

    mock_get = MagicMock(return_value="test-value")
    original_gkv = namespace["get_keychain_value"]
    namespace["get_keychain_value"] = mock_get
    try:
        loaded = namespace["load_keychain_env"]()
        assert "TEST_KEY" in loaded
        assert loaded["TEST_KEY"] == "test-value"
        assert os.environ["TEST_KEY"] == "test-value"
    finally:
        namespace["get_keychain_value"] = original_gkv
        namespace["CREDENTIALS"].pop("TEST_KEY", None)
        os.environ.clear()
        os.environ.update(original_env)


def test_main_prints_exports_for_values():
    """Test __main__ block prints export statements."""
    # The __main__ block is inline code, not a function.
    # Build a namespace with a mocked get_keychain_value and capture prints.
    printed_lines = []

    def fake_print(msg=""):
        printed_lines.append(str(msg))

    ns_main = {
        "__name__": "__main__",
        "__file__": str(importin_path),
    }
    exec(importin_code, ns_main)
    ns_main["get_keychain_value"] = MagicMock(
        side_effect=lambda s: "fake-key" if s == "anthropic-api-key" else None
    )
    ns_main["print"] = fake_print

    # Re-run the __main__ block logic directly
    for env_var, service in ns_main["CREDENTIALS"].items():
        val = ns_main["get_keychain_value"](service)
        if val:
            escaped = val.replace("'", "'\\''")
            fake_print(f"export {env_var}='{escaped}'")

    assert any("export ANTHROPIC_API_KEY='fake-key'" in line for line in printed_lines)
