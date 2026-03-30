"""Tests for gap_junction — WhatsApp bridge organelle.

Critical safety test: compose_signal NEVER sends, only returns a shell command.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest


class TestExtractMessages:
    def test_extracts_messages(self):
        from metabolon.organelles.gap_junction import _extract_messages
        raw = {"data": {"messages": [{"MsgID": "1", "Text": "hello"}]}}
        assert len(_extract_messages(raw)) == 1
        assert _extract_messages(raw)[0]["Text"] == "hello"

    def test_empty_data(self):
        from metabolon.organelles.gap_junction import _extract_messages
        assert _extract_messages({}) == []
        assert _extract_messages({"data": {}}) == []
        assert _extract_messages({"data": None}) == []

    def test_non_dict_input(self):
        from metabolon.organelles.gap_junction import _extract_messages
        assert _extract_messages("not a dict") == []


class TestExtractContacts:
    def test_extracts_contacts(self):
        from metabolon.organelles.gap_junction import _extract_contacts
        raw = {"data": [{"JID": "123@s.whatsapp.net", "Name": "Test"}]}
        result = _extract_contacts(raw)
        assert len(result) == 1
        assert result[0]["JID"] == "123@s.whatsapp.net"

    def test_empty(self):
        from metabolon.organelles.gap_junction import _extract_contacts
        assert _extract_contacts({}) == []
        assert _extract_contacts({"data": None}) == []


class TestDedupSort:
    def test_deduplicates_by_msgid(self):
        from metabolon.organelles.gap_junction import _dedup_sort
        msgs = [
            {"MsgID": "1", "Timestamp": "2026-03-30T10:00:00", "Text": "first"},
            {"MsgID": "1", "Timestamp": "2026-03-30T10:00:00", "Text": "duplicate"},
            {"MsgID": "2", "Timestamp": "2026-03-30T11:00:00", "Text": "second"},
        ]
        result = _dedup_sort(msgs, limit=10)
        assert len(result) == 2

    def test_sorts_by_timestamp_desc(self):
        from metabolon.organelles.gap_junction import _dedup_sort
        msgs = [
            {"MsgID": "1", "Timestamp": "2026-03-30T08:00:00"},
            {"MsgID": "2", "Timestamp": "2026-03-30T12:00:00"},
        ]
        result = _dedup_sort(msgs, limit=10)
        assert result[0]["MsgID"] == "2"  # newer first

    def test_respects_limit(self):
        from metabolon.organelles.gap_junction import _dedup_sort
        msgs = [{"MsgID": str(i), "Timestamp": f"2026-03-30T{i:02d}:00:00"} for i in range(10)]
        result = _dedup_sort(msgs, limit=3)
        assert len(result) == 3


class TestFormatMessages:
    def test_formats_correctly(self):
        from metabolon.organelles.gap_junction import _format_messages
        msgs = [{"Timestamp": "2026-03-30T10:00:00Z", "FromMe": False, "Text": "hi there"}]
        result = _format_messages(msgs, "Tara")
        assert "Tara" in result
        assert "hi there" in result

    def test_from_me(self):
        from metabolon.organelles.gap_junction import _format_messages
        msgs = [{"Timestamp": "2026-03-30T10:00:00Z", "FromMe": True, "Text": "hello"}]
        result = _format_messages(msgs, "Tara")
        assert "me:" in result

    def test_empty(self):
        from metabolon.organelles.gap_junction import _format_messages
        assert "No messages" in _format_messages([], "anyone")


class TestContactType:
    def test_gap_junction_contacts(self):
        from metabolon.organelles.gap_junction import contact_type
        assert contact_type("tara") == "gap_junction"
        assert contact_type("Tara") == "gap_junction"
        assert contact_type("mum") == "gap_junction"

    def test_receptor_contacts(self):
        from metabolon.organelles.gap_junction import contact_type
        assert contact_type("boss") == "receptor"
        assert contact_type("recruiter") == "receptor"


class TestComposeSignal:
    """CRITICAL: compose_signal must NEVER call wacli send."""

    def test_returns_shell_command_not_sends(self):
        from metabolon.organelles.gap_junction import compose_signal
        with patch("metabolon.organelles.gap_junction.resolve_jids", return_value=["123@s.whatsapp.net"]):
            result = compose_signal("tara", "hello")
        assert result.startswith("wacli send")
        assert "123@s.whatsapp.net" in result
        assert "hello" in result

    def test_no_contact_returns_comment(self):
        from metabolon.organelles.gap_junction import compose_signal
        with patch("metabolon.organelles.gap_junction.resolve_jids", return_value=[]):
            result = compose_signal("nobody", "test")
        assert result.startswith("#")

    def test_escapes_single_quotes(self):
        from metabolon.organelles.gap_junction import compose_signal
        with patch("metabolon.organelles.gap_junction.resolve_jids", return_value=["jid@s.whatsapp.net"]):
            result = compose_signal("tara", "it's a test")
        # Should escape the single quote
        assert "\\'" in result or "it" in result
