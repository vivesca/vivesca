"""CCBA eye Credit Card statement PDF parser."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

from metabolon.respirometry.schema import StatementMeta, Transaction

# Transaction line: description HKD amount [CR] Mon DD,YYYY Mon DD,YYYY
# Dates are adjacent to the amount/CR flag with no separating whitespace in
# pypdf-extracted text, so whitespace before the first date is optional.
_TXN_PAT = re.compile(
    r"^(.+?)\s+HKD\s+([\d,]+\.\d{2})\s*(CR)?"
    r"(\w{3} \d{2},\d{4})\s*(\w{3} \d{2},\d{4})"
)


def parse_ccba(pdf_path: Path) -> tuple[StatementMeta, list[Transaction]]:
    """Parse a CCBA eye Credit Card statement PDF.

    Returns (metadata, transactions). Raises ValueError if balance validation
    fails.
    """
    reader = PdfReader(pdf_path)

    full_text = ""
    for page in reader.pages:
        text = page.extract_text() or ""
        full_text += text + "\n"

    meta = _extract_metadata(full_text)
    txns = _parse_transactions(full_text)

    # Balance validation
    spending_total = sum(t.hkd for t in txns)
    if abs(spending_total - meta.balance) > 0.02:
        msg = f"Balance mismatch: parsed {spending_total:.2f}, statement says {meta.balance:.2f}"
        raise ValueError(msg)

    return meta, txns


def _extract_metadata(text: str) -> StatementMeta:
    """Extract statement-level metadata from PDF text."""
    # Statement date (fullwidth colon \uff1a in Chinese label)
    stmt_match = re.search(
        r"Statement Date\s*\u6708\u7d50\u55ae\u622a\u6578\u65e5[\uff1a:]\s*(\w{3} \d{2},\s*\d{4})",
        text,
    )
    statement_date = ""
    if stmt_match:
        dt = datetime.strptime(stmt_match.group(1).replace(" ", ""), "%b%d,%Y")
        statement_date = dt.strftime("%Y-%m-%d")

    # Credit limit, available credit, outstanding balance
    # Pattern: HKD amount\nHKD amount\nHKD amount\nRMB
    limits = re.search(
        r"HKD\s*([\d,]+\.\d{2})\s*\n"
        r"HKD\s*([\d,]+\.\d{2})\s*\n"
        r"HKD\s*([\d,]+\.\d{2})\s*\n"
        r"RMB",
        text,
    )
    credit_limit = float(limits.group(1).replace(",", "")) if limits else 0.0
    balance = -float(limits.group(3).replace(",", "")) if limits else 0.0

    # Card summary line for min payment and due date
    # "4317-8420-0303-6220 HKD 2,021.59 2,021.59 220.00 0.00 Oct 02,2025"
    # A space separates the card number from "HKD" in pypdf-extracted text.
    card_summary = re.search(
        r"\d{4}-\d{4}-\d{4}-\d{4}\s+HKD\s*([\d,]+\.\d{2})\s+"
        r"([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+"
        r"(\w{3} \d{2},\d{4})",
        text,
    )
    minimum_due = 0.0
    due_date = ""
    if card_summary:
        minimum_due = float(card_summary.group(3).replace(",", ""))
        dt = datetime.strptime(card_summary.group(5), "%b %d,%Y")
        due_date = dt.strftime("%Y-%m-%d")

    # Period: derive from transaction dates
    all_dates = re.findall(r"(\w{3} \d{2},\d{4})", text)
    period_start = ""
    period_end = ""
    if statement_date:
        period_end = datetime.strptime(statement_date, "%Y-%m-%d").strftime("%d %b %Y")
    if all_dates:
        # Filter to transaction dates (skip statement/due dates)
        txn_dates = []
        for d in all_dates:
            try:
                dt = datetime.strptime(d, "%b %d,%Y")
                txn_dates.append(dt)
            except ValueError:
                pass
        if txn_dates:
            period_start = min(txn_dates).strftime("%d %b %Y")

    return StatementMeta(
        bank="ccba",
        card="CCBA eye Credit Card",
        period_start=period_start,
        period_end=period_end,
        statement_date=statement_date,
        balance=balance,
        minimum_due=minimum_due,
        due_date=due_date,
        credit_limit=credit_limit,
    )


def _parse_transactions(full_text: str) -> list[Transaction]:
    """Parse transaction lines from CCBA statement text."""
    lines = full_text.split("\n")
    raw_txns: list[dict] = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Clean trailing junk (e.g., "Bonus Point Summary..." appended to a transaction line)
        line = re.sub(r"Bonus Point Summary.*$", "", line).strip()

        m = _TXN_PAT.match(line)
        if not m:
            i += 1
            continue

        desc = m.group(1).strip()
        amount = float(m.group(2).replace(",", ""))
        is_cr = m.group(3) == "CR"
        trans_date_raw = m.group(4)

        # Skip payments
        if "PPS PAYMENT" in desc.upper() and is_cr:
            i += 1
            continue

        # Cross-border fee — merge with preceding transaction
        if "CROSS-BORDER TXN" in desc.upper() or "FEE - CROSS-BORDER" in desc.upper():
            if raw_txns:
                raw_txns[-1]["hkd"] -= amount  # more negative = more spent
            i += 1
            continue

        # Parse transaction date
        dt = datetime.strptime(trans_date_raw, "%b %d,%Y")
        iso_date = dt.strftime("%Y-%m-%d")

        # Check for foreign currency info on following lines
        foreign_amount = None
        foreign_currency = "HKD"
        if i + 1 < len(lines) and "FOREIGN CURRENCY AMOUNT" in lines[i + 1]:
            fx_match = re.search(
                r"(USD|GBP|EUR|JPY|AUD|CAD|SGD|CNY)\s+([\d,]+\.\d{2})", lines[i + 1]
            )
            if fx_match:
                foreign_currency = fx_match.group(1)
                foreign_amount = -float(fx_match.group(2).replace(",", ""))
            i += 1  # skip FX line
            if i + 1 < len(lines) and "EXCHANGE RATE" in lines[i + 1]:
                i += 1  # skip exchange rate line

        # Clean merchant from description
        merchant = _clean_merchant(desc)

        hkd = amount if is_cr else -amount

        raw_txns.append(
            {
                "date": iso_date,
                "merchant": merchant,
                "currency": foreign_currency,
                "foreign_amount": foreign_amount,
                "hkd": hkd,
            }
        )

        i += 1

    return [
        Transaction(
            date=t["date"],
            merchant=t["merchant"],
            category="",  # categorised later by pipeline
            currency=t["currency"],
            foreign_amount=t["foreign_amount"],
            hkd=t["hkd"],
        )
        for t in raw_txns
    ]


def _clean_merchant(desc: str) -> str:
    """Clean CCBA merchant description into a readable name."""
    name = desc.strip()
    # Remove reference numbers (long digit strings)
    name = re.sub(r"\s+\d{10,}\s*$", "", name).strip()
    # Remove trailing country codes (US, SG, HK, etc.) after location
    name = re.sub(r"\s+[A-Z]{2}\s*$", "", name).strip()
    # Collapse multiple spaces
    name = re.sub(r"\s{2,}", " ", name).strip()
    return name
