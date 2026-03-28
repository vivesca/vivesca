"""Tests for Standard Chartered Smart Credit Card statement parser."""

from pathlib import Path

import pytest

from metabolon.respirometry.parsers.scb import extract_scb
from metabolon.respirometry.schema import RespirogramMeta

FIXTURE = Path(__file__).parent / "fixtures" / "scb_mar2026.pdf"


@pytest.mark.skipif(not FIXTURE.exists(), reason="test fixture not available")
class TestScbParser:
    def setup_method(self):
        self.meta, self.txns = extract_scb(FIXTURE)

    def test_returns_metadata(self):
        assert isinstance(self.meta, RespirogramMeta)
        assert self.meta.bank == "scb"
        assert self.meta.card == "SCB Smart Credit Card"

    def test_statement_date(self):
        assert self.meta.statement_date == "2026-03-10"

    def test_balance(self):
        assert self.meta.balance == -26345.39

    def test_credit_limit(self):
        assert self.meta.credit_limit == 106000.00

    def test_due_date(self):
        assert self.meta.due_date == "2026-04-07"

    def test_minimum_due(self):
        assert self.meta.minimum_due == 264.00

    def test_purchases_total_matches(self):
        """Critical integrity check: parsed charges must match statement purchases total."""
        charges = sum(abs(t.hkd) for t in self.txns if t.is_charge)
        assert abs(charges - 27345.39) < 0.02

    def test_payment_excluded(self):
        merchants = [t.merchant for t in self.txns]
        assert not any("PAYMENT" in m.upper() for m in merchants)

    def test_foreign_currency_parsed(self):
        fx_txns = [t for t in self.txns if t.currency != "HKD"]
        assert len(fx_txns) > 0
        for t in fx_txns:
            assert t.foreign_amount is not None

    def test_transaction_count(self):
        assert len(self.txns) == 70
