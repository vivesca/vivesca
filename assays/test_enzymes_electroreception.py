"""Tests for metabolon/enzymes/electroreception.py — iMessage/SMS reading."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fn():
    """Return the raw function behind the @tool decorator."""
    from metabolon.enzymes import electroreception as mod

    return mod.electroception_read


def _build_attributed_body(text: str) -> bytes:
    """Build a minimal NSAttributedString blob containing *text*.

    The real format is streamtyped but for _extract_text we only need
    the text to survive the regex split on control chars.
    """
    # Encode with a control-char separator that the regex will split on
    return f"\x01NSString\x02{text}".encode("utf-8")


# ---------------------------------------------------------------------------
# _extract_text unit tests
# ---------------------------------------------------------------------------

class TestExtractText:
    """Tests for _extract_text helper."""

    def test_none_blob_returns_none(self):
        from metabolon.enzymes.electroreception import _extract_text

        assert _extract_text(None) is None

    def test_empty_blob_returns_none(self):
        from metabolon.enzymes.electroreception import _extract_text

        assert _extract_text(b"") is None

    def test_extracts_plain_text(self):
        from metabolon.enzymes.electroreception import _extract_text

        blob = _build_attributed_body("Hello world")
        assert _extract_text(blob) == "Hello world"

    def test_skips_metadata_tokens(self):
        from metabolon.enzymes.electroreception import _extract_text

        # All runs are metadata — should return None
        blob = b"\x02NSString\x02NSDictionary\x02NSObject"
        assert _extract_text(blob) is None

    def test_short_runs_skipped(self):
        from metabolon.enzymes.electroreception import _extract_text

        # "ab" is < 3 chars but >= 2 after strip, so it should still be returned
        # Actually runs < 3 chars are skipped. A run of exactly "ab" has len 2 < 3 → skipped.
        blob = b"\x02ab\x02NSString"
        assert _extract_text(blob) is None

    def test_plus_prefix_stripped(self):
        from metabolon.enzymes.electroreception import _extract_text

        blob = b"\x02+ Hello there\x02NSString"
        result = _extract_text(blob)
        assert result == "Hello there"

    def test_returns_first_valid_text(self):
        from metabolon.enzymes.electroreception import _extract_text

        blob = b"\x02NSString\x02First match\x02Second match"
        assert _extract_text(blob) == "First match"

    def test_invalid_utf8_handled_gracefully(self):
        from metabolon.enzymes.electroreception import _extract_text

        # Garbage bytes — should not raise
        blob = b"\xff\xfe\xfd"
        # The regex split may produce nothing valid
        result = _extract_text(blob)
        # We just verify no exception; result depends on decode
        assert result is None or isinstance(result, str)


# ---------------------------------------------------------------------------
# electroreception_read — DB not found
# ---------------------------------------------------------------------------

class TestDBNotFound:
    """When chat.db does not exist."""

    def test_returns_error_message(self):
        fn = _fn()
        with patch("metabolon.enzymes.electroreception.os.path.exists", return_value=False):
            result = fn()
        assert result.count == 0
        assert len(result.messages) == 1
        assert "error" in result.messages[0]
        assert "chat.db not found" in result.messages[0]["error"]


# ---------------------------------------------------------------------------
# electroreception_read — with mock DB
# ---------------------------------------------------------------------------

class TestElectroreceptionRead:
    """Tests with an in-memory SQLite database."""

    @pytest.fixture()
    def mock_db(self, tmp_path):
        """Create a temporary chat.db and return its path."""
        db_path = tmp_path / "chat.db"
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        # macOS chat.db schema (simplified)
        cur.execute(
            """
            CREATE TABLE message (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                attributedBody BLOB,
                is_from_me INTEGER DEFAULT 0,
                handle_id INTEGER,
                date INTEGER
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE handle (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT
            )
            """
        )
        conn.commit()

        # Insert sample handles
        handles = [
            (1, "+85291234567"),
            (2, "MoxBank"),
            (3, "john@example.com"),
        ]
        cur.executemany("INSERT INTO handle (rowid, id) VALUES (?, ?)", handles)

        # Insert sample messages — date uses Apple epoch (nanoseconds since 2001-01-01)
        base = datetime(2025, 6, 15, 12, 0, 0)
        messages = [
            # (text, attributedBody, is_from_me, handle_id, date_ns_offset)
            ("Hello from MoxBank", None, 0, 2, 0),
            ("Sent message", None, 1, 1, -1_000_000_000_000),
            (None, _build_attributed_body("Blob message"), 0, 3, -2_000_000_000_000),
            ("Another from MoxBank", None, 0, 2, -3_000_000_000_000),
            (None, None, 0, 1, -4_000_000_000_000),  # empty — should be skipped
            ("Old message", None, 0, 1, -30 * 86_400_000_000_000),  # 30 days ago
        ]
        now_ns = int((base.timestamp() - 978307200) * 1_000_000_000)
        for text, body, from_me, handle_id, offset in messages:
            cur.execute(
                "INSERT INTO message (text, attributedBody, is_from_me, handle_id, date) "
                "VALUES (?, ?, ?, ?, ?)",
                (text, body, from_me, handle_id, now_ns + offset),
            )
        conn.commit()
        conn.close()
        return db_path

    def _call(self, mock_db, **kwargs):
        """Call electroreception_read with DB patched to our temp DB."""
        fn = _fn()
        db_str = str(mock_db)
        with (
            patch("metabolon.enzymes.electroreception.os.path.exists", return_value=True),
            patch("metabolon.enzymes.electroreception._DB", db_str),
        ):
            return fn(**kwargs)

    def test_basic_fetch(self, mock_db):
        result = self._call(mock_db, limit=10)
        # 4 non-empty messages (empty body+text one is skipped)
        assert result.count == 4
        assert all("dt" in m and "sender" in m and "text" in m for m in result.messages)

    def test_limit_respected(self, mock_db):
        result = self._call(mock_db, limit=2)
        assert result.count == 2

    def test_sender_filter(self, mock_db):
        result = self._call(mock_db, sender="MoxBank")
        assert result.count == 2
        assert all("MoxBank" in m["sender"] for m in result.messages)

    def test_incoming_only(self, mock_db):
        result = self._call(mock_db, incoming_only=True)
        assert result.count == 3
        assert all(not m["from_me"] for m in result.messages)

    def test_query_filter(self, mock_db):
        result = self._call(mock_db, query="Blob")
        assert result.count == 1
        assert "Blob" in result.messages[0]["text"]

    def test_query_case_insensitive(self, mock_db):
        result = self._call(mock_db, query="hello")
        assert result.count == 1
        assert "hello" in result.messages[0]["text"].lower()

    def test_from_me_sender_label(self, mock_db):
        result = self._call(mock_db, limit=10)
        sent = [m for m in result.messages if m["from_me"]]
        assert len(sent) == 1
        assert sent[0]["sender"] == "Me"

    def test_days_filter(self, mock_db):
        # Only messages from last 7 days — excludes the 30-day-old one
        # Our DB is anchored to 2025-06-15; patch datetime too
        fn = _fn()
        db_str = str(mock_db)
        fake_now = datetime(2025, 6, 15, 12, 0, 0)
        with (
            patch("metabolon.enzymes.electroreception.os.path.exists", return_value=True),
            patch("metabolon.enzymes.electroreception._DB", db_str),
            patch("metabolon.enzymes.electroreception.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            # timedelta still needs to work
            from datetime import timedelta as real_td
            mock_dt.timedelta = real_td
            result = fn(days=7)

        # Should exclude the 30-day-old message
        texts = [m["text"] for m in result.messages]
        assert "Old message" not in texts

    def test_empty_result(self, mock_db):
        result = self._call(mock_db, sender="NONEXISTENT")
        assert result.count == 0
        assert result.messages == []

    def test_result_is_electroreception_result(self, mock_db):
        from metabolon.enzymes.electroreception import ElectroreceptionResult

        result = self._call(mock_db, limit=1)
        assert isinstance(result, ElectroreceptionResult)

    def test_sender_sql_injection_safe(self, mock_db):
        """Single quotes in sender should be escaped."""
        result = self._call(mock_db, sender="MoxBank'; DROP TABLE message;--")
        # Should not crash — just return no results (no match)
        assert isinstance(result.count, int)
