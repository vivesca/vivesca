"""Tests for vault writing, PDF archival, and deduplication."""

from metabolon.respirometry.schema import StatementMeta, Transaction
from metabolon.respirometry.vault import (
    serialize_markdown,
    is_processed,
    stamp_processed,
    secrete_monthly_summary,
)


def _sample_meta() -> StatementMeta:
    return StatementMeta(
        bank="mox",
        card="Mox Credit",
        period_start="31 Dec 2024",
        period_end="30 Jan 2025",
        statement_date="2025-01-30",
        balance=-600.00,
        minimum_due=220.00,
        due_date="2025-02-24",
        credit_limit=108000.00,
    )


def _sample_txns() -> list[Transaction]:
    return [
        Transaction(
            date="2025-01-02",
            merchant="GOOGLE",
            category="Tech/Subscriptions",
            currency="HKD",
            foreign_amount=None,
            hkd=-16.00,
        ),
        Transaction(
            date="2025-01-02",
            merchant="SMOL AI",
            category="Tech/AI",
            currency="USD",
            foreign_amount=-20.00,
            hkd=-158.40,
        ),
        Transaction(
            date="2025-01-07",
            merchant="SMARTONE",
            category="Telecom",
            currency="HKD",
            foreign_amount=None,
            hkd=-168.00,
        ),
    ]


def test_serialize_markdown_has_frontmatter():
    md = serialize_markdown(_sample_meta(), _sample_txns())
    assert md.startswith("---\n")
    assert "bank: mox" in md
    assert "balance: -600.0" in md


def test_serialize_markdown_has_transactions():
    md = serialize_markdown(_sample_meta(), _sample_txns())
    assert "| 02 Jan | GOOGLE |" in md
    assert "| 02 Jan | SMOL AI |" in md


def test_serialize_markdown_has_summary():
    md = serialize_markdown(_sample_meta(), _sample_txns())
    assert "## Summary" in md
    assert "Tech/AI" in md
    assert "Telecom" in md


def test_dedup_new_file(tmp_path):
    ledger = tmp_path / ".processed"
    assert not is_processed("abc123", ledger)


def test_dedup_after_mark(tmp_path):
    ledger = tmp_path / ".processed"
    stamp_processed("abc123", ledger)
    assert is_processed("abc123", ledger)
    assert not is_processed("def456", ledger)


def test_dedup_multiple(tmp_path):
    ledger = tmp_path / ".processed"
    stamp_processed("abc123", ledger)
    stamp_processed("def456", ledger)
    assert is_processed("abc123", ledger)
    assert is_processed("def456", ledger)


def test_monthly_summary_single_card(tmp_path):
    """Generate summary from one statement file."""
    md = tmp_path / "2025-01-mox.md"
    md.write_text(
        "---\nbank: mox\ncard: Mox Credit\nstatement_date: 2025-01-30\n"
        "balance: -600.0\n---\n\n## Transactions\n\n"
        "| Date | Merchant | Category | Currency | Foreign | HKD |\n"
        "|------|----------|----------|----------|---------|-----|\n"
        "| 02 Jan | GOOGLE | Tech/Subscriptions | HKD | | -16.00 |\n"
        "| 07 Jan | SMARTONE | Telecom | HKD | | -168.00 |\n\n"
        "## Summary\n\n"
        "| Category | Count | Total (HKD) |\n"
        "|----------|-------|-------------|\n"
        "| Tech/Subscriptions | 1 | -16.00 |\n"
        "| Telecom | 1 | -168.00 |\n"
        "| **Total** | **2** | **-184.00** |\n"
    )
    summary_path = secrete_monthly_summary("2025-01", tmp_path)
    assert summary_path.exists()
    content = summary_path.read_text()
    assert "month: 2025-01" in content
    assert "mox" in content.lower()


def test_monthly_summary_multi_card(tmp_path):
    """Aggregates across multiple cards."""
    for bank in ("mox", "hsbc"):
        md = tmp_path / f"2025-02-{bank}.md"
        md.write_text(
            f"---\nbank: {bank}\ncard: {bank.upper()} Card\n"
            f"statement_date: 2025-02-28\nbalance: -500.0\n---\n\n"
            "## Summary\n\n"
            "| Category | Count | Total (HKD) |\n"
            "|----------|-------|-------------|\n"
            "| Dining | 2 | -300.00 |\n"
            "| **Total** | **2** | **-300.00** |\n"
        )
    summary_path = secrete_monthly_summary("2025-02", tmp_path)
    content = summary_path.read_text()
    assert "cards:" in content
    assert "mox" in content
    assert "hsbc" in content
