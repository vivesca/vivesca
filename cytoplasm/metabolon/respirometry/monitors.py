"""Deterministic spending monitors -- fraud, budget, subscriptions."""

from __future__ import annotations

from collections import Counter

from metabolon.respirometry.schema import Transaction


def flag_anomalies(transactions: list[Transaction], threshold: float = 500.0) -> list[str]:
    """Flag uncategorised transactions above threshold."""
    alerts = []
    for t in transactions:
        if t.category == "Uncategorised" and abs(t.hkd) > threshold:
            alerts.append(f"Unknown merchant: {t.merchant} ({t.hkd:,.2f} HKD) on {t.date}")
    return alerts


def flag_duplicates(transactions: list[Transaction]) -> list[str]:
    """Flag potential duplicate charges (same merchant, amount, date)."""
    keys = Counter((t.date, t.merchant, t.hkd) for t in transactions if t.is_charge)
    alerts = []
    for (date, merchant, hkd), count in keys.items():
        if count > 1:
            alerts.append(f"Possible duplicate: {merchant} {hkd:,.2f} HKD on {date} ({count}x)")
    return alerts


def assess_budget(
    transactions: list[Transaction],
    monthly_budget: float,
    category_budgets: dict[str, float] | None = None,
) -> list[str]:
    """Check total spend against budget thresholds."""
    total_spend = sum(abs(t.hkd) for t in transactions if t.is_charge)
    pct = (total_spend / monthly_budget * 100) if monthly_budget else 0
    alerts = []

    if pct >= 100:
        alerts.append(
            f"Budget exceeded: {total_spend:,.0f}/{monthly_budget:,.0f} HKD ({pct:.0f}%)"
        )
    elif pct >= 80:
        alerts.append(f"Budget warning: {total_spend:,.0f}/{monthly_budget:,.0f} HKD ({pct:.0f}%)")

    # Per-category checks
    if category_budgets:
        cat_totals: dict[str, float] = {}
        for t in transactions:
            if t.is_charge:
                cat_totals[t.category] = cat_totals.get(t.category, 0) + abs(t.hkd)
        for cat, budget in category_budgets.items():
            spent = cat_totals.get(cat, 0)
            if spent > budget:
                alerts.append(f"{cat} over budget: {spent:,.0f}/{budget:,.0f} HKD")

    return alerts


def assess_subscriptions(
    transactions: list[Transaction],
    expected: list[dict],
) -> list[str]:
    """Check for missing or price-changed subscriptions.

    Each expected entry: {"merchant": "SMARTONE", "amount": -168.00}
    """
    alerts = []
    for sub in expected:
        merchant = sub["merchant"]
        expected_amount = sub["amount"]
        matches = [
            t
            for t in transactions
            if t.merchant.upper().startswith(merchant.upper()) and t.is_charge
        ]
        if not matches:
            alerts.append(f"Missing subscription: {merchant} (expected {expected_amount:.2f} HKD)")
        else:
            actual = matches[0].hkd
            if abs(actual - expected_amount) / abs(expected_amount) > 0.05:
                alerts.append(
                    f"Subscription price change: {merchant} ({expected_amount:.2f} -> {actual:.2f} HKD)"
                )
    return alerts


def activate_monitors(
    transactions: list[Transaction],
    monthly_budget: float = 15000.0,
    category_budgets: dict[str, float] | None = None,
    expected_subscriptions: list[dict] | None = None,
) -> list[str]:
    """Run all monitors and return combined alerts."""
    alerts: list[str] = []
    alerts.extend(flag_anomalies(transactions))
    alerts.extend(flag_duplicates(transactions))
    alerts.extend(assess_budget(transactions, monthly_budget, category_budgets))
    if expected_subscriptions:
        alerts.extend(assess_subscriptions(transactions, expected_subscriptions))
    return alerts
