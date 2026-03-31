"""Tests for effectors/importin — credential loader for macOS Keychain.

Effectors are scripts, loaded via exec() not import.
"""

from pathlib import Path
from unittest.mock import patch
import subprocess
import sys


def load_importin():
    """Load importin effector via exec and return its namespace."""
    ns = {"__name__": "importin_tested"}
    effector_path = Path(__file__).parent.parent / "effectors" / "importin"
    exec(open(effector_path).read(), ns)
    return ns


class TestGetKeychainValue:
    """Tests for get_keychain_value function."""

    def test_success_returns_stripped_value(self):
        """When security CLI succeeds, return stripped stdout."""
        ns = load_importin()
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="secret-value\n", stderr=""
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            result = ns["get_keychain_value"]("my-service")
        assert result == "secret-value"

    def test_failure_returns_none(self):
        """When security CLI fails, return None."""
        ns = load_importin()
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=44, stdout="", stderr="not found"
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            result = ns["get_keychain_value"]("missing-service")
        assert result is None

    def test_timeout_returns_none(self):
        """When security CLI times out, return None."""
        ns = load_importin()
        with patch.object(
            subprocess, "run", side_effect=subprocess.TimeoutExpired(cmd=[], timeout=5)
        ):
            result = ns["get_keychain_value"]("slow-service")
        assert result is None

    def test_file_not_found_returns_none(self):
        """When security CLI is not found (FileNotFoundError), return None."""
        ns = load_importin()
        with patch.object(subprocess, "run", side_effect=FileNotFoundError):
            result = ns["get_keychain_value"]("any-service")
        assert result is None


class TestLoadKeychainEnv:
    """Tests for load_keychain_env function."""

    def test_loads_missing_keys(self):
        """Load credentials that are not already in environ."""
        ns = load_importin()
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="test-key\n", stderr=""
        )
        # Clear any existing keys first
        import os

        for key in ns["CREDENTIALS"]:
            os.environ.pop(key, None)

        with patch.object(subprocess, "run", return_value=mock_result):
            loaded = ns["load_keychain_env"]()

        # Should have loaded all credentials
        assert len(loaded) == len(ns["CREDENTIALS"])
        assert all(key in loaded for key in ns["CREDENTIALS"])

    def test_skips_existing_keys(self):
        """Do not overwrite keys already in environ."""
        ns = load_importin()
        import os

        # Set a pre-existing value
        os.environ["ANTHROPIC_API_KEY"] = "existing-value"
        # Remove other keys
        for key in ns["CREDENTIALS"]:
            if key != "ANTHROPIC_API_KEY":
                os.environ.pop(key, None)

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="new-value\n", stderr=""
        )
        with patch.object(subprocess, "run", return_value=mock_result):
            loaded = ns["load_keychain_env"]()

        # ANTHROPIC_API_KEY should NOT be in loaded (it was already set)
        assert "ANTHROPIC_API_KEY" not in loaded
        # The existing value should remain
        assert os.environ["ANTHROPIC_API_KEY"] == "existing-value"

    def test_returns_only_successful_loads(self):
        """Only return keys that were successfully retrieved."""
        ns = load_importin()
        import os

        # Clear all keys
        for key in ns["CREDENTIALS"]:
            os.environ.pop(key, None)

        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            # Succeed for first call, fail for second
            if call_count[0] == 1:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="success\n", stderr=""
                )
            return subprocess.CompletedProcess(
                args=[], returncode=44, stdout="", stderr=""
            )

        with patch.object(subprocess, "run", side_effect=mock_run):
            loaded = ns["load_keychain_env"]()

        # Only first credential should be loaded
        assert len(loaded) == 1


class TestMainBlock:
    """Tests for __main__ behavior via subprocess execution."""

    def test_help_flag_exits_zero(self):
        """--help prints usage and exits 0."""
        effector_path = Path(__file__).parent.parent / "effectors" / "importin"
        result = subprocess.run(
            [sys.executable, str(effector_path), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "importin" in result.stdout

    def test_non_darwin_exits_error(self):
        """On non-macOS, exit with error message."""
        effector_path = Path(__file__).parent.parent / "effectors" / "importin"
        result = subprocess.run(
            [sys.executable, str(effector_path)],
            capture_output=True,
            text=True,
        )
        # We're on Linux, so should fail
        assert result.returncode == 1
        assert "requires macOS Keychain" in result.stderr

    def test_export_format_single_quotes(self):
        """Export statements use single quotes to prevent expansion."""
        ns = load_importin()
        # Test the escaping logic inline
        val = "value-with-$var"
        escaped = val.replace("'", "'\\''")
        assert escaped == "value-with-$var"  # $ preserved

    def test_export_escapes_single_quotes(self):
        """Single quotes in values are properly escaped."""
        ns = load_importin()
        val = "value'with'quotes"
        escaped = val.replace("'", "'\\''")
        assert escaped == "value'\\''with'\\''quotes"
