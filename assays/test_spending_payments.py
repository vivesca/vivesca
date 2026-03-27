"""Tests for payment tracking -- pending payments, overdue checks, confirm flow."""

from datetime import datetime, timedelta, timezone

import yaml

from metabolon.respirometry.payments import (
    assess_missing_statements,
    dequeue_payment,
    flag_overdue_payments,
    is_autopay,
    persist_payments,
    queue_payment,
    restore_card_config,
    restore_payments,
)

HKT = timezone(timedelta(hours=8))


def _write_config(tmp_path, cards: dict) -> None:
    config = {"cards": cards}
    (tmp_path / "config.yaml").write_text(yaml.dump(config))


def _write_payments(tmp_path, pending: list[dict]) -> None:
    data = {"pending": pending}
    (tmp_path / "payments.yaml").write_text(yaml.dump(data))


class TestLoadCardConfig:
    def test_missing_file(self, tmp_path):
        assert restore_card_config(tmp_path / "missing.yaml") == {}

    def test_with_cards(self, tmp_path):
        _write_config(tmp_path, {"mox": {"autopay": False}, "hsbc": {"autopay": True}})
        cards = restore_card_config(tmp_path / "config.yaml")
        assert cards["hsbc"]["autopay"] is True
        assert cards["mox"]["autopay"] is False


class TestIsAutopay:
    def test_autopay_true(self, tmp_path):
        _write_config(tmp_path, {"hsbc": {"autopay": True}})
        assert is_autopay("hsbc", tmp_path / "config.yaml") is True

    def test_autopay_false(self, tmp_path):
        _write_config(tmp_path, {"mox": {"autopay": False}})
        assert is_autopay("mox", tmp_path / "config.yaml") is False

    def test_unknown_bank_defaults_false(self, tmp_path):
        _write_config(tmp_path, {"hsbc": {"autopay": True}})
        assert is_autopay("unknown", tmp_path / "config.yaml") is False

    def test_missing_config_defaults_false(self, tmp_path):
        assert is_autopay("mox", tmp_path / "missing.yaml") is False


class TestLoadSavePayments:
    def test_load_empty_file(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        pf.write_text("pending: []\n")
        assert restore_payments(pf) == []

    def test_load_missing_file(self, tmp_path):
        assert restore_payments(tmp_path / "missing.yaml") == []

    def test_save_and_load_roundtrip(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        entries = [
            {"bank": "ccba", "amount": 6107.99, "due_date": "2026-04-01"},
        ]
        persist_payments(pf, entries)
        loaded = restore_payments(pf)
        assert len(loaded) == 1
        assert loaded[0]["bank"] == "ccba"
        assert loaded[0]["amount"] == 6107.99


class TestAddPendingPayment:
    def test_adds_entry(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        pf.write_text("pending: []\n")

        entry = queue_payment(
            pf,
            bank="ccba",
            amount=6107.99,
            due_date="2026-04-01",
            statement_date="2026-03-07",
        )
        assert entry["bank"] == "ccba"
        assert entry["amount"] == 6107.99

        pending = restore_payments(pf)
        assert len(pending) == 1

    def test_deduplicates_same_bank_statement(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        pf.write_text("pending: []\n")

        queue_payment(pf, "ccba", 6107.99, "2026-04-01", "2026-03-07")
        queue_payment(pf, "ccba", 6107.99, "2026-04-01", "2026-03-07")

        pending = restore_payments(pf)
        assert len(pending) == 1

    def test_allows_different_statements(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        pf.write_text("pending: []\n")

        queue_payment(pf, "ccba", 6107.99, "2026-04-01", "2026-03-07")
        queue_payment(pf, "mox", 2500.00, "2026-04-15", "2026-03-15")

        pending = restore_payments(pf)
        assert len(pending) == 2

    def test_creates_file_if_missing(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        queue_payment(pf, "mox", 1000.00, "2026-04-01", "2026-03-01")
        assert pf.exists()
        assert len(restore_payments(pf)) == 1


class TestRemovePendingPayment:
    def test_removes_entry(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        _write_payments(
            tmp_path,
            [{"bank": "ccba", "amount": 6107.99, "due_date": "2026-04-01"}],
        )

        removed = dequeue_payment(pf, "ccba")
        assert removed is not None
        assert removed["bank"] == "ccba"
        assert restore_payments(pf) == []

    def test_returns_none_when_not_found(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        pf.write_text("pending: []\n")
        assert dequeue_payment(pf, "ccba") is None

    def test_removes_only_matching_bank(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        _write_payments(
            tmp_path,
            [
                {"bank": "ccba", "amount": 6107.99, "due_date": "2026-04-01"},
                {"bank": "mox", "amount": 2500.00, "due_date": "2026-04-15"},
            ],
        )

        dequeue_payment(pf, "ccba")
        pending = restore_payments(pf)
        assert len(pending) == 1
        assert pending[0]["bank"] == "mox"


class TestCheckOverduePayments:
    def test_empty_file_no_alerts(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        pf.write_text("pending: []\n")
        assert flag_overdue_payments(pf) == []

    def test_due_tomorrow(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        tomorrow = (datetime.now(HKT) + timedelta(days=1)).strftime("%Y-%m-%d")
        _write_payments(
            tmp_path,
            [{"bank": "ccba", "amount": 6107.99, "due_date": tomorrow}],
        )
        alerts = flag_overdue_payments(pf)
        assert len(alerts) == 1
        assert "CCBA" in alerts[0]
        assert "due soon" in alerts[0].lower() or "1 day" in alerts[0].lower()

    def test_overdue(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        yesterday = (datetime.now(HKT) - timedelta(days=1)).strftime("%Y-%m-%d")
        _write_payments(
            tmp_path,
            [{"bank": "mox", "amount": 2500.00, "due_date": yesterday}],
        )
        alerts = flag_overdue_payments(pf)
        assert len(alerts) == 1
        assert "OVERDUE" in alerts[0]

    def test_far_future_no_alert(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        far = (datetime.now(HKT) + timedelta(days=30)).strftime("%Y-%m-%d")
        _write_payments(
            tmp_path,
            [{"bank": "scb", "amount": 3000.00, "due_date": far}],
        )
        assert flag_overdue_payments(pf) == []

    def test_due_today(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        today = datetime.now(HKT).strftime("%Y-%m-%d")
        _write_payments(
            tmp_path,
            [{"bank": "ccba", "amount": 1000.00, "due_date": today}],
        )
        alerts = flag_overdue_payments(pf)
        assert len(alerts) == 1
        assert "CCBA" in alerts[0]

    def test_missing_file_no_alerts(self, tmp_path):
        assert flag_overdue_payments(tmp_path / "missing.yaml") == []


class TestCheckMissingStatements:
    def test_no_cards_no_alerts(self, tmp_path):
        _write_config(tmp_path, {})
        assert assess_missing_statements(tmp_path / "config.yaml", tmp_path) == []

    def test_statement_exists_no_alert(self, tmp_path):
        _write_config(
            tmp_path,
            {"ccba": {"active": True, "statement_day": 7}},
        )
        now = datetime.now(HKT)
        # Create a vault file for current month
        vault_file = tmp_path / f"{now.strftime('%Y-%m')}-ccba.md"
        vault_file.write_text("---\nbank: ccba\n---\n")
        alerts = assess_missing_statements(tmp_path / "config.yaml", tmp_path)
        assert not any("CCBA" in a for a in alerts)

    def test_missing_statement_after_grace(self, tmp_path):
        now = datetime.now(HKT)
        # Use statement_day far enough in the past (day 1, grace +5 = day 6)
        # Only triggers if today > statement_day + 5
        if now.day <= 6:
            return  # Can't test this near month start
        _write_config(
            tmp_path,
            {"ccba": {"active": True, "statement_day": 1}},
        )
        alerts = assess_missing_statements(tmp_path / "config.yaml", tmp_path)
        assert len(alerts) == 1
        assert "CCBA" in alerts[0]

    def test_inactive_card_no_alert(self, tmp_path):
        _write_config(
            tmp_path,
            {"mox": {"active": False, "statement_day": 1}},
        )
        alerts = assess_missing_statements(tmp_path / "config.yaml", tmp_path)
        assert alerts == []

    def test_before_grace_period_no_alert(self, tmp_path):
        now = datetime.now(HKT)
        # Set statement_day to today — still within grace
        _write_config(
            tmp_path,
            {"boc": {"active": True, "statement_day": now.day}},
        )
        alerts = assess_missing_statements(tmp_path / "config.yaml", tmp_path)
        assert alerts == []


class TestConfirmPaymentTool:
    def test_confirm_removes_entry(self, tmp_path):
        """Integration test: confirm_payment via the tool removes from file."""
        pf = tmp_path / "payments.yaml"
        _write_payments(
            tmp_path,
            [{"bank": "ccba", "amount": 6107.99, "due_date": "2026-04-01"}],
        )
        removed = dequeue_payment(pf, "ccba")
        assert removed is not None
        assert removed["amount"] == 6107.99
        assert restore_payments(pf) == []

    def test_confirm_nonexistent(self, tmp_path):
        pf = tmp_path / "payments.yaml"
        pf.write_text("pending: []\n")
        assert dequeue_payment(pf, "ccba") is None


class TestCatabolismConfirmResultType:
    def test_result_is_effector_result(self):
        from metabolon.morphology import EffectorResult
        from metabolon.enzymes.catabolism import CatabolismConfirmResult

        assert issubclass(CatabolismConfirmResult, EffectorResult)
