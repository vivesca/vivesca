
"""Standard Chartered Smart Credit Card statement PDF parser."""


import re
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


def extract_scb(pdf_path: Path) -> tuple[RespirogramMeta, list[ConsumptionEvent]]:
    """Parse a Standard Chartered Smart Credit Card statement PDF.

    Returns (metadata, transactions). Raises ValueError if balance validation
    fails.
    """
    reader = PdfReader(pdf_path)

    full_text = ""
    for page in reader.pages:
        text = page.extract_text() or ""
        full_text += text + "\n"

    meta = _extract_metadata(full_text)
    purchases_total = _extract_purchases_total(full_text)
    txns = _parse_transactions(full_text, meta.statement_date[:4])

    # Balance validation: sum of charges should equal purchases total
    charges_total = sum(abs(t.hkd) for t in txns if t.is_charge)
    if abs(charges_total - purchases_total) > 0.02:
        msg = (
            f"Balance mismatch: parsed charges {charges_total:.2f}, "
            f"statement purchases {purchases_total:.2f}"
        )
        raise ValueError(msg)

    return meta, txns


def _extract_metadata(text: str) -> RespirogramMeta:
    """Extract statement-level metadata from PDF text."""
    # Statement date: DD/MM/YYYY or DD Mon YYYY
    statement_date = ""
    stmt_match = re.search(r"Statement Date.*?(\d{2}/\d{2}/\d{4})", text, re.DOTALL)
    if stmt_match:
        dt = datetime.strptime(stmt_match.group(1), "%d/%m/%Y")
        statement_date = dt.strftime("%Y-%m-%d")
    else:
        stmt_match2 = re.search(r"Statement Date.*?:(\d{1,2} \w{3} \d{4})", text, re.DOTALL)
        if stmt_match2:
            dt = datetime.strptime(stmt_match2.group(1), "%d %b %Y")
            statement_date = dt.strftime("%Y-%m-%d")

    # Payment due date: DD/MM/YYYY or DD Mon YYYY
    due_date = ""
    due_match = re.search(r"Payment Due Date.*?(\d{2}/\d{2}/\d{4})", text, re.DOTALL)
    if due_match:
        dt = datetime.strptime(due_match.group(1), "%d/%m/%Y")
        due_date = dt.strftime("%Y-%m-%d")
    else:
        due_match2 = re.search(r"Payment Due Date.*?:(\d{1,2} \w{3} \d{4})", text, re.DOTALL)
        if due_match2:
            dt = datetime.strptime(due_match2.group(1), "%d %b %Y")
            due_date = dt.strftime("%Y-%m-%d")

    # Credit limit: "SMART CREDIT CARD 106,000264.00 26,345.39"
    # Format: limit (integer, comma-separated) immediately followed by min payment (has .00)
    cl_match = re.search(r"SMART CREDIT CARD\s+([\d]{1,3}(?:,\d{3})+)", text)
    credit_limit = float(cl_match.group(1).replace(",", "")) if cl_match else 0.0

    # Statement balance
    bal_match = re.search(r"STATEMENT BALANCE.*?([\d,]+\.\d{2})", text)
    balance = -float(bal_match.group(1).replace(",", "")) if bal_match else 0.0

    # Minimum payment
    min_match = re.search(r"MINIMUM PAYMENT DUE.*?([\d,]+\.\d{2})", text)
    minimum_due = float(min_match.group(1).replace(",", "")) if min_match else 0.0

    # Period: derive from transaction dates
    period_start = ""
    period_end = ""
    if statement_date:
        period_end = datetime.strptime(statement_date, "%Y-%m-%d").strftime("%d %b %Y")
        all_dates = re.findall(r"^(\d{2}/\d{2})\s+[\d,]+\.\d{2}", text, re.MULTILINE)
        if all_dates:
            year = int(statement_date[:4])
            first_dt = datetime.strptime(f"{all_dates[0]}/{year}", "%m/%d/%Y")
            period_start = first_dt.strftime("%d %b %Y")

    return RespirogramMeta(
        bank="scb",
        card="SCB Smart Credit Card",
        period_start=period_start,
        period_end=period_end,
        statement_date=statement_date,
        balance=balance,
        minimum_due=minimum_due,
        due_date=due_date,
        credit_limit=credit_limit,
    )


def _extract_purchases_total(text: str) -> float:
    """Extract the 'Purchases' total from the statement summary line.

    Summary: Previous - Payments - Credits + Purchases + Cash + Charges = Balance
    """
    m = re.search(
        r"([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+"
        r"([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})",
        text,
    )
    if m:
        return float(m.group(4).replace(",", ""))
    return 0.0


def _parse_transactions(full_text: str, year_str: str) -> list[ConsumptionEvent]:
    """Parse transactions from SCB statement text.

    SCB has a split layout: merchant descriptions in 'Transaction Ref' blocks
    (separated by non-breaking spaces), amounts in a separate Date/Amount table.
    Descriptions for purchases align 1:1 with non-CR amounts after removing
    PAYMENT entries. CR amounts are payments/cashback (excluded from spending).
    """
    year = int(year_str)

    # Extract descriptions from Transaction Ref blocks
    ref_pattern = re.compile(r"Transaction Ref \d+\s+")
    parts = ref_pattern.split(full_text)
    ref_positions = list(ref_pattern.finditer(full_text))

    all_descs: list[dict] = []
    for i, match in enumerate(ref_positions):
        desc_raw = parts[i + 1].split("\xa0")[0].strip().split("\n")[0].strip()

        # Check for preceding FX info
        pre_text = full_text[max(0, match.start() - 200) : match.start()]
        fx_match = re.search(r"Foreign Currency (\w+) ([\d,]+\.\d+),\s*Rate", pre_text)
        fx_currency = fx_match.group(1) if fx_match else None
        fx_amount = float(fx_match.group(2).replace(",", "")) if fx_match else None

        all_descs.append(
            {
                "merchant_raw": desc_raw,
                "fx_currency": fx_currency,
                "fx_amount": fx_amount,
            }
        )

    # Filter out PAYMENT descriptions (they correspond to CR amounts, not charges)
    charge_descs = [d for d in all_descs if "PAYMENT" not in d["merchant_raw"].upper()]

    # Extract non-CR amounts (charges/purchases)
    charge_amounts: list[dict] = []
    for m in re.finditer(r"^(\d{2}/\d{2})\s+([\d,]+\.\d{2})$", full_text, re.MULTILINE):
        charge_amounts.append(
            {
                "date_raw": m.group(1),
                "amount": float(m.group(2).replace(",", "")),
            }
        )

    # Pair charge descriptions with charge amounts (1:1)
    transactions: list[ConsumptionEvent] = []
    for i in range(min(len(charge_descs), len(charge_amounts))):
        desc_info = charge_descs[i]
        amt_info = charge_amounts[i]

        merchant_raw = desc_info["merchant_raw"]

        # Parse date (MM/DD format)
        dt = datetime.strptime(f"{amt_info['date_raw']}/{year}", "%m/%d/%Y")
        iso_date = dt.strftime("%Y-%m-%d")

        hkd = -amt_info["amount"]  # charges are negative

        # Foreign currency
        foreign_currency = "HKD"
        foreign_amount = None
        if desc_info["fx_currency"]:
            foreign_currency = desc_info["fx_currency"]
            foreign_amount = -desc_info["fx_amount"]

        merchant = _clean_merchant(merchant_raw)

        transactions.append(
            ConsumptionEvent(
                date=iso_date,
                merchant=merchant,
                category="",
                currency=foreign_currency,
                foreign_amount=foreign_amount,
                hkd=hkd,
            )
        )

    return transactions


def _clean_merchant(raw: str) -> str:
    """Clean SCB merchant description."""
    name = raw.strip()
    # Remove trailing location + country code
    name = re.sub(
        r"(?:HONG KONG|KOWLOON BAY|SAI WAN HO|CENTRAL|NORTH POINT|"
        r"TAI KOO SHIN|MA ON SHAN|KW\.TONG|QUARRY BAY|WAN CHAI|"
        r"Cheung Sha W|KL|HongKong|HONGKONG|SINGAPORE|TOKYO|"
        r"WWW\.PERPLEXI|ITUNES\.COM|GOOGLE\.CO|VERCEL\.COM|"
        r"aws\.amazon\.c|X\.AI/ABOUT)\s*"
        r"(?:HK|SG|US|JP|IE)?\s*$",
        "",
        name,
    ).rstrip()
    name = re.sub(r"\s+(?:HK|SG|US|JP|IE|AU|GB|CA|NL)\s*$", "", name).rstrip()
    name = re.sub(r"\s{2,}", " ", name).strip()
    return name
