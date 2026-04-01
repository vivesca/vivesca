from __future__ import annotations

from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


def test_consumption_event_properties() -> None:
    # Test a charge (negative HKD)
    charge_event = ConsumptionEvent(
        date="2024-05-15",
        merchant="ParknShop",
        category="Groceries",
        currency="HKD",
        foreign_amount=None,
        hkd=-125.50,
    )
    assert charge_event.is_charge is True
    assert charge_event.is_credit is False

    # Test a credit (positive HKD)
    credit_event = ConsumptionEvent(
        date="2024-05-16",
        merchant="Refund",
        category="Refund",
        currency="HKD",
        foreign_amount=None,
        hkd=50.00,
    )
    assert credit_event.is_charge is False
    assert credit_event.is_credit is True

    # Test with foreign amount
    foreign_event = ConsumptionEvent(
        date="2024-05-17",
        merchant="Amazon US",
        currency="USD",
        foreign_amount=30.00,
        category="Shopping",
        hkd=-234.00,
    )
    assert foreign_event.is_charge is True
    assert foreign_event.foreign_amount == 30.00


def test_resirogram_meta_filename_stem() -> None:
    meta = RespirogramMeta(
        bank="mox",
        card="Mox Credit Card",
        period_start="2024-05-01",
        period_end="2024-05-31",
        statement_date="2024-05-31",
        balance=1500.00,
        minimum_due=150.00,
        due_date="2024-06-15",
        credit_limit=50000.00,
    )
    assert meta.filename_stem == "2024-05-mox"

    # Test another bank
    hsbc_meta = RespirogramMeta(
        bank="hsbc",
        card="HSBC Visa",
        period_start="2024-04-01",
        period_end="2024-04-30",
        statement_date="2024-04-30",
        balance=0.0,
        minimum_due=0.0,
        due_date="2024-05-15",
        credit_limit=100000.00,
    )
    assert hsbc_meta.filename_stem == "2024-04-hsbc"
