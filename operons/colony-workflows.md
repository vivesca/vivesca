# Colony Workflows

Pre-defined workflows connecting colonies to triggers and cadences.
Colonies form at runtime when the quorum threshold is met.
Parallel buds are the default — colonies justify their coordination cost.

## Scheduled Colonies

| Cadence | Colony | Trigger | Product | Cost |
|---------|--------|---------|---------|------|
| Monthly | monthly-review | /ecdysis monthly or month end | Monthly review doc with trends | ~$4 |
| Quarterly | landscape-survey | Manual or /chemotaxis deep | Domain survey reference doc | ~$5 |

## Event-Triggered Colonies

| Event | Colony | Quorum signal | Product | Cost |
|-------|--------|---------------|---------|------|
| System break (multi-component) | incident-response | >1 component affected, blocking | Fix + incident report | ~$3 |
| New client engagement | governance-assessment | Client onboarding | AI governance maturity report | ~$5 |
| Architecture question (complex) | architecture-review | >3 modules touched, cross-cutting | Ranked findings doc | ~$3 |
| High-stakes deliverable | content-production | Client-facing, claims need verification | Polished doc with citations | ~$3 |

## Pre-Engagement Colonies

| When | Colony | Trigger | Product | Cost |
|------|--------|---------|---------|------|
| Before workshop | workshop-facilitation | Client workshop scheduled | Prep materials + debrief template | ~$4 |
| Before major build | skill-forge | /transcription produces complex spec | Validated SKILL.md + tests | ~$3 |
| Entering new domain | competitive-analysis | /proliferation identifies crowded niche | Comparative matrix | ~$4 |

## Colony Formation Protocol

```
1. Signal detected (trigger)
2. Quorum check: does this need coordination, or do parallel buds suffice?
   - Can the work be split into independent pieces? → parallel buds
   - Does the product require SYNTHESIS? → colony
3. Cost gate: estimate cost. Is the colony worth 3-5x a single bud?
4. Form: lead (opus) + workers (sonnet, max 5)
5. Execute protocol (from colony template)
6. Dissolve: colony terminates, product delivered
7. Log: colony formation + outcome to ~/code/epigenome/chromatin/colony-log.md
```

## Colony vs Parallel Buds Decision

```
                        Need synthesis?
                       /              \
                     YES               NO
                      |                 |
              Worth 3-5x cost?    Parallel buds
             /              \        (default)
           YES               NO
            |                 |
         Colony          Parallel buds
                         + manual merge
```

## Colony Log

After every colony formation, append to ~/code/epigenome/chromatin/colony-log.md:
- Date, colony template used, trigger
- Workers dispatched, cost estimate vs actual
- Product quality: did synthesis add value over parallel buds?
- Verdict: justified / overkill / should have been buds

This log feeds the selection pressure on colony templates.
Colonies that are consistently "overkill" get retired.
