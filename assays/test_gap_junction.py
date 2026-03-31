"""Tests for gap_junction enzyme."""

import pytest
from unittest.mock import patch, MagicMock

from metabolon.enzymes.gap_junction import gap_junction, GapJunctionResult


def test_unknown_action():
    """Test unknown action returns error message."""
    result = gap_junction(action="invalid")
    assert isinstance(result, GapJunctionResult)
    assert "Unknown action" in result.output
    assert "Valid: read, search, draft, list_chats, sync_status" in result.output


def test_read_missing_name():
    """Test read without name returns error."""
    result = gap_junction(action="read")
    assert result.output == "read requires: name"


def test_search_missing_query():
    """Test search without query returns error."""
    result = gap_junction(action="search")
    assert result.output == "search requires: query"


def test_draft_missing_params():
    """Test draft missing name or message returns error."""
    result = gap_junction(action="draft")
    assert result.output == "draft requires: name, message"

    result = gap_junction(action="draft", name="tara")
    assert result.output == "draft requires: name, message"

    result = gap_junction(action="draft", message="hello")
    assert result.output == "draft requires: name, message"


@patch("metabolon.organelles.gap_junction.receive_signals")
def test_read_success(mock_receive: MagicMock):
    """Test read successfully calls receive_signals."""
    mock_receive.return_value = "2024-01-01  tara: hello\n2024-01-01  me: hi"

    result = gap_junction(action="read", name="tara", limit=10)

    mock_receive.assert_called_once_with("tara", 10)
    assert "[gap_junction] " in result.output
    assert "tara: hello" in result.output


@patch("metabolon.organelles.gap_junction.receive_signals")
def test_read_non_gap_contact(mock_receive: MagicMock):
    """Test read doesn't add prefix to non-gap-junction contacts."""
    mock_receive.return_value = "No messages found"

    result = gap_junction(action="read", name="stranger", limit=10)

    mock_receive.assert_called_once_with("stranger", 10)
    assert result.output == "No messages found"
    assert "[gap_junction]" not in result.output


@patch("metabolon.organelles.gap_junction.search_signals")
def test_search_success(mock_search: MagicMock):
    """Test search successfully calls search_signals."""
    mock_search.return_value = "2024-01-01  tara: meeting tomorrow"

    result = gap_junction(action="search", query="meeting", limit=5)

    mock_search.assert_called_once_with("meeting", "", 5)
    assert "meeting tomorrow" in result.output


@patch("metabolon.organelles.gap_junction.search_signals")
def test_search_with_name(mock_search: MagicMock):
    """Test search with name parameter passes it through."""
    mock_search.return_value = "No messages found"

    result = gap_junction(action="search", query="lunch", name="dad", limit=10)

    mock_search.assert_called_once_with("lunch", "dad", 10)
    assert result.output == "No messages found"


@patch("metabolon.organelles.gap_junction.compose_signal")
def test_draft_success(mock_compose: MagicMock):
    """Test draft successfully calls compose_signal."""
    mock_compose.return_value = "wacli send --to '123456789@s.whatsapp.net' 'hello world'"

    result = gap_junction(action="draft", name="tara", message="hello world")

    mock_compose.assert_called_once_with("tara", "hello world")
    assert "wacli send" in result.output


@patch("metabolon.organelles.gap_junction.active_junctions")
def test_list_chats(mock_active: MagicMock):
    """Test list_chats calls active_junctions with limit."""
    mock_active.return_value = "1. tara\n2. dad\n3. mum"

    result = gap_junction(action="list_chats", limit=10)

    mock_active.assert_called_once_with(10)
    assert result.output == "1. tara\n2. dad\n3. mum"


@patch("metabolon.organelles.gap_junction.junction_status")
def test_sync_status(mock_status: MagicMock):
    """Test sync_status calls junction_status."""
    mock_status.return_value = "Sync daemon is running"

    result = gap_junction(action="sync_status")

    mock_status.assert_called_once()
    assert result.output == "Sync daemon is running"


def test_case_insensitive_action():
    """Test action is case-insensitive."""
    with patch("metabolon.organelles.gap_junction.receive_signals") as mock_receive:
        mock_receive.return_value = "test"
        result = gap_junction(action="READ", name="tara")
        mock_receive.assert_called_once()
        assert result.output == "[gap_junction] test"

    with patch("metabolon.organelles.gap_junction.search_signals") as mock_search:
        mock_search.return_value = "test"
        result = gap_junction(action="Search", query="test")
        mock_search.assert_called_once()
        assert result.output == "test"
