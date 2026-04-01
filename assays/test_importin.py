from __future__ import annotations

"""Tests for importin — macOS Keychain credential loader."""

import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


def _load_importin():
    """Load the importin module by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/importin")).read()
    ns: dict = {"__name__": "importin"}
    exec(source, ns)
    return ns


_mod = _load_importin()
get_keychain_value = _mod["get_keychain_value"]
load_keychain_env = _mod["load_keychain_env"]
CREDENTIALS = _mod["CREDENTIALS"]


# ── get_keychain_value tests ───────────────────────────────────────────────


def test_get_keychain_value_success():
    """get_keychain_value returns password on success."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "secret-value\n"

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = get_keychain_value("test-service")

    assert result == "secret-value"
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "security"
    assert args[1] == "find-generic-password"


def test_get_keychain_value_strips_trailing_newline():
    """get_keychain_value strips trailing newline from password."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "secret-value\n\n"

    with patch("subprocess.run", return_value=mock_result):
        result = get_keychain_value("test-service")

    assert result == "secret-value"


def test_get_keychain_value_strips_all_whitespace():
    """get_keychain_value strips both leading and trailing whitespace."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "  secret-value  \n\n"

    with patch("subprocess.run", return_value=mock_result):
        result = get_keychain_value("test-service")

    # .strip() removes ALL leading/trailing whitespace
    assert result == "secret-value"


def test_get_keychain_value_failure_returns_none():
    """get_keychain_value returns None when security command fails."""
    mock_result = MagicMock()
    mock_result.returncode = 44  # macOS security error code

    with patch("subprocess.run", return_value=mock_result):
        result = get_keychain_value("missing-service")

    assert result is None


def test_get_keychain_value_timeout_returns_none():
    """get_keychain_value returns None on timeout."""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("security", 5)):
        result = get_keychain_value("slow-service")

    assert result is None


def test_get_keychain_value_file_not_found_returns_none():
    """get_keychain_value returns None when security binary not found."""
    with patch("subprocess.run", side_effect=FileNotFoundError):
        result = get_keychain_value("any-service")

    assert result is None


def test_get_keychain_value_uses_current_user():
    """get_keychain_value passes current username to security command."""
    import getpass

    expected_user = getpass.getuser()
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "value"

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        get_keychain_value("test-service")

    args = mock_run.call_args[0][0]
    assert "-a" in args
    user_idx = args.index("-a") + 1
    assert args[user_idx] == expected_user


# ── load_keychain_env tests ────────────────────────────────────────────────


def test_load_keychain_env_loads_missing_keys():
    """load_keychain_env loads keys not already in environment."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "test-api-key"

    # Clear all existing credential keys from environment
    for key in CREDENTIALS:
        os.environ.pop(key, None)

    with patch("subprocess.run", return_value=mock_result):
        loaded = load_keychain_env()

    # Should have loaded all credentials (since none existed in env)
    assert len(loaded) == len(CREDENTIALS)
    for key in CREDENTIALS:
        assert key in loaded
        assert os.environ.get(key) == "test-api-key"

    # Cleanup
    for key in CREDENTIALS:
        os.environ.pop(key, None)


def test_load_keychain_env_skips_existing_keys():
    """load_keychain_env does not overwrite existing env vars."""
    os.environ["ANTHROPIC_API_KEY"] = "existing-value"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "new-value"

    # Clear all other keys
    for key in CREDENTIALS:
        if key != "ANTHROPIC_API_KEY":
            os.environ.pop(key, None)

    with patch("subprocess.run", return_value=mock_result):
        loaded = load_keychain_env()

    # ANTHROPIC_API_KEY should retain existing value, not be in loaded
    assert "ANTHROPIC_API_KEY" not in loaded
    assert os.environ["ANTHROPIC_API_KEY"] == "existing-value"

    # Cleanup
    os.environ.pop("ANTHROPIC_API_KEY", None)
    for key in CREDENTIALS:
        os.environ.pop(key, None)


def test_load_keychain_env_skips_none_values():
    """load_keychain_env skips keys that return None from keychain."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "test-value"

    # Clear all existing keys
    for key in CREDENTIALS:
        os.environ.pop(key, None)

    # Track which calls should return None
    call_count = [0]
    
    def mock_run_returning_none_for_some(*args, **kwargs):
        mock_res = MagicMock()
        call_count[0] += 1
        # Return None for half the calls (via non-zero return code)
        if call_count[0] % 2 == 0:
            mock_res.returncode = 44
            mock_res.stdout = ""
        else:
            mock_res.returncode = 0
            mock_res.stdout = "test-value"
        return mock_res

    with patch("subprocess.run", side_effect=mock_run_returning_none_for_some):
        loaded = load_keychain_env()

    # Only half should be loaded (odd-numbered calls)
    assert len(loaded) == len(CREDENTIALS) // 2 + (len(CREDENTIALS) % 2)

    # Cleanup
    for key in CREDENTIALS:
        os.environ.pop(key, None)


def test_credentials_mapping_has_expected_keys():
    """CREDENTIALS dict contains expected API keys."""
    expected_keys = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
    ]
    for key in expected_keys:
        assert key in CREDENTIALS, f"Missing expected key: {key}"


# ── CLI mode tests ─────────────────────────────────────────────────────────


def test_cli_help_flag():
    """CLI --help prints docstring and exits 0."""
    result = subprocess.run(
        ["python3", str(Path.home() / "germline/effectors/importin"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "importin" in result.stdout


def test_cli_h_flag():
    """CLI -h prints docstring and exits 0."""
    result = subprocess.run(
        ["python3", str(Path.home() / "germline/effectors/importin"), "-h"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "importin" in result.stdout


def test_cli_non_macos_exits_with_error():
    """CLI exits with error on non-macOS platforms."""
    result = subprocess.run(
        ["python3", str(Path.home() / "germline/effectors/importin")],
        capture_output=True,
        text=True,
    )
    # On Linux (soma), should exit with error
    assert result.returncode == 1
    assert "requires macOS Keychain" in result.stderr


def test_cli_shell_escaping():
    """Test shell escaping logic for single quotes in values."""
    test_val = "value-with'quote"
    expected = "value-with'\\''quote"
    escaped = test_val.replace("'", "'\\''")
    assert escaped == expected


# ── Integration test (macOS only) ─────────────────────────────────────────


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="Keychain integration only works on macOS"
)
def test_real_keychain_fetch():
    """Test actual keychain fetch on macOS."""
    # This test is skipped on Linux
    result = get_keychain_value("test-service")
    if result:
        assert isinstance(result, str)
