from __future__ import annotations

import json
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
)


def test_intake_emails_first_try_succeeds():
    with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
        mock_run.return_value = (True, "unread message 1\nunread message 2")
        result = intake_emails()
        assert result["label"] == "Unread Emails (inbox)"
        assert result["ok"] is True
        assert "unread message 1" in result["content"]
        mock_run.assert_called_once_with(["gog", "gmail", "read", "--unread"], timeout=30)


def test_intake_emails_first_try_fails_second_succeeds():
    with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
        mock_run.side_effect = [(False, "timeout"), (True, "message 1\nmessage 2")]
        result = intake_emails()
        assert result["ok"] is True
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[1][0][0] == [
            "gog",
            "gmail",
            "search",
            "in:inbox",
            "--limit",
            "20",
        ]


def test_intake_emails_timeout_returns_first_failure():
    with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
        mock_run.return_value = (False, "[timed out]")
        result = intake_emails()
        assert result["ok"] is False
        assert "[timed out]" in result["content"]


def test_intake_emails_archived_returns_result():
    with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
        mock_run.return_value = (True, "archived message")
        result = intake_emails_archived()
        assert result["label"] == "Today's Archived (Cora safety net)"
        assert result["ok"] is True
        assert "archived message" in result["content"]
        assert any("newer_than:1d" in arg for arg in mock_run.call_args[0][0])


def test_intake_whatsapp_main_succeeds():
    with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
        mock_run.return_value = (True, "msg1\nmsg2")
        result = intake_whatsapp()
        assert result["label"] == "WhatsApp Messages (last 24h)"
        assert result["ok"] is True
        mock_run.assert_called_once()
        assert any("--after" in arg for arg in mock_run.call_args[0][0])


def test_intake_whatsapp_main_falls_back_to_chats():
    with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
        mock_run.side_effect = [(False, "failed"), (True, "chat1\nchat2")]
        result = intake_whatsapp()
        assert result["ok"] is True
        assert "recent chats" in result["label"]
        assert mock_run.call_count == 2


def test_intake_whatsapp_both_fail():
    with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
        mock_run.side_effect = [(False, "msg failed"), (False, "chat failed")]
        result = intake_whatsapp()
        assert result["ok"] is False
        assert "msg failed" in result["content"]


def test_intake_reminders_pacemaker_succeeds():
    with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
        mock_run.return_value = (True, "reminder 1\nreminder 2")
        result = intake_reminders()
        assert result["label"] == "Reminders (pacemaker)"
        assert result["ok"] is True
        mock_run.assert_called_once_with(["pacemaker", "ls"], timeout=10)


def test_intake_reminders_falls_back_to_due():
    with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
        mock_run.side_effect = [(False, "pacemaker failed"), (True, "due reminder 1")]
        result = intake_reminders()
        assert result["label"] == "Due Reminders"
        assert result["ok"] is True
        assert mock_run.call_count == 2


def test_intake_email_threads_ok():
    with patch("metabolon.pinocytosis.interphase.read_file") as mock_read:
        mock_read.return_value = (True, "thread1\nthread2")
        result = intake_email_threads()
        assert result["label"] == "Email Threads Tracker"
        assert result["ok"] is True
        assert "Email Threads Tracker.md" in mock_read.call_args[0][0]


def test_intake_email_threads_not_ok():
    with patch("metabolon.pinocytosis.interphase.read_file") as mock_read:
        mock_read.return_value = (False, "file not found")
        result = intake_email_threads()
        assert result["ok"] is False


def test_intake_prospective_ok():
    with patch("metabolon.pinocytosis.interphase.read_file") as mock_read:
        mock_read.return_value = (True, "task1\ntask2")
        result = intake_prospective()
        assert result["label"] == "Prospective Memory"
        assert result["ok"] is True


def test_intake_prospective_not_ok():
    with patch("metabolon.pinocytosis.interphase.read_file") as mock_read:
        mock_read.return_value = (False, "file not found")
        result = intake_prospective()
        assert result["ok"] is False


def test_all_gatherers_registered():
    """Check all gatherers are registered and in section order."""
    for key in _SCRIPT_GATHERERS:
        assert key in SECTION_ORDER, f"Gatherer {key} not in SECTION_ORDER"


def test_intake_json_output_mocked():
    mock_ctx = {
        "date": {"datetime": "2024-01-01 10:00 HKT"},
        "todo": {"available": True, "items": []},
        "now": {"available": True, "raw": ""},
        "budget": {"available": True, "raw": ""},
    }

    with patch("metabolon.pinocytosis.interphase.intake_context") as mock_intake_ctx:
        mock_intake_ctx.return_value = mock_ctx

        with patch("metabolon.pinocytosis.interphase.sense_calendar") as mock_sense:
            mock_sense.return_value = {"available": True, "raw": "9:00 Meeting"}

            with patch("metabolon.pinocytosis.interphase.transduce") as mock_transduce:
                mock_transduce.return_value = {
                    "datetime": {"label": "Current Date", "ok": True, "content": "..."},
                    "emails": {"label": "Unread Emails", "ok": True, "content": "test"},
                }

                with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
                    mock_run.return_value = (True, "test content")

                    result = intake(as_json=True)
                    data = json.loads(result)

                    assert isinstance(data, dict)
                    assert "datetime" in data
                    mock_intake_ctx.assert_called_once()
                    assert mock_sense.call_count == 2


def test_intake_text_output_mocked():
    mock_ctx = {
        "date": {"datetime": "2024-01-01 10:00 HKT"},
        "todo": {"available": True, "items": []},
        "now": {"available": True, "raw": ""},
        "budget": {"available": True, "raw": ""},
    }

    with patch("metabolon.pinocytosis.interphase.intake_context") as mock_intake_ctx:
        mock_intake_ctx.return_value = mock_ctx

        with patch("metabolon.pinocytosis.interphase.sense_calendar") as mock_sense:
            mock_sense.return_value = {"available": True, "raw": "9:00 Meeting"}

            with patch("metabolon.pinocytosis.interphase.transduce") as mock_transduce:
                mock_transduce.return_value = {
                    "datetime": {"label": "Current Date", "ok": True, "content": "..."},
                }

                with patch("metabolon.pinocytosis.interphase.run_cmd") as mock_run:
                    mock_run.return_value = (True, "test content")

                    result = intake(as_json=False)
                    assert isinstance(result, str)
                    assert "INTERPHASE" in result
                    assert "Current Date" in result


def test_gatherer_exception_handling():
    """Test that exceptions in gatherers are caught and handled gracefully."""
    mock_ctx = {
        "date": {"datetime": "2024-01-01 10:00 HKT"},
        "todo": {"available": True, "items": []},
        "now": {"available": True, "raw": ""},
        "budget": {"available": True, "raw": ""},
    }

    with patch("metabolon.pinocytosis.interphase.intake_context") as mock_intake_ctx:
        mock_intake_ctx.return_value = mock_ctx

        with patch("metabolon.pinocytosis.interphase.sense_calendar") as mock_sense:
            mock_sense.return_value = {"available": True, "raw": ""}

            with patch("metabolon.pinocytosis.interphase.transduce") as mock_transduce:
                mock_transduce.return_value = {}

                # Make one of the gatherers raise an exception
                with patch.dict(_SCRIPT_GATHERERS, {"emails": lambda: 1 / 0}):
                    result = intake(as_json=True)
                    data = json.loads(result)
                    assert "emails" in data
                    assert data["emails"]["ok"] is False
                    assert "gatherer error" in data["emails"]["content"]
