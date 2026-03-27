---
name: expression
description: Weekly career compound machine — produce consulting IP from accumulated sparks.
user_invocable: true
context: fork
---

# The Forge — Weekly Career Compound Machine

Produces consulting intellectual capital from the week's accumulated sparks, AI landscape, and client work.

## Hard Rules

- **LinkedIn: NEVER post, draft full posts, or interact.** Produce seeds only (hook + bullets + angle).
- **Client-identifiable information: NEVER in the library.** Generalize before storing.
- **Quality bar: draft-grade.** All assets created with `maturity: draft`.
- **Autonomous flywheel:** See [[autonomous-flywheel]]. Agents create freely. Terry promotes on demand.

## Prerequisites

Before running, verify:
- `~/epigenome/chromatin/Consulting/_sparks.md` has content (daily spark agent has been running)
- `~/epigenome/chromatin/Thalamus.md` exists (landscape context)
- `~/epigenome/chromatin/AI News Log.md` exists (raw news)

If sparks are empty, warn Terry and offer to run a one-off spark generation first.

## Orchestration

### Phase 1: Planning (Opus lead)

Read all inputs and produce a work plan:

**Inputs to read:**
1. `~/epigenome/chromatin/Consulting/_sparks.md` — this week's pre-triaged sparks
2. `~/epigenome/chromatin/Thalamus.md` — AI landscape synthesis
3. `~/epigenome/chromatin/North Star.md` — taste filter
4. `~/epigenome/chromatin/AI News Log.md` — last 7 days (for context the sparks may have missed)
5. Existing library: `ls ~/epigenome/chromatin/Consulting/{Policies,Architectures,"Use Cases",Experiments}/` — for dedup and enrichment
6. Recent client work: `git log --oneline --since="7 days ago" -- ~/epigenome/chromatin/Capco/ ~/epigenome/chromatin/HSBC/ 2>/dev/null` (if any)

**Plan output:** Which sparks map to which workers. Which existing assets to enrich. What cross-pollination opportunities exist.

### Phase 2: Dispatch Workers (Sonnet, parallel)

Create a team and dispatch 6 parallel workers. Each worker gets:
- Its assigned sparks from the plan
- Read access to existing library (its subdirectory only)
- The frontmatter schema for its asset type
- Instruction to create files as `YYYY-MM-DD-slug.md` with correct frontmatter

**Workers:**

| Worker | Scope | Output directory |
|--------|-------|-----------------|
| content | Garden post drafts (via sarcio) + LinkedIn seeds | `~/epigenome/chromatin/Writing/Blog/Published/` + append to `_sparks.md` |
| policy | P&P templates, regulatory deltas, framework updates | `~/epigenome/chromatin/Consulting/Policies/` |
| architecture | Reference architectures, patterns, component notes | `~/epigenome/chromatin/Consulting/Architectures/` |
| use-case | Use case entries with structured frontmatter | `~/epigenome/chromatin/Consulting/Use Cases/` |
| experiment | Experiment designs (NOT execution), technique comparisons | `~/epigenome/chromatin/Consulting/Experiments/` |
| intelligence | Weekly brief + competitor lens from `#competitor` sparks | `~/epigenome/chromatin/Consulting/_weekly/` (embedded in weekly report) |

**Worker instructions template:**

Substitute `{role}`, `{sparks}`, and `{existing_files}` at dispatch time. The schema block below is fixed per worker type — copy the correct one verbatim into each worker's prompt.

```
You are the {role} worker for the Career Compound Machine.

Your task: produce draft-grade consulting IP from the assigned sparks.

Assigned sparks:
{sparks}

Existing assets in your directory (for dedup/enrichment):
{existing_files}

Frontmatter schema for your asset type:
[SEE PER-WORKER SCHEMA BELOW — copy the correct block verbatim]

Rules:
- One markdown file per asset, named YYYY-MM-DD-slug.md
- Include full frontmatter with maturity: draft
- Draft-grade: substance over polish. Get the ideas down.
- If a spark enriches an existing asset, update the existing file instead of creating a new one.
- Content worker: garden posts go through sarcio. LinkedIn items are seeds only (hook + bullets + angle), appended to _sparks.md with #linkedin-seed tag.
- Experiment worker: design the experiment (hypothesis, method, expected outcome). Do NOT execute.
```

**Frontmatter schemas — embed these verbatim in each worker prompt:**

**policy worker** (`~/epigenome/chromatin/Consulting/Policies/`):
```yaml
---
type: guideline | framework | standard | checklist
domain: ops | risk | compliance | data | technology | conduct
jurisdiction: global | UK | EU | HK | SG | US | APAC
maturity: draft
source: research | client-work | regulatory | synthesis
created: YYYY-MM-DD
---
```

**architecture worker** (`~/epigenome/chromatin/Consulting/Architectures/`):
```yaml
---
type: pattern | reference-architecture | component | integration
domain: agent-orchestration | data | security | mlops | platform
maturity: draft
source: research | client-work | synthesis
created: YYYY-MM-DD
---
```

**use-case worker** (`~/epigenome/chromatin/Consulting/Use Cases/`):
```yaml
---
type: use-case
domain: ops | risk | compliance | front-office | back-office | data
technique: agent | rag | fine-tuning | classification | generation | multimodal
risk-level: low | medium | high | critical
maturity: draft
source: research | client-work | market
created: YYYY-MM-DD
---
```

**experiment worker** (`~/epigenome/chromatin/Consulting/Experiments/`):
```yaml
---
type: benchmark | tabletop | ablation | pilot
domain: agents | governance | data | models | prompting
technique: (specific method being tested)
result: (pending — experiment not yet executed)
maturity: draft
source: research-replication | original | client-hypothesis
created: YYYY-MM-DD
---
```

**content worker** (`~/epigenome/chromatin/Writing/Blog/Published/`):
```yaml
---
title: "Post Title Here"
pubDatetime: YYYY-MM-DDTHH:MM:SS+08:00
description: "One-sentence summary for SEO and preview."
date: YYYY-MM-DD
draft: false
tags: [tag1, tag2, tag3]
---
```

**intelligence worker** (`~/epigenome/chromatin/Consulting/_weekly/`):
```yaml
---
type: intelligence-brief
week: YYYY-WNN
domain: competitive | regulatory | market | technology
maturity: draft
source: sparks | news | synthesis
created: YYYY-MM-DD
---
```

**Worker failure handling:**

Each worker must be treated as potentially failing. After all workers complete (or time out), before synthesis:

1. **Collect results.** For each of the 6 workers, check whether it produced output files in its target directory with a `created` date matching today.
2. **Identify failures.** A worker has failed if: it produced no files, its files lack valid frontmatter, or it threw an error.
3. **Log failures.** Record failed workers by name with the error or symptom.
4. **Do not silently drop.** Any worker failure must be included in the synthesis report and flagged to Terry via Telegram (even on an otherwise successful run — worker failures are always anomalies).
5. **Partial success is acceptable.** Synthesis proceeds with whatever workers succeeded. Do not abort the entire forge because one worker failed.
6. **Retry heuristic.** If 3 or more workers failed, abort synthesis, send Telegram, and ask Terry whether to retry or investigate.

### Phase 3: Synthesis (Sonnet, after all workers complete)

Run a synthesis agent that:
1. Reads all newly created/modified files across all subdirectories
2. Cross-pollinates: flag where one asset should reference another (add `**Related:**` wikilinks)
3. Identifies talk seeds: combinations of experiment + use case + insight that could become a conference talk
4. Regenerates `~/epigenome/chromatin/Consulting/_index.md` with updated stats
5. Archives processed sparks: move this week's sections from `_sparks.md` into the weekly report
6. Writes weekly report to `~/epigenome/chromatin/Consulting/_weekly/YYYY-WNN.md`, including:
   - Funnel metric: `Sources: N → Sparks: N → Assets: N → Promoted: N → Used: N`
     (count `maturity: reviewed` for promoted, check daily notes for used)
   - Cross-pollination map
   - Talk seeds
   - Three prompts for Terry:
     1. "Did you use anything from last week's batch?"
     2. "What surprised you this week?"
     3. "What did you predict that was wrong?"
7. Telegram: **only on anomaly** (zero sparks processed, any worker failure, funnel regression, or ≥3 workers failed triggering abort).
   Normal successful runs are silent — Terry reads the weekly report when he wants to.
   Worker failure messages must name the failed worker(s) and the symptom (no files, invalid frontmatter, error text).

### Phase 4: Cleanup

- Verify all new files have valid frontmatter
- Confirm `_sparks.md` only contains unprocessed items
- Log run metadata for future reference

## Output

After the forge completes, present Terry with:
1. The funnel metric (one line)
2. A one-paragraph prose summary of what was produced and why
3. Any items that need human judgment (experiment execution, client generalization)
4. Telegram only if something went wrong or needs attention

## Budget

Target: ~$1-2 per run. Opus lead (~$0.50-1.00) + 6 Sonnet workers (~$0.10 each) + Sonnet synthesis (~$0.10).
First runs may overshoot while prompts tune. Monitor and adjust.
