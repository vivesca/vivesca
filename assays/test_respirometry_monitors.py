from __future__ import annotations

from metabolon.respirometry.monitors import (
    activate_monitors,
    assess_budget,
    assess_subscriptions,
    flag_anomalies,
    flag_duplicates,
)
from metabolon.respirometry.schema import ConsumptionEvent


def test_flag_anomalies_no_flags():
    """Test that categorized transactions below threshold are not flagged."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Grocery Store",
            category="Groceries",
            currency="HKD",
            foreign_amount=None,
            hkd=-100.0,
        ),
        ConsumptionEvent(
            date="2024-01-02",
            merchant="Uncategorized Small",
            category="Uncategorised",
            currency="HKD",
            foreign_amount=None,
            hkd=-100.0,
        ),
    ]
    alerts = flag_anomalies(transactions)
    assert len(alerts) == 0


def test_flag_anomalies_flags_above_threshold():
    """Test that uncategorized transactions above threshold are flagged."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Big Unknown Purchase",
            category="Uncategorised",
            currency="HKD",
            foreign_amount=None,
            hkd=-600.0,
        ),
        ConsumptionEvent(
            date="2024-01-02",
            merchant="Credit Refund",
            category="Uncategorised",
            currency="HKD",
            foreign_amount=None,
            hkd=600.0,
        ),
    ]
    alerts = flag_anomalies(transactions, threshold=500.0)
    # Both should be flagged because abs(t.hkd) > threshold
    assert len(alerts) == 2
    assert any("Big Unknown Purchase" in alert for alert in alerts)
    assert any("600.00" in alert for alert in alerts)


def test_flag_duplicates_no_duplicates():
    """Test no duplicates returns empty alerts."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Store A",
            category="Shopping",
            currency="HKD",
            foreign_amount=None,
            hkd=-100.0,
        ),
        ConsumptionEvent(
            date="2024-01-02",
            merchant="Store A",
            category="Shopping",
            currency="HKD",
            foreign_amount=None,
            hkd=-100.0,
        ),
    ]
    alerts = flag_duplicates(transactions)
    assert len(alerts) == 0  # Different dates, no duplicate


def test_flag_duplicates_flags_duplicates():
    """Test that duplicates are flagged correctly."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Cafe X",
            category="Food",
            currency="HKD",
            foreign_amount=None,
            hkd=-50.0,
        ),
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Cafe X",
            category="Food",
            currency="HKD",
            foreign_amount=None,
            hkd=-50.0,
        ),
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Cafe X",
            category="Food",
            currency="HKD",
            foreign_amount=None,
            hkd=50.0,  # credit, should not count
        ),
    ]
    alerts = flag_duplicates(transactions)
    assert len(alerts) == 1
    assert "Cafe X" in alerts[0]
    assert "2x" in alerts[0]


def test_assess_budget_under_warning():
    """Test budget assessment below 80% has no alerts."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Store",
            category="Shopping",
            currency="HKD",
            foreign_amount=None,
            hkd=-7000.0,
        ),
    ]
    alerts = assess_budget(transactions, monthly_budget=10000.0)
    assert len(alerts) == 0


def test_assess_budget_warning():
    """Test budget assessment 80-100% gives warning."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Store",
            category="Shopping",
            currency="HKD",
            foreign_amount=None,
            hkd=-8500.0,
        ),
    ]
    alerts = assess_budget(transactions, monthly_budget=10000.0)
    assert len(alerts) == 1
    assert "Budget warning" in alerts[0]
    assert "8,500/10,000" in alerts[0]
    assert "85%" in alerts[0]


def test_assess_budget_exceeded():
    """Test budget assessment over 100% gives exceeded alert."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Store",
            category="Shopping",
            currency="HKD",
            foreign_amount=None,
            hkd=-12000.0,
        ),
    ]
    alerts = assess_budget(transactions, monthly_budget=10000.0)
    assert len(alerts) == 1
    assert "Budget exceeded" in alerts[0]


def test_assess_budget_zero_budget():
    """Test zero monthly budget handles division by zero."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Store",
            category="Shopping",
            currency="HKD",
            foreign_amount=None,
            hkd=-100.0,
        ),
    ]
    alerts = assess_budget(transactions, monthly_budget=0.0)
    assert len(alerts) == 0


def test_assess_budget_category_over():
    """Test category budgets are checked correctly."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Grocer",
            category="Groceries",
            currency="HKD",
            foreign_amount=None,
            hkd=-6000.0,
        ),
        ConsumptionEvent(
            date="2024-01-02",
            merchant="Dining",
            category="Dining",
            currency="HKD",
            foreign_amount=None,
            hkd=-2000.0,
        ),
    ]
    category_budgets = {
        "Groceries": 5000.0,
        "Dining": 3000.0,
    }
    alerts = assess_budget(transactions, monthly_budget=15000.0, category_budgets=category_budgets)
    assert len(alerts) == 1
    assert "Groceries over budget" in alerts[0]
    assert "6,000/5,000" in alerts[0]


def test_assess_subscriptions_missing():
    """Test missing subscriptions are flagged."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="HKT",
            category="Utilities",
            currency="HKD",
            foreign_amount=None,
            hkd=-298.0,
        ),
    ]
    expected = [
        {"merchant": "HKT", "amount": -298.0},
        {"merchant": "SMARTONE", "amount": -168.0},
    ]
    alerts = assess_subscriptions(transactions, expected)
    assert len(alerts) == 1
    assert "Missing subscription: SMARTONE" in alerts[0]


def test_assess_subscriptions_price_change():
    """Test significant price changes are flagged."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="smartone",
            category="Utilities",
            currency="HKD",
            foreign_amount=None,
            hkd=-180.0,
        ),
    ]
    expected = [
        {"merchant": "SMARTONE", "amount": -168.0},
    ]
    alerts = assess_subscriptions(transactions, expected)
    assert len(alerts) == 1
    assert "Subscription price change" in alerts[0]
    assert "168.00 -> -180.00" in alerts[0]


def test_assess_subscriptions_no_change():
    """Test when price change is within 5% no alert is generated."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Disney",
            category="Entertainment",
            currency="HKD",
            foreign_amount=None,
            hkd=-62.0,
        ),
    ]
    expected = [
        {"merchant": "Disney", "amount": -60.0},
    ]
    # (62-60)/60 = 3.3% < 5% → no alert
    alerts = assess_subscriptions(transactions, expected)
    assert len(alerts) == 0


def test_activate_monitors_runs_all():
    """Test activate_monitors runs all monitors and combines alerts."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Unknown Big",
            category="Uncategorised",
            currency="HKD",
            foreign_amount=None,
            hkd=-600.0,
        ),
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Dupe Shop",
            category="Shopping",
            currency="HKD",
            foreign_amount=None,
            hkd=-100.0,
        ),
        ConsumptionEvent(
            date="2024-01-01",
            merchant="Dupe Shop",
            category="Shopping",
            currency="HKD",
            foreign_amount=None,
            hkd=-100.0,
        ),
    ]
    # Total spend = 600 + 100 + 100 = 800 → 80% of 1000 → triggers warning
    # So expect 3 alerts total
    alerts = activate_monitors(
        transactions,
        monthly_budget=1000.0,
    )
    # Should have three alerts: one anomaly, one duplicate, one budget warning
    assert len(alerts) == 3


def test_activate_monitors_with_subscriptions():
    """Test activate_monitors includes subscription checks when expected is provided."""
    transactions = [
        ConsumptionEvent(
            date="2024-01-01",
            merchant="HKT",
            category="Utilities",
            currency="HKD",
            foreign_amount=None,
            hkd=-298.0,
        ),
    ]
    alerts = activate_monitors(
        transactions,
        monthly_budget=10000.0,
        expected_subscriptions=[
            {"merchant": "HKT", "amount": -298.0},
            {"merchant": "Missing", "amount": -100.0},
        ],
    )
    assert len(alerts) == 1
    assert "Missing subscription" in alerts[0]
