"""Tests for CCBA eye Credit Card statement parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from metabolon.respirometry.parsers.ccba import extract_ccba
from metabolon.respirometry.schema import RespirogramMeta

FIXTURE = Path(__file__).parent / "fixtures" / "ccba_sep2025.pdf"
FIXTURE_MAR = Path(__file__).parent / "fixtures" / "ccba_mar2026.pdf"


@pytest.mark.skipif(not FIXTURE.exists(), reason="test fixture not available")
class TestCcbaParser:
    def setup_method(self):
        self.meta, self.txns = extract_ccba(FIXTURE)

    def test_returns_metadata(self):
        assert isinstance(self.meta, RespirogramMeta)
        assert self.meta.bank == "ccba"
        assert self.meta.card == "CCBA eye Credit Card"

    def test_statement_date(self):
        assert self.meta.statement_date == "2025-09-07"

    def test_balance(self):
        assert self.meta.balance == -2021.59

    def test_credit_limit(self):
        assert self.meta.credit_limit == 49000.00

    def test_due_date(self):
        assert self.meta.due_date == "2025-10-02"

    def test_minimum_due(self):
        assert self.meta.minimum_due == 220.00

    def test_total_matches_balance(self):
        """Critical integrity check: parsed total must match statement balance."""
        total = sum(t.hkd for t in self.txns)
        assert abs(total - self.meta.balance) < 0.02

    def test_payment_excluded(self):
        merchants = [t.merchant for t in self.txns]
        assert not any("PPS PAYMENT" in m.upper() for m in merchants)

    def test_foreign_currency_parsed(self):
        usd_txns = [t for t in self.txns if t.currency == "USD"]
        assert len(usd_txns) > 0
        for t in usd_txns:
            assert t.foreign_amount is not None

    def test_cross_border_fee_merged(self):
        """Cross-border fees should be merged, not standalone."""
        merchants = [t.merchant for t in self.txns]
        assert not any("CROSS-BORDER" in m.upper() for m in merchants)


@pytest.mark.skipif(not FIXTURE_MAR.exists(), reason="test fixture not available")
class TestCcbaParserMar:
    def setup_method(self):
        self.meta, self.txns = extract_ccba(FIXTURE_MAR)

    def test_statement_date(self):
        assert self.meta.statement_date == "2026-03-07"

    def test_balance(self):
        assert self.meta.balance == -6107.99

    def test_total_matches_balance(self):
        """Balance validation on Mar 2026 fixture."""
        total = sum(t.hkd for t in self.txns)
        assert abs(total - self.meta.balance) < 0.02
