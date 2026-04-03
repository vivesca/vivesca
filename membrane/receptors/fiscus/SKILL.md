---
name: fiscus
description: Monthly credit card and bank statement review. Parses PDF statements, checks recurring charges against baseline, flags anomalies, sends Telegram digest via deltos.
triggers:
  - fiscus
  - statement
  - "check statements"
  - "financial review"
  - "process statement"
user_invocable: true
---

# fiscus — Monthly Statement Review

## Context

- **Statement source:** Standard Chartered (primary). Possibly HSBC later.
- **PDF drop folder:** `~/docs/financials/statements/` — confirm exact path on first run. Update this skill once confirmed.
- **Baseline file:** `~/docs/financials/recurring-baseline.json` — known recurring charges. Create on first run.
- **Output:** Telegram digest via `deltos`.

## Trigger

User exports statement PDF from SC/HSBC app → saves to drop folder → says "process statement" or "/fiscus".

## Steps

### Step 0 — Locate PDF

```bash
# Find most recent statement PDF in drop folder
ls -lt ~/docs/financials/statements/ | head -5
```

If folder path is wrong or unknown, ask Terry for the exact path. Update this skill once confirmed.

### Step 1 — Parse PDF

```bash
# Extract text from PDF
pdf2txt.py "<path>" 2>/dev/null || python3 -c "
import subprocess, sys
result = subprocess.run(['pdftotext', '-layout', sys.argv[1], '-'], capture_output=True, text=True)
print(result.stdout)
" "<path>"
```

If neither tool available: `pip install pdfminer.six` or `brew install poppler`.

Extract all transactions as structured data:
- Date
- Merchant / description
- Amount (HKD or foreign currency + FX rate if shown)
- Category (infer from merchant name)

### Step 2 — Load Baseline

```bash
cat ~/docs/financials/recurring-baseline.json 2>/dev/null || echo "FIRST_RUN"
```

**If FIRST_RUN:** Skip anomaly check. Present all transactions to Terry and ask him to identify which are expected recurring charges. Build and save the baseline. Done.

**If baseline exists:** Proceed to Step 3.

### Step 3 — Anomaly Check

For each transaction, classify:

| Status | Condition |
|--------|-----------|
| `OK` | Matches baseline entry (merchant + amount within ±10%) |
| `AMOUNT_DRIFT` | Known merchant but amount changed >10% |
| `NEW` | Merchant not in baseline |
| `MISSING` | Expected recurring charge absent this month |

### Step 4 — Digest

Send via `deltos`:

```
fiscus — [Month] [Year]

TOTAL: HKD X,XXX

OK (N recurring charges as expected)

FLAG:
- [Merchant] HKD XXX — NEW (not in baseline)
- [Merchant] HKD XXX → HKD YYY — AMOUNT_DRIFT (+N%)
- [Expected merchant] — MISSING

Action needed? Reply Y to update baseline, N to skip.
```

### Step 5 — Baseline Update (if flagged)

After Terry reviews:
- NEW charge confirmed as recurring → add to baseline
- AMOUNT_DRIFT confirmed → update baseline amount
- ONE-OFF → leave out of baseline

Save updated `~/docs/financials/recurring-baseline.json`.

## Baseline Format

```json
{
  "recurring": [
    {
      "merchant": "Netflix",
      "amount_hkd": 63,
      "tolerance_pct": 5,
      "cadence": "monthly",
      "notes": ""
    }
  ],
  "last_updated": "2026-03-08"
}
```

## Boundaries

- Do NOT make any payments — analysis and flagging only.
- Do NOT store raw statement PDFs anywhere except the drop folder Terry chose.
- Do NOT infer "OK to pay" — Terry approves all flagged items.

## Setup TODO (first run)

- [ ] Confirm iCloud Drive statement folder path — update Step 0
- [ ] Run on first SC statement PDF to build baseline
- [ ] Decide if HSBC account should be added

## Bank Automation Status

| Bank | Automatable? | Notes |
|------|-------------|-------|
| HSBC | No | Hard bot detection (EAC error) even in headed Chromium |
| CCBA | Likely yes | Loaded cleanly; "system busy" = unauthenticated only. Log in via headed Chromium → cookies persist |
| SCB | Untested | In maintenance Mar 8 |
