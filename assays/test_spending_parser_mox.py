"""Tests for Mox Credit statement parser."""

from pathlib import Path

import pytest

from metabolon.respirometry.parsers.mox import extract_mox
from metabolon.respirometry.schema import StatementMeta

FIXTURE = Path(__file__).parent / "fixtures" / "mox_jan2025.pdf"


@pytest.mark.skipif(not FIXTURE.exists(), reason="test fixture not available")
class TestMoxParser:
    def setup_method(self):
        self.meta, self.txns = extract_mox(FIXTURE)

    def test_returns_metadata(self):
        assert isinstance(self.meta, StatementMeta)
        assert self.meta.bank == "mox"
        assert self.meta.card == "Mox Credit"

    def test_statement_date(self):
        assert self.meta.statement_date == "2025-01-30"

    def test_period(self):
        assert self.meta.period_start == "31 Dec 2024"
        assert self.meta.period_end == "30 Jan 2025"

    def test_balance(self):
        assert self.meta.balance == -6004.03

    def test_credit_limit(self):
        assert self.meta.credit_limit == 108000.00

    def test_due_date(self):
        assert self.meta.due_date == "2025-02-24"

    def test_transaction_count(self):
        # 20 spending transactions (excluding internal transfer)
        charges = [t for t in self.txns if t.is_charge]
        assert len(charges) == 20

    def test_total_matches_balance(self):
        """Critical integrity check: parsed total must match statement balance."""
        total = sum(t.hkd for t in self.txns if t.category != "Transfer")
        assert abs(total - self.meta.balance) < 0.02  # float tolerance

    def test_foreign_currency_parsed(self):
        usd_txns = [t for t in self.txns if t.currency == "USD"]
        assert len(usd_txns) > 0
        for t in usd_txns:
            assert t.foreign_amount is not None

    def test_merchant_names_clean(self):
        merchants = [t.merchant for t in self.txns]
        # No trailing amounts in merchant names
        for m in merchants:
            assert not m.endswith(".00"), f"Merchant has trailing amount: {m}"
            assert not m.endswith(".40"), f"Merchant has trailing amount: {m}"

    def test_internal_transfer_excluded(self):
        """Internal Mox transfers should not appear as spending."""
        merchants = [t.merchant for t in self.txns]
        assert not any("Move between" in m for m in merchants)

    def test_known_merchants(self):
        merchants = {t.merchant for t in self.txns}
        assert "SMARTONE" in merchants
        assert "Bowtie Life Insurance" in merchants
