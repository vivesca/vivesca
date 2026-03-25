"""Spending metabolism -- credit card statement parsing and monitoring."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from metabolon.spending.categories import categorise, load_categories
from metabolon.spending.detect import detect_bank, filename_matches
from metabolon.spending.monitors import run_all_monitors
from metabolon.spending.parsers import get_parser
from metabolon.spending.vault import (
    archive_pdf,
    file_hash,
    is_processed,
    mark_processed,
    write_statement,
)

SPENDING_DIR = Path.home() / "notes" / "Spending"
CATEGORIES_FILE = SPENDING_DIR / "categories.yaml"
CONFIG_FILE = SPENDING_DIR / "config.yaml"
PAYMENTS_FILE = SPENDING_DIR / "payments.yaml"
DEDUP_LEDGER = SPENDING_DIR / ".processed"
ACTA_DIR = Path.home() / "notes" / "ACTA"
HKT = timezone(timedelta(hours=8))


def process_statement(
    pdf_path: Path,
    spending_dir: Path = SPENDING_DIR,
    categories_file: Path = CATEGORIES_FILE,
    config_file: Path | None = None,
    payments_file: Path | None = None,
    move_pdf: bool = True,
) -> dict:
    """Parse a single statement PDF end-to-end.

    Returns dict with: bank, md_path, transactions, alerts, payment_action.
    Raises ValueError on balance validation failure.
    """
    from pypdf import PdfReader

    from metabolon.spending.payments import (
        add_pending_payment,
        create_payment_reminder,
        is_autopay,
    )

    if config_file is None:
        config_file = spending_dir / "config.yaml"
    if payments_file is None:
        payments_file = spending_dir / "payments.yaml"

    # Detect bank
    reader = PdfReader(pdf_path)
    page1 = reader.pages[0].extract_text() or ""
    bank = detect_bank(page1)
    if bank is None:
        return {"error": f"Unrecognised bank: {pdf_path.name}"}

    # Parse
    parser = get_parser(bank)
    if parser is None:
        return {"error": f"No parser for bank: {bank}"}

    meta, txns = parser(pdf_path)

    # Categorise
    cats = load_categories(categories_file)
    for t in txns:
        if not t.category:
            t.category = categorise(t.merchant, cats)

    # Write to vault
    md_path = write_statement(meta, txns, spending_dir)

    # Write monthly summary
    from metabolon.spending.vault import write_monthly_summary

    month = meta.statement_date[:7]  # YYYY-MM
    write_monthly_summary(month, spending_dir)

    # Archive PDF
    pdf_dest = None
    if move_pdf:
        pdf_dest = archive_pdf(pdf_path, meta, spending_dir)

    # Run monitors
    alerts = run_all_monitors(txns)

    # Payment tracking
    balance = abs(meta.balance)
    payment_action = None
    if is_autopay(bank, config_file):
        payment_action = (
            f"{bank.upper()}: autopay active, HKD {balance:,.2f} "
            f"will be deducted by {meta.due_date}"
        )
    else:
        add_pending_payment(
            payments_file,
            bank=bank,
            amount=balance,
            due_date=meta.due_date,
            statement_date=meta.statement_date,
        )
        create_payment_reminder(bank, balance, meta.due_date)
        payment_action = f"ACTION: Pay {bank.upper()} HKD {balance:,.2f} by {meta.due_date}"

    return {
        "bank": bank,
        "card": meta.card,
        "statement_date": meta.statement_date,
        "md_path": str(md_path),
        "pdf_archived": str(pdf_dest) if pdf_dest else None,
        "transaction_count": len(txns),
        "total_hkd": sum(t.hkd for t in txns),
        "alerts": alerts,
        "payment_action": payment_action,
    }


def scan_and_process(
    scan_path: Path | None = None,
    spending_dir: Path = SPENDING_DIR,
    move_pdf: bool = True,
) -> list[dict]:
    """Scan iCloud for new statement PDFs and process each.

    Returns list of results (one per processed statement).
    """
    if scan_path is None:
        scan_path = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"

    if not scan_path.exists():
        return [{"error": f"Scan path not found: {scan_path}"}]

    ledger = spending_dir / ".processed"
    results = []

    for pdf in sorted(scan_path.iterdir()):
        if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
            continue
        if not filename_matches(pdf.name):
            continue

        sha = file_hash(pdf)
        if is_processed(sha, ledger):
            continue

        try:
            result = process_statement(pdf, spending_dir=spending_dir, move_pdf=move_pdf)
            if "error" not in result:
                mark_processed(sha, ledger)
            results.append(result)
        except ValueError as e:
            results.append(
                {
                    "error": str(e),
                    "file": pdf.name,
                    "quarantined": True,
                }
            )

    # Write ACTA note summarising what was processed
    if results:
        successes = [r for r in results if "error" not in r]
        if successes:
            _write_acta(successes, results)

    return results


def _write_acta(successes: list[dict], all_results: list[dict]) -> None:
    """Write an ACTA note summarising processed statements."""
    ACTA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(HKT)
    ts = now.strftime("%Y-%m-%dT%H:%M%z")
    ts_prefix = now.strftime("%Y-%m-%d-%H%M")

    # Build summary
    parts = []
    for r in successes:
        total = r.get("total_hkd", 0)
        parts.append(
            f"{r['card']} ({r['statement_date']}): {r['transaction_count']} txns, HKD {total:,.2f}"
        )

    all_alerts = []
    for r in successes:
        all_alerts.extend(r.get("alerts", []))

    errors = [r for r in all_results if "error" in r]

    # Collect payment actions
    payment_actions = [r.get("payment_action") for r in successes if r.get("payment_action")]

    body_lines = []
    body_lines.append(f"Processed {len(successes)} statement(s).")
    for p in parts:
        body_lines.append(f"- {p}")
    if payment_actions:
        body_lines.append("")
        body_lines.append("Payments:")
        for pa in payment_actions:
            body_lines.append(f"- {pa}")
    if all_alerts:
        body_lines.append("")
        body_lines.append("Alerts:")
        for a in all_alerts:
            body_lines.append(f"- {a}")
    if errors:
        body_lines.append("")
        for e in errors:
            body_lines.append(f"Error: {e.get('error', 'unknown')}")

    body = "\n".join(body_lines)

    # Slug from first 60 chars of summary
    slug_src = body_lines[0].lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug_src).strip("-")[:60]

    content = f"---\nfrom: spending\nto: terry\nseverity: info\nts: {ts}\n---\n\n{body}\n"

    acta_path = ACTA_DIR / f"{ts_prefix}-{slug}.md"
    acta_path.write_text(content)
