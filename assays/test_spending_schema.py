"""Tests for spending transaction schema."""

from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


def test_transaction_charge():
    t = ConsumptionEvent(
        date="2025-01-02",
        merchant="SMOL AI COMPANY",
        category="Tech/AI",
        currency="USD",
        foreign_amount=-20.00,
        hkd=-158.40,
    )
    assert t.is_charge
    assert not t.is_credit


def test_transaction_credit():
    t = ConsumptionEvent(
        date="2025-01-12",
        merchant="LI HO MING TERRY",
        category="Transfer",
        currency="HKD",
        foreign_amount=None,
        hkd=8450.20,
    )
    assert t.is_credit
    assert not t.is_charge


def test_transaction_hkd_only():
    t = ConsumptionEvent(
        date="2025-01-08",
        merchant="SMARTONE",
        category="Telecom",
        currency="HKD",
        foreign_amount=None,
        hkd=-168.00,
    )
    assert t.foreign_amount is None
    assert t.currency == "HKD"


def test_statement_meta():
    m = RespirogramMeta(
        bank="mox",
        card="Mox Credit",
        period_start="31 Dec 2024",
        period_end="30 Jan 2025",
        statement_date="2025-01-30",
        balance=-6004.03,
        minimum_due=220.00,
        due_date="2025-02-24",
        credit_limit=108000.00,
    )
    assert m.bank == "mox"
    assert m.filename_stem == "2025-01-mox"


def test_statement_meta_filename_from_date():
    m = RespirogramMeta(
        bank="hsbc",
        card="HSBC Visa Signature",
        period_start="07 Jan 2025",
        period_end="06 Feb 2025",
        statement_date="2025-02-06",
        balance=-46417.99,
        minimum_due=469.00,
        due_date="2025-03-04",
        credit_limit=60000.00,
    )
    assert m.filename_stem == "2025-02-hsbc"
