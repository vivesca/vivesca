"""Tests for endosomal enzyme — Gmail triage MCP tool wrapper."""

from unittest.mock import patch, MagicMock
from metabolon.enzymes.endosomal import endosomal, EndosomalResult


def test_search_missing_query():
    result = endosomal(action="search")
    assert not result.success
    assert "query" in result.message


def test_search_success():
    with patch("metabolon.enzymes.endosomal.invoke_organelle", return_value="3 results"):
        result = endosomal(action="search", query="from:boss")
        assert isinstance(result, EndosomalResult)
        assert "3 results" in result.output


def test_thread_missing_id():
    result = endosomal(action="thread")
    assert not result.success
    assert "thread_id" in result.message


def test_thread_success():
    with patch("metabolon.enzymes.endosomal.invoke_organelle", return_value="thread content"):
        result = endosomal(action="thread", thread_id="abc123")
        assert result.output == "thread content"


def test_categorize_deterministic():
    # The enzyme imports organelles.endosomal.classify — test that path
    from metabolon.organelles.endosomal import classify
    assert classify("From: noreply@github.com\nSubject: Notification\nBody") == "archive_now"


def test_categorize_missing_text():
    result = endosomal(action="categorize")
    assert not result.success


def test_archive_missing_ids():
    result = endosomal(action="archive")
    assert not result.success


def test_archive_success():
    with patch("metabolon.enzymes.endosomal.invoke_organelle", return_value="done"):
        result = endosomal(action="archive", message_ids=["id1", "id2"])
        assert result.success


def test_mark_read_success():
    with patch("metabolon.enzymes.endosomal.invoke_organelle", return_value="done"):
        result = endosomal(action="mark_read", message_ids=["id1"])
        assert result.success


def test_label_missing_name():
    result = endosomal(action="label")
    assert not result.success


def test_label_success():
    with patch("metabolon.enzymes.endosomal.invoke_organelle", return_value="created"):
        result = endosomal(action="label", name="Important")
        assert result.success


def test_send_missing_fields():
    result = endosomal(action="send")
    assert not result.success
    assert "require" in result.message.lower()


def test_send_reply():
    with patch("metabolon.enzymes.endosomal.invoke_organelle", return_value="sent"):
        result = endosomal(action="send", reply_to_message_id="msg123")
        assert result.success


def test_filter_missing_criteria():
    result = endosomal(action="filter")
    assert not result.success


def test_filter_missing_action():
    result = endosomal(action="filter", from_sender="x@y.com")
    assert not result.success
    assert "action" in result.message.lower() or "add_label" in result.message


def test_filter_success():
    with patch("metabolon.enzymes.endosomal.invoke_organelle", return_value="filter set"):
        result = endosomal(action="filter", from_sender="x@y.com", add_label="Spam")
        assert result.success
        assert "DRY RUN" in result.message  # dry_run=True by default


def test_unknown_action():
    result = endosomal(action="explode")
    assert not result.success
    assert "Unknown" in result.message
