---
name: karyotyping
description: Arrange components visually to find structural anomalies. "system audit".
user_invocable: true
model: sonnet
---

# Karyotyping — Chromosomal Layout for System Anomaly Detection

In cytogenetics, karyotyping arranges chromosomes by size and banding to reveal deletions, duplications, and translocations. Here: lay out the organism's components in canonical order and look for what's wrong at a glance.

**Sibling structural audits:** `/cytometry` (autonomy classification — who self-governs?) · `/histology` (client workshop — cell biology lens). For diagnostics: `/auscultation` (passive) → `/palpation` (deep probe) → `/integrin` (automated scan).

## When to Use

- Before a major refactor — know what's there before cutting
- System feels off but you can't name why
- Onboarding to an unfamiliar repo or organism instance
- After a period of rapid growth — check for structural drift

## Method

### Step 1 — Enumerate components

Collect all meaningful structural units:
- Receptors / skills (ls receptors/)
- MCP tools (receptor_list or mcp config)
- Scheduled processes (LaunchAgents, cron)
- Data stores (chromatin paths, DBs, files)
- External dependencies (APIs, services)

### Step 2 — Lay out the karyotype

Group by functional chromosome (domain):
```
SENSING         | integrin, palpation, auscultation, electroreception
METABOLISM      | glycolysis, autophagy, endocytosis, lysosome
COMMUNICATION   | secretion, exocytosis, conjugation, keryx
GROWTH          | endosymbiosis, differentiation, ontogenesis
OPERATIONS      | hemostasis, debridement, cytokinesis, ecdysis
MEMORY          | histone, ecphory, replication, oghma
```

### Step 3 — Read the banding

Flag anomalies:
| Pattern | Interpretation |
|---------|---------------|
| Domain with 1 component | Underdeveloped — growth candidate |
| Duplicate function across domains | Translocation — consolidate |
| Component with no domain fit | Novel chromosome — name it |
| Expected component missing | Deletion — deliberate or drift? |

### Step 4 — Report

One-page karyotype. Three findings max. Each finding: anomaly type + one recommended action.

## Anti-patterns

- **Audit without stopping:** karyotyping is a pause, not a sprint. Resist fixing during the layout phase.
- **Over-sorting:** don't spend more than 10 minutes on groupings. Approximate chromosomes beat perfect taxonomy.
- **Missing the missing:** the hardest anomaly to spot is the absent component. Ask "what should be here that isn't?"
