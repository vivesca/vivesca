"""Tests for gap_junction enzyme — edge cases and param coverage."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from metabolon.enzymes.gap_junction import (
    gap_junction,
    GapJunctionResult,
    GAP_JUNCTION_CONTACTS,
)


# ── helpers ──────────────────────────────────────────────────────────

def _result(**kwargs) -> GapJunctionResult:
    return gap_junction(**kwargs)


# ── return type consistency ──────────────────────────────────────────

class TestReturnType:
    """Every code path must return a GapJunctionResult."""

    def test_unknown_returns_result_type(self):
        r = _result(action="bogus")
        assert isinstance(r, GapJunctionResult)

    @patch("metabolon.organelles.gap_junction.receive_signals", return_value="ok")
    def test_read_returns_result_type(self, _):
        assert isinstance(_result(action="read", name="x"), GapJunctionResult)

    @patch("metabolon.organelles.gap_junction.search_signals", return_value="ok")
    def test_search_returns_result_type(self, _):
        assert isinstance(_result(action="search", query="x"), GapJunctionResult)

    @patch("metabolon.organelles.gap_junction.compose_signal", return_value="ok")
    def test_draft_returns_result_type(self, _):
        assert isinstance(_result(action="draft", name="x", message="y"), GapJunctionResult)

    @patch("metabolon.organelles.gap_junction.active_junctions", return_value="ok")
    def test_list_chats_returns_result_type(self, _):
        assert isinstance(_result(action="list_chats"), GapJunctionResult)

    @patch("metabolon.organelles.gap_junction.junction_status", return_value="ok")
    def test_sync_status_returns_result_type(self, _):
        assert isinstance(_result(action="sync_status"), GapJunctionResult)


# ── whitespace / case handling on action ─────────────────────────────

class TestActionNormalization:
    def test_whitespace_stripped_read(self):
        with patch("metabolon.organelles.gap_junction.receive_signals", return_value="msg") as m:
            r = _result(action="  read  ", name="tara")
            m.assert_called_once()

    def test_whitespace_stripped_search(self):
        with patch("metabolon.organelles.gap_junction.search_signals", return_value="x") as m:
            r = _result(action=" search ", query="hi")
            m.assert_called_once()

    def test_mixed_case_draft(self):
        with patch("metabolon.organelles.gap_junction.compose_signal", return_value="x") as m:
            r = _result(action="DrAfT", name="tara", message="hi")
            m.assert_called_once_with("tara", "hi")

    def test_empty_string_action(self):
        r = _result(action="")
        assert "Unknown action" in r.output


# ── default limit propagation ────────────────────────────────────────

class TestDefaultLimit:
    """Ensure limit=20 (the default) is forwarded to organelle functions."""

    @patch("metabolon.organelles.gap_junction.receive_signals", return_value="x")
    def test_read_default_limit(self, m):
        _result(action="read", name="tara")
        m.assert_called_once_with("tara", 20)

    @patch("metabolon.organelles.gap_junction.search_signals", return_value="x")
    def test_search_default_limit(self, m):
        _result(action="search", query="hi")
        m.assert_called_once_with("hi", "", 20)

    @patch("metabolon.organelles.gap_junction.active_junctions", return_value="x")
    def test_list_chats_default_limit(self, m):
        _result(action="list_chats")
        m.assert_called_once_with(20)


# ── GAP_JUNCTION_CONTACTS prefix coverage ───────────────────────────

class TestContactPrefix:
    """Every name in GAP_JUNCTION_CONTACTS should get the [gap_junction] prefix."""

    @pytest.mark.parametrize("contact", sorted(GAP_JUNCTION_CONTACTS))
    @patch("metabolon.organelles.gap_junction.receive_signals", return_value="msg")
    def test_known_contact_gets_prefix(self, _, contact):
        r = _result(action="read", name=contact)
        assert r.output.startswith("[gap_junction] ")

    @patch("metabolon.organelles.gap_junction.receive_signals", return_value="msg")
    def test_case_insensitive_contact_match(self, _):
        """Contact lookup should be case-insensitive."""
        r = _result(action="read", name="TARA")
        assert "[gap_junction] " in r.output

    @patch("metabolon.organelles.gap_junction.receive_signals", return_value="msg")
    def test_unknown_contact_no_prefix(self, _):
        r = _result(action="read", name="unknown_person")
        assert "[gap_junction]" not in r.output


# ── validation edge cases ────────────────────────────────────────────

class TestValidation:
    def test_read_empty_string_name(self):
        r = _result(action="read", name="")
        assert r.output == "read requires: name"

    def test_search_empty_query(self):
        r = _result(action="search", query="")
        assert r.output == "search requires: query"

    def test_draft_empty_name_nonempty_message(self):
        r = _result(action="draft", name="", message="hi")
        assert r.output == "draft requires: name, message"

    def test_draft_nonempty_name_empty_message(self):
        r = _result(action="draft", name="tara", message="")
        assert r.output == "draft requires: name, message"


# ── unknown action lists all valid actions ───────────────────────────

class TestUnknownActionMessage:
    def test_message_contains_all_actions(self):
        r = _result(action="explode")
        for a in ("read", "search", "draft", "list_chats", "sync_status"):
            assert a in r.output

    def test_message_echoes_bad_action(self):
        r = _result(action="explode")
        assert "explode" in r.output
