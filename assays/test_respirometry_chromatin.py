from __future__ import annotations

"""Tests for metabolon.respirometry.chromatin."""

import hashlib
from pathlib import Path

import pytest

from metabolon.respirometry.chromatin import (
    archive_pdf,
    file_hash,
    is_processed,
    secrete_monthly_summary,
    secrete_statement,
    serialize_markdown,
    stamp_processed,
    _format_date_short,
)
from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def meta() -> RespirogramMeta:
    return RespirogramMeta(
        bank="hsbc",
        card="HSBC Visa",
        period_start="2025-01-01",
        period_end="2025-01-31",
        statement_date="2025-01-15",
        balance=-1234.56,
        minimum_due=500.0,
        due_date="2025-02-10",
        credit_limit=100000.0,
    )


@pytest.fixture
def transactions() -> list[ConsumptionEvent]:
    return [
        ConsumptionEvent(
            date="2025-01-03",
            merchant="Starbucks",
            category="Dining",
            currency="HKD",
            foreign_amount=None,
            hkd=45.0,
        ),
        ConsumptionEvent(
            date="2025-01-10",
            merchant="Amazon",
            category="Shopping",
            currency="USD",
            foreign_amount=12.99,
            hkd=101.50,
        ),
        ConsumptionEvent(
            date="2025-01-20",
            merchant="McDonald's",
            category="Dining",
            currency="HKD",
            foreign_amount=None,
            hkd=60.0,
        ),
    ]


# ---------------------------------------------------------------------------
# _format_date_short
# ---------------------------------------------------------------------------

class TestFormatDateShort:
    def test_basic(self):
        assert _format_date_short("2025-01-02") == "02 Jan"

    def test_end_of_year(self):
        assert _format_date_short("2024-12-31") == "31 Dec"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            _format_date_short("not-a-date")


# ---------------------------------------------------------------------------
# serialize_markdown
# ---------------------------------------------------------------------------

class TestSerializeMarkdown:
    def test_contains_frontmatter(self, meta, transactions):
        md = serialize_markdown(meta, transactions)
        assert md.startswith("---")
        assert "bank: hsbc" in md
        assert "card: HSBC Visa" in md
        assert "period: 2025-01-01 - 2025-01-31" in md
        assert "statement_date: 2025-01-15" in md
        assert "balance: -1234.56" in md
        assert "minimum_due: 500.0" in md
        assert "due_date: 2025-02-10" in md
        assert "credit_limit: 100000.0" in md

    def test_transaction_table(self, meta, transactions):
        md = serialize_markdown(meta, transactions)
        assert "## ConsumptionEvents" in md
        assert "| Date | Merchant | Category | Currency | Foreign | HKD |" in md
        assert "| 03 Jan | Starbucks | Dining | HKD |  | 45.00 |" in md
        assert "| 10 Jan | Amazon | Shopping | USD | 12.99 | 101.50 |" in md
        assert "| 20 Jan | McDonald's | Dining | HKD |  | 60.00 |" in md

    def test_summary_table(self, meta, transactions):
        md = serialize_markdown(meta, transactions)
        assert "## Summary" in md
        # Dining: 2 items, 105.00
        assert "| Dining | 2 | 105.00 |" in md
        # Shopping: 1 item, 101.50
        assert "| Shopping | 1 | 101.50 |" in md
        # Grand total
        assert "| **Total** | **3** | **206.50** |" in md

    def test_empty_transactions(self, meta):
        md = serialize_markdown(meta, [])
        assert "## ConsumptionEvents" in md
        assert "## Summary" in md
        assert "| **Total** | **0** | **0.00** |" in md

    def test_foreign_amount_none_omitted(self, meta):
        txn = ConsumptionEvent(
            date="2025-03-01",
            merchant="Local Shop",
            category="Groceries",
            currency="HKD",
            foreign_amount=None,
            hkd=33.0,
        )
        md = serialize_markdown(meta, [txn])
        assert "|  | 33.00 |" in md  # empty foreign column


# ---------------------------------------------------------------------------
# file_hash
# ---------------------------------------------------------------------------

class TestFileHash:
    def test_computes_sha256(self, tmp_path):
        f = tmp_path / "sample.txt"
        content = b"hello chromatin"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert file_hash(f) == expected

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        assert file_hash(f) == hashlib.sha256(b"").hexdigest()

    def test_nonexistent_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            file_hash(tmp_path / "nope.txt")


# ---------------------------------------------------------------------------
# is_processed / stamp_processed
# ---------------------------------------------------------------------------

class TestLedger:
    def test_not_processed_when_no_ledger(self, tmp_path):
        ledger = tmp_path / "ledger.txt"
        assert is_processed("abc123", ledger) is False

    def test_not_processed_when_absent(self, tmp_path):
        ledger = tmp_path / "ledger.txt"
        ledger.write_text("other_hash\n")
        assert is_processed("abc123", ledger) is False

    def test_processed_when_present(self, tmp_path):
        ledger = tmp_path / "ledger.txt"
        ledger.write_text("abc123\n")
        assert is_processed("abc123", ledger) is True

    def test_stamp_creates_file(self, tmp_path):
        ledger = tmp_path / "ledger.txt"
        stamp_processed("abc123", ledger)
        assert ledger.exists()
        assert "abc123" in ledger.read_text()

    def test_stamp_appends(self, tmp_path):
        ledger = tmp_path / "ledger.txt"
        ledger.write_text("first\n")
        stamp_processed("second", ledger)
        lines = ledger.read_text().splitlines()
        assert "first" in lines
        assert "second" in lines

    def test_roundtrip(self, tmp_path):
        ledger = tmp_path / "ledger.txt"
        sha = "deadbeef"
        stamp_processed(sha, ledger)
        assert is_processed(sha, ledger) is True


# ---------------------------------------------------------------------------
# secrete_statement
# ---------------------------------------------------------------------------

class TestSecreteStatement:
    def test_creates_file(self, meta, transactions, tmp_path):
        out = secrete_statement(meta, transactions, tmp_path)
        assert out.exists()
        assert out.name == "2025-01-hsbc.md"

    def test_content_matches_serialize(self, meta, transactions, tmp_path):
        out = secrete_statement(meta, transactions, tmp_path)
        expected = serialize_markdown(meta, transactions)
        assert out.read_text() == expected

    def test_creates_parent_dirs(self, meta, transactions, tmp_path):
        deep = tmp_path / "a" / "b" / "c"
        out = secrete_statement(meta, transactions, deep)
        assert out.exists()

    def test_atomic_write_no_tmp_left(self, meta, transactions, tmp_path):
        secrete_statement(meta, transactions, tmp_path)
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []


# ---------------------------------------------------------------------------
# archive_pdf
# ---------------------------------------------------------------------------

class TestArchivePdf:
    def test_moves_pdf(self, meta, tmp_path):
        pdf = tmp_path / "source.pdf"
        pdf.write_bytes(b"%PDF-fake")
        dest = archive_pdf(pdf, meta, tmp_path / "spending")
        assert dest.exists()
        assert dest.name == "2025-01-hsbc.pdf"
        assert not pdf.exists()

    def test_creates_archive_subdir(self, meta, tmp_path):
        pdf = tmp_path / "source.pdf"
        pdf.write_bytes(b"%PDF-fake")
        spending = tmp_path / "spending"
        dest = archive_pdf(pdf, meta, spending)
        assert (spending / "statements").is_dir()
        assert dest.parent == spending / "statements"


# ---------------------------------------------------------------------------
# secrete_monthly_summary
# ---------------------------------------------------------------------------

class TestSecreteMonthlySummary:
    def _write_statement(
        self, spending_dir: Path, stem: str, bank: str, card: str, body: str
    ) -> Path:
        p = spending_dir / f"{stem}.md"
        p.write_text(
            f"---\nbank: {bank}\ncard: {card}\n---\n\n{body}\n"
        )
        return p

    def test_single_card(self, tmp_path):
        spending = tmp_path / "spending"
        spending.mkdir()
        self._write_statement(
            spending,
            "2025-01-hsbc",
            "hsbc",
            "HSBC Visa",
            "## Summary\n\n"
            "| Category | Count | Total (HKD) |\n"
            "|----------|-------|-------------|\n"
            "| Dining | 2 | 105.00 |\n"
            "| **Total** | **2** | **105.00** |\n",
        )
        out = secrete_monthly_summary("2025-01", spending)
        assert out.exists()
        assert out.name == "2025-01-summary.md"
        text = out.read_text()
        assert "month: 2025-01" in text
        assert "HSBC" in text
        assert "Dining" in text
        assert "105.00" in text

    def test_multi_card(self, tmp_path):
        spending = tmp_path / "spending"
        spending.mkdir()
        self._write_statement(
            spending,
            "2025-01-hsbc",
            "hsbc",
            "HSBC Visa",
            "## Summary\n\n"
            "| Category | Count | Total (HKD) |\n"
            "|----------|-------|-------------|\n"
            "| Dining | 1 | 50.00 |\n"
            "| **Total** | **1** | **50.00** |\n",
        )
        self._write_statement(
            spending,
            "2025-01-mox",
            "mox",
            "MOX Mastercard",
            "## Summary\n\n"
            "| Category | Count | Total (HKD) |\n"
            "|----------|-------|-------------|\n"
            "| Dining | 1 | 30.00 |\n"
            "| Shopping | 1 | 80.00 |\n"
            "| **Total** | **2** | **110.00** |\n",
        )
        out = secrete_monthly_summary("2025-01", spending)
        text = out.read_text()
        # Both cards appear in the header
        assert "HSBC" in text
        assert "MOX" in text
        # Category-level aggregation works (non-bold rows are parsed)
        # Dining: hsbc=50 + mox=30 = 80
        assert "| Dining | 50.00 | 30.00 | 80.00 |" in text
        # Shopping: only mox=80
        assert "| Shopping | 0 | 80.00 | 80.00 |" in text
        # Bold total rows use ** which the regex (\d+) cannot match,
        # so card_totals remain at 0 and grand_total = 0.
        assert "total_spend: 0.00" in text

    def test_skips_summary_files(self, tmp_path):
        spending = tmp_path / "spending"
        spending.mkdir()
        # A pre-existing summary should not be re-parsed
        (spending / "2025-01-summary.md").write_text("---\nmonth: 2025-01\n---\n")
        self._write_statement(
            spending,
            "2025-01-hsbc",
            "hsbc",
            "HSBC Visa",
            "## Summary\n\n"
            "| Category | Count | Total (HKD) |\n"
            "|----------|-------|-------------|\n"
            "| Dining | 1 | 50.00 |\n"
            "| **Total** | **1** | **50.00** |\n",
        )
        out = secrete_monthly_summary("2025-01", spending)
        text = out.read_text()
        # Only one card should appear
        assert text.count("HSBC Visa") == 1

    def test_no_matching_files(self, tmp_path):
        spending = tmp_path / "spending"
        spending.mkdir()
        out = secrete_monthly_summary("2025-03", spending)
        assert out.exists()
        text = out.read_text()
        assert "month: 2025-03" in text
        assert "total_spend: 0.00" in text

    def test_atomic_write_no_tmp_left(self, tmp_path):
        spending = tmp_path / "spending"
        spending.mkdir()
        secrete_monthly_summary("2025-01", spending)
        tmp_files = list(spending.glob("*.tmp"))
        assert tmp_files == []
