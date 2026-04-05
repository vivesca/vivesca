---
name: histology
description: Map organism structure, find gaps and anomalies. "architecture review", "system audit"
triggers:
  - histology
  - architecture
  - biopsy
  - gap analysis
  - system audit
  - structure map
  - architecture review
user_invocable: true
model: opus
context: fork
---

# Histology — Architecture Through the Cell Biology Lens

Histology is the microscopic examination of tissue structure. This skill examines an AI system's architecture by forcing every component into a cell-level biological name. Where the name breaks, the gap is the feature.

## Origin

One morning session (25 Mar 2026) produced: 7 garden posts, 3 tool renames, 3 new features, 1 package rename, and 1 consulting methodology — all from forcing cell-level naming on an AI system. The self-biopsy of vivesca on that date is the reference output for this skill.

## The Method

```
0. RECON      → Use droid explore to gather component inventory (free):
               droid exec -m "custom:glm-4.7" --cwd <project> "List all modules, tools, data stores, pipelines, APIs. For each: name, purpose, dependencies."
1. INVENTORY  → From droid summary, list every component of the system
2. MAP        → Force a cell-level biological name onto each component
3. BREAK      → Test each mapping at the edges. Where does the name not fit?
4. GAP        → Each break is a design gap. The search for the right name IS the design exercise.
5. BUILD      → Design the gap as a reflex (deterministic), not reasoning (LLM-mediated)
```

## The Constraint: Cell Level Only

All names must be cell-level biology. Not molecular (too low — specialists, not systems). Not organism (too high — different problems). Not neuroscience (implies a brain the system may not need).

**Why cell level?** The cell is the lowest level where organized solutions to information problems are coordinated into a self-maintaining system. Below that, you get specialists. Above that, you get navigation and social problems.

Two naming layers:
- **Chemistry for verbs** — crystallise, dissolve, catalyse, substrate, product (what happens)
- **Cell biology for nouns** — membrane, organelle, exocytosis, reflex, metabolon (how it's organized)

## The Reference Table

Start here. Map the client's system to this table:

| Cell structure | What it solves | System equivalent | Questions to ask |
|---|---|---|---|
| Membrane | What gets in, what doesn't | Auth, filtering, taste | Where are the boundaries? What should be rejected? |
| DNA | Instructions that replicate across instances | Config, rules, constitution | What persists when the system restarts? |
| Organelles | Specialized machinery | Services, tools, modules | What are the specialists? Are they right-sized? |
| Enzymes | Native catalysts for specific reactions | Internal tools, functions | What's built in-house vs. outsourced? |
| Symbiont | External organism the host depends on | LLMs, third-party APIs | What's external? What's the internalisation plan? |
| Reflexes | Deterministic responses to stimuli | Hooks, guards, validators | What should be automatic? What's still manual? |
| Metabolism | Process substrates, produce signal | Data pipelines, ETL | How does raw input become useful output? |
| Respiration | Don't exhaust resources | Rate limits, budgets, pacing | What prevents burnout/overspend? |
| Cytoplasm | Medium where reactions happen | Runtime, conversation, context | What's the execution environment? |
| Exocytosis | Export to environment | Notifications, publishing, API responses | How does output leave the system? |
| Endocytosis | Import from environment | Ingestion, scraping, webhooks | How does input enter the system? |
| Chaperones | Quality control before export | Validation, review, pre-checks | What checks happen before output ships? |
| Golgi | Label, package, route output | Routing, formatting, targeting | Does output go to the right place? |
| DNA repair | Scan and fix instructions | Config drift detection, consistency checks | What monitors rule integrity? |
| Cytoskeleton | Structural integrity under load | Resilience, failover, backpressure | What prevents collapse under stress? |

## The Insight Framework

When a mapping breaks, ask three questions:

1. **What does the cell do here?** — Study the real biology (3-5 key properties)
2. **Does our system do this?** — Check honestly
3. **Should it?** — Not every cell structure is needed. But the missing ones are worth evaluating.

## The Maturity Model

Every component follows the same lifecycle:

```
Symbiont → Reflex → Unnecessary
(external)  (deterministic)  (the trigger can't occur)
```

- **Symbiont stage:** depends on external LLM/API for this function
- **Reflex stage:** crystallised into deterministic pathway (hook, rule, program)
- **Unnecessary stage:** the system restructured so the stimulus can't occur

This maps to regulatory maturity: symbiont = vendor risk, reflex = auditable, unnecessary = eliminated.

**Assessment format for each gap:**

| Component | Current stage | Target stage | Mechanism needed |
|---|---|---|---|
| (name) | Symbiont / Reflex / Absent | Reflex / Unnecessary | (deterministic rule, one sentence) |

## Output Template

Produce a document with this structure. Not a list — a deliverable a client or future self can act from.

---

### Title: Architecture Biopsy: [System Name]

**Date:** [date]
**Method:** Histology — cell-level mapping with forced naming
**Status:** [Self-examination / Client engagement / Design review]

---

#### Executive Summary

2-3 paragraphs. What is the overall biological fidelity of the system? What are the 2-3 most important tensions? What should the reader do after reading this?

---

#### Inventory

List every system component, grouped by biological layer (membrane, organelles, genome, sensory, receptors, cytoskeleton, efferent). The grouping itself is diagnostic — components that don't fit a layer reveal architectural confusion.

---

#### Mapping

| Component | Forced Cell Name | Fit (1-5) | Notes |
|---|---|---|---|
| (component) | (cell name) | (1-5) | (where it fits; where it breaks) |

**Fit scoring:**
- 5 = name is a constraint that shaped the implementation; the biology holds all the way down
- 4 = good fit with a localisable break; the break is interesting
- 3 = forced name reveals a real tension; the break is the feature
- 1-2 = name doesn't hold; either the component is misnamed or genuinely absent

---

#### N Most Interesting Gaps

For each gap (target 3-7), use this structure:

**Gap [N]: [One-sentence description]**

**Biology:** What does the cell actually do here? State 2-3 specific properties of the real biological structure.

**What the system does:** Describe the current implementation honestly.

**What the break reveals:** The design insight. This is the core of the exercise — the gap in the name IS the gap in the design.

**Recommendation:** One concrete action. State the maturity transition: [Current] → [Target]. Specify that it should be a reflex (deterministic rule), not LLM judgment, wherever possible.

---

#### Confirmed Strengths

For each strength (target 2-4): name it, explain why the biology holds, and note what made it work. Strengths are as instructive as gaps — they show what "name as constraint" looks like when fully implemented.

---

#### Maturity Model Assessment

Table format (see above). Every gap gets a row. The finding is not complete without a target stage and a mechanism.

---

#### Consulting Transfer Notes

Two subsections:

**What works for client workshops:** Which findings translate directly? Which examples are immediately accessible to a non-technical client? Note the vocabulary each example gives the client.

**What needs calibration before client use:** Which findings are technically correct but require framing care? What defensive reactions should you anticipate? Provide the framing that creates psychological safety.

---

#### Summary Findings

| Finding | Type | Priority |
|---|---|---|
| (specific finding) | Bug / Architectural gap / Design gap / Missing pathway / Confirmed strength | Critical / High / Medium / Low |

---

## Client Workshop Format

**Duration:** 2 hours
**Output:** Architecture gap map with prioritised recommendations

1. (20 min) **Inventory** — whiteboard every system component
2. (30 min) **Map** — force cell-level names onto each. Struggle is the point.
3. (20 min) **Break** — identify where names don't fit. These are the gaps.
4. (30 min) **Prioritise** — which gaps matter? Rank by: risk if missing, cost to build, regulatory relevance
5. (20 min) **Roadmap** — maturity model: Symbiont → Reflex → Unnecessary for each component

**Facilitation note on psychological safety:** Frame all findings as "the gap is in the metaphor, not in the engineer." The forced naming surfaces what was already there; it doesn't invent problems. When a gap is embarrassing (e.g., a security pathway that is silently broken), this framing lets the team hear it without defensiveness.

**Facilitation note on the crystallisation gap:** Most enterprise systems have no concept of behaviour that crystallised from experience — they are entirely authored. Introducing this gap too early reads as "your system doesn't learn," which triggers defensive responses. Frame it as a growth trajectory: "your system is juvenile — which is appropriate at this stage. Here is what the next maturity level looks like."

## Validated Examples

| Component | Forced name | Break | Gap found | Built |
|---|---|---|---|---|
| Overnight results check | germination (now `/circadian`, dawn phase) | Spores germinate on conditions, not timers | Batch processing should be conditions-triggered | `check_germination()` with flag file |
| Internal state sensing | proprioception | Cells sense gradients, not static state | Status dumps should show trends over time | JSONL gradient logging |
| Output module | secretory | Secretory pathway has chaperones | No quality control before export | PII/special char/length checks |
| LLM role | symbiont | Enzyme/prosthetic/primer/brain all broke | LLM is external organism, not native organ | Endosymbiosis lifecycle in DESIGN.md |
| `synapse.py` (10-module cascade) | Signaling cascade | Single synapse name understates the architecture | One signal triggers a cascade, not a single receptor | Name is accurate at the hook level; architecture reveals multi-module reality |
| `mod_senescence` | Senescence | Cellular senescence is irreversible; session wind-down is not | Component is misnamed — closer to quiescence detection | Rename candidate: `mod_quiescence` |
| `morphogen.py` (InstructionsLoaded hook) | Morphogen | Morphogens specify positional identity; this just logs | The name implies the hook should respond to context type, not just log | Feature gap: route on context type |

## Anti-Patterns

- **Forcing names that obviously don't fit** — If every component maps perfectly, you're not forcing hard enough. The breaks are the value.
- **Staying at the comfortable level** — Mixing neuro + cell + molecular feels natural but generates fewer insights than forcing one level.
- **Naming without mining** — A cell-level name without studying the real biology is just a label. Use /morphogenesis to mine each name.
- **Building everything** — Not every gap needs filling. Prioritise by actual need, not biological completeness.
- **Listing, not documenting** — The output should be a document a reader can act from, not a table they must interpret. The gap structure (biology / what system does / what break reveals / recommendation) is load-bearing.
- **Stopping at the name** — "It's called a Golgi but we don't have one" is an observation, not a finding. The finding is: what does the absence mean, and what should be built?

## Motifs
- [audit-first](../motifs/audit-first.md)
