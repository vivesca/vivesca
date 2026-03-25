# AML Suppression Model — Post-Deployment Monitoring Design

Principles for monitoring AML alert suppression/hibernation mechanisms after deployment. Built from CNCBI hibernation analysis (Mar 2026). Applicable to any ML-based alert filtering with a reactivation mechanism.

---

## The Core Problem: Unobservable Misses

Any evaluation of a suppression mechanism using only *internally-generated outcomes* (STRs filed by analysts) is circular. Under suppression, some alerts that would have generated STRs are removed — so those STRs are never filed. The internal outcome count is a lower bound on true consequential exposure.

**Implication:** "We missed 21 STRs" means "21 STRs were filed through channels that weren't suppressed." It does not mean "21 is the total impact." The suppressed-but-consequential cases can only be detected through *external* channels.

---

## Monitoring Layers

### Layer 1 — Internal Re-scoring Events (automated)
When a hibernated customer generates a new non-low-risk alert, all prior low-risk alerts are reactivated. This is the wake-up mechanism. Measure:
- Reactivation count per period
- Latency from new alert generation to prior alert surfacing in analyst queue
- False positive rate among reactivated cases (should be low — reactivation means something changed)

**Limitation:** Only detects customers who generate a new non-low-risk alert. Customers whose risk never rises again are invisible.

### Layer 2 — Periodic Manual Sampling (required)
Sample hibernated customers for direct review. Size the sample to the miss rate:
- If miss rate = 0.19% of hibernated population, a 5% quarterly sample catches ~26% of expected misses per quarter
- If miss rate = 1%, sample 10% quarterly
- Stratify the sample toward customers with higher (but sub-threshold) risk scores and higher alert volume

**Cadence:** At minimum quarterly. Monthly if the mechanism is new or the miss rate is uncertain.

### Layer 3 — External Channel Monitoring (critical for unobservable misses)
This layer catches what internal monitoring structurally cannot:
- **Law enforcement referrals:** Cross-reference incoming LE requests / production orders against hibernated customer list
- **Correspondent bank SARs / Wolfsberg notifications:** Any incoming SAR or financial crime notification for a currently-hibernated customer
- **Adverse media:** Periodic name-screening of hibernated customers against adverse media feeds
- **Regulatory examiners:** During examinations, flag if examiner selects a case that was hibernated

For each hit: document entity_nbr, date of external flag, hibernation start date, and whether an internal non-low-risk alert was ever generated. This builds the "unobservable miss" dataset over time.

### Layer 4 — Post-STR Retrospective (quarterly)
After each STR filing, check: was this customer ever hibernated? If yes:
- When were they hibernated?
- What triggered the eventual STR (analyst review, reactivation, walk-in, etc.)?
- Would the STR have been filed earlier without hibernation?

This gives the truest measure of hibernation impact over time — but requires a 90–120 day lag to allow STR decisions to mature.

---

## Escalation Criteria

Define in advance:

| Metric | Threshold | Action |
|--------|-----------|--------|
| Confirmed miss rate (internal) | >0.5% of hibernated population | Review threshold calibration |
| External channel hits | ≥3 per quarter | Suspend hibernation; full audit |
| Layer 1 reactivation latency | >48 hours (batch lag) | Fix pipeline before deployment |
| Sampling detection rate | Rising trend over 3 quarters | Investigate model drift |

---

## Reporting to Governance / HKMA

Minimum quarterly governance pack:
1. Hibernated population count (point-in-time, end of period)
2. Reactivations triggered (Layer 1) — count and rate
3. Sampling results (Layer 2) — sample size, misses found, adjusted miss rate
4. External channel hits (Layer 3) — if any
5. Post-STR retrospective (Layer 4) — STRs where customer was previously hibernated
6. Cumulative adjusted miss rate (all layers combined)

Provide the cumulative rate, not just the point-in-time rate. A regulator will track trends.

---

*Source: CNCBI AML hibernation analysis, Consilium red-team, Mar 2026.*
*Related: `~/docs/solutions/aml-suppression-evaluation-checklist.md`, `~/docs/solutions/ml-evaluation-pitfalls.md`*
