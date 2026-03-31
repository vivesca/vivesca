from __future__ import annotations

"""Tests for electroreception enzyme."""


import sqlite3
import time
from unittest.mock import patch

import pytest


def test_missing_db():
    """When chat.db doesn't exist, return error result."""
    from metabolon.enzymes.electroreception import electroreception_read

    with patch("os.path.exists", return_value=False):
        result = electroreception_read()
        assert result.count == 0
        assert "error" in result.messages[0]


def test_basic_read_with_mock_db():
    """Basic message retrieval with in-memory DB."""
    from metabolon.enzymes.electroreception import electroreception_read

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE handle (rowid INTEGER PRIMARY KEY, id TEXT)")
    conn.execute(
        "CREATE TABLE message (rowid INTEGER PRIMARY KEY, date INTEGER, "
        "is_from_me INTEGER, text TEXT, attributedBody BLOB, handle_id INTEGER)"
    )
    conn.execute("INSERT INTO handle VALUES (1, '+85212345678')")
    apple_ns = int((time.time() - 978307200) * 1_000_000_000)
    conn.execute(f"INSERT INTO message VALUES (1, {apple_ns}, 0, 'Hello World', NULL, 1)")
    conn.commit()

    with patch("os.path.exists", return_value=True), patch(
        "sqlite3.connect", return_value=conn
    ):
        result = electroreception_read(limit=10)
        assert result.count >= 1
        assert any("Hello World" in m.get("text", "") for m in result.messages)


def test_sender_filter():
    """Filter messages by sender substring."""
    from metabolon.enzymes.electroreception import electroreception_read

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE handle (rowid INTEGER PRIMARY KEY, id TEXT)")
    conn.execute(
        "CREATE TABLE message (rowid INTEGER PRIMARY KEY, date INTEGER, "
        "is_from_me INTEGER, text TEXT, attributedBody BLOB, handle_id INTEGER)"
    )
    conn.execute("INSERT INTO handle VALUES (1, '+85212345678')")
    conn.execute("INSERT INTO handle VALUES (2, 'MoxBank')")
    apple_ns = int((time.time() - 978307200) * 1_000_000_000)
    conn.execute(f"INSERT INTO message VALUES (1, {apple_ns}, 0, 'Hello', NULL, 1)")
    conn.execute(
        f"INSERT INTO message VALUES (2, {apple_ns}, 0, 'Transaction alert', NULL, 2)"
    )
    conn.commit()

    with patch("os.path.exists", return_value=True), patch(
        "sqlite3.connect", return_value=conn
    ):
        result = electroreception_read(sender="MoxBank")
        assert all(
            "MoxBank" in m.get("sender", "") for m in result.messages if m.get("text")
        )


def test_query_filter():
    """Filter messages by query text substring."""
    from metabolon.enzymes.electroreception import electroreception_read

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE handle (rowid INTEGER PRIMARY KEY, id TEXT)")
    conn.execute(
        "CREATE TABLE message (rowid INTEGER PRIMARY KEY, date INTEGER, "
        "is_from_me INTEGER, text TEXT, attributedBody BLOB, handle_id INTEGER)"
    )
    conn.execute("INSERT INTO handle VALUES (1, 'someone')")
    apple_ns = int((time.time() - 978307200) * 1_000_000_000)
    conn.execute(
        f"INSERT INTO message VALUES (1, {apple_ns}, 0, 'Hello World', NULL, 1)"
    )
    conn.execute(
        f"INSERT INTO message VALUES (2, {apple_ns}, 0, 'Goodbye World', NULL, 1)"
    )
    conn.commit()

    with patch("os.path.exists", return_value=True), patch(
        "sqlite3.connect", return_value=conn
    ):
        result = electroreception_read(query="Goodbye")
        assert result.count == 1
        assert "Goodbye" in result.messages[0]["text"]


def test_incoming_only():
    """incoming_only=True excludes is_from_me=1 messages."""
    from metabolon.enzymes.electroreception import electroreception_read

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE handle (rowid INTEGER PRIMARY KEY, id TEXT)")
    conn.execute(
        "CREATE TABLE message (rowid INTEGER PRIMARY KEY, date INTEGER, "
        "is_from_me INTEGER, text TEXT, attributedBody BLOB, handle_id INTEGER)"
    )
    conn.execute("INSERT INTO handle VALUES (1, 'someone')")
    apple_ns = int((time.time() - 978307200) * 1_000_000_000)
    conn.execute(
        f"INSERT INTO message VALUES (1, {apple_ns}, 0, 'Incoming', NULL, 1)"
    )
    conn.execute(
        f"INSERT INTO message VALUES (2, {apple_ns}, 1, 'Outgoing', NULL, 1)"
    )
    conn.commit()

    with patch("os.path.exists", return_value=True), patch(
        "sqlite3.connect", return_value=conn
    ):
        result = electroreception_read(incoming_only=True)
        assert all(not m.get("from_me") for m in result.messages)


def test_extract_text_helper():
    """_extract_text handles None, empty bytes, and valid text."""
    from metabolon.enzymes.electroreception import _extract_text

    assert _extract_text(None) is None
    assert _extract_text(b"") is None
    assert _extract_text(b"Hello there friend") == "Hello there friend"
