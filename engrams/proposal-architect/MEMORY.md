# Proposal Architect — Agent Memory
## Persistent patterns across engagements. Updated as new evidence accumulates.

## Scope Traps (confirmed FS AI)

- **"Chatbot for X" = retrieval pipeline + structured Q&A + workflow, not a chat UI build.** Chatbot framing consistently undersells complexity. Reframe in engagement framing section before scope definition.
- **"3 years of data available" at a retail bank:** Almost always contains at least one core banking migration, schema change, or label inconsistency. WP1 data audit is non-negotiable — do not let client or internal pressure skip it.
- **Model validation at HKMA-regulated institutions = 8–12 weeks minimum.** Do not let Phase 1 discovery be called a "quick win" if it contains any model component. Compliance review cycles are the hard constraint, not build time.
- **Feature engineering is the most underestimated work package in FS AI.** Budget 20–30% of Phase 2 data engineering effort as contingency, always. State this as a range, not a contingency line.
- **Change management is the highest Phase 2 failure mode.** Officers, advisors, or analysts who feel surveilled by AI comparison give bad pilot feedback. Design parallel-runs as tool evaluations, not performance reviews.
- **"Stakeholders aligned" = data team and business team have different success metrics until proven otherwise.** Require both sponsors to sign success criteria before pilot design is locked. Run a dedicated alignment workshop in Week 2.

## Assumption Patterns by Client Type

### Retail Bank (HK / HKMA regulated)
- HKMA SP-14 model risk guidance is the relevant regulatory constraint for any credit or risk AI model.
- "Parallel-run testing" may constitute a material change under the bank's internal model risk policy — get written compliance confirmation before pilot design is finalised.
- IT skepticism at retail banks is structural (legacy stack, resource constraints) — always escalate to a named IT resource at kick-off. Do not accept "IT will support" without a name and a data access SLA.
- Data residency and PDPO (Personal Data Privacy Ordinance) constraints may require Capco to work behind VPN or on anonymised datasets. Confirm before scoping data access timelines.
- Budget approval thresholds at HK retail banks typically sit at department head level up to ~HK$1-2M; above that often requires a procurement or IT steering committee. Always ask the threshold question.

## Effort Benchmarks (FS AI, HK market)

- Phase 1 Discovery (interviews + data audit + reg review): 26–40 consultant days / 6 weeks elapsed
- Phase 2 Pilot Build (pipeline + model + interface + validation + change mgmt): 78–117 consultant days / 16 weeks elapsed
- Combined Phase 1+2: 104–157 consultant days / 22 weeks elapsed
- These are ranges for mid-size retail bank, single-product pilot. Widen for investment bank; compress for insurance (better data hygiene).

## Risk Register Defaults (always include)

1. Data quality risk (always HIGH likelihood in FS)
2. Regulatory interpretation risk (HIGH impact in HKMA context)
3. Stakeholder alignment risk (CDO vs. business champion misaligned success metrics)
4. Scope creep risk (adjacent use cases surfaced during Phase 2)
5. IT delivery friction (resource not committed, access delayed)

## Commercial Patterns

- "Pilot first / budget not disclosed" = phase the SOW with a separate gate. Phase 1 SOW (~HK$600K–900K) is easier to approve; Phase 2 requires separate sign-off. Price Phase 1 to win, design it to set up Phase 2.
- Point estimates on FS AI engagements signal overconfidence to sophisticated buyers. Always use ranges. Ranges will tighten after data audit.
- Include explicit scope change protocol in commercial terms — change request + impact assessment + sponsor approval before work begins.

## Delivery Framework Preferences

- Phase gates are hard stops, not reviews. Gate sign-off from all named stakeholders before next phase spend is committed.
- RAID log from kick-off. IT dependencies and data access items are the highest-frequency RAID entries in FS AI.
- Agile sprints within Phase 2, but phase gates are waterfall-style commercial checkpoints. Do not conflate the two.
- Internal scope trap notes in proposals — always mark "REMOVE BEFORE CLIENT SEND."
