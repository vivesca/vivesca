from __future__ import annotations

"""Tests for metabolon/respirometry/schema.py."""


from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta

# ── ConsumptionEvent tests ────────────────────────────────────────────────


def test_consumption_event_creation():
    """Test basic CreationEvent initialization."""
    event = ConsumptionEvent(
        date="2026-04-01",
        merchant="Coffee Shop",
        category="Food & Dining",
        currency="HKD",
        foreign_amount=None,
        hkd=-45.0,
    )
    assert event.date == "2026-04-01"
    assert event.merchant == "Coffee Shop"
    assert event.category == "Food & Dining"
    assert event.currency == "HKD"
    assert event.foreign_amount is None
    assert event.hkd == -45.0


def test_consumption_event_is_charge():
    """Test is_charge property (negative HKD)."""
    charge_event = ConsumptionEvent(
        date="2026-04-01",
        merchant="Coffee Shop",
        category="Food & Dining",
        currency="HKD",
        foreign_amount=None,
        hkd=-45.0,
    )
    assert charge_event.is_charge is True
    assert charge_event.is_credit is False


def test_consumption_event_is_credit():
    """Test is_credit property (positive HKD)."""
    credit_event = ConsumptionEvent(
        date="2026-04-01",
        merchant="Refund",
        category="Refunds",
        currency="HKD",
        foreign_amount=None,
        hkd=45.0,
    )
    assert credit_event.is_credit is True
    assert credit_event.is_charge is False


def test_consumption_event_with_foreign_amount():
    """Test ConsumptionEvent with foreign_amount set."""
    event = ConsumptionEvent(
        date="2026-04-01",
        merchant="Amazon US",
        category="Shopping",
        currency="USD",
        foreign_amount=29.99,
        hkd=-235.0,
    )
    assert event.currency == "USD"
    assert event.foreign_amount == 29.99
    assert event.hkd == -235.0


# ── RespirogramMeta tests ─────────────────────────────────────────────────


def test_resiprogram_meta_creation():
    """Test basic RespirogramMeta initialization."""
    meta = RespirogramMeta(
        bank="mox",
        card="Mox Credit Card",
        period_start="2026-03-01",
        period_end="2026-03-31",
        statement_date="2026-04-01",
        balance=5000.0,
        minimum_due=500.0,
        due_date="2026-04-21",
        credit_limit=100000.0,
    )
    assert meta.bank == "mox"
    assert meta.card == "Mox Credit Card"
    assert meta.period_start == "2026-03-01"
    assert meta.period_end == "2026-03-31"
    assert meta.statement_date == "2026-04-01"
    assert meta.balance == 5000.0
    assert meta.minimum_due == 500.0
    assert meta.due_date == "2026-04-21"
    assert meta.credit_limit == 100000.0


def test_resiprogram_meta_filename_stem():
    """Test filename_stem property."""
    meta = RespirogramMeta(
        bank="hsbc",
        card="HSBC Visa",
        period_start="2026-02-01",
        period_end="2026-02-28",
        statement_date="2026-03-05",
        balance=1234.56,
        minimum_due=123.46,
        due_date="2026-03-25",
        credit_limit=50000.0,
    )
    assert meta.filename_stem == "2026-03-hsbc"
