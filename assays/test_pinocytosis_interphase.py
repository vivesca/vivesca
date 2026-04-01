"""Tests for metabolon.pinocytosis.interphase module."""

from __future__ import annotations

import datetime
from unittest import mock

import pytest


# Import the module under test
from metabolon.pinocytosis import interphase


class TestIntakeEmails:
    """Tests for intake_emails function."""

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_success_first_try(self, mock_run_cmd):
        """Returns unread emails when first command succeeds."""
        mock_run_cmd.return_value = (True, "email1\nemail2")
        result = interphase.intake_emails()
        
        assert result["label"] == "Unread Emails (inbox)"
        assert result["ok"] is True
        assert result["content"] == "email1\nemail2"
        mock_run_cmd.assert_called_once_with(["gog", "gmail", "read", "--unread"], timeout=30)

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_fallback_on_timeout(self, mock_run_cmd):
        """Falls back to search when first command times out."""
        mock_run_cmd.side_effect = [
            (False, "[timed out after 30s]"),
            (True, "search result1\nsearch result2"),
        ]
        result = interphase.intake_emails()
        
        assert result["ok"] is True
        assert result["content"] == "search result1\nsearch result2"
        assert mock_run_cmd.call_count == 2

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_no_fallback_on_non_timeout_error(self, mock_run_cmd):
        """Does not fall back when error is not a timeout."""
        mock_run_cmd.return_value = (False, "connection refused")
        result = interphase.intake_emails()
        
        assert result["ok"] is False
        assert result["content"] == "connection refused"
        mock_run_cmd.assert_called_once()

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_empty_result(self, mock_run_cmd):
        """Handles empty output."""
        mock_run_cmd.return_value = (True, "")
        result = interphase.intake_emails()
        
        assert result["content"] == "(none)"

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_none_output(self, mock_run_cmd):
        """Handles None output."""
        mock_run_cmd.return_value = (True, None)
        result = interphase.intake_emails()
        
        assert result["content"] == "(none)"


class TestIntakeEmailsArchived:
    """Tests for intake_emails_archived function."""

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_success(self, mock_run_cmd):
        """Returns archived emails."""
        mock_run_cmd.return_value = (True, "archived1\narchived2")
        result = interphase.intake_emails_archived()
        
        assert result["label"] == "Today's Archived (Cora safety net)"
        assert result["ok"] is True
        assert result["content"] == "archived1\narchived2"
        expected_cmd = [
            "gog", "gmail", "search",
            "newer_than:1d -in:inbox -from:briefs@cora.computer",
            "--plain",
        ]
        mock_run_cmd.assert_called_once_with(expected_cmd, timeout=30)

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_failure(self, mock_run_cmd):
        """Handles command failure."""
        mock_run_cmd.return_value = (False, "error message")
        result = interphase.intake_emails_archived()
        
        assert result["ok"] is False
        assert result["content"] == "error message"

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_empty_output(self, mock_run_cmd):
        """Handles empty output."""
        mock_run_cmd.return_value = (True, "")
        result = interphase.intake_emails_archived()
        
        assert result["content"] == "(none)"


class TestIntakeWhatsapp:
    """Tests for intake_whatsapp function."""

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    @mock.patch("metabolon.pinocytosis.interphase.datetime")
    def test_success_messages(self, mock_dt, mock_run_cmd):
        """Returns WhatsApp messages when available."""
        mock_dt.date.today.return_value = datetime.date(2026, 4, 1)
        mock_run_cmd.return_value = (True, "msg1\nmsg2")
        result = interphase.intake_whatsapp()
        
        assert result["label"] == "WhatsApp Messages (last 24h)"
        assert result["ok"] is True
        assert result["content"] == "msg1\nmsg2"
        mock_run_cmd.assert_called_once_with(
            ["wacli", "messages", "list", "--after", "2026-03-31", "--limit", "40"],
            timeout=15,
        )

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    @mock.patch("metabolon.pinocytosis.interphase.datetime")
    def test_fallback_to_chats(self, mock_dt, mock_run_cmd):
        """Falls back to chats list when messages fail."""
        mock_dt.date.today.return_value = datetime.date(2026, 4, 1)
        mock_run_cmd.side_effect = [
            (False, "messages error"),
            (True, "chat1\nchat2"),
        ]
        result = interphase.intake_whatsapp()
        
        assert result["label"] == "WhatsApp (recent chats - messages unavailable)"
        assert result["ok"] is True
        assert result["content"] == "chat1\nchat2"

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    @mock.patch("metabolon.pinocytosis.interphase.datetime")
    def test_complete_failure(self, mock_dt, mock_run_cmd):
        """Returns failure when both commands fail."""
        mock_dt.date.today.return_value = datetime.date(2026, 4, 1)
        mock_run_cmd.side_effect = [
            (False, "messages error"),
            (False, "chats error"),
        ]
        result = interphase.intake_whatsapp()
        
        assert result["label"] == "WhatsApp Messages"
        assert result["ok"] is False
        assert result["content"] == "messages error"


class TestIntakeReminders:
    """Tests for intake_reminders function."""

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_pacemaker_success(self, mock_run_cmd):
        """Uses pacemaker when available."""
        mock_run_cmd.return_value = (True, "reminder1\nreminder2")
        result = interphase.intake_reminders()
        
        assert result["label"] == "Reminders (pacemaker)"
        assert result["ok"] is True
        assert result["content"] == "reminder1\nreminder2"
        mock_run_cmd.assert_called_once_with(["pacemaker", "ls"], timeout=10)

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_fallback_to_due(self, mock_run_cmd):
        """Falls back to 'due' when pacemaker fails."""
        mock_run_cmd.side_effect = [
            (False, "pacemaker error"),
            (True, "due reminder1"),
        ]
        result = interphase.intake_reminders()
        
        assert result["label"] == "Due Reminders"
        assert result["ok"] is True
        assert result["content"] == "due reminder1"

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_both_fail(self, mock_run_cmd):
        """Handles both reminder systems failing."""
        mock_run_cmd.side_effect = [
            (False, "pacemaker error"),
            (False, "due error"),
        ]
        result = interphase.intake_reminders()
        
        assert result["label"] == "Due Reminders"
        assert result["ok"] is False
        assert result["content"] == "due error"

    @mock.patch("metabolon.pinocytosis.interphase.run_cmd")
    def test_empty_reminders(self, mock_run_cmd):
        """Handles empty reminder list."""
        mock_run_cmd.return_value = (True, "")
        result = interphase.intake_reminders()
        
        assert result["content"] == "(none)"


class TestIntakeEmailThreads:
    """Tests for intake_email_threads function."""

    @mock.patch("metabolon.pinocytosis.interphase.read_file")
    def test_success(self, mock_read_file):
        """Returns email threads tracker content."""
        mock_read_file.return_value = (True, "thread1\nthread2")
        result = interphase.intake_email_threads()
        
        assert result["label"] == "Email Threads Tracker"
        assert result["ok"] is True
        assert result["content"] == "thread1\nthread2"
        mock_read_file.assert_called_once_with(
            "~/epigenome/chromatin/Email Threads Tracker.md", max_lines=60
        )

    @mock.patch("metabolon.pinocytosis.interphase.read_file")
    def test_failure(self, mock_read_file):
        """Handles file read failure."""
        mock_read_file.return_value = (False, "file not found")
        result = interphase.intake_email_threads()
        
        assert result["ok"] is False
        assert result["content"] == "file not found"


class TestIntakeProspective:
    """Tests for intake_prospective function."""

    @mock.patch("metabolon.pinocytosis.interphase.read_file")
    def test_success(self, mock_read_file):
        """Returns prospective memory content."""
        mock_read_file.return_value = (True, "prospective item1\nitem2")
        result = interphase.intake_prospective()
        
        assert result["label"] == "Prospective Memory"
        assert result["ok"] is True
        assert result["content"] == "prospective item1\nitem2"

    @mock.patch("metabolon.pinocytosis.interphase.read_file")
    def test_failure(self, mock_read_file):
        """Handles file read failure."""
        mock_read_file.return_value = (False, "file not found")
        result = interphase.intake_prospective()
        
        assert result["ok"] is False
        assert result["content"] == "file not found"


class TestIntake:
    """Tests for the main intake function."""

    @mock.patch("metabolon.pinocytosis.interphase.secrete_json")
    @mock.patch("metabolon.pinocytosis.interphase.secrete_text")
    @mock.patch("metabolon.pinocytosis.interphase.transduce")
    @mock.patch("metabolon.pinocytosis.interphase.sense_calendar")
    @mock.patch("metabolon.pinocytosis.interphase.intake_context")
    @mock.patch("metabolon.pinocytosis.interphase._SCRIPT_GATHERERS")
    def test_intake_json_output(
        self,
        mock_gatherers,
        mock_intake_context,
        mock_sense_calendar,
        mock_transduce,
        mock_secrete_text,
        mock_secrete_json,
    ):
        """Returns JSON output when as_json=True."""
        # Setup mocks
        mock_intake_context.return_value = {"date": "2026-04-01"}
        mock_sense_calendar.return_value = {"events": []}
        mock_transduce.return_value = {"calendar_today": {"label": "Today"}}
        mock_gatherers.items.return_value = []  # No script gatherers
        mock_secrete_json.return_value = '{"result": "json"}'
        
        result = interphase.intake(as_json=True)
        
        assert result == '{"result": "json"}'
        mock_secrete_json.assert_called_once()
        mock_secrete_text.assert_not_called()

    @mock.patch("metabolon.pinocytosis.interphase.secrete_json")
    @mock.patch("metabolon.pinocytosis.interphase.secrete_text")
    @mock.patch("metabolon.pinocytosis.interphase.transduce")
    @mock.patch("metabolon.pinocytosis.interphase.sense_calendar")
    @mock.patch("metabolon.pinocytosis.interphase.intake_context")
    @mock.patch("metabolon.pinocytosis.interphase._SCRIPT_GATHERERS")
    def test_intake_text_output(
        self,
        mock_gatherers,
        mock_intake_context,
        mock_sense_calendar,
        mock_transduce,
        mock_secrete_text,
        mock_secrete_json,
    ):
        """Returns text output when as_json=False."""
        mock_intake_context.return_value = {"date": "2026-04-01"}
        mock_sense_calendar.return_value = {"events": []}
        mock_transduce.return_value = {"calendar_today": {"label": "Today"}}
        mock_gatherers.items.return_value = []
        mock_secrete_text.return_value = "INTERPHASE CONTEXT BRIEF"
        
        result = interphase.intake(as_json=False)
        
        assert result == "INTERPHASE CONTEXT BRIEF"
        mock_secrete_text.assert_called_once()
        mock_secrete_json.assert_not_called()

    @mock.patch("metabolon.pinocytosis.interphase.secrete_json")
    @mock.patch("metabolon.pinocytosis.interphase.transduce")
    @mock.patch("metabolon.pinocytosis.interphase.sense_calendar")
    @mock.patch("metabolon.pinocytosis.interphase.intake_context")
    @mock.patch("metabolon.pinocytosis.interphase._SCRIPT_GATHERERS")
    def test_intake_calls_calendar_parallel(
        self,
        mock_gatherers,
        mock_intake_context,
        mock_sense_calendar,
        mock_transduce,
        mock_secrete_json,
    ):
        """Fetches today and tomorrow calendar in parallel."""
        mock_intake_context.return_value = {}
        mock_sense_calendar.return_value = {"events": []}
        mock_transduce.return_value = {}
        mock_gatherers.items.return_value = []
        mock_secrete_json.return_value = '{}'
        
        interphase.intake(as_json=True)
        
        # Calendar should be called twice: today and tomorrow
        assert mock_sense_calendar.call_count == 2
        calls = mock_sense_calendar.call_args_list
        assert calls[0] == mock.call("today", 1)
        assert calls[1] == mock.call("tomorrow", 1)

    @mock.patch("metabolon.pinocytosis.interphase.secrete_json")
    @mock.patch("metabolon.pinocytosis.interphase.transduce")
    @mock.patch("metabolon.pinocytosis.interphase.sense_calendar")
    @mock.patch("metabolon.pinocytosis.interphase.intake_context")
    @mock.patch("metabolon.pinocytosis.interphase._SCRIPT_GATHERERS")
    def test_intake_gatherer_exception_handling(
        self,
        mock_gatherers,
        mock_intake_context,
        mock_sense_calendar,
        mock_transduce,
        mock_secrete_json,
    ):
        """Handles exceptions from gatherers gracefully."""
        mock_intake_context.return_value = {}
        mock_sense_calendar.return_value = {}
        mock_transduce.return_value = {}
        
        # Mock a gatherer that raises an exception
        def failing_gatherer():
            raise RuntimeError("gatherer failed")
        
        mock_gatherers.items.return_value = [("emails", failing_gatherer)]
        mock_secrete_json.return_value = '{}'
        
        result = interphase.intake(as_json=True)
        
        # Should not raise, should include error in results
        assert result == '{}'
        mock_secrete_json.assert_called_once()
        # Check that the error was captured in results
        call_args = mock_secrete_json.call_args[0][0]
        assert "emails" in call_args
        assert call_args["emails"]["ok"] is False
        assert "gatherer error" in call_args["emails"]["content"]

    @mock.patch("metabolon.pinocytosis.interphase.secrete_json")
    @mock.patch("metabolon.pinocytosis.interphase.transduce")
    @mock.patch("metabolon.pinocytosis.interphase.sense_calendar")
    @mock.patch("metabolon.pinocytosis.interphase.intake_context")
    def test_intake_context_parameters(
        self,
        mock_intake_context,
        mock_sense_calendar,
        mock_transduce,
        mock_secrete_json,
    ):
        """Calls intake_context with correct parameters."""
        mock_intake_context.return_value = {}
        mock_sense_calendar.return_value = {}
        mock_transduce.return_value = {}
        mock_secrete_json.return_value = '{}'
        
        interphase.intake(as_json=True)
        
        mock_intake_context.assert_called_once_with(
            include=["date", "now", "budget", "todo"],
            calendar_date="today",
            calendar_days=2,
            todo_filter="all",
        )


class TestSectionOrder:
    """Tests for SECTION_ORDER constant."""

    def test_section_order_is_list(self):
        """SECTION_ORDER is a list."""
        assert isinstance(interphase.SECTION_ORDER, list)

    def test_section_order_contains_expected_keys(self):
        """SECTION_ORDER contains all expected sections."""
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
        assert interphase.SECTION_ORDER == expected


class TestScriptGatherers:
    """Tests for _SCRIPT_GATHERERS constant."""

    def test_script_gatherers_is_dict(self):
        """_SCRIPT_GATHERERS is a dictionary."""
        assert isinstance(interphase._SCRIPT_GATHERERS, dict)

    def test_script_gatherers_keys_in_section_order(self):
        """All script gatherer keys are in SECTION_ORDER."""
        for key in interphase._SCRIPT_GATHERERS:
            assert key in interphase.SECTION_ORDER, f"{key} not in SECTION_ORDER"

    def test_script_gatherers_are_callables(self):
        """All script gatherer values are callable."""
        for key, fn in interphase._SCRIPT_GATHERERS.items():
            assert callable(fn), f"{key} is not callable"


class TestMain:
    """Tests for CLI main function."""

    @mock.patch("builtins.print")
    @mock.patch("metabolon.pinocytosis.interphase.intake")
    def test_main_default(self, mock_intake, mock_print):
        """Main prints intake result without --json flag."""
        mock_intake.return_value = "text output"
        
        with mock.patch("sys.argv", ["interphase"]):
            interphase.main()
        
        mock_intake.assert_called_once_with(as_json=False)
        mock_print.assert_called_once_with("text output")

    @mock.patch("builtins.print")
    @mock.patch("metabolon.pinocytosis.interphase.intake")
    def test_main_json_flag(self, mock_intake, mock_print):
        """Main prints JSON output with --json flag."""
        mock_intake.return_value = '{"json": "output"}'
        
        with mock.patch("sys.argv", ["interphase", "--json"]):
            interphase.main()
        
        mock_intake.assert_called_once_with(as_json=True)
        mock_print.assert_called_once_with('{"json": "output"}')
