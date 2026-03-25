"""Tests for spending monitors."""

from metabolon.respirometry.monitors import (
    assess_budget,
    flag_duplicates,
    assess_subscriptions,
    flag_anomalies,
)
from metabolon.respirometry.schema import Transaction


def _txn(merchant: str, hkd: float, category: str = "Dining") -> Transaction:
    return Transaction(
        date="2025-01-15",
        merchant=merchant,
        category=category,
        currency="HKD",
        foreign_amount=None,
        hkd=hkd,
    )


class TestUnknownHigh:
    def test_flags_unknown_over_500(self):
        txns = [_txn("WEIRD MERCHANT", -800.00, "Uncategorised")]
        alerts = flag_anomalies(txns)
        assert len(alerts) == 1
        assert "WEIRD MERCHANT" in alerts[0]

    def test_ignores_known_merchant(self):
        txns = [_txn("SMARTONE", -800.00, "Telecom")]
        alerts = flag_anomalies(txns)
        assert len(alerts) == 0

    def test_ignores_unknown_under_500(self):
        txns = [_txn("WEIRD MERCHANT", -100.00, "Uncategorised")]
        alerts = flag_anomalies(txns)
        assert len(alerts) == 0


class TestDuplicates:
    def test_flags_same_merchant_amount_date(self):
        txns = [
            _txn("GOOGLE", -78.00),
            _txn("GOOGLE", -78.00),
        ]
        alerts = flag_duplicates(txns)
        assert len(alerts) == 1

    def test_ignores_different_amounts(self):
        txns = [
            _txn("GOOGLE", -78.00),
            _txn("GOOGLE", -16.00),
        ]
        alerts = flag_duplicates(txns)
        assert len(alerts) == 0


class TestBudget:
    def test_under_budget(self):
        txns = [_txn("FOOD", -5000.00)]
        alerts = assess_budget(txns, monthly_budget=15000.00)
        assert len(alerts) == 0

    def test_at_80_percent(self):
        txns = [_txn("FOOD", -12500.00)]
        alerts = assess_budget(txns, monthly_budget=15000.00)
        assert len(alerts) == 1
        assert "83%" in alerts[0] or "80%" in alerts[0]

    def test_over_budget(self):
        txns = [_txn("FOOD", -16000.00)]
        alerts = assess_budget(txns, monthly_budget=15000.00)
        assert any("100%" in a or "exceed" in a.lower() for a in alerts)


class TestSubscriptions:
    def test_missing_subscription(self):
        expected = [{"merchant": "SMARTONE", "amount": -168.00}]
        txns = []  # no transactions at all
        alerts = assess_subscriptions(txns, expected)
        assert len(alerts) == 1
        assert "SMARTONE" in alerts[0]

    def test_subscription_present(self):
        expected = [{"merchant": "SMARTONE", "amount": -168.00}]
        txns = [_txn("SMARTONE", -168.00, "Telecom")]
        alerts = assess_subscriptions(txns, expected)
        assert len(alerts) == 0

    def test_price_change(self):
        expected = [{"merchant": "SMARTONE", "amount": -168.00}]
        txns = [_txn("SMARTONE", -200.00, "Telecom")]
        alerts = assess_subscriptions(txns, expected)
        assert len(alerts) == 1
        assert "price" in alerts[0].lower() or "change" in alerts[0].lower()
