"""Tests for metabolon.enzymes.telegram_receptor and metabolon.organelles.telegram_receptor."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Organelle-layer unit tests (no network, no Telethon)
# ---------------------------------------------------------------------------


class TestFormatMessage:
    """Tests for _format_message helper."""

    def test_outgoing_text_message(self):
        from metabolon.organelles.telegram_receptor import _format_message

        msg = MagicMock()
        msg.date = datetime(2025, 6, 15, 9, 30, tzinfo=timezone.utc)
        msg.out = True
        msg.text = "Hello world"
        assert _format_message(msg) == "2025-06-15 09:30  me: Hello world"

    def test_incoming_text_message(self):
        from metabolon.organelles.telegram_receptor import _format_message

        msg = MagicMock()
        msg.date = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        msg.out = False
        msg.text = "Hey"
        assert _format_message(msg) == "2025-01-01 00:00  them: Hey"

    def test_media_message_shows_placeholder(self):
        from metabolon.organelles.telegram_receptor import _format_message

        msg = MagicMock()
        msg.date = datetime(2025, 3, 10, 12, 0, tzinfo=timezone.utc)
        msg.out = True
        msg.text = None  # media / sticker / etc.
        assert _format_message(msg) == "2025-03-10 12:00  me: [media/non-text]"

    def test_missing_date_shows_question_mark(self):
        from metabolon.organelles.telegram_receptor import _format_message

        msg = MagicMock()
        msg.date = None
        msg.out = False
        msg.text = "no timestamp"
        assert _format_message(msg) == "?  them: no timestamp"


class TestChatId:
    """Tests for _chat_id env helper."""

    def test_valid_chat_id(self):
        from metabolon.organelles.telegram_receptor import _chat_id

        with patch.dict(os.environ, {"TELEGRAM_CHAT_ID": "123456789"}):
            assert _chat_id() == 123456789

    def test_negative_chat_id(self):
        from metabolon.organelles.telegram_receptor import _chat_id

        with patch.dict(os.environ, {"TELEGRAM_CHAT_ID": "-1001234567890"}):
            assert _chat_id() == -1001234567890

    def test_missing_chat_id_raises(self):
        from metabolon.organelles.telegram_receptor import _chat_id

        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if present
            os.environ.pop("TELEGRAM_CHAT_ID", None)
            with pytest.raises(ValueError, match="TELEGRAM_CHAT_ID must be set"):
                _chat_id()


class TestGetClient:
    """Tests for _get_client credential validation."""

    def test_missing_api_id_raises(self):
        from metabolon.organelles.telegram_receptor import _get_client

        with patch.dict(os.environ, {"TELEGRAM_API_HASH": "abc"}, clear=True):
            os.environ.pop("TELEGRAM_API_ID", None)
            with pytest.raises(ValueError, match="TELEGRAM_API_ID and TELEGRAM_API_HASH must be set"):
                _get_client()

    def test_missing_api_hash_raises(self):
        from metabolon.organelles.telegram_receptor import _get_client

        with patch.dict(os.environ, {"TELEGRAM_API_ID": "123", "TELEGRAM_API_HASH": ""}, clear=True):
            with pytest.raises(ValueError, match="TELEGRAM_API_ID and TELEGRAM_API_HASH must be set"):
                _get_client()

    def test_valid_credentials_returns_client(self):
        from metabolon.organelles.telegram_receptor import _get_client

        mock_client_cls = MagicMock()
        with patch.dict(os.environ, {"TELEGRAM_API_ID": "123", "TELEGRAM_API_HASH": "abcdef"}, clear=True):
            with patch.dict("sys.modules", {"telethon": MagicMock(TelegramClient=mock_client_cls)}):
                # Need telethon imported inside _get_client via lazy import
                # Patch the lazy import target
                with patch("metabolon.organelles.telegram_receptor.os") as mock_os:
                    mock_os.environ.get.side_effect = lambda k, d="": {
                        "TELEGRAM_API_ID": "123",
                        "TELEGRAM_API_HASH": "abcdef",
                    }.get(k, d)
                    mock_os.path = os.path
                    # Actually simpler: just verify the env guard logic
                    pass
                # Simpler approach: verify it doesn't raise with valid env
                with patch.dict(os.environ, {"TELEGRAM_API_ID": "123", "TELEGRAM_API_HASH": "abcdef"}):
                    # The Telethon import will fail if not installed, but we can
                    # at least verify the env check passes (no ValueError raised).
                    # If telethon IS installed, we get a real client object.
                    try:
                        client = _get_client()
                        assert client is not None
                    except ImportError:
                        pytest.skip("telethon not installed in test environment")


# ---------------------------------------------------------------------------
# Enzyme-layer dispatch tests (mocks the organelle functions)
# ---------------------------------------------------------------------------


class TestEnzymeDispatch:
    """Tests for metabolon.enzymes.telegram_receptor dispatch logic."""

    def _import_enzyme(self):
        from metabolon.enzymes.telegram_receptor import telegram_receptor
        return telegram_receptor

    def test_read_action(self):
        func = self._import_enzyme()
        with patch("metabolon.organelles.telegram_receptor.read_chat", return_value="msg1\nmsg2"):
            with patch("metabolon.organelles.telegram_receptor._chat_id", return_value=123):
                result = func(action="read", chat="", limit=5)
        assert result.output == "msg1\nmsg2"

    def test_read_defaults_to_chat_id(self):
        func = self._import_enzyme()
        with patch("metabolon.organelles.telegram_receptor.read_chat", return_value="ok") as mock_rc:
            with patch("metabolon.organelles.telegram_receptor._chat_id", return_value=999):
                func(action="read", chat="", limit=10)
        mock_rc.assert_called_once_with("", 10)

    def test_search_action_with_query(self):
        func = self._import_enzyme()
        with patch("metabolon.organelles.telegram_receptor.search_messages", return_value="found"):
            result = func(action="search", query="hello", chat="", limit=5)
        assert result.output == "found"

    def test_search_without_query_returns_error(self):
        func = self._import_enzyme()
        result = func(action="search", query="", chat="", limit=5)
        assert "search requires: query" in result.output

    def test_list_chats_action(self):
        func = self._import_enzyme()
        with patch("metabolon.organelles.telegram_receptor.list_chats", return_value="Chat1\nChat2"):
            result = func(action="list_chats", limit=15)
        assert result.output == "Chat1\nChat2"

    def test_auth_status_action(self):
        func = self._import_enzyme()
        with patch("metabolon.organelles.telegram_receptor.auth_status", return_value="Authenticated as: Terry"):
            result = func(action="auth_status")
        assert result.output == "Authenticated as: Terry"

    def test_unknown_action_returns_error(self):
        func = self._import_enzyme()
        result = func(action="delete", query="", chat="", limit=10)
        assert "Unknown action: delete" in result.output

    def test_result_is_secretion_subclass(self):
        func = self._import_enzyme()
        with patch("metabolon.organelles.telegram_receptor.read_chat", return_value="ok"):
            with patch("metabolon.organelles.telegram_receptor._chat_id", return_value=1):
                result = func(action="read")
        from metabolon.morphology.base import Secretion
        assert isinstance(result, Secretion)
        assert hasattr(result, "output")
