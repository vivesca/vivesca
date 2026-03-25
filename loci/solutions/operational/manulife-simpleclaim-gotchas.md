# Manulife SimpleClaim Gotchas

## Submissions can vanish silently

Feb 22 submission ($3,638 QHMS) had no record 2 days later. Resubmitted Feb 24 with clinic receipt.

**Rule:** Check the Manulife app within 24-48h to confirm your claim appears. Don't assume submission = received. Keep the physical receipt until confirmed.

## Category for health screening: use "Others"

Annual health checks (QHMS, body checks) don't have a dedicated SimpleClaim category. Submit under **"Others"**.

## Receipt type matters

Upload the **clinic receipt** (the one from the medical provider), not a shop/payment receipt. Multi-page receipts: use `pdftoppm` for PDF→PNG conversion (not `sips`, which only handles single pages).

## "Others" → Routine Physical Examination benefit cap ($840/year)

Submitting a body check under "Others" causes Manulife to classify it as **Routine Physical Examination** — a sub-benefit with its own annual cap (~$840), completely separate from the general Plan C limit ($2,800). Once exhausted, further body check claims pay $0.

**Rule:** Check the benefit schedule before submitting body checks. Don't assume the general Plan C ceiling applies — the sub-benefit cap bites first.

Discovered: Mar 2026 (QHMS $3,638 claimed, $840 paid, remark: "05 Overall maximum benefit exhausted").

## Non-panel doctors are claimable

Manulife Plan C covers non-panel specialists at full reimbursement rate. No pre-approved provider list needed. Just submit the claim.

## Insurance gap at job transition

Map the exact gap between old scheme end and new scheme start. Front-load all diagnostic appointments (X-rays, specialist assessments, dental) under the old plan in the final 2 weeks. Ongoing treatment (physio) can shift to the new plan.

Example: Manulife ends ~Mar 15, Capco AIA starts Apr 8 = 3-week gap. Strategy: ortho + X-ray under Manulife, physio under AIA.

Discovered: Feb 2026 (CNCBI → Capco transition)
