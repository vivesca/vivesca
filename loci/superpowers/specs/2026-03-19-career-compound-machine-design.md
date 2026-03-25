# Career Compound Machine — Design Spec

> **Status:** Draft
> **Date:** 2026-03-19
> **North Star:** #2 Build a career worth having

## Purpose

A recurring autonomous pipeline that compounds Terry's consulting intellectual capital. Transforms raw inputs (AI news, client work, industry reports) into seven interconnected asset streams that build toward "the person banks call when they need to govern AI at scale."

## Hard Constraints

- **LinkedIn: never post, never draft full posts, never interact.** Agents produce seeds only (hook + bullets + angle). Terry promotes manually.
- **WhatsApp: never send.** Existing rule, unchanged.
- **Client-identifiable information: never in the library.** Generalize before storing.
- **Quality bar: draft-grade.** Polish on demand when an engagement needs it. Sarcio judge gate for garden posts only.
- **Budget: Max20 green.** Daily ~$0.02 (sonnet). Weekly ~$1-2 target (first runs may overshoot while prompts tune).
- **Autonomous flywheel principle:** Agents create freely at draft-grade. Human attention is a promotion gate, not a creation gate. See [[autonomous-flywheel]].

## Human-in-the-Loop Design

The flywheel never blocks on Terry. Three irreducible human judgments exist; all are pull-based.

| Moment | Terry's role | Trigger | Blocks flywheel? |
|--------|-------------|---------|-------------------|
| **Experiment selection** | Decide which proposed experiments are worth running | Scan `Experiments/` when curious or when a client question arises | No — unreviewed designs stay as library reference |
| **Client work generalization** | Flag "generalize this" post-delivery, review for identifiable details | After a deliverable ships | No — only fires on Terry's initiative |
| **LinkedIn promotion** | Pick a seed, rewrite in own voice, post | Scan `_sparks.md` when inspiration strikes | No — seeds accumulate indefinitely |
| **Draft → reviewed promotion** | Upgrade an asset when an engagement needs it | Pull on demand | No — drafts serve as searchable reference at any maturity |

Everything else — daily sparks, weekly forge, garden posts, intelligence briefs, talking points, cross-pollination — runs without human input.

**Notification, not obligation:** The weekly Telegram report summarises what was produced. It is informational, not a to-do list.

## Asset Schema & Storage

All consulting IP lives under `~/code/epigenome/chromatin/Consulting/`:

```
~/code/epigenome/chromatin/Consulting/
├── Policies/          # FS AI governance P&P templates
├── Architectures/     # Reference AI agent solution architectures
├── Use Cases/         # FS AI use case library
├── Experiments/       # Technique benchmarks, comparisons, test results
├── _sparks.md         # Daily agent output: flagged items + LinkedIn seeds
├── _index.md          # Auto-generated catalogue with counts/stats
└── _weekly/           # Weekly compound reports (archived)
```

### Frontmatter Standards

**Policies:**
```yaml
---
type: policy | procedure | framework | guideline
domain: model-risk | data-governance | explainability | bias | ops | security
jurisdiction: HK | SG | AU | EU | US | global
maturity: draft | reviewed | client-tested
source: hsbc-generalized | research | regulatory-delta
created: YYYY-MM-DD
---
```

**Architectures:**
```yaml
---
type: reference | pattern | component
domain: llm-gateway | agent-orchestration | rag | evaluation | monitoring
maturity: draft | reviewed | client-tested
source: hsbc-generalized | research | vendor-analysis
created: YYYY-MM-DD
---
```

**Use Cases:**
```yaml
---
type: use-case
domain: credit | compliance | ops | trading | wealth | insurance
technique: llm | agent | rag | classification | extraction | generation
risk-level: low | medium | high | critical
maturity: draft | reviewed | client-tested
source: client-work | research | industry-report | evident-ai
created: YYYY-MM-DD
---
```

**Experiments:**
```yaml
---
type: benchmark | comparison | proof-of-concept
domain: rag | extraction | classification | summarisation | agents
technique: [what was tested]
result: [one-line finding]
maturity: draft | reviewed | published
source: personal-test | client-derived | research-replication
created: YYYY-MM-DD
---
```

Frontmatter values are extensible — agents may add new domain/technique values as the library grows. The listed values are starting points, not an enum.

## Pipeline Architecture

### Enrichment Graph

Streams are interconnected, not parallel:

```
Lustro (raw AI news, 8x/day)
    → Forge lead agent synthesises landscape (replaces dialexis dependency for v1)
        → Garden post (opinionated take)
            → LinkedIn seed (hook + bullets, never full post)
        → P&P delta (regulatory implication)
        → Use case spark (new pattern spotted)
    → Talking points (meeting-relevant subset)

Evident AI / industry reports (manual ingest or flagged by daily agent)
    → Use case library (new entries)
    → Reference architecture (pattern validation)
    → P&P gap analysis (what's not covered?)

Client work (HSBC, future — generalized after delivery)
    → Generalized P&P (strip client specifics)
    → Reference architecture (abstract the solution)
    → Use case entry (add to library)
    → Garden post seed (lessons learned, anonymised)

Experiments (designed by weekly agent, executed manually or via heuretes)
    → Results feed all other streams
    → Conference talk seeds (experiment + use case + insight = talk)
```

### Daily Layer — "Spark Agent"

**Trigger:** LaunchAgent, ~7am HKT daily
**Model:** Sonnet (cheap, fast)
**Runtime:** <2 minutes

**Inputs:**
- Lustro output from previous 24h (`~/code/epigenome/chromatin/AI News Log.md`, last 24h entries)
- Calendar for today + tomorrow (fasti)
- Existing `_sparks.md` (to avoid duplicates)

**Outputs (appended to `_sparks.md`):**
1. Talking points for today's meetings (if any calendar matches)
2. Flagged sparks for weekly batch, tagged by stream:
   - `#policy-gap` — regulatory news with P&P implications
   - `#architecture` — new tool/pattern worth documenting
   - `#use-case` — FS AI application spotted
   - `#experiment-idea` — something worth testing
   - `#garden-seed` — opinionated take worth writing
   - `#linkedin-seed` — hook + 3 bullets + angle (NEVER a full post)
   - `#competitor` — McKinsey/Deloitte/EY/Accenture AI governance move
3. "Nothing notable" if a quiet day (don't fabricate signal)

**Implementation:** Python script at `~/officina/forge/daily-spark.py`, dispatched via LaunchAgent.

**Idempotency & failure handling:**
- Each day's sparks are written under a date header (`## 2026-03-19`). Duplicate runs for the same date append under the same header — visible and harmless.
- "Last 24h" is determined by parsing date headers in `AI News Log.md`, not file modification time.
- If lustro had no new entries, the agent writes `## 2026-03-19\n- Nothing notable` and exits.
- `_sparks.md` is created if missing on first run.
- If the LaunchAgent fires after sleep/wake, the date header dedup prevents double-processing.

### Weekly Layer — "The Forge"

**Trigger:** Manual via `/forge` command initially. Schedule (Sunday night) once proven.
**Model:** Opus lead + Sonnet workers (vigilia pattern)
**Runtime:** ~15-30 minutes
**Budget:** ~$1-2

**Inputs:**
- Week's `_sparks.md` (pre-triaged by daily agents)
- Thalamus landscape notes (`~/code/epigenome/chromatin/Thalamus.md`) — lead agent synthesises directly, no dialexis dependency
- Git log of client work committed that week
- Existing library (for dedup + gap identification)
- North Star doc (taste filter)

**Orchestration:**
1. Lead agent (Opus) reads all inputs, plans enrichment graph for the week
2. Dispatches parallel worker agents (Sonnet):
   - **Content worker:** 1-2 garden post drafts + LinkedIn seeds from sparks
   - **Policy worker:** P&P drafts + regulatory deltas from `#policy-gap` sparks
   - **Architecture worker:** Architecture notes + use case entries from `#architecture` and `#use-case` sparks
   - **Experiment worker:** Designs next experiments from `#experiment-idea` sparks (does not execute — flags for Terry or heuretes)
   - **Intelligence worker:** Weekly brief + competitor lens
3. Synthesis agent (Sonnet) runs after all workers complete:
   - Cross-pollinates: use case → garden seed, experiment + insight → talk idea
   - Regenerates `_index.md` with current library stats
   - Archives processed sparks: moves them into the weekly report, then truncates `_sparks.md` to only unprocessed date sections (gives daily agent a clean dedup surface)
   - Writes weekly compound report to `_weekly/YYYY-WNN.md` (includes archived sparks for provenance)
   - Sends summary via Telegram (deltos)

**Worker output rules:**
- Each worker creates files directly in the appropriate `~/code/epigenome/chromatin/Consulting/` subdirectory
- Filenames: `YYYY-MM-DD-slug.md` with standard frontmatter
- Workers read existing library to avoid duplicates and to enrich existing entries
- Workers flag items that upgrade existing drafts (e.g. a new data point that strengthens an existing use case)

## First Iteration Scope

Build only what's needed to test the loop:

1. **Create directory structure** — `~/code/epigenome/chromatin/Consulting/` with subdirectories
2. **Seed the library** — generalize HSBC work into 3-5 initial assets
3. **Daily spark agent** — `daily-spark.py` + LaunchAgent
4. **`/forge` skill** — manual weekly batch trigger
5. **Telegram report** — summary of what was produced

**Second iteration (post-HSBC):**
- **Regulatory feed** — automated ingestion of MAS, HKMA, EU AI Act, BCBS updates into sparks (highest-value addition; directly serves P&P stream and differentiates from generic AI news)
- **Industry report ingestion** — Evident AI, McKinsey, BIS papers flagged as sparks
- **Incident feed** — AI failures in banking, enforcement actions (serves use cases + garden posts)
- Sunday night auto-schedule (manual `/forge` first)
- Conference talk pipeline (synthesis agent flags, no dedicated stream)
- Experiment execution (design only, execute via heuretes separately)
- LinkedIn automation (seeds only, manual promotion)
- `garden-auto.py` → max20 migration

## Success Criteria

### Activity metrics (machine is running)

After 4 weeks:
- Library has 20+ assets across the streams
- Daily sparks feel relevant (not fabricated noise)
- At least one garden post originated from the pipeline
- At least one talking point was useful in a meeting

### Outcome metrics (machine moves the needle)

These matter more than activity:

| Metric | What it measures | How to track |
|--------|-----------------|--------------|
| **Promotion rate** | Is output useful enough to polish? | `maturity: reviewed` / total assets |
| **Meeting relevance** | Did talking points land? | Terry flags in daily note |
| **Delivery acceleration** | Did a library asset save time on client work? | Terry flags post-delivery |
| **Inbound signal** | Did content attract the right audience? | LinkedIn engagement, garden analytics |
| **Cross-pollination** | Is the compound property working? | Assets with `**Related:**` links to other assets |

Weekly forge Telegram report includes: *"Did you use anything from last week's batch?"*

### North star feedback loop

The measurement loop feeds back into the destination, not just the machine:

```
Set North Star → Build machine → Measure output → Reflect → Adjust North Star
       ↑                                                            ↓
       └────────────────────────────────────────────────────────────┘
```

- **Monthly:** Does the machine's output match where the market pulls?
- **Quarterly:** Do the north stars still reflect what matters?

If the forge keeps producing AI governance assets but client work pulls toward AI operations — adjust the north star, don't force the machine.

## Related

- [[North Star]] — taste filter
- [[autonomous-flywheel]] — human-in-the-loop design principle
- [[automation-spectrum]] — where to place the LLM
- [[Capco Transition]] — current career context
- [[Thalamus]] — landscape synthesis input
- [[AI News Log]] — lustro raw input
