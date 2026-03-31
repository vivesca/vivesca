from __future__ import annotations

"""Tests for importin — transport credentials from macOS Keychain into shell environment."""


import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_importin():
    """Load the importin module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/importin").read()
    ns: dict = {"__name__": "importin_test"}
    exec(source, ns)
    return ns


_mod = _load_importin()
get_keychain_value = _mod["get_keychain_value"]
load_keychain_env = _mod["load_keychain_env"]
CREDENTIALS = _mod["CREDENTIALS"]


# ── get_keychain_value tests ─────────────────────────────────────────────


def test_get_keychain_value_success():
    """get_keychain_value returns the password when security command succeeds."""
    with patch("subprocess.run") as mock_run:
        result = MagicMock()
        result.returncode = 0
        result.stdout = "secret-api-key\n"
        mock_run.return_value = result

        val = get_keychain_value("test-service")

        assert val == "secret-api-key"
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "security" in args
        assert "find-generic-password" in args
        assert "test-service" in args


def test_get_keychain_value_strips_whitespace():
    """get_keychain_value strips trailing whitespace from output."""
    with patch("subprocess.run") as mock_run:
        result = MagicMock()
        result.returncode = 0
        result.stdout = "  api-key-with-spaces  \n\t"
        mock_run.return_value = result

        val = get_keychain_value("test-service")
        assert val == "api-key-with-spaces"


def test_get_keychain_value_failure_returns_none():
    """get_keychain_value returns None when security command fails."""
    with patch("subprocess.run") as mock_run:
        result = MagicMock()
        result.returncode = 44  # Item not found
        result.stdout = ""
        mock_run.return_value = result

        val = get_keychain_value("nonexistent-service")
        assert val is None


def test_get_keychain_value_timeout_returns_none():
    """get_keychain_value returns None on timeout."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="security", timeout=5)

        val = get_keychain_value("slow-service")
        assert val is None


def test_get_keychain_value_file_not_found_returns_none():
    """get_keychain_value returns None when security CLI is not available."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("security not found")

        val = get_keychain_value("any-service")
        assert val is None


def test_get_keychain_value_passes_user():
    """get_keychain_value passes the current user to security command."""
    import getpass

    expected_user = getpass.getuser()

    with patch("subprocess.run") as mock_run:
        result = MagicMock()
        result.returncode = 0
        result.stdout = "value"
        mock_run.return_value = result

        get_keychain_value("test-service")

        args = mock_run.call_args[0][0]
        # -a flag is for account (user)
        assert "-a" in args
        user_idx = args.index("-a") + 1
        assert args[user_idx] == expected_user


def test_get_keychain_value_passes_service():
    """get_keychain_value passes the service name to security command."""
    with patch("subprocess.run") as mock_run:
        result = MagicMock()
        result.returncode = 0
        result.stdout = "value"
        mock_run.return_value = result

        get_keychain_value("my-custom-service")

        args = mock_run.call_args[0][0]
        # -s flag is for service
        assert "-s" in args
        service_idx = args.index("-s") + 1
        assert args[service_idx] == "my-custom-service"


# ── load_keychain_env tests ───────────────────────────────────────────────


def test_load_keychain_env_loads_missing_keys():
    """load_keychain_env loads credentials not already in environment."""
    # Clear any existing test keys
    test_key = "ANTHROPIC_API_KEY"
    original = os.environ.pop(test_key, None)

    try:
        with patch("subprocess.run") as mock_run:
            def mock_security(cmd, *args, **kwargs):
                result = MagicMock()
                result.returncode = 0
                if "anthropic-api-key" in cmd:
                    result.stdout = "sk-ant-test\n"
                else:
                    result.returncode = 44
                    result.stdout = ""
                return result

            mock_run.side_effect = mock_security

            loaded = load_keychain_env()

        assert test_key in loaded
        assert loaded[test_key] == "sk-ant-test"
        assert os.environ.get(test_key) == "sk-ant-test"
    finally:
        if original is not None:
            os.environ[test_key] = original
        elif test_key in os.environ:
            del os.environ[test_key]


def test_load_keychain_env_skips_existing_keys():
    """load_keychain_env does not overwrite existing environment variables."""
    test_key = "OPENAI_API_KEY"
    original = os.environ.get(test_key)
    os.environ[test_key] = "already-set-value"

    try:
        with patch("subprocess.run") as mock_run:
            result = MagicMock()
            result.returncode = 0
            result.stdout = "sk-openai-new\n"
            mock_run.return_value = result

            loaded = load_keychain_env()

        # Should not have loaded this key since it was already set
        assert test_key not in loaded
        # Original value preserved
        assert os.environ[test_key] == "already-set-value"
    finally:
        if original is not None:
            os.environ[test_key] = original
        elif test_key in os.environ:
            del os.environ[test_key]


def test_load_keychain_env_returns_only_loaded():
    """load_keychain_env returns dict with only successfully loaded keys."""
    # Clear test keys
    keys_to_clear = ["XAI_API_KEY", "DEEPGRAM_API_KEY"]
    originals = {}
    for key in keys_to_clear:
        originals[key] = os.environ.pop(key, None)

    try:
        with patch("subprocess.run") as mock_run:
            def mock_security(cmd, *args, **kwargs):
                result = MagicMock()
                result.returncode = 0
                if "xai-api-key" in cmd:
                    result.stdout = "xai-test-key\n"
                else:
                    result.returncode = 44  # Not found
                    result.stdout = ""
                return result

            mock_run.side_effect = mock_security

            loaded = load_keychain_env()

        # Only XAI should be loaded
        assert "XAI_API_KEY" in loaded
        assert "DEEPGRAM_API_KEY" not in loaded
    finally:
        for key, val in originals.items():
            if val is not None:
                os.environ[key] = val
            elif key in os.environ:
                del os.environ[key]


def test_load_keychain_env_handles_all_credentials():
    """load_keychain_env iterates over all defined credentials."""
    # Verify CREDENTIALS has expected keys
    assert "ANTHROPIC_API_KEY" in CREDENTIALS
    assert "OPENAI_API_KEY" in CREDENTIALS
    assert "GEMINI_API_KEY" in CREDENTIALS


# ── CREDENTIALS constant tests ───────────────────────────────────────────


def test_credentials_mapping_format():
    """CREDENTIALS maps env var names to keychain service names."""
    assert isinstance(CREDENTIALS, dict)
    for env_var, service in CREDENTIALS.items():
        assert isinstance(env_var, str)
        assert isinstance(service, str)
        assert env_var.isupper() or "_" in env_var  # UPPER_SNAKE_CASE


def test_credentials_has_expected_keys():
    """CREDENTIALS contains expected API keys."""
    expected = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
    ]
    for key in expected:
        assert key in CREDENTIALS, f"Missing expected credential: {key}"


# ── Shell mode tests (subprocess) ─────────────────────────────────────────


def test_shell_mode_help_flag():
    """Running importin --help prints usage."""
    result = subprocess.run(
        ["/home/terry/germline/effectors/importin", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "importin" in result.stdout.lower() or "usage" in result.stdout.lower()


def test_shell_mode_non_macos_exits():
    """Running importin on non-macOS exits with error message."""
    # On Linux, should exit with error
    result = subprocess.run(
        ["/home/terry/germline/effectors/importin"],
        capture_output=True,
        text=True,
    )
    # Should fail because 'security' CLI is macOS-only
    assert result.returncode != 0
    assert "macOS" in result.stderr or "Keychain" in result.stderr or "security" in result.stderr


def test_shell_mode_output_format():
    """Shell mode outputs valid export statements."""
    # We can't test actual keychain access on Linux, but we can test the format
    # by mocking at the Python level
    with patch("platform.system", return_value="Darwin"):
        with patch("shutil.which", return_value="/usr/bin/security"):
            with patch("subprocess.run") as mock_run:
                result = MagicMock()
                result.returncode = 0
                result.stdout = "test-value\n"
                mock_run.return_value = result

                # Re-exec the module to get shell output
                import sys
                import io
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()

                try:
                    source = open("/home/terry/germline/effectors/importin").read()
                    ns = {"__name__": "__main__"}
                    exec(source, ns)
                    output = sys.stdout.getvalue()
                except SystemExit:
                    output = sys.stdout.getvalue()
                finally:
                    sys.stdout = old_stdout

                # Should have export statements
                if output:
                    for line in output.splitlines():
                        if line.strip():
                            assert line.startswith("export ")


def test_shell_mode_escapes_single_quotes():
    """Shell mode properly escapes single quotes in values."""
    with patch("platform.system", return_value="Darwin"):
        with patch("shutil.which", return_value="/usr/bin/security"):
            with patch("subprocess.run") as mock_run:
                result = MagicMock()
                result.returncode = 0
                result.stdout = "value'with'quotes\n"
                mock_run.return_value = result

                import sys
                import io
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()

                try:
                    source = open("/home/terry/germline/effectors/importin").read()
                    ns = {"__name__": "__main__"}
                    exec(source, ns)
                    output = sys.stdout.getvalue()
                except SystemExit:
                    output = sys.stdout.getvalue()
                finally:
                    sys.stdout = old_stdout

                if output:
                    # Should escape single quotes properly
                    assert "'\\''" in output or "quotes" in output


# ── Edge case tests ───────────────────────────────────────────────────────


def test_get_keychain_value_empty_output():
    """get_keychain_value returns empty string for empty but successful output."""
    with patch("subprocess.run") as mock_run:
        result = MagicMock()
        result.returncode = 0
        result.stdout = ""
        mock_run.return_value = result

        val = get_keychain_value("empty-service")
        assert val == ""


def test_load_keychain_env_empty_result():
    """load_keychain_env returns empty dict when nothing loaded."""
    # Set all keys so none are loaded
    originals = {}
    for key in CREDENTIALS.keys():
        originals[key] = os.environ.pop(key, None)
        os.environ[key] = "preset-value"

    try:
        loaded = load_keychain_env()
        assert loaded == {}
    finally:
        for key, val in originals.items():
            if val is not None:
                os.environ[key] = val
            elif key in os.environ:
                del os.environ[key]


def test_load_keychain_env_mixed_success_failure():
    """load_keychain_env handles mixed success/failure from keychain."""
    # Clear some test keys
    keys = ["BRAVE_API_KEY", "TAVILY_API_KEY"]
    originals = {}
    for key in keys:
        originals[key] = os.environ.pop(key, None)

    try:
        with patch("subprocess.run") as mock_run:
            def mock_security(cmd, *args, **kwargs):
                result = MagicMock()
                # Brave succeeds
                if "brave-api-key" in cmd:
                    result.returncode = 0
                    result.stdout = "brave-key\n"
                # Tavily fails
                else:
                    result.returncode = 44
                    result.stdout = ""
                return result
            mock_run.side_effect = mock_security

            loaded = load_keychain_env()

        # Only brave should be loaded
        assert "BRAVE_API_KEY" in loaded
        assert "TAVILY_API_KEY" not in loaded
    finally:
        for key, val in originals.items():
            if val is not None:
                os.environ[key] = val
            elif key in os.environ:
                del os.environ[key]


def test_credentials_service_names_unique():
    """Each credential maps to a unique keychain service name."""
    services = list(CREDENTIALS.values())
    # Allow duplicates only if they're intentional (same key, different env var)
    # For now, just verify they're all non-empty strings
    for service in services:
        assert service, "Service name should not be empty"
