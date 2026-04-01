from __future__ import annotations

"""Tests for metabolon.respirometry.payments."""

import subprocess
from datetime import datetime, timedelta, timezone, date
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

from metabolon.respirometry.payments import (
    restore_payments,
    persist_payments,
    restore_card_config,
    is_autopay,
    queue_payment,
    dequeue_payment,
    schedule_payment_reminder,
    assess_missing_statements,
    flag_overdue_payments,
    HKT,
)


# ── restore_payments ──────────────────────────────────────────────

class TestRestorePayments:
    def test_missing_file_returns_empty(self, tmp_path: Path):
        assert restore_payments(tmp_path / "gone.yml") == []

    def test_empty_file_returns_empty(self, tmp_path: Path):
        f = tmp_path / "pay.yml"
        f.write_text("")
        assert restore_payments(f) == []

    def test_no_pending_key_returns_empty(self, tmp_path: Path):
        f = tmp_path / "pay.yml"
        f.write_text(yaml.dump({"other": [1, 2]}))
        assert restore_payments(f) == []

    def test_loads_pending_entries(self, tmp_path: Path):
        f = tmp_path / "pay.yml"
        entries = [{"bank": "hsbc", "amount": 5000.0, "due_date": "2026-04-15"}]
        f.write_text(yaml.dump({"pending": entries}))
        assert restore_payments(f) == entries


# ── persist_payments ──────────────────────────────────────────────

class TestPersistPayments:
    def test_creates_parent_dirs(self, tmp_path: Path):
        target = tmp_path / "deep" / "nested" / "pay.yml"
        persist_payments(target, [{"bank": "hsbc"}])
        assert target.exists()

    def test_writes_header_comment(self, tmp_path: Path):
        f = tmp_path / "pay.yml"
        persist_payments(f, [])
        text = f.read_text()
        assert text.startswith("# Auto-managed")

    def test_roundtrip(self, tmp_path: Path):
        f = tmp_path / "pay.yml"
        entries = [{"bank": "citi", "amount": 1200}]
        persist_payments(f, entries)
        loaded = restore_payments(f)
        assert loaded == entries


# ── restore_card_config / is_autopay ──────────────────────────────

class TestCardConfig:
    def test_missing_config_returns_empty(self, tmp_path: Path):
        assert restore_card_config(tmp_path / "nope.yml") == {}

    def test_loads_cards(self, tmp_path: Path):
        f = tmp_path / "cfg.yml"
        cards = {"hsbc": {"autopay": True}, "citi": {"autopay": False}}
        f.write_text(yaml.dump({"cards": cards}))
        assert restore_card_config(f) == cards

    def test_is_autopay_true(self, tmp_path: Path):
        f = tmp_path / "cfg.yml"
        f.write_text(yaml.dump({"cards": {"hsbc": {"autopay": True}}}))
        assert is_autopay("hsbc", f) is True

    def test_is_autopay_false(self, tmp_path: Path):
        f = tmp_path / "cfg.yml"
        f.write_text(yaml.dump({"cards": {"hsbc": {"autopay": False}}}))
        assert is_autopay("hsbc", f) is False

    def test_is_autopay_missing_key(self, tmp_path: Path):
        f = tmp_path / "cfg.yml"
        f.write_text(yaml.dump({"cards": {"hsbc": {}}}))
        assert is_autopay("hsbc", f) is False

    def test_is_autopay_unknown_bank(self, tmp_path: Path):
        f = tmp_path / "cfg.yml"
        f.write_text(yaml.dump({"cards": {"hsbc": {"autopay": True}}}))
        assert is_autopay("citi", f) is False


# ── queue_payment ─────────────────────────────────────────────────

class TestQueuePayment:
    @patch("metabolon.respirometry.payments.datetime")
    def test_adds_entry(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 1, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        entry = queue_payment(f, "hsbc", 5000.0, "2026-04-15", "2026-03-15")
        assert entry["bank"] == "hsbc"
        assert entry["amount"] == 5000.0
        assert entry["due_date"] == "2026-04-15"
        assert entry["statement_date"] == "2026-03-15"
        assert entry["created"] == "2026-04-01"
        # persisted
        loaded = restore_payments(f)
        assert len(loaded) == 1
        assert loaded[0] == entry

    @patch("metabolon.respirometry.payments.datetime")
    def test_no_duplicate_same_bank_statement(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 1, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        e1 = queue_payment(f, "hsbc", 5000.0, "2026-04-15", "2026-03-15")
        e2 = queue_payment(f, "hsbc", 6000.0, "2026-05-15", "2026-03-15")
        assert e2 == e1  # duplicate ignored
        assert len(restore_payments(f)) == 1

    @patch("metabolon.respirometry.payments.datetime")
    def test_allows_different_statement_dates(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 1, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        queue_payment(f, "hsbc", 5000.0, "2026-04-15", "2026-03-15")
        entry2 = queue_payment(f, "hsbc", 6000.0, "2026-05-15", "2026-04-15")
        assert entry2["amount"] == 6000.0
        assert len(restore_payments(f)) == 2


# ── dequeue_payment ───────────────────────────────────────────────

class TestDequeuePayment:
    def test_removes_oldest_for_bank(self, tmp_path: Path):
        f = tmp_path / "pay.yml"
        entries = [
            {"bank": "hsbc", "amount": 1000},
            {"bank": "citi", "amount": 2000},
            {"bank": "hsbc", "amount": 3000},
        ]
        persist_payments(f, entries)
        removed = dequeue_payment(f, "hsbc")
        assert removed["amount"] == 1000
        remaining = restore_payments(f)
        assert len(remaining) == 2
        assert remaining[0]["bank"] == "citi"
        assert remaining[1]["bank"] == "hsbc"
        assert remaining[1]["amount"] == 3000

    def test_returns_none_if_not_found(self, tmp_path: Path):
        f = tmp_path / "pay.yml"
        persist_payments(f, [{"bank": "citi", "amount": 100}])
        assert dequeue_payment(f, "hsbc") is None

    def test_empty_file_returns_none(self, tmp_path: Path):
        f = tmp_path / "pay.yml"
        assert dequeue_payment(f, "hsbc") is None


# ── schedule_payment_reminder ─────────────────────────────────────

class TestSchedulePaymentReminder:
    @patch("metabolon.respirometry.payments.subprocess.run")
    def test_success_returns_stdout(self, mock_run):
        mock_run.return_value = MagicMock(stdout="event-id-123\n", returncode=0)
        result = schedule_payment_reminder("hsbc", 5000.0, "2026-04-15")
        assert result == "event-id-123"
        call_args = mock_run.call_args
        assert "--date" in call_args[0][0]
        # reminder is 3 days before due
        idx = call_args[0][0].index("--date")
        assert call_args[0][0][idx + 1] == "2026-04-12"

    @patch("metabolon.respirometry.payments.subprocess.run")
    def test_failure_returns_none(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", returncode=1)
        assert schedule_payment_reminder("hsbc", 5000.0, "2026-04-15") is None

    @patch("metabolon.respirometry.payments.subprocess.run")
    def test_timeout_returns_none(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="fasti", timeout=30)
        assert schedule_payment_reminder("hsbc", 5000.0, "2026-04-15") is None

    @patch("metabolon.respirometry.payments.subprocess.run")
    def test_filenotfound_returns_none(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        assert schedule_payment_reminder("hsbc", 5000.0, "2026-04-15") is None

    def test_invalid_date_returns_none(self):
        assert schedule_payment_reminder("hsbc", 5000.0, "not-a-date") is None

    @patch("metabolon.respirometry.payments.subprocess.run")
    def test_summary_format(self, mock_run):
        mock_run.return_value = MagicMock(stdout="ok\n", returncode=0)
        schedule_payment_reminder("hsbc", 5000.0, "2026-04-15")
        cmd = mock_run.call_args[0][0]
        # cmd[2] is the summary (after "fasti" "create")
        assert cmd[2] == "Pay HSBC HKD 5,000.00"


# ── assess_missing_statements ─────────────────────────────────────

class TestAssessMissingStatements:
    @patch("metabolon.respirometry.payments.datetime")
    def test_flags_missing_statement(self, mock_dt, tmp_path: Path):
        # Day 20 of month, statement_day=10, grace=5, 20>=15 so flagged
        mock_dt.now.return_value = datetime(2026, 4, 20, 12, 0, 0, tzinfo=HKT)
        cfg = tmp_path / "cfg.yml"
        cfg.write_text(yaml.dump({"cards": {"hsbc": {"statement_day": 10, "active": True}}}))
        spending = tmp_path / "spending"
        spending.mkdir()
        alerts = assess_missing_statements(cfg, spending)
        assert len(alerts) == 1
        assert "HSBC" in alerts[0]
        assert "Missing statement" in alerts[0]

    @patch("metabolon.respirometry.payments.datetime")
    def test_no_alert_if_statement_exists(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 20, 12, 0, 0, tzinfo=HKT)
        cfg = tmp_path / "cfg.yml"
        cfg.write_text(yaml.dump({"cards": {"hsbc": {"statement_day": 10}}}))
        spending = tmp_path / "spending"
        spending.mkdir()
        (spending / "2026-04-hsbc.md").write_text("statement data")
        assert assess_missing_statements(cfg, spending) == []

    @patch("metabolon.respirometry.payments.datetime")
    def test_no_alert_within_grace_period(self, mock_dt, tmp_path: Path):
        # Day 12, statement_day=10, grace=5, expected_by=15, 12<15 so no alert
        mock_dt.now.return_value = datetime(2026, 4, 12, 12, 0, 0, tzinfo=HKT)
        cfg = tmp_path / "cfg.yml"
        cfg.write_text(yaml.dump({"cards": {"hsbc": {"statement_day": 10}}}))
        spending = tmp_path / "spending"
        spending.mkdir()
        assert assess_missing_statements(cfg, spending) == []

    @patch("metabolon.respirometry.payments.datetime")
    def test_inactive_card_not_flagged(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 20, 12, 0, 0, tzinfo=HKT)
        cfg = tmp_path / "cfg.yml"
        cfg.write_text(yaml.dump({"cards": {"hsbc": {"statement_day": 10, "active": False}}}))
        spending = tmp_path / "spending"
        spending.mkdir()
        assert assess_missing_statements(cfg, spending) == []

    @patch("metabolon.respirometry.payments.datetime")
    def test_no_statement_day_skipped(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 20, 12, 0, 0, tzinfo=HKT)
        cfg = tmp_path / "cfg.yml"
        cfg.write_text(yaml.dump({"cards": {"hsbc": {"active": True}}}))
        spending = tmp_path / "spending"
        spending.mkdir()
        assert assess_missing_statements(cfg, spending) == []

    @patch("metabolon.respirometry.payments.datetime")
    def test_empty_config_no_alerts(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 20, 12, 0, 0, tzinfo=HKT)
        cfg = tmp_path / "cfg.yml"
        cfg.write_text(yaml.dump({"cards": {}}))
        spending = tmp_path / "spending"
        spending.mkdir()
        assert assess_missing_statements(cfg, spending) == []


# ── flag_overdue_payments ─────────────────────────────────────────

class TestFlagOverduePayments:
    @patch("metabolon.respirometry.payments.datetime")
    def test_overdue_payment(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 5, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        persist_payments(f, [{"bank": "hsbc", "amount": 5000, "due_date": "2026-04-01"}])
        alerts = flag_overdue_payments(f)
        assert len(alerts) == 1
        assert "OVERDUE" in alerts[0]
        assert "HSBC" in alerts[0]

    @patch("metabolon.respirometry.payments.datetime")
    def test_due_soon(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 13, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        persist_payments(f, [{"bank": "hsbc", "amount": 5000, "due_date": "2026-04-15"}])
        alerts = flag_overdue_payments(f)
        assert len(alerts) == 1
        assert "due soon" in alerts[0].lower()
        assert "2 days left" in alerts[0]

    @patch("metabolon.respirometry.payments.datetime")
    def test_due_today(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 15, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        persist_payments(f, [{"bank": "hsbc", "amount": 5000, "due_date": "2026-04-15"}])
        alerts = flag_overdue_payments(f)
        assert len(alerts) == 1
        assert "0 days left" in alerts[0]

    @patch("metabolon.respirometry.payments.datetime")
    def test_not_due_soon(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 10, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        persist_payments(f, [{"bank": "hsbc", "amount": 5000, "due_date": "2026-04-20"}])
        assert flag_overdue_payments(f) == []

    def test_empty_file_no_alerts(self, tmp_path: Path):
        assert flag_overdue_payments(tmp_path / "none.yml") == []

    @patch("metabolon.respirometry.payments.datetime")
    def test_invalid_due_date_skipped(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 15, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        persist_payments(f, [{"bank": "hsbc", "amount": 5000, "due_date": "bad-date"}])
        assert flag_overdue_payments(f) == []

    @patch("metabolon.respirometry.payments.datetime")
    def test_date_object_as_due_date(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 13, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        persist_payments(f, [{"bank": "hsbc", "amount": 5000, "due_date": date(2026, 4, 15)}])
        alerts = flag_overdue_payments(f)
        assert len(alerts) == 1
        assert "due soon" in alerts[0].lower()

    @patch("metabolon.respirometry.payments.datetime")
    def test_datetime_object_as_due_date(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 13, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        persist_payments(f, [{"bank": "hsbc", "amount": 5000, "due_date": datetime(2026, 4, 15)}])
        alerts = flag_overdue_payments(f)
        assert len(alerts) == 1

    @patch("metabolon.respirometry.payments.datetime")
    def test_singular_day_label(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 14, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        persist_payments(f, [{"bank": "hsbc", "amount": 5000, "due_date": "2026-04-15"}])
        alerts = flag_overdue_payments(f)
        assert len(alerts) == 1
        assert "1 day left" in alerts[0]

    @patch("metabolon.respirometry.payments.datetime")
    def test_missing_due_date_key_skipped(self, mock_dt, tmp_path: Path):
        mock_dt.now.return_value = datetime(2026, 4, 15, 12, 0, 0, tzinfo=HKT)
        f = tmp_path / "pay.yml"
        persist_payments(f, [{"bank": "hsbc", "amount": 5000}])
        assert flag_overdue_payments(f) == []
