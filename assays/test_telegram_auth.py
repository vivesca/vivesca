"""Tests for metabolon.organelles.telegram_auth."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.organelles.telegram_auth import SESSION_DIR, SESSION_NAME, main


def _make_client(**overrides):
    """Build a mock TelegramClient with sensible async defaults."""
    client = AsyncMock()
    client.is_user_authorized.return_value = overrides.get("authorized", True)
    client.get_me.return_value = overrides.get(
        "me", MagicMock(first_name="Alice", phone="+15551234567")
    )
    return client


class TestConstants:
    """Module-level constants are correct."""

    def test_session_dir_under_config(self):
        assert Path.home() / ".config" / "telethon" == SESSION_DIR

    def test_session_name(self):
        assert SESSION_NAME == "vivesca"


class TestMainAlreadyAuthorized:
    """When the user is already authorized, skip code-request flow."""

    def test_skips_code_request(self):
        mock_cls = MagicMock(return_value=_make_client(authorized=True))
        with (
            patch.dict(os.environ, {"TELEGRAM_API_ID": "12345", "TELEGRAM_API_HASH": "deadbeef"}),
            patch("telethon.TelegramClient", mock_cls),
        ):
            asyncio.run(main())

        mock_client = mock_cls.return_value
        mock_client.send_code_request.assert_not_called()
        mock_client.sign_in.assert_not_called()

    def test_prints_user_info(self):
        me = MagicMock(first_name="Bob", phone="+15559876543")
        mock_cls = MagicMock(return_value=_make_client(authorized=True, me=me))
        with (
            patch.dict(os.environ, {"TELEGRAM_API_ID": "12345", "TELEGRAM_API_HASH": "deadbeef"}),
            patch("telethon.TelegramClient", mock_cls),
            patch("builtins.print") as mock_print,
        ):
            asyncio.run(main())

        mock_print.assert_called_once_with("Authenticated as: Bob (+15559876543)")

    def test_disconnect_called(self):
        mock_cls = MagicMock(return_value=_make_client(authorized=True))
        with (
            patch.dict(os.environ, {"TELEGRAM_API_ID": "12345", "TELEGRAM_API_HASH": "deadbeef"}),
            patch("telethon.TelegramClient", mock_cls),
        ):
            asyncio.run(main())

        mock_cls.return_value.disconnect.assert_awaited_once()


class TestMainNotAuthorized:
    """When the user is not yet authorized, run the code-request flow."""

    def test_sends_code_and_signs_in(self):
        me = MagicMock(first_name="Carol", phone="+15550001111")
        mock_cls = MagicMock(return_value=_make_client(authorized=False, me=me))
        with (
            patch.dict(os.environ, {"TELEGRAM_API_ID": "99", "TELEGRAM_API_HASH": "abc123"}),
            patch("telethon.TelegramClient", mock_cls),
            patch("sys.argv", ["telegram_auth", "+15550001111", "54321"]),
        ):
            asyncio.run(main())

        client = mock_cls.return_value
        client.send_code_request.assert_awaited_once_with("+15550001111")
        client.sign_in.assert_awaited_once_with("+15550001111", "54321")

    def test_handles_missing_user_attrs(self):
        """User object with no first_name/phone should print 'unknown'."""
        me = MagicMock(spec=[])
        mock_cls = MagicMock(return_value=_make_client(authorized=True, me=me))
        with (
            patch.dict(os.environ, {"TELEGRAM_API_ID": "1", "TELEGRAM_API_HASH": "x"}),
            patch("telethon.TelegramClient", mock_cls),
            patch("builtins.print") as mock_print,
        ):
            asyncio.run(main())

        mock_print.assert_called_once_with("Authenticated as: unknown (unknown)")

    def test_session_dir_created(self):
        """SESSION_DIR.mkdir is called via Path.mkdir."""
        mock_cls = MagicMock(return_value=_make_client(authorized=True))
        with (
            patch.dict(os.environ, {"TELEGRAM_API_ID": "1", "TELEGRAM_API_HASH": "x"}),
            patch("telethon.TelegramClient", mock_cls),
            patch.object(Path, "mkdir") as mock_mkdir,
        ):
            asyncio.run(main())

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


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
