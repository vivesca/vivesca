# AML Suppression / Hibernation Model Evaluation Checklist

Consulting tool for evaluating any AML alert suppression or hibernation proposal before regulatory submission. Built from CNCBI hibernation analysis red-team (Mar 2026). Applicable at future clients.

---

## Before Running the Numbers

- [ ] **Define "suppressed" precisely.** Fully removed vs partially visible (mixed customer) is a material distinction. Use separate denominators.
- [ ] **Identify all denominators upfront.** For a miss rate: fully-removed population? All customers with any low-risk alert? All customers with consequential outcomes? Present all three; choose the primary based on what HKMA/regulator expects.
- [ ] **Check for look-ahead bias.** If the "suppressed" cohort is defined retrospectively across the full window, it's survivorship-filtered. State whether the denominator is point-in-time or survivorship-clean.

---

## Numerator Integrity

- [ ] **Dedup alerts correctly.** If alerts are re-scored weekly, use `DISTINCT alert_id` (not row count). Weekly re-scores create duplicate rows for the same alert.
- [ ] **Check crossover alerts.** Alerts that cross the threshold in different scoring batches inflate both sides of the numerator/denominator split. Verify no alert_id appears on both sides.
- [ ] **Verify STR flag source.** If joining to a disposition table, confirm the table contains *only* STR outcomes (not all dispositions). Apply an explicit `str = 1` filter if the table includes all outcome types.

---

## Protection Claims ("Would Have Been Reviewed Anyway")

- [ ] **Verify alert state, not just existence.** For each "protected" customer, confirm their non-low-risk alert was *open and unresolved* at the time of the suspicious behaviour — not just at STR filing time.
- [ ] **Use trigger date, not outcome date.** Suspicious behaviour precedes STR filing by weeks to months. Protection checks keyed to filing date overstate coverage.
- [ ] **Check alert termination timing.** If a non-low-risk alert was reviewed and closed as a false positive *before* the suspicious behaviour, it was not protective. Count such customers as missed.

---

## Safety Net Validation

- [ ] **Is the reactivation/wake-up mechanism production-tested?** Distinguish between backtested and operationally deployed. If backtested only, disclose this explicitly.
- [ ] **What is the reactivation latency?** Real-time, hourly batch, or overnight batch? A batch delay creates a window where an analyst can review and close the triggering alert before historical context is surfaced.
- [ ] **Has the end-to-end pipeline been tested?** Reactivation logic, downstream queue injection, analyst UI surfacing — all three must work.

---

## Annualised Projections

- [ ] **Is the observation window mature?** STR decisions typically lag 60–95 days. If the final quarter is immature, present a range, not a point estimate.
- [ ] **Present Q1–Q3 confirmed separately from Q4 projected.** "21 confirmed through Q3; Q4 pending" is more defensible than "~21 per year."
- [ ] **Don't call a number a "lower bound" and also use it as the headline figure.** These are contradictory.

---

## Disclosure Decisions

- [ ] **Concentration / systematic archetype under-scoring:** If discovered, do not omit. Concealing known model deficiencies from a regulator is worse than disclosing them. But always attach a remediation plan or characterisation timeline alongside the disclosure.
- [ ] **Dual denominator:** Present both the population rate (miss/all hibernated) and the control-failure rate (miss/consequential cases). Explain what each measures. Don't let the regulator compute the harder number and find you didn't offer it.
- [ ] **Backtest-only controls:** State explicitly. Propose pilot or parallel-run period before full deployment.

---

## Post-Deployment Monitoring

- [ ] **Design monitoring to catch unobservable misses.** The observed STR count is a lower bound — under suppression, some STRs would never be filed. Sample hibernated customers via: law enforcement referrals, correspondent bank SARs, adverse media, periodic manual review.
- [ ] **Set sampling frequency and size.** Link to the miss rate and the population size. If miss rate is 0.19%, a 5% sample of hibernated customers per quarter catches ~26% of expected misses.
- [ ] **Define escalation criteria.** At what adjusted miss rate would the bank suspend or modify the suppression mechanism?

---

*Source: CNCBI AML hibernation analysis, Mar 2026.*
*Related: `~/docs/solutions/ml-evaluation-pitfalls.md`, `~/docs/solutions/aml-suppression-monitoring.md`*
