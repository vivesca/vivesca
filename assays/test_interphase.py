from __future__ import annotations

"""Tests for metabolon.pinocytosis.interphase — evening routine gather."""

import json
import sys
from unittest.mock import patch

from metabolon.pinocytosis.interphase import (
    _SCRIPT_GATHERERS,
    SECTION_ORDER,
    intake,
    intake_email_threads,
    intake_emails,
    intake_emails_archived,
    intake_prospective,
    intake_reminders,
    intake_whatsapp,
    main,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MODULE = "metabolon.pinocytosis.interphase"


def _make_gatherers(exc_key=None):
    """Build a dict of mock gatherer functions. Optionally raise for one key."""
    results = {
        "emails": {"label": "Unread Emails", "ok": True, "content": "none"},
        "emails_archived": {"label": "Archived", "ok": True, "content": "none"},
        "whatsapp": {"label": "WhatsApp", "ok": True, "content": "none"},
        "reminders": {"label": "Reminders", "ok": True, "content": "none"},
        "email_threads": {"label": "Threads", "ok": True, "content": "none"},
        "prospective": {"label": "Prospective", "ok": True, "content": "none"},
    }

    def _make_fn(result):
        return lambda: result

    def _make_exc():
        return lambda: (_ for _ in ()).throw(RuntimeError("boom"))

    gatherers = {}
    for key, val in results.items():
        gatherers[key] = _make_exc() if key == exc_key else _make_fn(val)
    return gatherers


# ---------------------------------------------------------------------------
# intake_emails
# ---------------------------------------------------------------------------


class TestIntakeEmails:
    @patch(f"{MODULE}.run_cmd")
    def test_success(self, mock_run):
        mock_run.return_value = (True, "From: alice@example.com\nSubject: Hello")
        result = intake_emails()
        assert result["ok"] is True
        assert "alice" in result["content"]
        assert result["label"] == "Unread Emails (inbox)"
        mock_run.assert_called_once()

    @patch(f"{MODULE}.run_cmd")
    def test_failure_falls_back_to_search(self, mock_run):
        mock_run.side_effect = [
            (False, "some error"),
            (True, "From: bob@example.com\nSubject: Fallback"),
        ]
        result = intake_emails()
        assert result["ok"] is True
        assert "bob" in result["content"]
        assert mock_run.call_count == 2

    @patch(f"{MODULE}.run_cmd")
    def test_timeout_does_not_fallback(self, mock_run):
        mock_run.return_value = (False, "[timed out after 30s]")
        result = intake_emails()
        assert result["ok"] is False
        assert "timed out" in result["content"]
        mock_run.assert_called_once()

    @patch(f"{MODULE}.run_cmd")
    def test_empty_output(self, mock_run):
        mock_run.return_value = (True, "")
        result = intake_emails()
        assert result["ok"] is True
        assert result["content"] == "(none)"


# ---------------------------------------------------------------------------
# intake_emails_archived
# ---------------------------------------------------------------------------


class TestIntakeEmailsArchived:
    @patch(f"{MODULE}.run_cmd")
    def test_success(self, mock_run):
        mock_run.return_value = (True, "From: cora@service.com\nSubject: Digest")
        result = intake_emails_archived()
        assert result["ok"] is True
        assert "cora" in result["content"]
        assert "Archived" in result["label"]

    @patch(f"{MODULE}.run_cmd")
    def test_empty_output(self, mock_run):
        mock_run.return_value = (True, "")
        result = intake_emails_archived()
        assert result["content"] == "(none)"


# ---------------------------------------------------------------------------
# intake_whatsapp
# ---------------------------------------------------------------------------


class TestIntakeWhatsApp:
    @patch(f"{MODULE}.run_cmd")
    def test_success(self, mock_run):
        mock_run.return_value = (True, "Mom: Don't forget dinner")
        result = intake_whatsapp()
        assert result["ok"] is True
        assert "dinner" in result["content"]
        assert "last 24h" in result["label"]

    @patch(f"{MODULE}.run_cmd")
    def test_messages_fail_chats_succeed(self, mock_run):
        mock_run.side_effect = [
            (False, "wacli error"),
            (True, "Mom\nDad\nAlice"),
        ]
        result = intake_whatsapp()
        assert result["ok"] is True
        assert "recent chats" in result["label"]

    @patch(f"{MODULE}.run_cmd")
    def test_both_fail_returns_first_error(self, mock_run):
        mock_run.side_effect = [
            (False, "messages error"),
            (False, "chats error"),
        ]
        result = intake_whatsapp()
        assert result["ok"] is False
        assert result["content"] == "messages error"


# ---------------------------------------------------------------------------
# intake_reminders
# ---------------------------------------------------------------------------


class TestIntakeReminders:
    @patch(f"{MODULE}.run_cmd")
    def test_pacemaker_success(self, mock_run):
        mock_run.return_value = (True, "Buy milk\nCall dentist")
        result = intake_reminders()
        assert result["ok"] is True
        assert "pacemaker" in result["label"]
        assert "Buy milk" in result["content"]

    @patch(f"{MODULE}.run_cmd")
    def test_pacemaker_fails_due_fallback(self, mock_run):
        mock_run.side_effect = [
            (False, "not found"),
            (True, "Task 1\nTask 2"),
        ]
        result = intake_reminders()
        assert result["ok"] is True
        assert result["label"] == "Due Reminders"
        assert "Task 1" in result["content"]

    @patch(f"{MODULE}.run_cmd")
    def test_both_fail_nonempty_output(self, mock_run):
        """Both fail with non-empty stderr — content is the last error string."""
        mock_run.side_effect = [
            (False, "no pacemaker"),
            (False, "no due"),
        ]
        result = intake_reminders()
        assert result["ok"] is False
        assert result["content"] == "no due"

    @patch(f"{MODULE}.run_cmd")
    def test_both_fail_empty_output(self, mock_run):
        """Both fail with empty output → fallback to (none)."""
        mock_run.side_effect = [
            (False, ""),
            (False, ""),
        ]
        result = intake_reminders()
        assert result["ok"] is False
        assert result["content"] == "(none)"


# ---------------------------------------------------------------------------
# intake_email_threads
# ---------------------------------------------------------------------------


class TestIntakeEmailThreads:
    @patch(f"{MODULE}.read_file")
    def test_success(self, mock_read):
        mock_read.return_value = (True, "Thread 1: awaiting reply\nThread 2: closed")
        result = intake_email_threads()
        assert result["ok"] is True
        assert "Thread 1" in result["content"]
        assert result["label"] == "Email Threads Tracker"

    @patch(f"{MODULE}.read_file")
    def test_file_missing(self, mock_read):
        mock_read.return_value = (False, "[file not found: ...]")
        result = intake_email_threads()
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# intake_prospective
# ---------------------------------------------------------------------------


class TestIntakeProspective:
    @patch(f"{MODULE}.read_file")
    def test_success(self, mock_read):
        mock_read.return_value = (True, "Follow up with Bob on Thursday")
        result = intake_prospective()
        assert result["ok"] is True
        assert "Bob" in result["content"]
        assert "Prospective" in result["label"]

    @patch(f"{MODULE}.read_file")
    def test_file_missing(self, mock_read):
        mock_read.return_value = (False, "[file not found: ...]")
        result = intake_prospective()
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# Section ordering & gatherer registry
# ---------------------------------------------------------------------------


class TestSectionOrder:
    def test_all_script_gatherers_in_section_order(self):
        for key in _SCRIPT_GATHERERS:
            assert key in SECTION_ORDER, f"{key} missing from SECTION_ORDER"

    def test_section_order_has_standard_keys(self):
        expected = [
            "datetime",
            "emails",
            "emails_archived",
            "whatsapp",
            "calendar_today",
            "calendar_tomorrow",
            "todo",
            "now",
            "budget",
            "reminders",
            "email_threads",
            "prospective",
        ]
        assert expected == SECTION_ORDER


class TestScriptGatherers:
    def test_all_six_gatherers_registered(self):
        assert set(_SCRIPT_GATHERERS.keys()) == {
            "emails",
            "emails_archived",
            "whatsapp",
            "reminders",
            "email_threads",
            "prospective",
        }


# ---------------------------------------------------------------------------
# intake (full pipeline)
# ---------------------------------------------------------------------------


def _fake_intake_context(**kwargs):
    return {
        "date": {"datetime": "2026-03-31 11:27", "date": "2026-03-31", "weekday": "Tuesday"},
        "todo": {"available": True, "items": [{"raw": "Task A", "done": False}]},
        "now": {"available": True, "raw": "state: active"},
        "budget": {"available": True, "raw": "spent: $5"},
        "calendar": None,
    }


def _fake_calendar(date, days=1):
    return {"available": True, "raw": f"Event at 10am ({date})", "events": [], "error": None}


def _fake_transduce(ctx, calendar_keys=None):
    return {
        "datetime": {"label": "Current Date / Time", "ok": True, "content": "2026-03-31 11:27"},
        "calendar_today": {"label": "Today's Calendar", "ok": True, "content": "Event at 10am"},
        "calendar_tomorrow": {"label": "Tomorrow's Calendar", "ok": True, "content": "No events"},
        "todo": {"label": "Praxis.md", "ok": True, "content": "- [ ] Task A"},
        "now": {"label": "Tonus (current state)", "ok": True, "content": "state: active"},
        "budget": {"label": "Budget", "ok": True, "content": "spent: $5"},
    }


class TestIntake:
    """Tests for intake() — patches _SCRIPT_GATHERERS with a real dict."""

    @patch(f"{MODULE}.transduce", side_effect=_fake_transduce)
    @patch(f"{MODULE}.sense_calendar", side_effect=_fake_calendar)
    @patch(f"{MODULE}.intake_context", side_effect=_fake_intake_context)
    @patch(f"{MODULE}._SCRIPT_GATHERERS", _make_gatherers())
    def test_json_output(self, mock_ctx, mock_cal, mock_trans):
        result = intake(as_json=True)
        parsed = json.loads(result)
        assert "datetime" in parsed
        assert "emails" in parsed
        assert "prospective" in parsed

    @patch(f"{MODULE}.transduce", side_effect=_fake_transduce)
    @patch(f"{MODULE}.sense_calendar", side_effect=_fake_calendar)
    @patch(f"{MODULE}.intake_context", side_effect=_fake_intake_context)
    @patch(f"{MODULE}._SCRIPT_GATHERERS", _make_gatherers())
    def test_text_output(self, mock_ctx, mock_cal, mock_trans):
        result = intake(as_json=False)
        assert "INTERPHASE CONTEXT BRIEF" in result
        assert "END OF INTERPHASE" in result

    @patch(f"{MODULE}.transduce", side_effect=_fake_transduce)
    @patch(f"{MODULE}.sense_calendar", side_effect=_fake_calendar)
    @patch(f"{MODULE}.intake_context", side_effect=_fake_intake_context)
    @patch(f"{MODULE}._SCRIPT_GATHERERS", _make_gatherers())
    def test_ordering_preserved(self, mock_ctx, mock_cal, mock_trans):
        result = intake(as_json=True)
        parsed = json.loads(result)
        keys = list(parsed.keys())
        assert keys == SECTION_ORDER

    @patch(f"{MODULE}.transduce", side_effect=_fake_transduce)
    @patch(f"{MODULE}.sense_calendar", side_effect=_fake_calendar)
    @patch(f"{MODULE}.intake_context", side_effect=_fake_intake_context)
    @patch(f"{MODULE}._SCRIPT_GATHERERS", _make_gatherers(exc_key="emails"))
    def test_gatherer_error_handled(self, mock_ctx, mock_cal, mock_trans):
        """A gatherer exception should be caught, not propagated."""
        result = intake(as_json=True)
        parsed = json.loads(result)
        assert "emails" in parsed
        assert "gatherer error" in parsed["emails"]["content"]


# ---------------------------------------------------------------------------
# main (CLI)
# ---------------------------------------------------------------------------


class TestMain:
    @patch(f"{MODULE}.intake", return_value='{"datetime": {}}')
    def test_default_no_json(self, mock_intake, capsys):
        with patch.object(sys, "argv", ["interphase"]):
            main()
        mock_intake.assert_called_once_with(as_json=False)
        captured = capsys.readouterr()
        assert captured.out.strip() == '{"datetime": {}}'

    @patch(f"{MODULE}.intake", return_value='{"ok": true}')
    def test_json_flag(self, mock_intake, capsys):
        with patch.object(sys, "argv", ["interphase", "--json"]):
            main()
        mock_intake.assert_called_once_with(as_json=True)
