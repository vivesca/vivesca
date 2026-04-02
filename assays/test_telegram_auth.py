"""Tests for metabolon.organelles.telegram_auth."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.organelles.telegram_auth import SESSION_DIR, SESSION_NAME, main


class TestConstants:
    """Module-level constants are correct."""

    def test_session_dir_under_config(self):
        assert SESSION_DIR == Path.home() / ".config" / "telethon"

    def test_session_name(self):
        assert SESSION_NAME == "vivesca"


class TestMainAlreadyAuthorized:
    """When the user is already authorized, skip code-request flow."""

    @patch("metabolon.organelles.telegram_auth.TelegramClient", create=True)
    def test_skips_code_request(self, mock_client_cls):
        mock_client = AsyncMock()
        mock_client.is_user_authorized.return_value = True
        me = MagicMock(first_name="Alice", phone="+15551234567")
        mock_client.get_me.return_value = me
        mock_client_cls.return_value = mock_client

        with (
            patch.dict(os.environ, {"TELEGRAM_API_ID": "12345", "TELEGRAM_API_HASH": "deadbeef"}),
            patch("metabolon.organelles.telegram_auth.TelegramClient", mock_client_cls),
        ):
            asyncio.run(main())

        mock_client.send_code_request.assert_not_called()
        mock_client.sign_in.assert_not_called()

    @patch("metabolon.organelles.telegram_auth.TelegramClient", create=True)
    def test_prints_user_info(self, mock_client_cls):
        mock_client = AsyncMock()
        mock_client.is_user_authorized.return_value = True
        me = MagicMock(first_name="Bob", phone="+15559876543")
        mock_client.get_me.return_value = me
        mock_client_cls.return_value = mock_client

        with (
            patch.dict(os.environ, {"TELEGRAM_API_ID": "12345", "TELEGRAM_API_HASH": "deadbeef"}),
            patch("metabolon.organelles.telegram_auth.TelegramClient", mock_client_cls),
            patch("builtins.print") as mock_print,
        ):
            asyncio.run(main())

        mock_print.assert_called_once_with("Authenticated as: Bob (+15559876543)")

    @patch("metabolon.organelles.telegram_auth.TelegramClient", create=True)
    def test_disconnect_called(self, mock_client_cls):
        mock_client = AsyncMock()
        mock_client.is_user_authorized.return_value = True
        mock_client.get_me.return_value = MagicMock(first_name="X", phone="+1")
        mock_client_cls.return_value = mock_client

        with (
            patch.dict(os.environ, {"TELEGRAM_API_ID": "12345", "TELEGRAM_API_HASH": "deadbeef"}),
            patch("metabolon.organelles.telegram_auth.TelegramClient", mock_client_cls),
        ):
            asyncio.run(main())

        mock_client.disconnect.assert_awaited_once()


class TestMainNotAuthorized:
    """When the user is not yet authorized, run the code-request flow."""

    @patch("metabolon.organelles.telegram_auth.TelegramClient", create=True)
    def test_sends_code_and_signs_in(self, mock_client_cls):
        mock_client = AsyncMock()
        mock_client.is_user_authorized.return_value = False
        mock_client.send_code_request.return_value = None
        mock_client.sign_in.return_value = None
        mock_client.get_me.return_value = MagicMock(first_name="Carol", phone="+15550001111")
        mock_client_cls.return_value = mock_client

        with (
            patch.dict(os.environ, {"TELEGRAM_API_ID": "99", "TELEGRAM_API_HASH": "abc123"}),
            patch("metabolon.organelles.telegram_auth.TelegramClient", mock_client_cls),
            patch("sys.argv", ["telegram_auth", "+15550001111", "54321"]),
        ):
            asyncio.run(main())

        mock_client.send_code_request.assert_awaited_once_with("+15550001111")
        mock_client.sign_in.assert_awaited_once_with("+15550001111", "54321")

    @patch("metabolon.organelles.telegram_auth.TelegramClient", create=True)
    def test_handles_missing_user_attrs(self, mock_client_cls):
        """User object with no first_name/phone should print 'unknown'."""
        mock_client = AsyncMock()
        mock_client.is_user_authorized.return_value = True
        mock_client.get_me.return_value = MagicMock(spec=[])  # no attributes
        mock_client_cls.return_value = mock_client

        with (
            patch.dict(os.environ, {"TELEGRAM_API_ID": "1", "TELEGRAM_API_HASH": "x"}),
            patch("metabolon.organelles.telegram_auth.TelegramClient", mock_client_cls),
            patch("builtins.print") as mock_print,
        ):
            asyncio.run(main())

        mock_print.assert_called_once_with("Authenticated as: unknown (unknown)")


class TestMissingEnvVars:
    """Missing required env vars should raise KeyError."""

    def test_missing_api_id(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(KeyError, match="TELEGRAM_API_ID"):
                asyncio.run(main())

    def test_missing_api_hash(self):
        with patch.dict(os.environ, {"TELEGRAM_API_ID": "123"}, clear=True):
            with pytest.raises(KeyError, match="TELEGRAM_API_HASH"):
                asyncio.run(main())
