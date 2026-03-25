"""Generate synthetic PDF test fixtures for spending parser tests.

Run with: python tests/create_synthetic_fixtures.py

Uses fpdf2 to create PDFs whose pypdf-extracted text matches the exact patterns
each parser expects.  All personal data is replaced with fake equivalents.
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

FIXTURES = Path(__file__).parent / "fixtures"
ARIAL_UNICODE = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"


def _pdf_with_text(lines: list[str], unicode_font: bool = False) -> FPDF:
    """Return an FPDF with one page containing the given lines of text."""
    pdf = FPDF()
    pdf.add_page()
    if unicode_font:
        pdf.add_font("ArialUnicode", fname=ARIAL_UNICODE, uni=True)
        pdf.set_font("ArialUnicode", size=9)
    else:
        pdf.set_font("Helvetica", size=9)
    for line in lines:
        pdf.cell(0, 4, line, new_x="LMARGIN", new_y="NEXT")
    return pdf


def _pdf_two_pages(
    page1_lines: list[str],
    page2_lines: list[str],
    unicode_font: bool = False,
) -> FPDF:
    """Return an FPDF with two pages."""
    pdf = FPDF()
    if unicode_font:
        pdf.add_font("ArialUnicode", fname=ARIAL_UNICODE, uni=True)

    def write_page(lines: list[str]) -> None:
        pdf.add_page()
        if unicode_font:
            pdf.set_font("ArialUnicode", size=9)
        else:
            pdf.set_font("Helvetica", size=9)
        for line in lines:
            pdf.cell(0, 4, line, new_x="LMARGIN", new_y="NEXT")

    write_page(page1_lines)
    write_page(page2_lines)
    return pdf


# ---------------------------------------------------------------------------
# MOX  (mox_jan2025.pdf)
# ---------------------------------------------------------------------------
# Parser regex patterns:
#   period: r"(\d{1,2} \w+ \d{4})\s*-\s*(\d{1,2} \w+ \d{4})"
#   credit limit: r"Total credit limit[^:]*:\s*([\d,]+\.\d{2})"
#   balance: r"(-?[\d,]+\.\d{2})\s*HKD\s*\nStatement balance"
#   min due: r"([\d,]+\.\d{2})\s*HKD\s*\nMinimum amount due"
#   due date: r"(\d{1,2} \w+ \d{4})\s*\nPayment due date"
#   transactions: date_pat = r"(\d{2} \w{3}) (\d{2} \w{3})" then rest of line
#   Stops at "Repayment calculator" or "Rate summary"
#   balance check: sum(spending txns) == balance (-6004.03)
#   20 spending charges; "SMARTONE" and "Bowtie Life Insurance" required
#   internal transfers ("Move between own Mox") skipped
#   payments ("LI HO MING TERRY ...") skipped


def make_mox() -> None:
    txns = [
        # (activity_date, settlement_date, merchant, fx_str, hkd_amount)
        ("01 Jan", "02 Jan", "SMARTONE", "", 450.00),
        ("03 Jan", "04 Jan", "Bowtie Life Insurance", "", 1200.00),
        ("05 Jan", "06 Jan", "WELLCOME SUPERMARKET", "", 320.50),
        ("07 Jan", "08 Jan", "MCDONALD'S", "", 85.00),
        ("09 Jan", "10 Jan", "STARBUCKS", "", 62.00),
        ("11 Jan", "12 Jan", "APPLE STORE", "", 128.00),
        ("13 Jan", "14 Jan", "NETFLIX", "15.49 USD", 120.82),
        ("14 Jan", "15 Jan", "SPOTIFY", "", 48.00),
        ("15 Jan", "16 Jan", "OCTOPUS", "", 200.00),
        ("16 Jan", "17 Jan", "MANNINGS", "", 156.30),
        ("17 Jan", "18 Jan", "PARKN SHOP", "", 412.00),
        ("18 Jan", "19 Jan", "AEON", "", 288.00),
        ("19 Jan", "20 Jan", "SUSHI EXPRESS", "", 198.00),
        ("20 Jan", "21 Jan", "CITY SUPER", "", 344.41),
        ("21 Jan", "22 Jan", "WATSONS", "", 89.00),
        ("22 Jan", "23 Jan", "MAXIM'S", "", 175.00),
        ("23 Jan", "24 Jan", "HAIR SALON", "", 280.00),
        ("24 Jan", "25 Jan", "BOOKSHOP", "", 157.00),
        ("25 Jan", "26 Jan", "PHARMACY", "", 200.00),
        ("26 Jan", "27 Jan", "GYM MEMBERSHIP", "", 650.00),
    ]

    # Adjust last txn so total == 6004.03
    current_total = sum(t[4] for t in txns)
    diff = 6004.03 - current_total
    last = txns[-1]
    txns[-1] = (last[0], last[1], last[2], last[3], round(last[4] + diff, 2))

    total = sum(t[4] for t in txns)
    assert abs(total - 6004.03) < 0.01, f"Mox txn total mismatch: {total}"

    lines: list[str] = [
        "Mox Bank Limited",
        "Jane Doe",
        "123 Example St, Hong Kong",
        "",
        "31 Dec 2024 - 30 Jan 2025",
        "",
        "Total credit limit: 108,000.00",
        "",
        "-6,004.03 HKD",
        "Statement balance",
        "",
        "100.00 HKD",
        "Minimum amount due",
        "",
        "24 Feb 2025",
        "Payment due date",
        "",
        "Activity date Settlement date Description Amount (HKD)",
        "",
    ]

    for act, sett, merchant, fx, hkd in txns:
        # Mox PDFs show charges as negative amounts
        if fx:
            lines.append(f"{act} {sett} {merchant} {fx} -{hkd:.2f}")
        else:
            lines.append(f"{act} {sett} {merchant} -{hkd:.2f}")

    # Internal transfer -- should be skipped
    lines.append("01 Jan 02 Jan Move between own Mox accounts -500.00")
    # Payment -- should be skipped (no leading minus, cardholder name pattern)
    lines.append("15 Jan 16 Jan LI HO MING TERRY 2,711.86")

    # "Repayment calculator" must be on a SEPARATE page so the parser
    # collects all transaction lines before breaking on that sentinel.
    page2_lines = [
        "Repayment calculator",
        "Rate summary",
        "This section is after the break.",
    ]

    pdf = _pdf_two_pages(lines, page2_lines, unicode_font=False)
    pdf.output(str(FIXTURES / "mox_jan2025.pdf"))
    print("Created mox_jan2025.pdf")


# ---------------------------------------------------------------------------
# HSBC  (hsbc_mar2025.pdf  +  hsbc_feb2025.pdf)
# ---------------------------------------------------------------------------
# Parser regex patterns:
#   metadata:
#     r"Statementdate\s+Statementbalance\n(\d{2}[A-Z]{3}\d{4})HKD([\d,]+\.\d{2})"
#     credit limit: r"HSBCVisaSignatureHKD([\d,]+\.\d{2})"
#     min+due: r"Total minimum payment due\s+HKD\n([\d,]+\.\d{2})\n(\d{2}[A-Z]{3}\d{4})"
#   transactions:
#     _TXN_PAT = r"^(\d{2}[A-Z]{3})(\d{2}[A-Z]{3})(.+)"
#     FX: r"(USD|...)\s*([\d,]+\.\d{2})\s*([\d,]+\.\d{2})$"
#     HKD only: r"([\d,]+\.\d{2})$"
#     skip: PREVIOUSBALANCE, PAYMENT-THANKYOU, 16-digit card lines, DCCFEE
#   balance check: sum(hkd) == balance (both negative)


def _hsbc_lines(
    stmt_date: str,
    balance: float,
    credit_limit: float,
    min_payment: float,
    due_date: str,
    txns: list[tuple],
) -> list[str]:
    lines = [
        "HSBC Bank (Hong Kong) Limited",
        "Jane Doe",
        "123 Example St, Hong Kong",
        "",
        f"HSBCVisaSignatureHKD{credit_limit:,.2f}",
        "",
        "Statementdate  Statementbalance",
        f"{stmt_date}HKD{balance:,.2f}",
        "",
        "Total minimum payment due  HKD",
        f"{min_payment:,.2f}",
        f"{due_date}",
        "",
        "Transactions",
        "01JAN01JANPREVIOUSBALANCE 0.00",
        "01JAN01JANPAYMENT-THANKYOU 0.00CR",
    ]
    for post, trans, desc, amount, fx in txns:
        if fx:
            lines.append(f"{post}{trans}{desc} {fx} {amount:,.2f}")
        else:
            lines.append(f"{post}{trans}{desc} {amount:,.2f}")
    return lines


def make_hsbc_mar() -> None:
    # balance = -26119.50 -> txns must sum to -26119.50
    # charges are negative; we create all-charge txns
    # amounts are positive in the PDF line; parser makes them negative

    txn_data = [
        ("07MAR", "05MAR", "WELLCOME SUPERMARKET HONG KONGHK", 458.00, ""),
        ("07MAR", "05MAR", "STARBUCKS COFFEE HONG KONGHK", 62.00, ""),
        ("06MAR", "04MAR", "MCDONALD'S HONG KONGHK", 95.50, ""),
        ("06MAR", "04MAR", "AMAZON WEB SERVICES", "", 0),  # placeholder for FX
        ("05MAR", "03MAR", "NETFLIX.COM", 128.00, ""),
        ("05MAR", "03MAR", "GOOGLE STORAGE", 15.00, ""),
        ("04MAR", "02MAR", "APPLE STORE HONG KONGHK", 988.00, ""),
        ("04MAR", "02MAR", "MANNINGS CHEMIST HONG KONGHK", 156.00, ""),
        ("03MAR", "01MAR", "PARKN SHOP HONG KONGHK", 512.00, ""),
        ("03MAR", "01MAR", "WATSONS HONG KONGHK", 89.00, ""),
        ("02MAR", "28FEB", "CITY SUPER HONG KONGHK", 788.00, ""),
        ("02MAR", "28FEB", "SUSHI RESTAURANT HONG KONGHK", 445.00, ""),
        ("01MAR", "27FEB", "MTR CORPORATION", 200.00, ""),
        ("01MAR", "27FEB", "HAIR SALON HONG KONGHK", 350.00, ""),
        ("28FEB", "26FEB", "GYM MEMBERSHIP HONG KONGHK", 580.00, ""),
        ("28FEB", "26FEB", "PHARMACY HONG KONGHK", 178.00, ""),
        ("27FEB", "25FEB", "BOOKSHOP HONG KONGHK", 245.00, ""),
        ("27FEB", "25FEB", "SUPERMARKET HONG KONGHK", 389.00, ""),
        ("26FEB", "24FEB", "RESTAURANT HONG KONGHK", 320.00, ""),
        ("25FEB", "23FEB", "CONVENIENCE STORE HONG KONGHK", 45.00, ""),
        ("24FEB", "22FEB", "DEPARTMENT STORE HONG KONGHK", 678.00, ""),
        ("23FEB", "21FEB", "ELECTRONICS SHOP HONG KONGHK", 1258.00, ""),
        ("22FEB", "20FEB", "CLOTHING STORE HONG KONGHK", 860.00, ""),
        ("21FEB", "19FEB", "COFFEE SHOP HONG KONGHK", 88.00, ""),
        ("20FEB", "18FEB", "MOBILE SHOP HONG KONGHK", 220.00, ""),
        ("19FEB", "17FEB", "BAKERY HONG KONGHK", 56.00, ""),
        ("18FEB", "16FEB", "TRANSPORT HONG KONGHK", 150.00, ""),
        ("17FEB", "15FEB", "INSURANCE CO HONG KONGHK", 1800.00, ""),
        ("16FEB", "14FEB", "UTILITY HONG KONGHK", 560.00, ""),
        ("15FEB", "13FEB", "DENTIST HONG KONGHK", 1200.00, ""),
        ("14FEB", "12FEB", "FLOWERS SHOP HONG KONGHK", 380.00, ""),
        ("13FEB", "11FEB", "LINGERIE SHOP HONG KONGHK", 455.00, ""),
        ("12FEB", "10FEB", "TOY SHOP HONG KONGHK", 322.00, ""),
        ("11FEB", "09FEB", "STATIONERY HONG KONGHK", 145.00, ""),
        ("10FEB", "08FEB", "LAUNDRY HONG KONGHK", 280.00, ""),
        ("09FEB", "07FEB", "MISCELLANEOUS HONG KONGHK", 125.00, ""),
        ("08FEB", "06FEB", "LAST ITEM HONG KONGHK", 0.00, ""),  # adjusted below
    ]

    # Set USD txn: fx pattern "USD 25.00 194.50" — parser picks last two floats as fx_amount, hkd
    usd_hkd = 194.50
    txn_data[3] = ("06MAR", "04MAR", "AMAZON WEB SERVICES", usd_hkd, "USD 25.00")

    # Sum all known amounts
    total_known = sum(t[3] for t in txn_data if t[3] != 0.0 and t[4] != "USD 25.00")
    total_known += usd_hkd

    diff = 26119.50 - total_known
    # Set last txn
    last = txn_data[-1]
    txn_data[-1] = (last[0], last[1], last[2], round(diff, 2), last[4])

    # Verify
    total = sum(t[3] for t in txn_data)
    assert abs(total - 26119.50) < 0.01, f"HSBC mar total: {total}"

    lines = _hsbc_lines(
        stmt_date="07MAR2025",
        balance=26119.50,
        credit_limit=72000.00,
        min_payment=300.00,
        due_date="02APR2025",
        txns=txn_data,
    )
    pdf = _pdf_with_text(lines)
    pdf.output(str(FIXTURES / "hsbc_mar2025.pdf"))
    print("Created hsbc_mar2025.pdf")


def make_hsbc_feb() -> None:
    # statement_date = 2025-02-06; balance = sum of txns
    txn_data = [
        ("06FEB", "04FEB", "WELLCOME SUPERMARKET HONG KONGHK", 512.00, ""),
        ("05FEB", "03FEB", "STARBUCKS COFFEE HONG KONGHK", 78.00, ""),
        ("04FEB", "02FEB", "NETFLIX HONG KONGHK", 128.00, ""),
        ("03FEB", "01FEB", "AMAZON HONG KONGHK", 117.15, "USD 15.00"),
        ("02FEB", "31JAN", "RESTAURANT HONG KONGHK", 345.00, ""),
        ("01FEB", "30JAN", "SUPERMARKET HONG KONGHK", 289.00, ""),
    ]
    balance = sum(t[3] for t in txn_data)

    lines = _hsbc_lines(
        stmt_date="06FEB2025",
        balance=balance,
        credit_limit=72000.00,
        min_payment=150.00,
        due_date="04MAR2025",
        txns=txn_data,
    )
    pdf = _pdf_with_text(lines)
    pdf.output(str(FIXTURES / "hsbc_feb2025.pdf"))
    print("Created hsbc_feb2025.pdf")


# ---------------------------------------------------------------------------
# CCBA  (ccba_sep2025.pdf  +  ccba_mar2026.pdf)
# ---------------------------------------------------------------------------
# Parser regex patterns:
#   statement date: r"Statement Date\s*\u6708\u7d50\u55ae\u622a\u6578\u65e5[\uff1a:]\s*(\w{3} \d{2},\s*\d{4})"
#   limits: r"HKD\s*([\d,]+\.\d{2})\s*\nHKD\s*([\d,]+\.\d{2})\s*\nHKD\s*([\d,]+\.\d{2})\s*\nRMB"
#   card summary: r"\d{4}-\d{4}-\d{4}-\d{4}\s+HKD\s*([\d,]+\.\d{2})\s+..."
#     groups: stmt_bal, stmt_bal2, min_due, 0.00, due_date
#   transactions: r"^(.+?)\s+HKD\s+([\d,]+\.\d{2})\s*(CR)?(\w{3} \d{2},\d{4})\s*(\w{3} \d{2},\d{4})"
#   FX: next line "FOREIGN CURRENCY AMOUNT USD ..."
#   balance check: sum(hkd) == balance
# NOTE: needs unicode_font=True for the CJK statement date label


def _ccba_lines(
    stmt_date_str: str,
    credit_limit: float,
    available_credit: float,
    outstanding: float,
    min_payment: float,
    due_date_str: str,
    card_no: str,
    txns: list[tuple],
) -> list[str]:
    # CJK characters for "月結單截數日" = \u6708\u7d50\u55ae\u622a\u6578\u65e5
    cjk_label = "\u6708\u7d50\u55ae\u622a\u6578\u65e5"
    lines = [
        "CCBA eye Credit Card",
        "Jane Doe",
        "123 Example St, Hong Kong",
        "",
        f"Statement Date {cjk_label}\uff1a {stmt_date_str}",
        "",
        f"HKD {credit_limit:,.2f}",
        f"HKD {available_credit:,.2f}",
        f"HKD {outstanding:,.2f}",
        "RMB 0.00",
        "",
        f"{card_no} HKD {outstanding:,.2f} {outstanding:,.2f} {min_payment:,.2f} 0.00 {due_date_str}",
        "",
        "Transaction Details",
    ]
    for desc, amount, is_cr, trans_date, post_date in txns:
        cr_flag = "CR" if is_cr else ""
        lines.append(f"{desc} HKD {amount:,.2f} {cr_flag}{trans_date}{post_date}")
    return lines


def make_ccba_sep() -> None:
    # balance = -2021.59, outstanding = 2021.59
    txns = [
        ("WELLCOME SUPERMARKET HK", 450.00, False, "Aug 15,2025", "Aug 16,2025"),
        ("STARBUCKS COFFEE HK", 78.00, False, "Aug 17,2025", "Aug 18,2025"),
        ("NETFLIX HK", 128.00, False, "Aug 20,2025", "Aug 21,2025"),
        ("AMAZON COM US", 155.59, False, "Aug 22,2025", "Aug 23,2025"),
        ("PARKN SHOP HK", 320.00, False, "Aug 25,2025", "Aug 26,2025"),
        ("RESTAURANT HK", 280.00, False, "Aug 28,2025", "Aug 29,2025"),
        ("PHARMACY HK", 610.00, False, "Sep 01,2025", "Sep 02,2025"),
    ]
    total = sum(t[1] for t in txns)
    assert abs(total - 2021.59) < 0.01, f"CCBA sep total: {total}"

    lines = _ccba_lines(
        stmt_date_str="Sep 07,2025",
        credit_limit=49000.00,
        available_credit=46978.41,
        outstanding=2021.59,
        min_payment=220.00,
        due_date_str="Oct 02,2025",
        card_no="4317-8420-0303-6220",
        txns=txns,
    )
    # Insert FX line after AMAZON COM line
    fx_idx = next(i for i, line in enumerate(lines) if "AMAZON COM" in line)
    lines.insert(fx_idx + 1, "FOREIGN CURRENCY AMOUNT USD 19.99")
    lines.insert(fx_idx + 2, "EXCHANGE RATE 7.79")

    # PPS PAYMENT CR -- should be skipped
    lines.append("PPS PAYMENT HKD 2,021.59 CRSep 07,2025Sep 07,2025")

    pdf = _pdf_with_text(lines, unicode_font=True)
    pdf.output(str(FIXTURES / "ccba_sep2025.pdf"))
    print("Created ccba_sep2025.pdf")


def make_ccba_mar() -> None:
    # balance = -6107.99, statement_date = 2026-03-07
    txns = [
        ("WELLCOME SUPERMARKET HK", 800.00, False, "Feb 10,2026", "Feb 11,2026"),
        ("STARBUCKS COFFEE HK", 156.00, False, "Feb 15,2026", "Feb 16,2026"),
        ("NETFLIX HK", 128.00, False, "Feb 18,2026", "Feb 19,2026"),
        ("AMAZON COM US", 388.99, False, "Feb 20,2026", "Feb 21,2026"),
        ("PARKN SHOP HK", 650.00, False, "Feb 22,2026", "Feb 23,2026"),
        ("RESTAURANT HK", 985.00, False, "Feb 25,2026", "Feb 26,2026"),
        ("GYM MEMBERSHIP HK", 600.00, False, "Feb 28,2026", "Mar 01,2026"),
        ("INSURANCE HK", 1200.00, False, "Mar 01,2026", "Mar 02,2026"),
        ("PHARMACY HK", 400.00, False, "Mar 03,2026", "Mar 04,2026"),
        ("LAST TXNS HK", 800.00, False, "Mar 05,2026", "Mar 06,2026"),
    ]
    current = sum(t[1] for t in txns)
    diff = 6107.99 - current
    last = txns[-1]
    txns[-1] = (last[0], round(last[1] + diff, 2), last[2], last[3], last[4])
    total = sum(t[1] for t in txns)
    assert abs(total - 6107.99) < 0.01, f"CCBA mar total: {total}"

    lines = _ccba_lines(
        stmt_date_str="Mar 07,2026",
        credit_limit=49000.00,
        available_credit=42892.01,
        outstanding=6107.99,
        min_payment=300.00,
        due_date_str="Apr 02,2026",
        card_no="4317-8420-0303-6220",
        txns=txns,
    )
    fx_idx = next(i for i, line in enumerate(lines) if "AMAZON COM" in line)
    lines.insert(fx_idx + 1, "FOREIGN CURRENCY AMOUNT USD 49.87")
    lines.insert(fx_idx + 2, "EXCHANGE RATE 7.80")

    lines.append("PPS PAYMENT HKD 6,107.99 CRMar 07,2026Mar 07,2026")

    pdf = _pdf_with_text(lines, unicode_font=True)
    pdf.output(str(FIXTURES / "ccba_mar2026.pdf"))
    print("Created ccba_mar2026.pdf")


# ---------------------------------------------------------------------------
# BOC  (boc_feb2026.pdf)
# ---------------------------------------------------------------------------
# Parser regex patterns:
#   "Payment Slip" marker triggers in_slip mode
#   r"^HKD\s*([\d,]+\.\d{2})\s*$" -> [credit_limit, balance_magnitude, min_payment]
#   r"^(\d{2}-[A-Z]{3}-\d{4})\s*$" -> [statement_date, due_date]
#   stops at "Balance B/F" or "Gift Points"
#   card type: r"Card Type:.*?\n(BOC .+?)(?:\n|$)"
#   transactions: r"^(\d{2}-[A-Z]{3})\s+(\d{2}-[A-Z]{3})\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR)?\s*$"
#   balance_bf: r"BALANCE B/F\s+([\d,]+\.\d{2})" -> negative
#   odd_cents: r"ODD CENTS TO NEXT BILL\s+([\d,]+\.\d{2})\s*(CR)?"
#   payments: PPS PAYMENT ... CR lines
#   balance check: sum(txns) == meta.balance - balance_bf - payments - odd_cents
#
#   Tests:
#     card = "BOC Taobao World Mastercard"
#     statement_date = 2026-02-27, balance = -19613.00
#     credit_limit = 200000, due = 2026-03-24, min = 230
#     period_start = "03 Feb 2026"  (earliest txn)
#     33 txns, 2 credits (hkd > 0), one = "ALIPAY FINANCIAL"
#     no "HONG KONG" in merchant names (clean_merchant strips it)


def make_boc() -> None:
    # balance_bf = 0 (no carry-forward), payments = 0, odd_cents = 0
    # expected = meta.balance - balance_bf - payments - odd_cents
    #          = -19613 - 0 - 0 - 0 = -19613
    # sum(txns) must equal -19613
    # 31 charges (negative) + 2 credits (positive)
    # -charges_sum + credits_sum = -19613
    # credits: 500 + 200 = 700
    # charges_sum = 19613 + 700 = 20313

    charges = [
        # (trans_date, post_date, merchant, amount)
        ("02-FEB", "03-FEB", "TAOBAO HONG KONG HKG", 1200.00),
        ("03-FEB", "04-FEB", "WELLCOME SUPERMARKET HONG KONG HKG", 450.00),
        ("05-FEB", "06-FEB", "STARBUCKS COFFEE HONG KONG HKG", 78.00),
        ("06-FEB", "07-FEB", "MCDONALD'S HONG KONG HKG", 95.00),
        ("07-FEB", "08-FEB", "PARKN SHOP HONG KONG HKG", 380.00),
        ("08-FEB", "09-FEB", "WATSONS HONG KONG HKG", 156.00),
        ("09-FEB", "10-FEB", "MANNINGS HONG KONG HKG", 120.00),
        ("10-FEB", "11-FEB", "AEON HONG KONG HKG", 288.00),
        ("11-FEB", "12-FEB", "CITY SUPER HONG KONG HKG", 450.00),
        ("12-FEB", "13-FEB", "SUSHI EXPRESS HONG KONG HKG", 198.00),
        ("13-FEB", "14-FEB", "MAXIM'S RESTAURANT HONG KONG HKG", 320.00),
        ("14-FEB", "15-FEB", "HAIR SALON HONG KONG HKG", 280.00),
        ("15-FEB", "16-FEB", "GYM MEMBERSHIP HONG KONG HKG", 650.00),
        ("16-FEB", "17-FEB", "MTR CORPORATION HONG KONG HKG", 200.00),
        ("17-FEB", "18-FEB", "NETFLIX HONG KONG HKG", 128.00),
        ("18-FEB", "19-FEB", "SPOTIFY HONG KONG HKG", 48.00),
        ("19-FEB", "20-FEB", "APPLE STORE HONG KONG HKG", 988.00),
        ("20-FEB", "21-FEB", "BOOKSHOP HONG KONG HKG", 245.00),
        ("21-FEB", "22-FEB", "PHARMACY HONG KONG HKG", 178.00),
        ("22-FEB", "23-FEB", "RESTAURANT CENTRAL HONG KONG HKG", 560.00),
        ("23-FEB", "24-FEB", "ELECTRONICS SHOP HONG KONG HKG", 1258.00),
        ("24-FEB", "25-FEB", "CLOTHING STORE HONG KONG HKG", 860.00),
        ("25-FEB", "26-FEB", "COFFEE SHOP HONG KONG HKG", 88.00),
        ("26-FEB", "27-FEB", "CONVENIENCE STORE HONG KONG HKG", 45.00),
        ("27-FEB", "27-FEB", "DENTIST HONG KONG HKG", 1200.00),
        ("27-FEB", "27-FEB", "FLOWERS SHOP HONG KONG HKG", 380.00),
        ("27-FEB", "27-FEB", "INSURANCE CO HONG KONG HKG", 1800.00),
        ("27-FEB", "27-FEB", "UTILITY COMPANY HONG KONG HKG", 560.00),
        ("27-FEB", "27-FEB", "DEPARTMENT STORE HONG KONG HKG", 678.00),
        ("27-FEB", "27-FEB", "TOY SHOP HONG KONG HKG", 322.00),
        ("27-FEB", "27-FEB", "STATIONERY HONG KONG HKG", 145.00),
    ]

    assert len(charges) == 31, f"Expected 31 charges, got {len(charges)}"

    charges_sum = sum(c[3] for c in charges)
    target_charges = 20313.00
    diff = target_charges - charges_sum
    last = charges[-1]
    charges[-1] = (last[0], last[1], last[2], round(last[3] + diff, 2))
    charges_sum = sum(c[3] for c in charges)
    assert abs(charges_sum - target_charges) < 0.01, f"BOC charges sum: {charges_sum}"

    credits_list = [
        ("20-FEB", "21-FEB", "ALIPAY FINANCIAL SERVICES HONG KONG HKG", 500.00),
        ("22-FEB", "23-FEB", "REFUND SHOP RETURN HONG KONG HKG", 200.00),
    ]

    # Verify total
    txn_sum = -charges_sum + 500.00 + 200.00
    assert abs(txn_sum - (-19613.00)) < 0.01, f"BOC total: {txn_sum}"

    lines = [
        "BOC Credit Card Statement",
        "Jane Doe",
        "123 Example St, Hong Kong",
        "",
        "Payment Slip",
        "Card Type: taobao",
        "BOC Taobao World Mastercard",
        "",
        "HKD 200,000.00",
        "HKD 19,613.00",
        "HKD 230.00",
        "27-FEB-2026",
        "24-MAR-2026",
        "",
        "BALANCE B/F  0.00",
        "",
    ]

    for trans_d, post_d, merchant, amount in charges:
        lines.append(f"{trans_d} {post_d} {merchant}  {amount:,.2f}")

    for trans_d, post_d, merchant, amount in credits_list:
        lines.append(f"{trans_d} {post_d} {merchant}  {amount:,.2f} CR")

    lines += [
        "",
        "ODD CENTS TO NEXT BILL 0.00",
        "CURRENT BALANCE  19,613.00",
        "LAST ITEM",
        "",
        "Gift Points Summary",
    ]

    pdf = _pdf_with_text(lines, unicode_font=False)
    pdf.output(str(FIXTURES / "boc_feb2026.pdf"))
    print("Created boc_feb2026.pdf")


# ---------------------------------------------------------------------------
# SCB  (scb_mar2026.pdf)
# ---------------------------------------------------------------------------
# Parser regex patterns:
#   statement date: r"Statement Date.*?(\d{2}/\d{2}/\d{4})" (DD/MM/YYYY)
#   due date: r"Payment Due Date.*?(\d{2}/\d{2}/\d{4})"
#   credit limit: r"SMART CREDIT CARD\s+([\d]{1,3}(?:,\d{3})+)"
#   statement balance: r"STATEMENT BALANCE.*?([\d,]+\.\d{2})"
#   minimum payment: r"MINIMUM PAYMENT DUE.*?([\d,]+\.\d{2})"
#   purchases total: 7-float summary line, group(4) = purchases
#   transactions: split on r"Transaction Ref \d+\s+"
#     desc = parts[i+1].split("\xa0")[0].strip().split("\n")[0].strip()
#     "PAYMENT" -> excluded from charge_descs
#   charge_amounts: r"^(\d{2}/\d{2})\s+([\d,]+\.\d{2})$" (MM/DD format)
#   FX: "Foreign Currency CCY amount, Rate ..." in pre_text before Transaction Ref
#   balance check: sum(abs(t.hkd) for charge txns) == purchases_total (27345.39)
#
#   Tests:
#     statement_date=2026-03-10, balance=-26345.39, credit_limit=106000
#     due=2026-04-07, min_due=264, purchases_total=27345.39
#     70 txns, 1+ FX, no "PAYMENT" in merchants
#
#   NOTE: statement_date parser: r"Statement Date.*?(\d{2}/\d{2}/\d{4})"
#     uses re.DOTALL so date can be on next line
#     "10/03/2026" -> strptime("%d/%m/%Y") -> 2026-03-10 ✓
#   NOTE: period_start from r"^(\d{2}/\d{2})\s+[\d,]+\.\d{2}" -> first match
#     parsed as %m/%d/%Y -> month/day format
#   NOTE: credit limit pattern r"SMART CREDIT CARD\s+([\d]{1,3}(?:,\d{3})+)"
#     matches the INTEGER part before the decimal; "106,000" works


def make_scb() -> None:
    n_txns = 70
    purchases_total = 27345.39

    # Build 70 charges: 69 at 380.00 + 1 adjusted
    base_amount = 380.00
    base_total = base_amount * (n_txns - 1)
    last_amount = round(purchases_total - base_total, 2)
    assert last_amount > 0, f"last_amount negative: {last_amount}"

    # txns: (mm_dd, amount, merchant_name, fx_ccy, fx_amount)
    txns = []
    for i in range(n_txns - 1):
        mm = 2 if i < 35 else 3  # Feb and Mar
        dd = (i % 28) + 1
        mm_dd = f"{mm:02d}/{dd:02d}"
        merchant = f"MERCHANT {i + 1:02d} HONG KONG"
        txns.append((mm_dd, base_amount, merchant, None, None))

    # Last txn is FX
    txns.append(("03/08", last_amount, "AMAZON AWS US", "USD", 35.00))

    total = sum(t[1] for t in txns)
    assert abs(total - purchases_total) < 0.01, f"SCB total: {total}"

    lines = [
        "Standard Chartered Bank (Hong Kong) Limited",
        "SCB Smart Credit Card",
        "Jane Doe",
        "123 Example St, Hong Kong",
        "",
        "Statement Date",
        "10/03/2026",
        "",
        "Payment Due Date",
        "07/04/2026",
        "",
        # Credit limit: parser matches "SMART CREDIT CARD\s+([\d]{1,3}(?:,\d{3})+)"
        # The integer part must be comma-grouped 3-digit groups (no decimal)
        "SMART CREDIT CARD 106,000264.00 26,345.39",
        "",
        "STATEMENT BALANCE 26,345.39",
        "MINIMUM PAYMENT DUE 264.00",
        "",
        # Summary line: 7 floats; group(4) = purchases = 27,345.39
        # Label row ensures no float bleeds from previous line into this one
        "Previous Balance Payments Credits Purchases Cash Charges New Balance",
        "1,000.00 1,000.00 0.00 27,345.39 0.00 0.00 26,345.39",
        "",
        "Transaction Details",
        "",
    ]

    # PAYMENT Transaction Ref (excluded from charge_descs)
    lines.append("Transaction Ref 0001 ")
    lines.append("PAYMENT RECEIVED\xa0")
    lines.append("")

    # Charge Transaction Ref blocks
    for i, (_mm_dd, _amount, merchant, fx_ccy, fx_amt) in enumerate(txns):
        ref_num = i + 2
        if fx_ccy:
            # FX info must appear within 200 chars BEFORE the Transaction Ref
            lines.append(f"Foreign Currency {fx_ccy} {fx_amt:,.2f}, Rate 7.8")
        lines.append(f"Transaction Ref {ref_num:04d} ")
        lines.append(f"{merchant}\xa0")
        lines.append("")

    # Date/Amount table for charge_amounts (MM/DD format)
    lines.append("")
    lines.append("Date Amount")
    # CR line for payment (no match because it ends in CR not just amount)
    lines.append("03/01 1,000.00CR")
    for mm_dd, amount, _merchant, _fx_ccy, _fx_amt in txns:
        lines.append(f"{mm_dd} {amount:,.2f}")

    pdf = _pdf_with_text(lines, unicode_font=False)
    pdf.output(str(FIXTURES / "scb_mar2026.pdf"))
    print("Created scb_mar2026.pdf")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    FIXTURES.mkdir(exist_ok=True)
    make_mox()
    make_hsbc_mar()
    make_hsbc_feb()
    make_ccba_sep()
    make_ccba_mar()
    make_boc()
    make_scb()
    print("All fixtures created.")


if __name__ == "__main__":
    main()
