"""Tests for telegram_receptor enzyme — dispatch, validation, and param forwarding."""

from __future__ import annotations

from unittest.mock import patch

from metabolon.enzymes.telegram_receptor import (
    TelegramResult,
    telegram_receptor,
)

# ── helpers ──────────────────────────────────────────────────────────


def _call(**kwargs) -> TelegramResult:
    return telegram_receptor(**kwargs)


# ── return type consistency ──────────────────────────────────────────


class TestReturnType:
    """Every code path must return a TelegramResult."""

    def test_unknown_action_returns_result_type(self):
        r = _call(action="bogus")
        assert isinstance(r, TelegramResult)

    @patch("metabolon.organelles.telegram_receptor.read_chat", return_value="ok")
    def test_read_returns_result_type(self, _):
        assert isinstance(_call(action="read"), TelegramResult)

    @patch("metabolon.organelles.telegram_receptor.search_messages", return_value="ok")
    def test_search_returns_result_type(self, _):
        assert isinstance(_call(action="search", query="hello"), TelegramResult)

    @patch("metabolon.organelles.telegram_receptor.list_chats", return_value="ok")
    def test_list_chats_returns_result_type(self, _):
        assert isinstance(_call(action="list_chats"), TelegramResult)

    @patch("metabolon.organelles.telegram_receptor.auth_status", return_value="ok")
    def test_auth_status_returns_result_type(self, _):
        assert isinstance(_call(action="auth_status"), TelegramResult)


# ── action normalization ─────────────────────────────────────────────


class TestActionNormalization:
    def test_whitespace_stripped_read(self):
        with patch("metabolon.organelles.telegram_receptor.read_chat", return_value="msg") as m:
            _call(action="  read  ", chat="me")
            m.assert_called_once()

    def test_whitespace_stripped_search(self):
        with patch(
            "metabolon.organelles.telegram_receptor.search_messages", return_value="x"
        ) as m:
            _call(action=" search ", query="hi")
            m.assert_called_once()

    def test_mixed_case_action(self):
        with patch("metabolon.organelles.telegram_receptor.auth_status", return_value="ok") as m:
            _call(action="AuTh_StAtUs")
            m.assert_called_once()

    def test_uppercase_list_chats(self):
        with patch("metabolon.organelles.telegram_receptor.list_chats", return_value="chats") as m:
            _call(action="LIST_CHATS")
            m.assert_called_once()

    def test_empty_string_action(self):
        r = _call(action="")
        assert "Unknown action" in r.output


# ── read action ──────────────────────────────────────────────────────


class TestReadAction:
    @patch("metabolon.organelles.telegram_receptor.read_chat", return_value="chat messages")
    def test_read_default_params(self, m):
        r = _call(action="read")
        m.assert_called_once_with("me", 30)
        assert r.output == "chat messages"

    @patch("metabolon.organelles.telegram_receptor.read_chat", return_value="chat messages")
    def test_read_custom_params(self, m):
        _call(action="read", chat="general", limit=10)
        m.assert_called_once_with("general", 10)

    @patch("metabolon.organelles.telegram_receptor.read_chat", return_value="")
    def test_read_empty_result(self, _):
        r = _call(action="read")
        assert r.output == ""


# ── search action ────────────────────────────────────────────────────


class TestSearchAction:
    def test_search_without_query_returns_error(self):
        r = _call(action="search", query="")
        assert "search requires" in r.output
        assert "query" in r.output

    @patch("metabolon.organelles.telegram_receptor.search_messages", return_value="found: 3")
    def test_search_with_query_default_params(self, m):
        r = _call(action="search", query="hello")
        m.assert_called_once_with("hello", "me", 30)
        assert r.output == "found: 3"

    @patch("metabolon.organelles.telegram_receptor.search_messages", return_value="found: 0")
    def test_search_custom_chat_and_limit(self, m):
        _call(action="search", query="test", chat="devops", limit=5)
        m.assert_called_once_with("test", "devops", 5)

    def test_search_query_only_whitespace_still_has_value(self):
        """Whitespace-only query is truthy in Python, so it passes validation."""
        with patch(
            "metabolon.organelles.telegram_receptor.search_messages", return_value="ok"
        ) as m:
            _call(action="search", query="  ")
            m.assert_called_once()


# ── list_chats action ────────────────────────────────────────────────


class TestListChatsAction:
    @patch("metabolon.organelles.telegram_receptor.list_chats", return_value="Chat1\nChat2")
    def test_list_chats_default_limit(self, m):
        r = _call(action="list_chats")
        m.assert_called_once_with(30)
        assert "Chat1" in r.output

    @patch("metabolon.organelles.telegram_receptor.list_chats", return_value="No chats")
    def test_list_chats_custom_limit(self, m):
        _call(action="list_chats", limit=50)
        m.assert_called_once_with(50)

    @patch("metabolon.organelles.telegram_receptor.list_chats", return_value="No chats")
    def test_list_chats_ignores_query_param(self, m):
        """list_chats should not forward irrelevant params to organelle."""
        _call(action="list_chats", query="ignored", chat="ignored")
        m.assert_called_once_with(30)


# ── auth_status action ───────────────────────────────────────────────


class TestAuthStatusAction:
    @patch(
        "metabolon.organelles.telegram_receptor.auth_status",
        return_value="Authenticated as: Terry (+123456)",
    )
    def test_auth_status_success(self, m):
        r = _call(action="auth_status")
        m.assert_called_once_with()
        assert "Authenticated" in r.output

    @patch("metabolon.organelles.telegram_receptor.auth_status", return_value="Not authenticated")
    def test_auth_status_not_authed(self, m):
        r = _call(action="auth_status")
        assert "Not authenticated" in r.output

    @patch("metabolon.organelles.telegram_receptor.auth_status", return_value="ok")
    def test_auth_status_ignores_all_optional_params(self, m):
        _call(action="auth_status", chat="ignored", query="ignored", limit=999)
        m.assert_called_once_with()


# ── unknown action ───────────────────────────────────────────────────


class TestUnknownActionMessage:
    def test_message_contains_all_valid_actions(self):
        r = _call(action="explode")
        for a in ("read", "search", "list_chats", "auth_status"):
            assert a in r.output, f"Missing '{a}' in unknown-action message"

    def test_message_echoes_bad_action(self):
        r = _call(action="send_message")
        assert "send_message" in r.output

    def test_unknown_action_output_format(self):
        r = _call(action="foo")
        assert r.output.startswith("Unknown action:")


# ── TelegramResult is a proper model ─────────────────────────────────


class TestTelegramResultModel:
    def test_output_field_populated(self):
        r = TelegramResult(output="hello")
        assert r.output == "hello"

    def test_result_is_secretion_subclass(self):
        from metabolon.morphology import Secretion

        r = TelegramResult(output="x")
        assert isinstance(r, Secretion)
