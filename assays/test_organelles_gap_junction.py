from __future__ import annotations

"""Tests for metabolon.organelles.gap_junction — WhatsApp via wacli."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.gap_junction import (
    GAP_JUNCTION_CONTACTS,
    WACLI,
    active_junctions,
    compose_signal,
    contact_type,
    junction_status,
    receive_signals,
    resolve_jids,
    search_signals,
    sync_catchup,
    _cli,
    _dedup_sort,
    _extract_contacts,
    _extract_messages,
    _format_messages,
    _wacli,
    _wacli_json,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_run(stdout: str = "", stderr: str = "", returncode: int = 0) -> MagicMock:
    """Build a subprocess.run-like MagicMock."""
    m = MagicMock()
    m.stdout = stdout
    m.stderr = stderr
    m.returncode = returncode
    return m


# ---------------------------------------------------------------------------
# _wacli
# ---------------------------------------------------------------------------

class TestWacli:
    @patch("metabolon.organelles.gap_junction.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = _mock_run(stdout="ok\n")
        assert _wacli(["chats", "list"]) == "ok"

    @patch("metabolon.organelles.gap_junction.subprocess.run")
    def test_strips_whitespace(self, mock_run):
        mock_run.return_value = _mock_run(stdout="  hello  \n")
        assert _wacli(["x"]) == "hello"

    @patch("metabolon.organelles.gap_junction.subprocess.run")
    def test_failure_raises(self, mock_run):
        mock_run.return_value = _mock_run(stderr="boom", returncode=1)
        with pytest.raises(ValueError, match="wacli failed: boom"):
            _wacli(["bad"])

    @patch("metabolon.organelles.gap_junction.subprocess.run")
    def test_passes_timeout(self, mock_run):
        mock_run.return_value = _mock_run(stdout="")
        _wacli(["x"], timeout=30)
        _, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 30

    @patch("metabolon.organelles.gap_junction.subprocess.run")
    def test_passes_args(self, mock_run):
        mock_run.return_value = _mock_run(stdout="")
        _wacli(["sync", "status"])
        args, _ = mock_run.call_args
        assert args[0] == [WACLI, "sync", "status"]


# ---------------------------------------------------------------------------
# _wacli_json
# ---------------------------------------------------------------------------

class TestWacliJson:
    @patch("metabolon.organelles.gap_junction._wacli")
    def test_valid_json(self, mock_wacli):
        mock_wacli.return_value = '{"success": true}'
        assert _wacli_json(["contacts", "search", "tara", "--json"]) == {"success": True}

    @patch("metabolon.organelles.gap_junction._wacli")
    def test_invalid_json_returns_empty_dict(self, mock_wacli):
        mock_wacli.return_value = "not json"
        assert _wacli_json(["x"]) == {}


# ---------------------------------------------------------------------------
# _extract_messages
# ---------------------------------------------------------------------------

class TestExtractMessages:
    def test_normal_envelope(self):
        raw = {"data": {"messages": [{"MsgID": "1"}]}}
        assert _extract_messages(raw) == [{"MsgID": "1"}]

    def test_missing_messages_key(self):
        assert _extract_messages({"data": {}}) == []

    def test_none_messages(self):
        assert _extract_messages({"data": {"messages": None}}) == []

    def test_non_dict_input(self):
        assert _extract_messages("string") == []

    def test_non_dict_data(self):
        assert _extract_messages({"data": 42}) == []

    def test_missing_data_key(self):
        assert _extract_messages({}) == []


# ---------------------------------------------------------------------------
# _extract_contacts
# ---------------------------------------------------------------------------

class TestExtractContacts:
    def test_list_of_contacts(self):
        raw = {"data": [{"JID": "a@s.whatsapp.net"}, {"JID": "a@lid"}]}
        assert _extract_contacts(raw) == [{"JID": "a@s.whatsapp.net"}, {"JID": "a@lid"}]

    def test_non_list_data(self):
        assert _extract_contacts({"data": "nope"}) == []

    def test_non_dict_input(self):
        assert _extract_contacts(42) == []

    def test_missing_data_key(self):
        assert _extract_contacts({}) == []


# ---------------------------------------------------------------------------
# _dedup_sort
# ---------------------------------------------------------------------------

class TestDedupSort:
    def test_deduplicates_by_msgid(self):
        msgs = [
            {"MsgID": "a", "Timestamp": "2025-01-01"},
            {"MsgID": "a", "Timestamp": "2025-01-01"},
        ]
        assert len(_dedup_sort(msgs, 10)) == 1

    def test_sorts_descending(self):
        msgs = [
            {"MsgID": "1", "Timestamp": "2025-01-01"},
            {"MsgID": "2", "Timestamp": "2025-01-02"},
        ]
        result = _dedup_sort(msgs, 10)
        assert result[0]["MsgID"] == "2"

    def test_respects_limit(self):
        msgs = [{"MsgID": str(i), "Timestamp": f"2025-01-{i:02d}"} for i in range(1, 6)]
        assert len(_dedup_sort(msgs, 2)) == 2

    def test_skips_empty_msgid(self):
        msgs = [{"MsgID": "", "Timestamp": "2025-01-01"}, {"MsgID": "x", "Timestamp": "2025-01-02"}]
        result = _dedup_sort(msgs, 10)
        assert len(result) == 1
        assert result[0]["MsgID"] == "x"


# ---------------------------------------------------------------------------
# _format_messages
# ---------------------------------------------------------------------------

class TestFormatMessages:
    def test_formats_sent(self):
        msgs = [{"Timestamp": "2025-01-01T12:00:00Z", "FromMe": True, "Text": "hi"}]
        out = _format_messages(msgs, "tara")
        assert "me: hi" in out
        assert "2025-01-01T12:00:00" in out

    def test_formats_received(self):
        msgs = [{"Timestamp": "2025-01-01T12:00:00Z", "FromMe": False, "Text": "hello"}]
        out = _format_messages(msgs, "tara")
        assert "tara: hello" in out

    def test_empty_returns_no_messages(self):
        assert _format_messages([], "tara") == "No messages found"

    def test_truncates_timestamp(self):
        msgs = [{"Timestamp": "2025-06-15T10:30:45.12345Z", "FromMe": False, "Text": "x"}]
        out = _format_messages(msgs, "bob")
        # Should show first 19 chars of timestamp
        assert "2025-06-15T10:30:45" in out


# ---------------------------------------------------------------------------
# contact_type
# ---------------------------------------------------------------------------

class TestContactType:
    def test_known_contacts(self):
        for name in GAP_JUNCTION_CONTACTS:
            assert contact_type(name) == "gap_junction"

    def test_case_insensitive(self):
        assert contact_type("Tara") == "gap_junction"
        assert contact_type("TARA") == "gap_junction"

    def test_unknown_is_receptor(self):
        assert contact_type("boss") == "receptor"


# ---------------------------------------------------------------------------
# resolve_jids
# ---------------------------------------------------------------------------

class TestResolveJids:
    @patch("metabolon.organelles.gap_junction._wacli_json")
    def test_returns_jids(self, mock_json):
        mock_json.return_value = {
            "data": [
                {"JID": "tara@s.whatsapp.net", "Name": "tara"},
                {"JID": "tara@lid", "Name": "tara"},
            ]
        }
        result = resolve_jids("tara")
        assert result == ["tara@s.whatsapp.net", "tara@lid"]

    @patch("metabolon.organelles.gap_junction._wacli_json")
    def test_empty_when_no_contacts(self, mock_json):
        mock_json.return_value = {"data": []}
        assert resolve_jids("nobody") == []


# ---------------------------------------------------------------------------
# receive_signals
# ---------------------------------------------------------------------------

class TestReceiveSignals:
    @patch("metabolon.organelles.gap_junction._wacli_json")
    def test_merges_jid_threads(self, mock_json):
        # First call: resolve_jids → 2 JIDs
        # Next 2 calls: messages for each JID
        mock_json.side_effect = [
            {"data": [{"JID": "a@s.whatsapp.net"}, {"JID": "a@lid"}]},
            {"data": {"messages": [{"MsgID": "1", "Timestamp": "2025-01-01T10:00:00Z", "FromMe": False, "Text": "hi"}]}},
            {"data": {"messages": [{"MsgID": "2", "Timestamp": "2025-01-01T11:00:00Z", "FromMe": True, "Text": "hey"}]}},
        ]
        out = receive_signals("tara", limit=10)
        assert "tara: hi" in out
        assert "me: hey" in out

    @patch("metabolon.organelles.gap_junction._wacli_json")
    def test_no_contact_found(self, mock_json):
        mock_json.return_value = {"data": []}
        out = receive_signals("ghost")
        assert "No contact found" in out


# ---------------------------------------------------------------------------
# search_signals
# ---------------------------------------------------------------------------

class TestSearchSignals:
    @patch("metabolon.organelles.gap_junction._wacli_json")
    def test_global_search(self, mock_json):
        mock_json.return_value = {
            "data": {"messages": [{"MsgID": "s1", "Timestamp": "2025-03-01T09:00:00Z", "FromMe": False, "Text": "found it"}]}
        }
        out = search_signals("findme")
        assert "them: found it" in out

    @patch("metabolon.organelles.gap_junction._wacli_json")
    def test_scoped_to_contact(self, mock_json):
        mock_json.side_effect = [
            {"data": [{"JID": "tara@s.whatsapp.net"}]},
            {"data": {"messages": [{"MsgID": "s2", "Timestamp": "2025-03-01T09:00:00Z", "FromMe": True, "Text": "scoped"}]}},
        ]
        out = search_signals("findme", name="tara")
        assert "me: scoped" in out

    @patch("metabolon.organelles.gap_junction._wacli_json")
    def test_scoped_no_contact(self, mock_json):
        mock_json.return_value = {"data": []}
        out = search_signals("findme", name="nobody")
        assert "No contact found" in out


# ---------------------------------------------------------------------------
# compose_signal
# ---------------------------------------------------------------------------

class TestComposeSignal:
    @patch("metabolon.organelles.gap_junction._wacli_json")
    def test_generates_command(self, mock_json):
        mock_json.return_value = {"data": [{"JID": "tara@s.whatsapp.net"}]}
        out = compose_signal("tara", "hello world")
        assert "wacli send --to 'tara@s.whatsapp.net' 'hello world'" in out

    @patch("metabolon.organelles.gap_junction._wacli_json")
    def test_escapes_single_quotes(self, mock_json):
        mock_json.return_value = {"data": [{"JID": "tara@s.whatsapp.net"}]}
        out = compose_signal("tara", "it's done")
        assert "'it'\\''s done'" in out

    @patch("metabolon.organelles.gap_junction._wacli_json")
    def test_no_contact(self, mock_json):
        mock_json.return_value = {"data": []}
        out = compose_signal("ghost", "hi")
        assert out.startswith("# No contact found")


# ---------------------------------------------------------------------------
# active_junctions / junction_status / sync_catchup
# ---------------------------------------------------------------------------

class TestActiveJunctions:
    @patch("metabolon.organelles.gap_junction._wacli")
    def test_returns_output(self, mock_wacli):
        mock_wacli.return_value = "chat1\nchat2"
        assert active_junctions() == "chat1\nchat2"


class TestJunctionStatus:
    @patch("metabolon.organelles.gap_junction._wacli")
    def test_returns_status(self, mock_wacli):
        mock_wacli.return_value = "running"
        assert junction_status() == "running"


class TestSyncCatchup:
    @patch("metabolon.organelles.gap_junction._wacli")
    def test_passes_long_timeout(self, mock_wacli):
        mock_wacli.return_value = "done"
        sync_catchup()
        mock_wacli.assert_called_once_with(["sync", "--once"], timeout=120)


# ---------------------------------------------------------------------------
# _cli
# ---------------------------------------------------------------------------

class TestCli:
    @patch("metabolon.organelles.gap_junction.sync_catchup", return_value="synced")
    def test_sync_catchup_success(self, mock_sync, capsys):
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            _cli()
        assert "synced" in capsys.readouterr().out

    @patch("metabolon.organelles.gap_junction.sync_catchup", side_effect=ValueError("store is locked"))
    def test_sync_locked_exits_zero(self, mock_sync, capsys):
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            with pytest.raises(SystemExit) as exc_info:
                _cli()
        assert exc_info.value.code == 0

    @patch("metabolon.organelles.gap_junction.sync_catchup", side_effect=ValueError("other error"))
    def test_sync_other_error_exits_one(self, mock_sync):
        with patch("sys.argv", ["gap_junction", "sync", "catchup"]):
            with pytest.raises(SystemExit) as exc_info:
                _cli()
        assert exc_info.value.code == 1

    def test_bad_args_exits_two(self):
        with patch("sys.argv", ["gap_junction", "bad"]):
            with pytest.raises(SystemExit) as exc_info:
                _cli()
        assert exc_info.value.code == 2

    def test_no_args_exits_two(self):
        with patch("sys.argv", ["gap_junction"]):
            with pytest.raises(SystemExit) as exc_info:
                _cli()
        assert exc_info.value.code == 2
