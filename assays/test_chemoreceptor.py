from __future__ import annotations

"""Tests for chemoreceptor — Oura health sensing."""

from unittest.mock import patch, MagicMock

import pytest


class TestGetToken:
    def test_env_var(self):
        from metabolon.organelles.chemoreceptor import _get_token
        with patch.dict("os.environ", {"OURA_TOKEN": "test-token"}):
            assert _get_token() == "test-token"

    def test_keychain_fallback(self):
        from metabolon.organelles.chemoreceptor import _get_token
        with patch.dict("os.environ", {}, clear=True), \
             patch("metabolon.organelles.chemoreceptor._keychain_token", return_value="keychain-tok"):
            # Clear OURA_TOKEN from env
            import os
            os.environ.pop("OURA_TOKEN", None)
            assert _get_token() == "keychain-tok"

    def test_no_token_raises(self):
        from metabolon.organelles.chemoreceptor import _get_token
        with patch.dict("os.environ", {}, clear=True), \
             patch("metabolon.organelles.chemoreceptor._keychain_token", return_value=None):
            import os
            os.environ.pop("OURA_TOKEN", None)
            with pytest.raises(RuntimeError, match="OURA_TOKEN"):
                _get_token()


class TestKeychainToken:
    def test_success(self):
        from metabolon.organelles.chemoreceptor import _keychain_token
        with patch("metabolon.organelles.chemoreceptor.subprocess") as mock_sp:
            mock_sp.run.return_value = MagicMock(returncode=0, stdout="my-oura-token\n")
            assert _keychain_token() == "my-oura-token"

    def test_failure(self):
        from metabolon.organelles.chemoreceptor import _keychain_token
        with patch("metabolon.organelles.chemoreceptor.subprocess") as mock_sp:
            mock_sp.run.return_value = MagicMock(returncode=1, stdout="")
            assert _keychain_token() is None

    def test_exception(self):
        from metabolon.organelles.chemoreceptor import _keychain_token
        with patch("metabolon.organelles.chemoreceptor.subprocess") as mock_sp:
            mock_sp.run.side_effect = Exception("timeout")
            assert _keychain_token() is None


class TestDateHelpers:
    def test_today_date(self):
        from metabolon.organelles.chemoreceptor import _today_date
        from datetime import date
        result = _today_date()
        assert result == str(date.today())

    def test_week_start_date(self):
        from metabolon.organelles.chemoreceptor import _week_start_date
        from datetime import date, timedelta
        result = _week_start_date(7)
        expected = str(date.today() - timedelta(days=7))
        assert result == expected
