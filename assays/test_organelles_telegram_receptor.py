from __future__ import annotations

"""Tests for metabolon.organelles.telegram_receptor."""

import asyncio
import os
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.organelles.telegram_receptor import (
    SESSION_DIR,
    SESSION_NAME,
    _auth_check_async,
    _format_message,
    _get_client,
    _list_chats_async,
    _read_chat_async,
    _run,
    _search_async,
    auth_status,
    list_chats,
    read_chat,
    search_messages,
)


# ---------------------------------------------------------------------------
# _format_message
# ---------------------------------------------------------------------------


class TestFormatMessage:
    """Test _format_message with various message shapes."""

    def test_outgoing_message(self):
        msg = SimpleNamespace(
            date=datetime(2025, 3, 14, 9, 30, tzinfo=timezone.utc),
            out=True,
            text="Hello world",
        )
        assert _format_message(msg) == "2025-03-14 09:30  me: Hello world"

    def test_incoming_message(self):
        msg = SimpleNamespace(
            date=datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc),
            out=False,
            text="Reply",
        )
        assert _format_message(msg) == "2025-01-01 00:00  them: Reply"

    def test_no_date(self):
        msg = SimpleNamespace(date=None, out=True, text="No date msg")
        assert _format_message(msg) == "?  me: No date msg"

    def test_media_non_text(self):
        msg = SimpleNamespace(
            date=datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc),
            out=False,
            text=None,
        )
        assert _format_message(msg) == "2025-06-15 12:00  them: [media/non-text]"

    def test_empty_text(self):
        msg = SimpleNamespace(
            date=datetime(2025, 7, 4, 18, 30, tzinfo=timezone.utc),
            out=True,
            text="",
        )
        # empty string is falsy, so should show media placeholder
        assert _format_message(msg) == "2025-07-04 18:30  me: [media/non-text]"


# ---------------------------------------------------------------------------
# _get_client
# ---------------------------------------------------------------------------


class TestGetClient:
    """Test _get_client credential validation."""

    @patch("metabolon.organelles.telegram_receptor.os.environ.get")
    @patch("metabolon.organelles.telegram_receptor.SESSION_DIR", new_callable=lambda: MagicMock)
    def test_raises_on_missing_api_id(self, mock_dir, mock_env):
        """ValueError when TELEGRAM_API_ID is unset or zero."""
        mock_env.side_effect = lambda k, d="": {"TELEGRAM_API_ID": "0", "TELEGRAM_API_HASH": "abc"}.get(k, d)
        with pytest.raises(ValueError, match="TELEGRAM_API_ID"):
            _get_client()

    @patch("metabolon.organelles.telegram_receptor.os.environ.get")
    def test_raises_on_missing_api_hash(self, mock_env):
        """ValueError when TELEGRAM_API_HASH is empty."""
        mock_env.side_effect = lambda k, d="": {"TELEGRAM_API_ID": "12345", "TELEGRAM_API_HASH": ""}.get(k, d)
        with pytest.raises(ValueError, match="TELEGRAM_API_HASH"):
            _get_client()

    @patch("telethon.TelegramClient")
    @patch("metabolon.organelles.telegram_receptor.os.environ.get")
    def test_creates_client_with_valid_creds(self, mock_env, mock_client_cls):
        """Returns a TelegramClient when creds are present."""
        mock_env.side_effect = lambda k, d="": {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "deadbeef",
        }.get(k, d)
        mock_client_cls.return_value = MagicMock(name="client")
        client = _get_client()
        assert client is mock_client_cls.return_value
        # Session path should contain SESSION_DIR / SESSION_NAME
        call_args = mock_client_cls.call_args
        assert SESSION_NAME in call_args[0][0]
        assert call_args[0][1] == 12345  # int(api_id)
        assert call_args[0][2] == "deadbeef"


# ---------------------------------------------------------------------------
# _run helper
# ---------------------------------------------------------------------------


class TestRun:
    """Test the _run event-loop bridge."""

    def test_runs_coroutine_no_existing_loop(self):
        """When no loop is running, _run uses asyncio.run directly."""

        async def coro():
            return 42

        result = _run(coro())
        assert result == 42

    def test_runs_coroutine_with_running_loop(self):
        """When a loop IS running, _run dispatches to a thread pool."""

        async def coro():
            return 99

        async def outer():
            # We're inside a running loop — _run should use ThreadPoolExecutor
            return _run(coro())

        result = asyncio.run(outer())
        assert result == 99


# ---------------------------------------------------------------------------
# _read_chat_async
# ---------------------------------------------------------------------------


class TestReadChatAsync:
    """Test _read_chat_async with mocked client."""

    def _make_mock_client(self, messages):
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.get_entity = AsyncMock(return_value=MagicMock(name="entity"))
        client.get_messages = AsyncMock(return_value=messages)
        return client

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_returns_formatted_messages(self, mock_get_client):
        msgs = [
            SimpleNamespace(
                date=datetime(2025, 3, 14, 9, 0, tzinfo=timezone.utc),
                out=False,
                text="Hi",
            ),
            SimpleNamespace(
                date=datetime(2025, 3, 14, 9, 1, tzinfo=timezone.utc),
                out=True,
                text="Hello",
            ),
        ]
        mock_get_client.return_value = self._make_mock_client(msgs)
        result = asyncio.run(_read_chat_async("test_chat", limit=10))
        assert "them: Hi" in result
        assert "me: Hello" in result
        # reversed(msgs): [Hello, Hi] — oldest first after reversal
        lines = result.split("\n")
        assert lines[0].endswith("me: Hello")
        assert lines[1].endswith("them: Hi")

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_no_messages(self, mock_get_client):
        mock_get_client.return_value = self._make_mock_client([])
        result = asyncio.run(_read_chat_async("empty_chat"))
        assert result == "No messages found"

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_passes_limit_to_get_messages(self, mock_get_client):
        client = self._make_mock_client([])
        mock_get_client.return_value = client
        asyncio.run(_read_chat_async("chat", limit=5))
        client.get_messages.assert_called_once()
        assert client.get_messages.call_args.kwargs.get("limit") == 5 or client.get_messages.call_args[1].get("limit") == 5


# ---------------------------------------------------------------------------
# _search_async
# ---------------------------------------------------------------------------


class TestSearchAsync:
    """Test _search_async with mocked client."""

    def _make_mock_client(self, messages):
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.get_entity = AsyncMock(return_value=MagicMock(name="entity"))
        client.get_messages = AsyncMock(return_value=messages)
        return client

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_search_with_chat_scope(self, mock_get_client):
        msgs = [
            SimpleNamespace(
                date=datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc),
                out=True,
                text="found it",
            ),
        ]
        client = self._make_mock_client(msgs)
        mock_get_client.return_value = client
        result = asyncio.run(_search_async("found", chat="my_chat"))
        assert "me: found it" in result
        client.get_entity.assert_called_once_with("my_chat")

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_search_without_chat_scope(self, mock_get_client):
        msgs = [
            SimpleNamespace(
                date=datetime(2025, 2, 1, 0, 0, tzinfo=timezone.utc),
                out=False,
                text="global result",
            ),
        ]
        client = self._make_mock_client(msgs)
        mock_get_client.return_value = client
        result = asyncio.run(_search_async("global"))
        assert "them: global result" in result
        # get_entity should NOT have been called
        client.get_entity.assert_not_called()
        # get_messages called with entity=None
        call_kwargs = client.get_messages.call_args
        assert call_kwargs[0][0] is None  # first positional = entity

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_search_no_results(self, mock_get_client):
        client = self._make_mock_client([])
        mock_get_client.return_value = client
        result = asyncio.run(_search_async("nonexistent"))
        assert result == "No messages matching 'nonexistent'"


# ---------------------------------------------------------------------------
# _list_chats_async
# ---------------------------------------------------------------------------


class TestListChatsAsync:
    """Test _list_chats_async with mocked client."""

    def _make_mock_client(self, dialogs):
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.get_dialogs = AsyncMock(return_value=dialogs)
        return client

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_lists_dialogs_with_unread(self, mock_get_client):
        dialogs = [
            SimpleNamespace(name="Alice", id=1, unread_count=3),
            SimpleNamespace(name="Bob", id=2, unread_count=0),
        ]
        client = self._make_mock_client(dialogs)
        mock_get_client.return_value = client
        result = asyncio.run(_list_chats_async(limit=10))
        lines = result.split("\n")
        assert "Alice [3 unread]" in lines[0]
        assert "Bob" in lines[1]
        assert "unread" not in lines[1]

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_dialog_with_no_name_uses_id(self, mock_get_client):
        dialogs = [SimpleNamespace(name=None, id=42, unread_count=0)]
        client = self._make_mock_client(dialogs)
        mock_get_client.return_value = client
        result = asyncio.run(_list_chats_async())
        assert "42" in result

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_no_dialogs(self, mock_get_client):
        client = self._make_mock_client([])
        mock_get_client.return_value = client
        result = asyncio.run(_list_chats_async())
        assert result == "No chats"

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_passes_limit(self, mock_get_client):
        client = self._make_mock_client([])
        mock_get_client.return_value = client
        asyncio.run(_list_chats_async(limit=5))
        client.get_dialogs.assert_called_once_with(limit=5)


# ---------------------------------------------------------------------------
# _auth_check_async
# ---------------------------------------------------------------------------


class TestAuthCheckAsync:
    """Test _auth_check_async with mocked client."""

    def _make_mock_client(self, me_result):
        client = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.get_me = AsyncMock(return_value=me_result)
        return client

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_authenticated(self, mock_get_client):
        me = SimpleNamespace(first_name="Terry", phone="+15551234567")
        client = self._make_mock_client(me)
        mock_get_client.return_value = client
        result = asyncio.run(_auth_check_async())
        assert "Authenticated as: Terry (+15551234567)" == result

    @patch("metabolon.organelles.telegram_receptor._get_client")
    def test_not_authenticated(self, mock_get_client):
        client = self._make_mock_client(None)
        mock_get_client.return_value = client
        result = asyncio.run(_auth_check_async())
        assert "Not authenticated" in result


# ---------------------------------------------------------------------------
# Public sync API wrappers — verify they delegate to _run + correct async fn
# ---------------------------------------------------------------------------


class TestPublicSyncAPI:
    """Test that public sync functions invoke the right async coroutines."""

    @patch("metabolon.organelles.telegram_receptor._run")
    @patch("metabolon.organelles.telegram_receptor._read_chat_async")
    def test_read_chat_delegates(self, mock_async, mock_run):
        mock_run.return_value = "some output"
        result = read_chat(chat="me", limit=5)
        mock_run.assert_called_once()
        mock_async.assert_called_once_with("me", 5)
        assert result == "some output"

    @patch("metabolon.organelles.telegram_receptor._run")
    @patch("metabolon.organelles.telegram_receptor._search_async")
    def test_search_messages_delegates(self, mock_async, mock_run):
        mock_run.return_value = "search output"
        result = search_messages(query="test", chat="ch", limit=10)
        mock_async.assert_called_once_with("test", "ch", 10)
        assert result == "search output"

    @patch("metabolon.organelles.telegram_receptor._run")
    @patch("metabolon.organelles.telegram_receptor._list_chats_async")
    def test_list_chats_delegates(self, mock_async, mock_run):
        mock_run.return_value = "chat list"
        result = list_chats(limit=15)
        mock_async.assert_called_once_with(15)
        assert result == "chat list"

    @patch("metabolon.organelles.telegram_receptor._run")
    @patch("metabolon.organelles.telegram_receptor._auth_check_async")
    def test_auth_status_delegates(self, mock_async, mock_run):
        mock_run.return_value = "auth ok"
        result = auth_status()
        mock_async.assert_called_once()
        assert result == "auth ok"


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify module constants are sensible."""

    def test_session_dir_under_home_config(self):
        assert ".config/telethon" in str(SESSION_DIR)

    def test_session_name(self):
        assert SESSION_NAME == "vivesca"
