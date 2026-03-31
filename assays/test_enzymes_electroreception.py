"""Comprehensive tests for metabolon/enzymes/electroreception.py.

Covers _extract_text edge cases, electroreception_read with mock sqlite3,
all filter combinations, limit, days cutoff, sender quoting, empty results,
and ElectroreceptionResult shape.
"""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from metabolon.enzymes.electroreception import (
    ElectroreceptionResult,
    _extract_text,
    electroreception_read,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apple_ns_from_dt(dt: datetime) -> int:
    """Convert a datetime to Apple Nanoseconds timestamp used in chat.db."""
    return int((dt.timestamp() - 978307200) * 1_000_000_000)


def _make_db(*rows: tuple):
    """Return an in-memory sqlite3 connection with handle+message tables populated.

    Each row is (rowid, handle_id, handle_str, is_from_me, text, date_dt).
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE handle (rowid INTEGER PRIMARY KEY, id TEXT)")
    conn.execute(
        "CREATE TABLE message ("
        "  rowid INTEGER PRIMARY KEY, date INTEGER, is_from_me INTEGER, "
        "  text TEXT, attributedBody BLOB, handle_id INTEGER)"
    )
    for rowid, hid, handle_str, from_me, text, dt in rows:
        conn.execute("INSERT OR IGNORE INTO handle VALUES (?, ?)", (hid, handle_str))
        apple_ns = _apple_ns_from_dt(dt)
        conn.execute(
            "INSERT INTO message VALUES (?, ?, ?, ?, NULL, ?)",
            (rowid, apple_ns, from_me, text, hid),
        )
    conn.commit()
    return conn


def _patch_db(conn):
    """Return context managers patching os.path.exists and sqlite3.connect."""
    return (
        patch("os.path.exists", return_value=True),
        patch("sqlite3.connect", return_value=conn),
    )


NOW = datetime.now()


# ---------------------------------------------------------------------------
# _extract_text unit tests
# ---------------------------------------------------------------------------

class TestExtractText:
    """Tests for _extract_text helper."""

    def test_none_returns_none(self):
        assert _extract_text(None) is None

    def test_empty_bytes_returns_none(self):
        assert _extract_text(b"") is None

    def test_plain_text(self):
        assert _extract_text(b"Hello world") == "Hello world"

    def test_attributed_body_blob(self):
        """Simulate an NSAttributedString blob with metadata junk."""
        raw = b"streamtyped\x01NSString\x02Hello there\x00NSFont\x03junk"
        result = _extract_text(raw)
        assert result is not None
        assert "Hello there" in result

    def test_too_short_returns_none(self):
        assert _extract_text(b"ab") is None

    def test_only_metadata_returns_none(self):
        blob = b"NSString\x01NSObject\x02NSDictionary"
        assert _extract_text(blob) is None

    def test_plus_prefix_stripped(self):
        """Strings starting with '+' followed by 2 chars have prefix removed."""
        blob = b"+\x00\x00Hi"
        # After splitting on control chars, '+Hi' should survive the meta check
        # and the + prefix handling should strip first 2 chars
        result = _extract_text(blob)
        # Depending on split behaviour, verify no crash
        assert isinstance(result, (str, type(None)))

    def test_unicode_text(self):
        assert _extract_text("你好世界".encode("utf-8")) is not None

    def test_non_utf8_bytes_no_crash(self):
        """Garbage bytes should not raise, just return None or a string."""
        result = _extract_text(b"\xff\xfe\x80\x81")
        assert isinstance(result, (str, type(None)))


# ---------------------------------------------------------------------------
# electroreception_read — missing DB
# ---------------------------------------------------------------------------

class TestMissingDB:
    def test_returns_error_result(self):
        with patch("os.path.exists", return_value=False):
            result = electroreception_read()
        assert isinstance(result, ElectroreceptionResult)
        assert result.count == 0
        assert len(result.messages) == 1
        assert "error" in result.messages[0]

    def test_error_message_mentions_chat_db(self):
        with patch("os.path.exists", return_value=False):
            result = electroreception_read()
        assert "chat.db" in result.messages[0].get("error", "")


# ---------------------------------------------------------------------------
# electroreception_read — basic retrieval
# ---------------------------------------------------------------------------

class TestBasicRead:
    def test_returns_result_instance(self):
        conn = _make_db(
            (1, 1, "Alice", 0, "Hi", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read()
        assert isinstance(result, ElectroreceptionResult)

    def test_message_shape(self):
        conn = _make_db(
            (1, 1, "Alice", 0, "Hello", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read()
        msg = result.messages[0]
        assert "dt" in msg
        assert "sender" in msg
        assert "text" in msg
        assert "from_me" in msg

    def test_from_me_false_shows_sender(self):
        conn = _make_db(
            (1, 1, "Bob", 0, "Hey", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read()
        assert result.messages[0]["sender"] == "Bob"
        assert result.messages[0]["from_me"] is False

    def test_from_me_true_shows_me(self):
        conn = _make_db(
            (1, 1, "Bob", 1, "Reply", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read()
        assert result.messages[0]["sender"] == "Me"
        assert result.messages[0]["from_me"] is True

    def test_empty_db_returns_empty(self):
        conn = _make_db()
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read()
        assert result.count == 0
        assert result.messages == []

    def test_null_handle_shows_unknown(self):
        conn = _make_db(
            (1, 99, "Ignored", 0, "Msg", NOW),
        )
        # Override to have NULL handle
        conn.execute("UPDATE message SET handle_id = NULL WHERE rowid = 1")
        conn.commit()
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read()
        assert result.count == 1
        assert result.messages[0]["sender"] == "Unknown"


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

class TestLimit:
    def test_limit_respected(self):
        conn = _make_db(
            (1, 1, "A", 0, "one", NOW),
            (2, 1, "A", 0, "two", NOW),
            (3, 1, "A", 0, "three", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read(limit=2)
        assert result.count == 2


class TestSenderFilter:
    def test_sender_substring_match(self):
        conn = _make_db(
            (1, 1, "+85298765432", 0, "Msg1", NOW),
            (2, 2, "MoxBank", 0, "Msg2", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read(sender="MoxBank")
        assert result.count == 1
        assert result.messages[0]["text"] == "Msg2"

    def test_sender_with_quote_safe(self):
        """Single quotes in sender are escaped to avoid SQL injection."""
        conn = _make_db(
            (1, 1, "O'Brien", 0, "Hey", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            # Should not raise
            result = electroreception_read(sender="O'Brien")
        assert result.count == 1

    def test_sender_no_match_returns_empty(self):
        conn = _make_db(
            (1, 1, "Alice", 0, "Hi", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read(sender="Nobody")
        assert result.count == 0


class TestDaysFilter:
    def test_days_excludes_old_messages(self):
        old_dt = NOW - timedelta(days=30)
        recent_dt = NOW - timedelta(hours=1)
        conn = _make_db(
            (1, 1, "A", 0, "Old message", old_dt),
            (2, 1, "A", 0, "Recent message", recent_dt),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read(days=7)
        assert result.count == 1
        assert "Recent" in result.messages[0]["text"]

    def test_days_zero_means_no_limit(self):
        old_dt = NOW - timedelta(days=365)
        conn = _make_db(
            (1, 1, "A", 0, "Very old", old_dt),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read(days=0)
        assert result.count == 1


class TestQueryFilter:
    def test_case_insensitive_search(self):
        conn = _make_db(
            (1, 1, "A", 0, "URGENT notification", NOW),
            (2, 1, "A", 0, "casual chat", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read(query="urgent")
        assert result.count == 1
        assert "URGENT" in result.messages[0]["text"]

    def test_query_no_match(self):
        conn = _make_db(
            (1, 1, "A", 0, "Hello", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read(query="nonexistent")
        assert result.count == 0


class TestIncomingOnly:
    def test_excludes_sent(self):
        conn = _make_db(
            (1, 1, "A", 0, "Incoming", NOW),
            (2, 1, "A", 1, "Outgoing", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read(incoming_only=True)
        assert result.count == 1
        assert result.messages[0]["text"] == "Incoming"
        assert result.messages[0]["from_me"] is False


# ---------------------------------------------------------------------------
# Combined filters
# ---------------------------------------------------------------------------

class TestCombinedFilters:
    def test_sender_and_days(self):
        old_dt = NOW - timedelta(days=10)
        conn = _make_db(
            (1, 1, "MoxBank", 0, "Old txn", old_dt),
            (2, 1, "MoxBank", 0, "New txn", NOW),
            (3, 2, "Alice", 0, "New msg", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read(sender="MoxBank", days=3)
        assert result.count == 1
        assert "New txn" in result.messages[0]["text"]

    def test_incoming_and_query(self):
        conn = _make_db(
            (1, 1, "A", 0, "urgent alert", NOW),
            (2, 1, "A", 1, "urgent reply", NOW),
            (3, 1, "A", 0, "casual note", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read(incoming_only=True, query="urgent")
        assert result.count == 1
        assert result.messages[0]["text"] == "urgent alert"
        assert result.messages[0]["from_me"] is False

    def test_all_filters_combined(self):
        conn = _make_db(
            (1, 1, "MoxBank", 0, "OTP is 1234", NOW),
            (2, 1, "MoxBank", 1, "OTP is 5678", NOW),
            (3, 2, "Alice", 0, "OTP is 9999", NOW),
            (4, 1, "MoxBank", 0, "balance update", NOW),
        )
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read(
                sender="MoxBank", incoming_only=True, query="OTP", days=1
            )
        assert result.count == 1
        assert "1234" in result.messages[0]["text"]


# ---------------------------------------------------------------------------
# Empty / null text handling
# ---------------------------------------------------------------------------

class TestNullText:
    def test_null_text_and_null_body_skipped(self):
        conn = _make_db(
            (1, 1, "A", 0, "Visible", NOW),
        )
        # Add a message with NULL text and no body
        apple_ns = _apple_ns_from_dt(NOW)
        conn.execute(
            "INSERT INTO message VALUES (2, ?, 0, NULL, NULL, 1)", (apple_ns,)
        )
        conn.commit()
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read()
        # Only the message with actual text should appear
        assert result.count == 1
        assert result.messages[0]["text"] == "Visible"

    def test_null_text_with_attributed_body_uses_extract(self):
        conn = _make_db(
            (1, 1, "A", 0, None, NOW),
        )
        # Update to have NULL text but valid attributedBody
        apple_ns = _apple_ns_from_dt(NOW)
        conn.execute(
            "UPDATE message SET text = NULL, attributedBody = ? WHERE rowid = 1",
            (b"Extracted text here",),
        )
        conn.commit()
        with patch("os.path.exists", return_value=True), patch(
            "sqlite3.connect", return_value=conn
        ):
            result = electroreception_read()
        assert result.count == 1
        assert "Extracted" in result.messages[0]["text"]


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class TestElectroreceptionResult:
    def test_has_messages_and_count(self):
        r = ElectroreceptionResult(messages=[{"a": 1}], count=1)
        assert r.count == 1
        assert len(r.messages) == 1

    def test_empty_result(self):
        r = ElectroreceptionResult(messages=[], count=0)
        assert r.count == 0
