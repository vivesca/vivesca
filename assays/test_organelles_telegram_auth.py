"""Tests for metabolon.organelles.telegram_auth."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.organelles.telegram_auth import SESSION_DIR, SESSION_NAME, main

# ── Constants ──────────────────────────────────────────────────────────


class TestConstants:
    def test_session_dir_is_under_home_config(self):
        assert Path.home() / ".config" / "telethon" == SESSION_DIR

    def test_session_name(self):
        assert SESSION_NAME == "vivesca"

    def test_session_dir_is_a_path(self):
        assert isinstance(SESSION_DIR, Path)

    def test_session_name_is_str(self):
        assert isinstance(SESSION_NAME, str)


# ── main() ─────────────────────────────────────────────────────────────


def _make_mock_client(authorized: bool = True):
    """Build a fully-mocked TelegramClient replacement."""
    client = AsyncMock()
    client.is_user_authorized = AsyncMock(return_value=authorized)

    me = MagicMock()
    me.first_name = "Alice"
    me.phone = "+15551234567"
    client.get_me = AsyncMock(return_value=me)

    client.send_code_request = AsyncMock()
    client.sign_in = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    return client


class TestMainAlreadyAuthorized:
    """When the session is already authorized, no code request or sign-in."""

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "deadbeef",
        },
    )
    @patch("sys.argv", ["telegram_auth"])
    def test_prints_user_info(self):
        client = _make_mock_client(authorized=True)
        with patch("telethon.TelegramClient", return_value=client):
            with patch("builtins.print") as mock_print:
                asyncio.run(main())

        mock_print.assert_called_once_with("Authenticated as: Alice (+15551234567)")

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "deadbeef",
        },
    )
    @patch("sys.argv", ["telegram_auth"])
    def test_connects_and_disconnects(self):
        client = _make_mock_client(authorized=True)
        with patch("telethon.TelegramClient", return_value=client):
            asyncio.run(main())

        client.connect.assert_awaited_once()
        client.disconnect.assert_awaited_once()

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "deadbeef",
        },
    )
    @patch("sys.argv", ["telegram_auth"])
    def test_no_code_request_when_authorized(self):
        client = _make_mock_client(authorized=True)
        with patch("telethon.TelegramClient", return_value=client):
            asyncio.run(main())

        client.send_code_request.assert_not_awaited()
        client.sign_in.assert_not_awaited()

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "deadbeef",
        },
    )
    @patch("sys.argv", ["telegram_auth"])
    def test_session_path_passed_to_client(self):
        client = _make_mock_client(authorized=True)
        with patch("telethon.TelegramClient", return_value=client) as Tc:
            asyncio.run(main())

        expected_session = str(SESSION_DIR / SESSION_NAME)
        Tc.assert_called_once_with(expected_session, 12345, "deadbeef")


class TestMainUnauthorizedFromArgv:
    """Unauthorized session; phone and code supplied via argv."""

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "deadbeef",
        },
    )
    @patch("sys.argv", ["telegram_auth", "+15550000001", "54321"])
    def test_sends_code_and_signs_in(self):
        client = _make_mock_client(authorized=False)
        with patch("telethon.TelegramClient", return_value=client):
            asyncio.run(main())

        client.send_code_request.assert_awaited_once_with("+15550000001")
        client.sign_in.assert_awaited_once_with("+15550000001", "54321")

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "deadbeef",
        },
    )
    @patch("sys.argv", ["telegram_auth", "+15550000001", "54321"])
    def test_prints_info_after_sign_in(self):
        client = _make_mock_client(authorized=False)
        with patch("telethon.TelegramClient", return_value=client):
            with patch("builtins.print") as mock_print:
                asyncio.run(main())

        mock_print.assert_called_once_with("Authenticated as: Alice (+15551234567)")


class TestMainUnauthorizedFromInput:
    """Unauthorized session; phone and code supplied via input()."""

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "deadbeef",
        },
    )
    @patch("sys.argv", ["telegram_auth"])
    def test_prompts_for_phone_and_code(self):
        client = _make_mock_client(authorized=False)
        with patch("telethon.TelegramClient", return_value=client):
            with patch("builtins.input", side_effect=["+15550000099", "99887"]):
                asyncio.run(main())

        client.send_code_request.assert_awaited_once_with("+15550000099")
        client.sign_in.assert_awaited_once_with("+15550000099", "99887")


class TestMainMissingEnvVars:
    """Missing required env vars should raise KeyError."""

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_HASH": "deadbeef",
        },
    )
    @patch("sys.argv", ["telegram_auth"])
    def test_missing_api_id_raises_key_error(self):
        with pytest.raises(KeyError, match="TELEGRAM_API_ID"):
            with patch("telethon.TelegramClient"):
                asyncio.run(main())

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_ID": "12345",
        },
    )
    @patch("sys.argv", ["telegram_auth"])
    def test_missing_api_hash_raises_key_error(self):
        with pytest.raises(KeyError, match="TELEGRAM_API_HASH"):
            with patch("telethon.TelegramClient"):
                asyncio.run(main())


class TestMainSessionDirCreation:
    """Session directory should be created if it doesn't exist."""

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "deadbeef",
        },
    )
    @patch("sys.argv", ["telegram_auth"])
    def test_creates_session_dir(self):
        client = _make_mock_client(authorized=True)
        mock_dir = MagicMock()
        mock_dir.__truediv__ = MagicMock(return_value=Path("/tmp/fake/session"))
        with patch("telethon.TelegramClient", return_value=client):
            with patch("metabolon.organelles.telegram_auth.SESSION_DIR", mock_dir):
                asyncio.run(main())

        mock_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestMainFallbackNames:
    """When get_me() returns None-ish attributes, fallback to 'unknown'."""

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "deadbeef",
        },
    )
    @patch("sys.argv", ["telegram_auth"])
    def test_missing_first_name_falls_back(self):
        client = _make_mock_client(authorized=True)
        me = MagicMock()
        me.first_name = None
        me.phone = "+15551234567"
        client.get_me = AsyncMock(return_value=me)

        with patch("telethon.TelegramClient", return_value=client):
            with patch("builtins.print") as mock_print:
                asyncio.run(main())

        mock_print.assert_called_once_with("Authenticated as: unknown (+15551234567)")

    @patch(
        "metabolon.organelles.telegram_auth.os.environ",
        {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "deadbeef",
        },
    )
    @patch("sys.argv", ["telegram_auth"])
    def test_missing_phone_falls_back(self):
        client = _make_mock_client(authorized=True)
        me = MagicMock()
        me.first_name = "Bob"
        me.phone = None
        client.get_me = AsyncMock(return_value=me)

        with patch("telethon.TelegramClient", return_value=client):
            with patch("builtins.print") as mock_print:
                asyncio.run(main())

        mock_print.assert_called_once_with("Authenticated as: Bob (unknown)")
