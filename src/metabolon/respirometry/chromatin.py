from __future__ import annotations

"""Write parsed statements to chromatin as markdown."""


import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path

from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


def serialize_markdown(meta: RespirogramMeta, transactions: list[ConsumptionEvent]) -> str:
    """Generate chromatin markdown from parsed statement data."""
    lines: list[str] = []

    # Frontmatter
    lines.append("---")
    lines.append(f"bank: {meta.bank}")
    lines.append(f"card: {meta.card}")
    lines.append(f"period: {meta.period_start} - {meta.period_end}")
    lines.append(f"statement_date: {meta.statement_date}")
    lines.append(f"balance: {meta.balance}")
    lines.append(f"minimum_due: {meta.minimum_due}")
    lines.append(f"due_date: {meta.due_date}")
    lines.append(f"credit_limit: {meta.credit_limit}")
    lines.append("---")
    lines.append("")

    # ConsumptionEvents
    lines.append("## ConsumptionEvents")
    lines.append("")
    lines.append("| Date | Merchant | Category | Currency | Foreign | HKD |")
    lines.append("|------|----------|----------|----------|---------|-----|")

    for t in transactions:
        date_short = _format_date_short(t.date)
        foreign = f"{t.foreign_amount:.2f}" if t.foreign_amount else ""
        hkd = f"{t.hkd:,.2f}"
        lines.append(
            f"| {date_short} | {t.merchant} | {t.category} | {t.currency} | {foreign} | {hkd} |"
        )

    lines.append("")

    # Summary by category
    cats: dict[str, dict[str, float | int]] = {}
    for t in transactions:
        if t.category not in cats:
            cats[t.category] = {"count": 0, "total": 0.0}
        cats[t.category]["count"] += 1
        cats[t.category]["total"] += t.hkd

    sorted_cats = sorted(cats.items(), key=lambda x: x[1]["total"])

    lines.append("## Summary")
    lines.append("")
    lines.append("| Category | Count | Total (HKD) |")
    lines.append("|----------|-------|-------------|")
    for cat, data in sorted_cats:
        lines.append(f"| {cat} | {int(data['count'])} | {data['total']:,.2f} |")
    total = sum(t.hkd for t in transactions)
    lines.append(f"| **Total** | **{len(transactions)}** | **{total:,.2f}** |")
    lines.append("")

    return "\n".join(lines)


def _format_date_short(iso_date: str) -> str:
    """'2025-01-02' -> '02 Jan'"""
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return dt.strftime("%d %b")


def file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_processed(sha: str, ledger: Path) -> bool:
    """Check if a file hash has already been processed."""
    if not ledger.exists():
        return False
    return sha in ledger.read_text().splitlines()


def stamp_processed(sha: str, ledger: Path) -> None:
    """Record a file hash as processed."""
    with open(ledger, "a") as f:
        f.write(sha + "\n")


def secrete_statement(
    meta: RespirogramMeta,
    transactions: list[ConsumptionEvent],
    spending_dir: Path,
) -> Path:
    """Write parsed statement and return the file path."""
    spending_dir.mkdir(parents=True, exist_ok=True)
    md_path = spending_dir / f"{meta.filename_stem}.md"
    tmp = md_path.with_suffix(".md.tmp")
    tmp.write_text(serialize_markdown(meta, transactions))
    tmp.replace(md_path)
    return md_path


def archive_pdf(pdf_path: Path, meta: RespirogramMeta, spending_dir: Path) -> Path:
    """Move original PDF to archive."""
    archive_dir = spending_dir / "statements"
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / f"{meta.filename_stem}.pdf"
    shutil.move(str(pdf_path), str(dest))  # shutil handles cross-filesystem
    return dest


def secrete_monthly_summary(month: str, spending_dir: Path) -> Path:
    """Generate/update YYYY-MM-summary.md aggregating all cards for the month.

    Args:
        month: YYYY-MM string
        spending_dir: spending directory
    """
    # Find all per-statement files for this month
    statements = sorted(spending_dir.glob(f"{month}-*.md"))
    statements = [s for s in statements if not s.name.endswith("-summary.md")]

    cards: list[str] = []
    all_categories: dict[str, dict[str, float]] = {}  # cat -> {card: total}
    card_totals: dict[str, dict] = {}

    for stmt_path in statements:
        text = stmt_path.read_text()
        # Extract bank from frontmatter
        bank = ""
        card_name = ""
        for line in text.splitlines():
            if line.startswith("bank: "):
                bank = line.split(": ", 1)[1]
            elif line.startswith("card: "):
                card_name = line.split(": ", 1)[1]
        if not bank:
            continue
        cards.append(bank)

        # Parse category totals from summary table
        txn_count = 0
        total = 0.0
        for m in re.finditer(r"\| (.+?) \| (\d+) \| (-?[\d,]+\.\d{2}) \|", text):
            cat = m.group(1).strip()
            if cat.startswith("**"):
                txn_count = int(m.group(2).strip("*"))
                total = float(m.group(3).strip("*").replace(",", ""))
                continue
            cat_total = float(m.group(3).replace(",", ""))
            if cat not in all_categories:
                all_categories[cat] = {}
            all_categories[cat][bank] = cat_total

        card_totals[bank] = {
            "card": card_name,
            "count": txn_count,
            "total": total,
        }

    # Build summary markdown
    grand_total = sum(ct["total"] for ct in card_totals.values())
    lines = [
        "---",
        f"month: {month}",
        f"cards: [{', '.join(cards)}]",
        f"total_spend: {grand_total:.2f}",
        "---",
        "",
        "## By Category",
        "",
    ]

    # Header with card columns
    header = "| Category |"
    sep = "|----------|"
    for bank in cards:
        header += f" {bank.upper()} |"
        sep += "------|"
    header += " Total |"
    sep += "-------|"
    lines.extend([header, sep])

    for cat in sorted(all_categories.keys()):
        row = f"| {cat} |"
        cat_total = 0.0
        for bank in cards:
            val = all_categories[cat].get(bank, 0)
            cat_total += val
            row += f" {val:,.2f} |" if val else " 0 |"
        row += f" {cat_total:,.2f} |"
        lines.append(row)

    lines.extend(
        [
            "",
            "## By Card",
            "",
            "| Card | ConsumptionEvents | Total (HKD) |",
            "|------|-------------|-------------|",
        ]
    )
    for bank in cards:
        ct = card_totals[bank]
        lines.append(f"| {ct['card']} | {ct['count']} | {ct['total']:,.2f} |")
    lines.append("")

    summary_path = spending_dir / f"{month}-summary.md"
    tmp = summary_path.with_suffix(".md.tmp")
    tmp.write_text("\n".join(lines))
    tmp.replace(summary_path)
    return summary_path
