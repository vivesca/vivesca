from __future__ import annotations

"""Tests for secretory_vesicle — Telegram export organelle."""

from unittest.mock import patch

import pytest


class TestHtmlEscape:
    def test_escapes_ampersand(self):
        from metabolon.organelles.secretory_vesicle import _html_escape
        assert _html_escape("a & b") == "a &amp; b"

    def test_escapes_lt_gt(self):
        from metabolon.organelles.secretory_vesicle import _html_escape
        assert _html_escape("<script>") == "&lt;script&gt;"

    def test_no_escaping_needed(self):
        from metabolon.organelles.secretory_vesicle import _html_escape
        assert _html_escape("hello world") == "hello world"

    def test_combined(self):
        from metabolon.organelles.secretory_vesicle import _html_escape
        assert _html_escape("a < b & c > d") == "a &lt; b &amp; c &gt; d"


class TestRateLimit:
    def test_no_lock_file(self, tmp_path):
        """No lock file = no delay."""
        from metabolon.organelles.secretory_vesicle import _rate_limit
        import metabolon.organelles.secretory_vesicle as sv
        with patch.object(sv, "_LOCK", tmp_path / "nolock"):
            _rate_limit()  # should not raise or sleep

    def test_old_lock_file_no_delay(self, tmp_path):
        """Lock file older than 1 second = no delay."""
        import time
        from metabolon.organelles.secretory_vesicle import _rate_limit
        import metabolon.organelles.secretory_vesicle as sv
        lock = tmp_path / "lock"
        lock.touch()
        # Make it 2 seconds old
        import os
        os.utime(lock, (time.time() - 2, time.time() - 2))
        with patch.object(sv, "_LOCK", lock):
            _rate_limit()  # should not sleep


class TestKeychain:
    def test_missing_credential_raises(self):
        from metabolon.organelles.secretory_vesicle import _keychain
        with patch("metabolon.organelles.secretory_vesicle.subprocess") as mock_sp:
            mock_sp.run.return_value = type("R", (), {"returncode": 1, "stdout": ""})()
            with pytest.raises(ValueError, match="missing"):
                _keychain("nonexistent")

    def test_valid_credential(self):
        from metabolon.organelles.secretory_vesicle import _keychain
        with patch("metabolon.organelles.secretory_vesicle.subprocess") as mock_sp:
            mock_sp.run.return_value = type("R", (), {"returncode": 0, "stdout": "my-token\n"})()
            assert _keychain("test-service") == "my-token"
