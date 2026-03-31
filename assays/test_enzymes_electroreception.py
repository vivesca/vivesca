"""Tests for metabolon.enzymes.electroreception — iMessage/SMS reader.

Covers _extract_text blob parsing, electroreception_read with all filter
combinations, edge cases for limit/days/sender/query, and result model shape.
"""
from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helper: build an in-memory chat.db with the expected schema
# ---------------------------------------------------------------------------

def _make_db(rows: list[tuple], handles: list[tuple] | None = None):
    """Return an in-memory sqlite3 connection mimicking chat.db.

    rows: list of (rowid, date_apple_ns, is_from_me, text, body_bytes|None, handle_id)
    handles: list of (rowid, id)
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE handle (rowid INTEGER PRIMARY KEY, id TEXT)")
    conn.execute(
        "CREATE TABLE message ("
        "  rowid INTEGER PRIMARY KEY, date INTEGER, is_from_me INTEGER, "
        "  text TEXT, attributedBody BLOB, handle_id INTEGER)"
    )
    for h in handles or []:
        conn.execute("INSERT INTO handle VALUES (?, ?)", h)
    for r in rows:
        conn.execute("INSERT INTO message VALUES (?, ?, ?, ?, ?, ?)", r)
    conn.commit()
    return conn


def _apple_ns(days_ago: int = 0) -> int:
    """Apple NSDate in nanoseconds (epoch = 2001-01-01)."""
    ts = (datetime.now() - timedelta(days=days_ago)).timestamp()
    return int((ts - 978307200) * 1_000_000_000)


# ---------------------------------------------------------------------------
# _extract_text unit tests
# ---------------------------------------------------------------------------

class TestExtractText:
    """Unit tests for _extract_text(blob)."""

    def test_none_returns_none(self):
        from metabolon.enzymes.electroreception import _extract_text
        assert _extract_text(None) is None

    def test_empty_bytes_returns_none(self):
        from metabolon.enzymes.electroreception import _extract_text
        assert _extract_text(b"") is None

    def test_plain_text_blob(self):
        from metabolon.enzymes.electroreception import _extract_text
        assert _extract_text(b"Simple message text") == "Simple message text"

    def test_blob_with_metadata_prefix_stripped(self):
        """AttributedString blobs have metadata before actual text."""
        from metabolon.enzymes.electroreception import _extract_text
        # Simulate: control chars separate metadata from content
        blob = b"NSString\x01\x02streamtyped\x03\x04Hello from blob"
        result = _extract_text(blob)
        assert result == "Hello from blob"

    def test_blob_only_metadata_returns_none(self):
        from metabolon.enzymes.electroreception import _extract_text
        blob = b"NSObject\x01NSDictionary\x02NSAttributed"
        assert _extract_text(blob) is None

    def test_blob_with_plus_prefix_stripped(self):
        """Strings starting with '+' followed by space get prefix removed."""
        from metabolon.enzymes.electroreception import _extract_text
        blob = b"\x01\x02+ Hello plus"
        result = _extract_text(blob)
        assert result == "Hello plus"

    def test_blob_with_short_run_skipped(self):
        """Runs shorter than 3 chars after strip are ignored."""
        from metabolon.enzymes.electroreception import _extract_text
        blob = b"ab\x01real message here"
        result = _extract_text(blob)
        assert result == "real message here"

    def test_blob_with_classname_keywords_skipped(self):
        """Runs containing $classname, $classes etc. are metadata."""
        from metabolon.enzymes.electroreception import _extract_text
        blob = b"$classname\x01\x02real content\x03$classes"
        result = _extract_text(blob)
        assert result == "real content"

    def test_blob_kIM_keyword_skipped(self):
        from metabolon.enzymes.electroreception import _extract_text
        blob = b"__kIMMessagePartTimeStamp\x01\x02Actual text"
        result = _extract_text(blob)
        assert result == "Actual text"

    def test_unreadable_bytes_handled_gracefully(self):
        """Non-UTF-8 bytes with ignore errors should not crash."""
        from metabolon.enzymes.electroreception import _extract_text
        blob = b"\xff\xfe\x01\x02valid text part"
        result = _extract_text(blob)
        # Should not raise; result is whatever survives decode+filter
        assert isinstance(result, (str, type(None)))


# ---------------------------------------------------------------------------
# electroreception_read integration tests (mocked sqlite3)
# ---------------------------------------------------------------------------

class TestElectroreceptionRead:
    """Tests for electroreception_read with mocked DB connection."""

    def test_missing_db_returns_error(self):
        from metabolon.enzymes.electroreception import electroreception_read
        with patch("os.path.exists", return_value=False):
            result = electroreception_read()
        assert result.count == 0
        assert len(result.messages) == 1
        assert "error" in result.messages[0]

    def test_basic_read(self):
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        db = _make_db(
            [(1, ns, 0, "Hello World", None, 1)],
            handles=[(1, "+85212345678")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read(limit=10)
        assert result.count == 1
        assert result.messages[0]["text"] == "Hello World"
        assert result.messages[0]["sender"] == "+85212345678"
        assert result.messages[0]["from_me"] is False

    def test_from_me_shows_as_sender_me(self):
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        db = _make_db(
            [(1, ns, 1, "Sent by me", None, 1)],
            handles=[(1, "+85212345678")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read()
        assert result.messages[0]["sender"] == "Me"
        assert result.messages[0]["from_me"] is True

    def test_no_handle_shows_unknown(self):
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        db = _make_db(
            [(1, ns, 0, "No handle", None, 999)],  # handle_id 999 doesn't exist
            handles=[(1, "+85212345678")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read()
        assert result.messages[0]["sender"] == "Unknown"

    def test_limit_enforced(self):
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        rows = [(i, ns, 0, f"Msg {i}", None, 1) for i in range(1, 11)]
        db = _make_db(rows, handles=[(1, "someone")])
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read(limit=3)
        assert result.count == 3

    def test_sender_filter(self):
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        db = _make_db(
            [
                (1, ns, 0, "From bank", None, 1),
                (2, ns, 0, "From friend", None, 2),
            ],
            handles=[(1, "MoxBank"), (2, "friend")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read(sender="MoxBank")
        assert result.count == 1
        assert "MoxBank" in result.messages[0]["sender"]

    def test_sender_with_single_quote_sanitized(self):
        """Single quotes in sender should be escaped, not cause SQL error."""
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        db = _make_db(
            [(1, ns, 0, "Test", None, 1)],
            handles=[(1, "O'Brien")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            # Should not raise
            result = electroreception_read(sender="O'Brien")
        assert isinstance(result.count, int)

    def test_query_filter(self):
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        db = _make_db(
            [
                (1, ns, 0, "Hello World", None, 1),
                (2, ns, 0, "Goodbye World", None, 1),
            ],
            handles=[(1, "someone")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read(query="Goodbye")
        assert result.count == 1
        assert "Goodbye" in result.messages[0]["text"]

    def test_query_filter_case_insensitive(self):
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        db = _make_db(
            [(1, ns, 0, "UPPERCASE text", None, 1)],
            handles=[(1, "someone")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read(query="uppercase")
        assert result.count == 1

    def test_incoming_only_excludes_sent(self):
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        db = _make_db(
            [
                (1, ns, 0, "Incoming", None, 1),
                (2, ns, 1, "Outgoing", None, 1),
            ],
            handles=[(1, "someone")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read(incoming_only=True)
        assert result.count == 1
        assert result.messages[0]["from_me"] is False

    def test_days_filter_excludes_old_messages(self):
        from metabolon.enzymes.electroreception import electroreception_read
        recent_ns = _apple_ns(0)     # today
        old_ns = _apple_ns(10)       # 10 days ago
        db = _make_db(
            [
                (1, recent_ns, 0, "Recent", None, 1),
                (2, old_ns, 0, "Old", None, 1),
            ],
            handles=[(1, "someone")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read(days=5)
        assert result.count == 1
        assert result.messages[0]["text"] == "Recent"

    def test_days_zero_means_no_filter(self):
        from metabolon.enzymes.electroreception import electroreception_read
        old_ns = _apple_ns(365)  # 1 year ago
        db = _make_db(
            [(1, old_ns, 0, "Old message", None, 1)],
            handles=[(1, "someone")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read(days=0)
        assert result.count == 1

    def test_attributedBody_fallback(self):
        """When text is NULL, _extract_text is called on attributedBody."""
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        body = b"Blob message content"
        db = _make_db(
            [(1, ns, 0, None, body, 1)],
            handles=[(1, "someone")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read()
        assert result.count == 1
        assert "Blob message content" in result.messages[0]["text"]

    def test_message_with_no_text_or_body_skipped(self):
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        db = _make_db(
            [(1, ns, 0, None, None, 1)],
            handles=[(1, "someone")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read()
        assert result.count == 0
        assert result.messages == []

    def test_empty_db_returns_empty_result(self):
        from metabolon.enzymes.electroreception import electroreception_read
        db = _make_db([], handles=[])
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read()
        assert result.count == 0
        assert result.messages == []

    def test_combined_filters(self):
        """sender + days + incoming_only all applied together."""
        from metabolon.enzymes.electroreception import electroreception_read
        recent_ns = _apple_ns(0)
        db = _make_db(
            [
                (1, recent_ns, 0, "Bank alert", None, 1),
                (2, recent_ns, 1, "My reply", None, 1),
                (3, recent_ns, 0, "Other person", None, 2),
            ],
            handles=[(1, "MoxBank"), (2, "friend")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read(
                sender="MoxBank", days=1, incoming_only=True
            )
        assert result.count == 1
        assert result.messages[0]["text"] == "Bank alert"

    def test_result_model_structure(self):
        """ElectroreceptionResult has messages list and count int."""
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        db = _make_db(
            [(1, ns, 0, "Test", None, 1)],
            handles=[(1, "someone")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read()
        assert hasattr(result, "messages")
        assert hasattr(result, "count")
        assert isinstance(result.messages, list)
        assert isinstance(result.count, int)
        assert result.count == len(result.messages)
        msg = result.messages[0]
        assert "dt" in msg
        assert "sender" in msg
        assert "text" in msg
        assert "from_me" in msg

    def test_query_skips_message_with_no_content_match(self):
        from metabolon.enzymes.electroreception import electroreception_read
        ns = _apple_ns(0)
        db = _make_db(
            [(1, ns, 0, "Alpha beta gamma", None, 1)],
            handles=[(1, "someone")],
        )
        with patch("os.path.exists", return_value=True), \
             patch("sqlite3.connect", return_value=db):
            result = electroreception_read(query="zzzzz")
        assert result.count == 0
        assert result.messages == []
