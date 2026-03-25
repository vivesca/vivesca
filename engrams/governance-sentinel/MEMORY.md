# Governance Sentinel — Persistent Memory

## Jurisdiction Patterns

### HK / HKMA
- CR-G-14 in client briefs is often the credit risk SPM reference, not the derivatives module — confirm scope at intake.
- HKMA 2024 GenAI circular extends 2019 AI principles; any GPT/LLM system at a HK bank is in scope for GenAI circular, not just the 2019 framework.
- PDPO cross-border transfer: Azure OpenAI data residency must be confirmed; enterprise agreement necessary but not sufficient — explicit documentation required for validation package.
- Model risk appetite statements at HK retail banks frequently predate LLM adoption — flag proactively; CRO sign-off or appetite amendment needed before submission.
- Board-level accountability is a recurring HKMA examination finding — named Senior Management owner (individual, not committee) must be in the submission.

## Recurring Validation Team Findings by Institution Type

### HK Retail Bank — LLM Decision-Support Tools
- Monitoring plans without thresholds and named owners are rejected (not just flagged).
- Decision-support framing challenged when override rates are not logged — validators ask for evidence officers are genuinely overriding.
- Explainability sections describing global model behaviour (interpretability) rejected; validators want per-decision explainability pathway for adverse outcomes.
- Azure/cloud data transfer triggers DPO review that tech teams typically haven't started — initiate in parallel with build, not at submission.
- Azure OpenAI silent model version increments (under same GPT-4x name) are a recurring gap — always check whether model version is pinned.

## Universal RED Flags (Any Jurisdiction)
- "We will add monitoring after go-live" — always a submission blocker, never a finding.
- Missing model inventory classification — validation cannot begin without written classification decision.
- Uncontrolled third-party model versioning (e.g., Azure OpenAI without pinned version) — invalidates the validation in production.

## Key Distinctions to Enforce
- Explainability (per-decision reason) != interpretability (global model behaviour). Customers and regulators need explainability. Don't let clients conflate them.
- Decision support != automated decision. Preserve the framing by ensuring override logging exists — nominal human-in-the-loop without logged overrides will be reclassified.
- Model risk clearance != AI risk + operational risk clearance. Always note the remaining risk domains in the report.

## Remediation Sequencing That Works
For HK retail bank LLM decision-support tools, optimal sequence:
1. Model classification memo (unlocks validation start)
2. Model version pinning + monitoring plan (parallel)
3. Use specification + prompt documentation (Capco-led, fast)
4. Human evaluation + fairness assessment (longest lead time, start early)
5. Audit log spec + PIA (parallel to evaluation)
6. Governance chain / board accountability confirmation
7. Assemble and submit

## Client Types — Known Biases
- HK retail banks: strong on credit process governance, weak on AI/LLM-specific governance overlays. They have MRM frameworks but they predate GenAI.
- Typically underestimate: monitoring plan specificity, fairness assessment, data transfer documentation.
- Typically overestimate: "decision support" classification as a governance safe harbour (it reduces burden but does not eliminate it).
