"""Tests for metabolon/enzymes/electroreception.py — iMessage reader."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.electroreception import (
    ElectroreceptionResult,
    _extract_text,
    electroreception_read,
)


# ---------------------------------------------------------------------------
# _extract_text
# ---------------------------------------------------------------------------

class TestExtractText:
    """Unit tests for _extract_text helper."""

    def test_none_blob_returns_none(self):
        assert _extract_text(None) is None

    def test_empty_blob_returns_none(self):
        assert _extract_text(b"") is None

    def test_plain_text_blob(self):
        blob = b"Hello, world"
        result = _extract_text(blob)
        assert result == "Hello, world"

    def test_extracts_text_from_attributed_body(self):
        # Simulated attributedBody: control-char separated runs with metadata junk
        blob = b"streamtyped\x00NSString\x06Hello there\x0bNSFont\x01NSColor"
        result = _extract_text(blob)
        assert result == "Hello there"

    def test_skips_short_runs(self):
        # All runs are < 3 chars after stripping
        blob = b"ab\x00cd\x01ef"
        assert _extract_text(blob) is None

    def test_strips_plus_prefix(self):
        # Runs starting with "+\x00" get prefix removed (starts with "+", len > 2)
        blob = b"+\x00\x00My message text\x00NSObject"
        result = _extract_text(blob)
        # After + stripping: "My message text"
        assert result is not None
        assert "My message text" in result

    def test_all_metadata_returns_none(self):
        blob = b"NSString\x00NSObject\x00NSDictionary"
        assert _extract_text(blob) is None

    def test_unicode_content(self):
        blob = "Café résumé".encode("utf-8")
        result = _extract_text(blob)
        assert "Café" in result

    def test_returns_first_valid_run(self):
        blob = b"NSFont\x00\x00First good\x00NSNumber\x00Second good"
        result = _extract_text(blob)
        assert result == "First good"


# ---------------------------------------------------------------------------
# electroreception_read — DB not found
# ---------------------------------------------------------------------------

class TestElectroreceptionReadNoDb:
    """When chat.db does not exist."""

    @patch("metabolon.enzymes.electroreception.os.path.exists", return_value=False)
    def test_returns_error_when_db_missing(self, mock_exists):
        result = electroreception_read()
        assert isinstance(result, ElectroreceptionResult)
        assert result.count == 0
        assert len(result.messages) == 1
        assert "error" in result.messages[0]
        assert "chat.db not found" in result.messages[0]["error"]


# ---------------------------------------------------------------------------
# electroreception_read — with mock DB
# ---------------------------------------------------------------------------

def _make_in_memory_db(rows: list[tuple]) -> sqlite3.Connection:
    """Create an in-memory SQLite DB that mimics the chat.db query shape.

    rows: list of (rowid, dt, sender, text, attributedBody, is_from_me)
    """
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE message (
            rowid INTEGER PRIMARY KEY,
            date INTEGER,
            text TEXT,
            attributedBody BLOB,
            is_from_me INTEGER,
            handle_id INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE handle (
            rowid INTEGER PRIMARY KEY,
            id TEXT
        )
        """
    )
    for i, (rowid, dt, sender, text, body, from_me) in enumerate(rows):
        # Insert a handle if sender is not 'Me'
        handle_id = 0
        if sender != "Me":
            handle_id = i + 1
            conn.execute(
                "INSERT INTO handle (rowid, id) VALUES (?, ?)",
                (handle_id, sender),
            )
        # Apple NSDate: (unix_timestamp - 978307200) * 1e9
        # We store a plausible integer; the SQL formats it.
        conn.execute(
            "INSERT INTO message (rowid, date, text, attributedBody, is_from_me, handle_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (rowid, 700000000000000000, text, body, from_me, handle_id),
        )
    conn.commit()
    return conn


class TestElectroreceptionReadWithDb:
    """When chat.db exists and returns rows."""

    SAMPLE_ROWS = [
        (1, "2025-01-01 10:00:00", "+8521234", "Hello from bank", None, 0),
        (2, "2025-01-01 11:00:00", "Me", "My reply", None, 1),
        (3, "2025-01-02 09:00:00", "+8525678", "Another message", None, 0),
        (4, "2025-01-02 10:00:00", "+8521234", "Bank OTP 123456", None, 0),
    ]

    def _run_with_mock(self, **kwargs):
        """Patch os.path.exists + sqlite3.connect to use in-memory DB."""
        mem_db = _make_in_memory_db(self.SAMPLE_ROWS)

        with (
            patch("metabolon.enzymes.electroreception.os.path.exists", return_value=True),
            patch("metabolon.enzymes.electroreception.sqlite3.connect", return_value=mem_db),
        ):
            result = electroreception_read(**kwargs)
        return result

    def test_basic_fetch(self):
        result = self._run_with_mock()
        assert isinstance(result, ElectroreceptionResult)
        assert result.count == len(result.messages)
        assert result.count == 4

    def test_limit(self):
        result = self._run_with_mock(limit=2)
        assert result.count == 2

    def test_incoming_only(self):
        result = self._run_with_mock(incoming_only=True)
        assert all(not m["from_me"] for m in result.messages)
        # Row 2 is from_me=1, so should be excluded
        assert result.count == 3

    def test_sender_filter(self):
        result = self._run_with_mock(sender="+8521234")
        assert result.count == 2
        assert all("+8521234" in m["sender"] for m in result.messages)

    def test_query_filter(self):
        result = self._run_with_mock(query="OTP")
        assert result.count == 1
        assert "OTP" in result.messages[0]["text"]

    def test_query_filter_case_insensitive(self):
        result = self._run_with_mock(query="otp")
        assert result.count == 1

    def test_empty_result(self):
        result = self._run_with_mock(query="nonexistent_xyz")
        assert result.count == 0
        assert result.messages == []

    def test_result_fields(self):
        result = self._run_with_mock(limit=1)
        msg = result.messages[0]
        assert "dt" in msg
        assert "sender" in msg
        assert "text" in msg
        assert "from_me" in msg

    def test_text_falls_back_to_attributed_body(self):
        """When text is NULL but attributedBody has content, extract from blob."""
        rows = [
            (1, "2025-01-01 10:00:00", "+8529999", None, b"Extracted text here", 0),
        ]
        mem_db = _make_in_memory_db(rows)
        # Patch _extract_text to return known value
        with (
            patch("metabolon.enzymes.electroreception.os.path.exists", return_value=True),
            patch("metabolon.enzymes.electroreception.sqlite3.connect", return_value=mem_db),
            patch(
                "metabolon.enzymes.electroreception._extract_text",
                return_value="Extracted text here",
            ),
        ):
            result = electroreception_read()

        assert result.count == 1
        assert result.messages[0]["text"] == "Extracted text here"

    def test_skips_rows_with_no_content(self):
        """Rows where both text and _extract_text(body) are None are skipped."""
        rows = [
            (1, "2025-01-01 10:00:00", "+8529999", None, None, 0),
            (2, "2025-01-01 11:00:00", "Me", "Visible", None, 1),
        ]
        mem_db = _make_in_memory_db(rows)
        with (
            patch("metabolon.enzymes.electroreception.os.path.exists", return_value=True),
            patch("metabolon.enzymes.electroreception.sqlite3.connect", return_value=mem_db),
            patch("metabolon.enzymes.electroreception._extract_text", return_value=None),
        ):
            result = electroreception_read()

        assert result.count == 1
        assert result.messages[0]["text"] == "Visible"
