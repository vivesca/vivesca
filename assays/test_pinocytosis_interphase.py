from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from metabolon.pinocytosis.interphase import (
    intake_emails,
    intake_emails_archived,
    intake_whatsapp,
    intake_reminders,
    intake_email_threads,
    intake_prospective,
    intake,
    SECTION_ORDER,
    _SCRIPT_GATHERERS,
)


def test_section_order_constant():
    """Test SECTION_ORDER has expected keys."""
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
    assert SECTION_ORDER == expected
    assert set(_SCRIPT_GATHERERS.keys()) == {
        "emails",
        "emails_archived",
        "whatsapp",
        "reminders",
        "email_threads",
        "prospective",
    }


class TestIntakeEmails:
    """Tests for intake_emails."""

    def test_first_command_succeeds(self):
        """Test when first unread command succeeds."""
        with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
            mock_run.return_value = (True, "email1\nemail2")
            result = intake_emails()
            
            mock_run.assert_called_once_with(["gog", "gmail", "read", "--unread"], timeout=30)
            assert result["label"] == "Unread Emails (inbox)"
            assert result["ok"] is True
            assert result["content"] == "email1\nemail2"

    def test_second_command_tried_after_timeout(self):
        """Test that timeout falls back to search command."""
        with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
            mock_run.return_value = (False, "[timed out] connection error")
            result = intake_emails()
            
            assert mock_run.call_count == 2
            mock_run.assert_called_with(
                ["gog", "gmail", "search", "in:inbox", "--limit", "20"], timeout=30
            )
            assert result["ok"] is False
            assert "[timed out" in result["content"]

    def test_second_command_succeeds_after_failure(self):
        """Test second command succeeds after first failure (not timeout)."""
        with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
            mock_run.side_effect = [(False, "error"), (True, "results")]
            result = intake_emails()
            
            assert mock_run.call_count == 2
            assert result["ok"] is True
            assert result["content"] == "results"

    def test_empty_content_returns_none(self):
        """Test empty content becomes '(none)'."""
        with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
            mock_run.return_value = (True, "")
            result = intake_emails()
            assert result["content"] == "(none)"


class TestIntakeEmailsArchived:
    """Tests for intake_emails_archived."""

    def test_returns_correct_structure(self):
        """Test basic execution."""
        with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
            mock_run.return_value = (True, "archived1\narchived2")
            result = intake_emails_archived()
            
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args == [
                "gog",
                "gmail",
                "search",
                "newer_than:1d -in:inbox -from:briefs@cora.computer",
                "--plain",
            ]
            assert result["label"] == "Today's Archived (Cora safety net)"
            assert result["ok"] is True
            assert result["content"] == "archived1\narchived2"


class TestIntakeWhatsapp:
    """Tests for intake_whatsapp."""

    def test_main_command_succeeds(self):
        """Test when primary messages command succeeds."""
        with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
            mock_run.return_value = (True, "msg1\nmsg2")
            with patch("datetime.date.today") as mock_date:
                mock_date.return_value.isoformat.return_value = "2024-01-01"
                result = intake_whatsapp()
            
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[:3] == ["wacli", "messages", "list"]
            assert "--after" in args
            assert "2023-12-31" in args  # yesterday
            assert result["label"] == "WhatsApp Messages (last 24h)"
            assert result["ok"] is True

    def test_chats_list_fallback_succeeds(self):
        """Test fallback to chats list when messages fail."""
        with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
            mock_run.side_effect = [(False, "messages error"), (True, "chat1\nchat2")]
            result = intake_whatsapp()
            
            assert mock_run.call_count == 2
            assert result["label"] == "WhatsApp (recent chats - messages unavailable)"
            assert result["ok"] is True
            assert result["content"] == "chat1\nchat2"

    def test_both_commands_fail(self):
        """Test when both messages and chats commands fail."""
        with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
            mock_run.side_effect = [(False, "msg err"), (False, "chat err")]
            result = intake_whatsapp()
            
            assert result["label"] == "WhatsApp Messages"
            assert result["ok"] is False
            assert result["content"] == "msg err"


class TestIntakeReminders:
    """Tests for intake_reminders."""

    def test_pacemaker_succeeds(self):
        """Test when pacemaker ls succeeds."""
        with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
            mock_run.return_value = (True, "reminder1\nreminder2")
            result = intake_reminders()
            
            mock_run.assert_called_once_with(["pacemaker", "ls"], timeout=10)
            assert result["label"] == "Reminders (pacemaker)"
            assert result["ok"] is True

    def test_fallback_to_due(self):
        """Test fallback to due list when pacemaker fails."""
        with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
            mock_run.side_effect = [(False, "pacemaker fail"), (True, "due1\ndue2")]
            result = intake_reminders()
            
            assert mock_run.call_count == 2
            mock_run.assert_called_with(["due", "list"], timeout=10)
            assert result["label"] == "Due Reminders"
            assert result["ok"] is True

    def test_empty_content_shows_none(self):
        """Test empty content becomes '(none)'."""
        with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
            mock_run.return_value = (True, "")
            result = intake_reminders()
            assert result["content"] == "(none)"


class TestIntakeEmailThreads:
    """Tests for intake_email_threads."""

    def test_returns_correct_structure(self):
        """Test basic execution calls read_file correctly."""
        with patch("metabolon.pinocytosis.interphase.read_file") as mock_read:
            mock_read.return_value = (True, "thread1\nthread2")
            result = intake_email_threads()
            
            mock_read.assert_called_once_with(
                "~/epigenome/chromatin/Email Threads Tracker.md", max_lines=60
            )
            assert result["label"] == "Email Threads Tracker"
            assert result["ok"] is True
            assert result["content"] == "thread1\nthread2"


class TestIntakeProspective:
    """Tests for intake_prospective."""

    def test_returns_correct_structure(self):
        """Test basic execution."""
        from pathlib import Path
        with patch("metabolon.pinocytosis.interphase.read_file") as mock_read:
            mock_read.return_value = (True, "item1\nitem2")
            result = intake_prospective()
            
            # Check it's called with the correct path
            call_args = mock_read.call_args[0][0]
            assert isinstance(call_args, Path)
            assert "prospective.md" in str(call_args)
            assert result["label"] == "Prospective Memory"
            assert result["ok"] is True
            assert result["content"] == "item1\nitem2"


class TestIntake:
    """Tests for the main intake function."""

    @patch("metabolon.pinocytosis.interphase.secrete_json")
    @patch("metabolon.pinocytosis.interphase.transduce")
    @patch("metabolon.pinocytosis.interphase.sense_calendar")
    @patch("metabolon.pinocytosis.interphase.intake_context")
    def test_intake_json_output(
        self, mock_intake_ctx, mock_sense_cal, mock_transduce, mock_secrete
    ):
        """Test intake returns json output."""
        # Setup mocks
        mock_intake_ctx.return_value = {
            "datetime": "2024-01-01",
            "now": "10:00",
            "budget": "$100",
            "todo": "stuff",
        }
        
        mock_future_today = MagicMock()
        mock_future_today.result.return_value = {"ok": True, "content": "today event"}
        mock_future_tomorrow = MagicMock()
        mock_future_tomorrow.result.return_value = {"ok": True, "content": "tomorrow event"}
        
        with patch("concurrent.futures.ThreadPoolExecutor") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool_instance.submit.side_effect = [mock_future_today, mock_future_tomorrow]
            mock_pool.return_value.__enter__.return_value = mock_pool_instance
            
            mock_transduce.return_value = {}  # base ctx from transduce
            mock_secrete.return_value = '{"test": "json"}'
            
            result = intake(as_json=True)
            
            # Verify all the pieces
            mock_intake_ctx.assert_called_once_with(
                include=["date", "now", "budget", "todo"],
                calendar_date="today",
                calendar_days=2,
                todo_filter="all",
            )
            assert mock_pool_instance.submit.call_count == 2
            assert mock_transduce.called
            mock_secrete_json.assert_called_once()
            assert result == '{"test": "json"}'

    @patch("metabolon.pinocytosis.interphase.secrete_text")
    @patch("metabolon.pinocytosis.interphase.transduce")
    @patch("metabolon.pinocytosis.interphase.sense_calendar")
    @patch("metabolon.pinocytosis.interphase.intake_context")
    def test_intake_text_output(
        self, mock_intake_ctx, mock_sense_cal, mock_transduce, mock_secrete
    ):
        """Test intake returns text output."""
        mock_intake_ctx.return_value = {"datetime": "2024-01-01"}
        mock_future_today = MagicMock()
        mock_future_today.result.return_value = {"ok": True, "content": "today"}
        mock_future_tomorrow = MagicMock()
        mock_future_tomorrow.result.return_value = {"ok": True, "content": "tomorrow"}
        
        with patch("concurrent.futures.ThreadPoolExecutor"):
            mock_transduce.return_value = {}
            mock_secrete.return_value = "FORMATTED TEXT OUTPUT"
            
            result = intake(as_json=False)
            
            mock_secrete_text.assert_called_once()
            assert result == "FORMATTED TEXT OUTPUT"

    def test_gatherer_exception_handling(self):
        """Test that exceptions in gatherers are caught and formatted."""
        with patch("metabolon.pinocytosis.interphase.intake_context") as mock_intake_ctx:
            mock_intake_ctx.return_value = {}
            
            mock_future_today = MagicMock()
            mock_future_today.result.return_value = {}
            mock_future_tomorrow = MagicMock()
            mock_future_tomorrow.result.return_value = {}
            
            with patch("concurrent.futures.ThreadPoolExecutor") as mock_pool:
                # First pool for calendar
                mock_pool_instance = MagicMock()
                mock_pool_instance.submit.side_effect = [
                    mock_future_today, 
                    mock_future_tomorrow,
                ]
                mock_pool.return_value.__enter__.return_value = mock_pool_instance
                
                # Second pool for gatherers - make a gatherer raise
                def mock_submit(fn):
                    f = MagicMock()
                    f.result.side_effect = RuntimeError("Something went wrong")
                    return f
                
                # We need to mock the second pool creation
                first_pool = True
                def patched_pool_ctor(*args, **kwargs):
                    nonlocal first_pool
                    if first_pool:
                        first_pool = False
                        return mock_pool.return_value
                    else:
                        inst = MagicMock()
                        inst.submit = mock_submit
                        inst.__enter__ = MagicMock(return_value=inst)
                        # Make as_completed return all futures
                        futures = [mock_submit(fn) for key, fn in _SCRIPT_GATHERERS.items()]
                        inst.__exit__ = MagicMock(return_value=None)
                        return inst
                
                with patch("concurrent.futures.ThreadPoolExecutor", patched_pool_ctor):
                    from metabolon.pinocytosis.interphase import intake
                    with patch("metabolon.pinocytosis.interphase.sense_calendar"), \
                         patch("metabolon.pinocytosis.interphase.transduce") as mock_transduce:
                        mock_transduce.return_value = {}
                        with patch("metabolon.pinocytosis.interphase.secrete_json") as mock_secrete:
                            mock_secrete.return_value = "{}"
                            # Should not raise, should handle the exception
                            result = intake(as_json=True)
                            # Check that the error was captured in results
                            called_order = mock_secrete.call_args[0][0]
                            assert len(called_order) > 0
                            # At least one key should have the error
                            has_error = any(
                                "gatherer error" in val.get("content", "") 
                                for val in called_order.values()
                            )
                            assert has_error


def test_main_parses_args():
    """Test main function parses arguments."""
    import sys
    from metabolon.pinocytosis.interphase import main
    
    with patch("argparse.ArgumentParser.parse_args") as mock_parse:
        mock_parse.return_value = MagicMock(json=True)
        with patch("metabolon.pinocytosis.interphase.intake") as mock_intake:
            mock_intake.return_value = "output"
            with patch("builtins.print") as mock_print:
                main()
                mock_intake.assert_called_once_with(as_json=True)
                mock_print.assert_called_once_with("output")
