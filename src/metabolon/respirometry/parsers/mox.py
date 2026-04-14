"""Mox Credit statement PDF parser."""
from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

from pypdf import PdfReader

from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta

if TYPE_CHECKING:
    from pathlib import Path


def extract_mox(pdf_path: Path) -> tuple[RespirogramMeta, list[ConsumptionEvent]]:
    """Parse a Mox Credit statement PDF.

    Returns (metadata, transactions). Raises ValueError if balance validation
    fails.
    """
    reader = PdfReader(pdf_path)

    # Extract text from transaction pages only
    full_text = ""
    for page in reader.pages:
        text = page.extract_text() or ""
        if "Repayment calculator" in text or "Rate summary" in text:
            break
        full_text += text + "\n"

    meta = _extract_metadata(full_text)
    txns = _parse_transactions(full_text, meta.statement_date[:4])

    # Balance validation: spending transactions must sum to statement balance
    spending_total = sum(t.hkd for t in txns if t.category != "Transfer")
    if abs(spending_total - meta.balance) > 0.02:
        msg = f"Balance mismatch: parsed {spending_total:.2f}, statement says {meta.balance:.2f}"
        raise ValueError(msg)

    return meta, txns


def _extract_metadata(text: str) -> RespirogramMeta:
    """Extract statement-level metadata from page 1."""
    period_match = re.search(r"(\d{1,2} \w+ \d{4})\s*-\s*(\d{1,2} \w+ \d{4})", text)
    period_start = period_match.group(1) if period_match else ""
    period_end = period_match.group(2) if period_match else ""

    # Parse period_end to ISO date
    statement_date = ""
    if period_end:
        dt = datetime.strptime(period_end, "%d %b %Y")
        statement_date = dt.strftime("%Y-%m-%d")

    credit_limit = _extract_float(r"Total credit limit[^:]*:\s*([\d,]+\.\d{2})", text)
    balance = _extract_float(r"(-?[\d,]+\.\d{2})\s*HKD\s*\nStatement balance", text)
    minimum_due = _extract_float(r"([\d,]+\.\d{2})\s*HKD\s*\nMinimum amount due", text)
    due_date_match = re.search(r"(\d{1,2} \w+ \d{4})\s*\nPayment due date", text)
    due_date = ""
    if due_date_match:
        dt = datetime.strptime(due_date_match.group(1), "%d %b %Y")
        due_date = dt.strftime("%Y-%m-%d")

    return RespirogramMeta(
        bank="mox",
        card="Mox Credit",
        period_start=period_start,
        period_end=period_end,
        statement_date=statement_date,
        balance=balance,
        minimum_due=minimum_due,
        due_date=due_date,
        credit_limit=credit_limit,
    )


def _extract_float(pattern: str, text: str) -> float:
    m = re.search(pattern, text)
    return float(m.group(1).replace(",", "")) if m else 0.0


def _parse_transactions(full_text: str, year: str) -> list[ConsumptionEvent]:
    """Parse transaction blocks from extracted PDF text."""
    # Remove page headers
    text = re.sub(r"Page \d+ of \d+", "", full_text)
    text = re.sub(
        r"Activity date\n交易⽇期Settlement date\n結算⽇期Description\n詳情"
        r"Foreign currency amount\n外幣⾦額Amount \(HKD\)\n⾦額\s+\(港幣\s*\)",
        "",
        text,
    )

    date_pat = r"(\d{2} \w{3}) (\d{2} \w{3})"
    parts = re.split(f"(?={date_pat})", text)

    transactions: list[ConsumptionEvent] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        m = re.match(date_pat, part)
        if not m:
            continue

        activity_date_raw = m.group(1)
        rest = part[m.end() :].strip()

        # Internal transfers — skip
        if "Move between own Mox" in rest:
            continue

        # Payment from cardholder (e.g., "LI HO MING TERRY 2,711.86") — skip
        if re.match(r"LI HO MING TERRY\s+[\d,]+\.\d{2}", rest):
            continue

        # Extract amounts
        amounts = re.findall(r"(-?[\d,]+\.\d{2})", rest)
        if not amounts:
            continue

        hkd = float(amounts[-1].replace(",", ""))

        # Foreign currency
        foreign_amount = None
        foreign_currency = "HKD"
        fx_match = re.search(
            r"(-?[\d,]+\.\d{2})\s+(USD|GBP|EUR|JPY|AUD|CAD|SGD|CNY|TWD|THB|KRW)\b",
            rest,
        )
        if fx_match and len(amounts) >= 2:
            foreign_amount = float(fx_match.group(1).replace(",", ""))
            foreign_currency = fx_match.group(2)

        # Merchant name — first line, cleaned
        desc_lines = rest.split("\n")
        merchant_raw = desc_lines[0].strip()
        merchant_raw = re.sub(r"\s+-?[\d,]+\.\d{2}\s*$", "", merchant_raw)
        merchant = re.sub(r"\s*\+\d[\d\s]*\w{2,3}\s*$", "", merchant_raw).strip()
        merchant = re.sub(
            r"\s+(USA|GBR|IRL|CAN|HKG|AUS|SGP|JPN|NEW|TWN|KOR)\s*$",
            "",
            merchant,
        ).strip()
        merchant = re.sub(r"\s+(GOO|II)\s*$", "", merchant).strip()

        # Parse date to ISO
        dt = datetime.strptime(f"{activity_date_raw} {year}", "%d %b %Y")
        iso_date = dt.strftime("%Y-%m-%d")

        transactions.append(
            ConsumptionEvent(
                date=iso_date,
                merchant=merchant,
                category="",  # categorised later by pipeline
                currency=foreign_currency,
                foreign_amount=foreign_amount,
                hkd=hkd,
            )
        )

    return transactions
