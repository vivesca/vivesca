"""Tests for metabolon.respirometry.monitors."""

from metabolon.respirometry.schema import ConsumptionEvent
from metabolon.respirometry.monitors import (
    flag_anomalies,
    flag_duplicates,
    assess_budget,
    assess_subscriptions,
    activate_monitors,
)


def make_event(date: str, merchant: str, category: str, hkd: float) -> ConsumptionEvent:
    """Helper to make test ConsumptionEvent."""
    return ConsumptionEvent(
        date=date,
        merchant=merchant,
        category=category,
        currency="HKD",
        foreign_amount=None,
        hkd=hkd,
    )


class TestFlagAnomalies:
    """Tests for flag_anomalies."""

    def test_no_anomalies_when_under_threshold(self) -> None:
        """No alerts when uncategorised under threshold."""
        transactions = [
            make_event("2024-03-01", "UNKNOWN", "Uncategorised", -400.0),
        ]
        result = flag_anomalies(transactions, threshold=500.0)
        assert len(result) == 0

    def test_flags_uncategorised_over_threshold(self) -> None:
        """Flag uncategorised transactions over threshold."""
        transactions = [
            make_event("2024-03-01", "MYSTERY SHOP", "Uncategorised", -600.0),
            make_event("2024-03-02", "KNOWN", "Food", -1000.0),
        ]
        result = flag_anomalies(transactions, threshold=500.0)
        assert len(result) == 1
        assert "MYSTERY SHOP" in result[0]
        assert "600.00" in result[0]
        assert "2024-03-01" in result[0]


class TestFlagDuplicates:
    """Tests for flag_duplicates."""

    def test_no_duplicates_returns_empty(self) -> None:
        """No duplicates -> empty list."""
        transactions = [
            make_event("2024-03-01", "STARBUCKS", "Food", -45.0),
            make_event("2024-03-02", "STARBUCKS", "Food", -45.0),  # different date
        ]
        result = flag_duplicates(transactions)
        assert len(result) == 0

    def test_duplicates_flagged(self) -> None:
        """Multiple identical charges flagged."""
        transactions = [
            make_event("2024-03-01", "STARBUCKS", "Food", -45.0),
            make_event("2024-03-01", "STARBUCKS", "Food", -45.0),
            make_event("2024-03-01", "STARBUCKS", "Food", -45.0),
        ]
        result = flag_duplicates(transactions)
        assert len(result) == 1
        assert "STARBUCKS" in result[0]
        assert "45.00" in result[0]
        assert "(3x)" in result[0]

    def test_credits_not_checked(self) -> None:
        """Credits are not checked for duplicates."""
        transactions = [
            make_event("2024-03-01", "REFUND", "Refund", 45.0),
            make_event("2024-03-01", "REFUND", "Refund", 45.0),
        ]
        result = flag_duplicates(transactions)
        assert len(result) == 0  # because they are credits, not charges


class TestAssessBudget:
    """Tests for assess_budget."""

    def test_budget_not_exceeded_warning_below_80(self) -> None:
        """No alert when under 80%."""
        transactions = [
            make_event("2024-03-01", "A", "Food", -4000),
        ]
        result = assess_budget(transactions, 10000)
        assert len(result) == 0

    def test_budget_warning_between_80_100(self) -> None:
        """Warning between 80% and 100%."""
        transactions = [
            make_event("2024-03-01", "A", "Food", -8500),
        ]
        result = assess_budget(transactions, 10000)
        assert len(result) == 1
        assert "Budget warning" in result[0]
        assert "8,500/10,000" in result[0]
        assert "85%" in result[0]

    def test_budget_exceeded_over_100(self) -> None:
        """Alert when over budget."""
        transactions = [
            make_event("2024-03-01", "A", "Food", -12000),
        ]
        result = assess_budget(transactions, 10000)
        assert len(result) == 1
        assert "Budget exceeded" in result[0]
        assert "12,000/10,000" in result[0]

    def test_category_budgets(self) -> None:
        """Per-category budget checking."""
        transactions = [
            make_event("2024-03-01", "A", "Food", -2000),
            make_event("2024-03-01", "B", "Shopping", -3000),
            make_event("2024-03-01", "C", "Transport", -500),
        ]
        category_budgets = {
            "Food": 1500,  # over
            "Shopping": 3000,  # exactly at limit -> not over
            "Transport": 1000,  # under
            "Entertainment": 1000,  # no spending
        }
        result = assess_budget(transactions, 10000, category_budgets)
        assert len(result) == 1
        assert "Food over budget: 2,000/1,500" in result[0]

    def test_zero_monthly_budget_no_error(self) -> None:
        """Zero monthly budget handled without division by zero."""
        transactions = [make_event("2024-03-01", "A", "Food", -1000)]
        result = assess_budget(transactions, 0)
        assert len(result) == 0


class TestAssessSubscriptions:
    """Tests for assess_subscriptions."""

    def test_missing_subscription_flagged(self) -> None:
        """Missing subscription flagged."""
        transactions = [
            make_event("2024-03-01", "STARBUCKS", "Food", -45),
        ]
        expected = [
            {"merchant": "SMARTONE", "amount": -168},
        ]
        result = assess_subscriptions(transactions, expected)
        assert len(result) == 1
        assert "Missing subscription: SMARTONE" in result[0]

    def test_price_change_detected(self) -> None:
        """Price change beyond 5% detected."""
        transactions = [
            make_event("2024-03-01", "SMARTONE", "Bills", -180),
        ]
        expected = [
            {"merchant": "SMARTONE", "amount": -168},
        ]
        result = assess_subscriptions(transactions, expected)
        assert len(result) == 1
        assert "Subscription price change" in result[0]
        assert "168.00 -> -180.00" in result[0]

    def test_no_price_change_no_alert(self) -> None:
        """Small price difference (<5%) no alert."""
        transactions = [
            make_event("2024-03-01", "NETFLIX", "Entertainment", -48),
        ]
        expected = [
            {"merchant": "NETFLIX", "amount": -48},
        ]
        result = assess_subscriptions(transactions, expected)
        assert len(result) == 0

    def test_case_insensitive_prefix_match(self) -> None:
        """Case insensitive prefix matching works."""
        transactions = [
            make_event("2024-03-01", "smartone limited", "Bills", -168),
        ]
        expected = [
            {"merchant": "SMARTONE", "amount": -168},
        ]
        result = assess_subscriptions(transactions, expected)
        assert len(result) == 0


class TestActivateMonitors:
    """Tests for activate_monitors."""

    def test_runs_all_monitors(self) -> None:
        """Runs all monitors and combines alerts."""
        transactions = [
            make_event("2024-03-01", "UNKNOWN", "Uncategorised", -600),  # anomaly
            make_event("2024-03-01", "DUPE", "Food", -100),
            make_event("2024-03-01", "DUPE", "Food", -100),  # duplicate
        ]
        result = activate_monitors(transactions, monthly_budget=5000)
        assert len(result) == 2
        # One from each monitor that triggered
