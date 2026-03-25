# ML Evaluation Pitfalls

Lessons from AML hibernation analysis red-team (CNCBI, Mar 2026). Generalise to any ML-based suppression, filtering, or control mechanism evaluated retrospectively.

## 1. Survivorship Bias in Cohort Denominators

When building a "would have been suppressed/hibernated" cohort retrospectively, selecting only customers who *never* escalated during the full observation window creates a survivorship-filtered denominator. In production, the suppressed pool at any given time includes customers who haven't *yet* escalated but will. The retrospective denominator is the minimum possible.

**Fix:** Build cohorts as rolling point-in-time snapshots. If only retrospective data is available, disclose that the denominator represents the minimum (survivorship-clean) population, not the production-day average.

## 2. Backtest ≠ Operational Validation

A control mechanism validated only on historical data where the control was *never actually deployed* has not been operationally validated. Presenting a backtest as a validated control is a category error — especially for regulators and governance bodies who distinguish between tested and proposed controls.

**Fix:** Distinguish explicitly between "backtested" and "production-tested" in any submission. If the control has not been deployed, propose a monitored pilot period. Measure actual reactivation latency, pipeline error rates, and edge cases before claiming the control is proven.

## 3. Outcome Date vs Trigger Date

When assessing whether a control "protected" a case, use the date when protection was *needed* (the moment suspicious behaviour first occurred or was first visible), not the date when the outcome was *recorded* (STR filing, case closure). Outcome dates lag trigger dates by weeks to months. Using the outcome date overstates protection coverage.

**Example:** STR filed Day 90. Suspicious behaviour started Day 1. An alert generated Day 80 appears "protective" at filing time but was irrelevant at the actual moment of exposure.

**Fix:** Reconstruct event timelines from raw timestamps. Use the earliest suspicious-behaviour indicator as the anchor for protection checks, not the downstream outcome date.

## 4. Circular Evaluation of Suppression Mechanisms

Evaluating a suppression mechanism using only outcomes observed under the *current* (non-suppressive) process understates the true miss rate. Under suppression, some outcomes (STRs, flags) would never be generated because the inputs that triggered them would be removed. The observed outcome count is a lower bound on consequential exposure.

**Fix:** Acknowledge this circularity explicitly in methodology notes. Design post-deployment monitoring to detect cases where suppressed customers surface via *external* channels (law enforcement referrals, correspondent bank SARs, adverse media), not only through internal re-scoring events.

## 5. Alert Existence vs Alert Active Status

"Customer had a non-low-risk alert in the queue" conflates alert *existence* with alert *active/unresolved status*. A reviewed-and-closed alert does not constitute active protection. Always check alert disposition status at the point when protection was needed, not at the time the outcome was recorded.

**Fix:** For any "protected by existing alert" claim, verify: (a) the alert existed before the exposure event, and (b) the alert was still open/unresolved at that time.

---

*Source: CNCBI AML hibernation analysis, Consilium red-team, Mar 2026.*
*Related: `~/docs/solutions/aml-suppression-evaluation-checklist.md`, `~/docs/solutions/aml-suppression-monitoring.md`*
