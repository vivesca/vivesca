"""Tests for Standard Chartered Smart Credit Card statement PDF parser."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from metabolon.respirometry.parsers.scb import (
    _clean_merchant,
    _extract_metadata,
    _extract_purchases_total,
    _parse_transactions,
    extract_scb,
)
from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


def test_clean_merchant_removes_trailing_location():
    """Test that merchant cleaning removes trailing location/country codes."""
from __future__ import annotations

    cases = [
        ("SOME STORE HONG KONG HK", "SOME STORE"),
        ("CENTRAL STORE CENTRAL HK", "CENTRAL STORE"),
        ("GOOGLE GOOGLE.CO US", "GOOGLE"),
        ("AMAZON aws.amazon.c SG", "AMAZON"),
        ("X CORP X.AI/ABOUT US", "X CORP"),
        ("STREET SHOP KL HK", "STREET SHOP"),
        ("MULTIPLE  SPACES   SHOP", "MULTIPLE SPACES SHOP"),
        ("SINGAPORE SHOP SINGAPORE SG", "SINGAPORE SHOP"),
        ("LOCAL SHOP HK", "LOCAL SHOP"),
        ("STORE AT TOKYO TOKYO JP", "STORE AT TOKYO"),
    ]
    for input_text, expected in cases:
        result = _clean_merchant(input_text)
        assert result == expected, f"input: {input_text!r}, got {result!r}, expected {expected!r}"


def test_extract_metadata_dmy_slash():
    """Test metadata extraction with DD/MM/YYYY date format."""
    text = """
Statement Date: 31/03/2024
Payment Due Date: 15/04/2024
SMART CREDIT CARD 106,000264.00 26,345.39
STATEMENT BALANCE 26,345.39
MINIMUM PAYMENT DUE 264.00

03/01  100.00
03/15  250.50
    """
    meta = _extract_metadata(text)
    
    assert isinstance(meta, RespirogramMeta)
    assert meta.bank == "scb"
    assert meta.card == "SCB Smart Credit Card"
    assert meta.statement_date == "2024-03-31"
    assert meta.due_date == "2024-04-15"
    assert meta.credit_limit == 106000.0
    assert meta.balance == -26345.39
    assert meta.minimum_due == 264.00
    assert meta.period_start == "01 Mar 2024"
    assert meta.period_end == "31 Mar 2024"


def test_extract_metadata_d_mon_yyyy():
    """Test metadata extraction with DD Mon YYYY date format - matches the existing regex pattern expectation."""
    # The regex expects "Statement Date" -> any chars -> colon -> date.
    # (Non-greedy matches stops at first colon, so date must be right after first colon.)
    text = """
Statement Date:31 Mar 2024
Payment Due Date:15 Apr 2024
SMART CREDIT CARD 100,000
STATEMENT BALANCE 12,345.67
MINIMUM PAYMENT DUE 123.00
    """
    meta = _extract_metadata(text)
    
    assert meta.statement_date == "2024-03-31"
    assert meta.due_date == "2024-04-15"
    assert meta.credit_limit == 100000.0
    assert meta.balance == -12345.67
    assert meta.minimum_due == 123.00


def test_extract_metadata_partial():
    """Test metadata extraction with missing fields."""
    text = "Statement Date: 01/01/2024"
    meta = _extract_metadata(text)
    
    assert meta.statement_date == "2024-01-01"
    assert meta.due_date == ""
    assert meta.credit_limit == 0.0
    assert meta.balance == 0.0
    assert meta.minimum_due == 0.0


def test_extract_purchases_total_found():
    """Test extraction of purchases total from summary section."""
    text = """
Previous  Payments Credits Purchases Cash Charges Balance
100.00 200.00 50.00 1500.50 100.00 20.00 1470.50
    """
    result = _extract_purchases_total(text)
    # 4th group is Purchases
    assert result == 1500.50


def test_extract_purchases_total_not_found():
    """Test that _extract_purchases_total returns 0 when pattern doesn't match."""
    text = "No summary here"
    result = _extract_purchases_total(text)
    assert result == 0.0


def test_parse_transactions_hkd_only():
    """Test parsing of HKD domestic transactions."""
    text = """
Transaction Ref 1  THE STORE\xa0
Transaction Ref 2  ANOTHER SHOP\xa0
03/01  100.00
03/15  250.50
    """
    year_str = "2024"
    txns = _parse_transactions(text, year_str)
    
    assert len(txns) == 2
    assert all(isinstance(t, ConsumptionEvent) for t in txns)
    
    # First transaction
    assert txns[0].date == "2024-03-01"
    assert txns[0].merchant == "THE STORE"
    assert txns[0].currency == "HKD"
    assert txns[0].foreign_amount is None
    assert txns[0].hkd == -100.00
    assert txns[0].is_charge is True
    
    # Second transaction
    assert txns[1].date == "2024-03-15"
    assert txns[1].merchant == "ANOTHER SHOP"
    assert txns[1].currency == "HKD"
    assert txns[1].foreign_amount is None
    assert txns[1].hkd == -250.50


def test_parse_transactions_foreign_currency():
    """Test parsing of foreign currency transactions with FX info."""
    text = """
Foreign Currency USD 100.00, Rate 7.8
Transaction Ref 1  AMERICAN STORE\xa0
03/01  780.00
    """
    year_str = "2024"
    txns = _parse_transactions(text, year_str)
    
    assert len(txns) == 1
    assert txns[0].currency == "USD"
    assert txns[0].foreign_amount == -100.00
    assert txns[0].hkd == -780.00
    assert txns[0].merchant == "AMERICAN STORE"


def test_parse_transactions_skips_payment():
    """Test that PAYMENT entries are filtered out from transactions."""
    text = """
Transaction Ref 1  PURCHASE ONE\xa0
Transaction Ref 2  PAYMENT THANK YOU\xa0
Transaction Ref 3  PURCHASE TWO\xa0
03/01  100.00
03/05  500.00
03/10  200.00
    """
    year_str = "2024"
    txns = _parse_transactions(text, year_str)
    
    # Should filter out the PAYMENT description, leaving two purchases
    # which map to the first two amounts (100, 500)
    assert len(txns) == 2
    assert [t.hkd for t in txns] == [-100.00, -500.00]


def test_parse_transactions_with_commas_in_amount():
    """Test parsing of amounts with thousands separators."""
    text = """
Transaction Ref 1  BIG PURCHASE\xa0
03/01  1,234.56
    """
    year_str = "2024"
    txns = _parse_transactions(text, year_str)
    
    assert len(txns) == 1
    assert txns[0].hkd == -1234.56


def test_parse_transactions_handles_different_lengths():
    """Test that _parse_transactions handles mismatched desc/amount counts gracefully."""
    # Three descriptions, two amounts -> should return min(3, 2) = 2
    text = """
Transaction Ref 1  ONE\xa0
Transaction Ref 2  TWO\xa0
Transaction Ref 3  THREE\xa0
03/01  100.00
03/02  200.00
    """
    txns = _parse_transactions(text, "2024")
    assert len(txns) == 2


@patch("metabolon.respirometry.parsers.scb.PdfReader")
def test_extract_scb_success(mock_pdf_reader):
    """Test successful extraction with balance validation passes."""
    # Mock PDF pages
    mock_page1 = Mock()
    mock_page1.extract_text.return_value = """
Statement Date: 31/03/2024
Payment Due Date: 15/04/2024
SMART CREDIT CARD 100,000
STATEMENT BALANCE 350.00
MINIMUM PAYMENT DUE 35.00

Previous  Payments Credits Purchases Cash Charges Balance
0.00 0.00 0.00 350.00 0.00 0.00 350.00

Transaction Ref 1  STORE ONE\xa0
Transaction Ref 2  STORE TWO\xa0
03/01  150.00
03/15  200.00
    """
    mock_pdf_reader.return_value.pages = [mock_page1]
    
    from pathlib import Path
    meta, txns = extract_scb(Mock(spec=Path))
    
    assert isinstance(meta, RespirogramMeta)
    assert len(txns) == 2
    assert meta.statement_date == "2024-03-31"
    
    # Sum of charges: 150 + 200 = 350, matches purchases total
    charges = sum(abs(t.hkd) for t in txns if t.is_charge)
    assert charges == 350.00


@patch("metabolon.respirometry.parsers.scb.PdfReader")
def test_extract_scb_balance_mismatch_raises_value_error(mock_pdf_reader):
    """Test that ValueError is raised when balance validation fails."""
    mock_page1 = Mock()
    mock_page1.extract_text.return_value = """
Statement Date: 31/03/2024
Payment Due Date: 15/04/2024
SMART CREDIT CARD 100,000
STATEMENT BALANCE 350.00
MINIMUM PAYMENT DUE 35.00

Previous  Payments Credits Purchases Cash Charges Balance
0.00 0.00 0.00 350.00 0.00 0.00 350.00

Transaction Ref 1  STORE ONE\xa0
03/01  150.00
    """
    mock_pdf_reader.return_value.pages = [mock_page1]
    
    from pathlib import Path
    with pytest.raises(ValueError, match="Balance mismatch"):
        extract_scb(Mock(spec=Path))


def test_consumption_event_properties():
    """Test ConsumptionEvent is_charge and is_credit properties."""
    charge = ConsumptionEvent(
        date="2024-03-01",
        merchant="Test",
        category="",
        currency="HKD",
        foreign_amount=None,
        hkd=-100.0,
    )
    credit = ConsumptionEvent(
        date="2024-03-01",
        merchant="Refund",
        category="",
        currency="HKD", 
        foreign_amount=None,
        hkd=50.0,
    )
    
    assert charge.is_charge is True
    assert charge.is_credit is False
    assert credit.is_charge is False
    assert credit.is_credit is True


def test_respirogram_meta_filename_stem():
    """Test filename stem generation for RespirogramMeta."""
    meta = RespirogramMeta(
        bank="scb",
        card="Test Card",
        period_start="",
        period_end="",
        statement_date="2024-03-31",
        balance=0.0,
        minimum_due=0.0,
        due_date="",
        credit_limit=0.0,
    )
    
    assert meta.filename_stem == "2024-03-scb"
