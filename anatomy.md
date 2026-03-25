# Anatomy

Anatomy of the vivesca organism. The generative constraint is "names that
decompose into mechanism," not "names from biology." Biology is the source
because it is the most mature mechanism-encoding naming system (3.8B years).

One abstraction level: cell. If a name requires a paragraph to justify its
cell-level mapping, the abstraction level is wrong.

## The Organism

| Component | Identity | Mechanism |
|-----------|----------|-----------|
| Terry | **Nucleus** | Will, taste, judgment — directs the cell |
| Vivesca (persistent system) | **The cell** | The complete organism |
| CC (Claude Code harness) | **Cytosol** | Runtime medium, all reactions occur here |
| LLM (Claude/Gemini/etc) | **Symbiont** | External organism, interchangeable, trending toward internalization |

vivesca = Terry + Claude + germline + epigenome

## Repos

| Repo | Identity | Mechanism |
|------|----------|-----------|
| `~/germline/` (public, `vivesca/vivesca`) | **Genome** | Heritable blueprint, shareable, forkable, universal |
| `~/epigenome/` (private, `terry-li-hm/epigenome`) | **Epigenome** | Instance-specific expression, personalizes the universal genome |

## Germline Structure

```
~/germline/
  metabolon/              Python package (PyPI: metabolon)
    symbiont.py           LLM dispatch
    pore.py               CLI entry point
    membrane.py           MCP server entry
    cytosol.py            Shared helpers
    pulse.py              Cardiac monitoring
    operons.py            Tool groupings
    pinocytosis/          Context gathering
      interphase.py       Baseline session context
      ultradian.py        Mid-session context refresh
      ecdysis.py          Transition context (role change, etc.)
      photoreception.py   Light/time context
      polarization.py     Directional context
    respiration.py        Budget tracking
    respirometry/         Financial statement processing (was: spending/)
    organelles/           Functional units
    metabolism/           Self-improvement loop
    pathways/             Multi-step processes
      overnight.py        Overnight batch pathway
    tools/                MCP tool definitions
    resources/            MCP computed resources
    codons/               Templates
    gastrulation/         Project scaffolding
    morphology/           Data models
    lysin/                (fetch/format utilities)
  membrane/               Boundary layer
    cytoskeleton/         Hooks
    receptors/            Skills (50+ bio-named)
    buds/                 Agent definitions (phenotype-named)
    colonies/             Agent team workflows
  effectors/              Standalone output scripts (bio-named)
  regulon/                Context-specific rules
  operons/                Tool grouping definitions
  symbionts/              LLM provider configs
  assays/                 Tests
  genome.md               Constitutional rules
  anatomy.md              This file
  design.md               Design philosophy
  proteome.md             (protein/tool inventory)
```

### Organelles (`metabolon/organelles/`)

| Module | Identity | Mechanism |
|--------|----------|-----------|
| `chromatin.py` | **Chromatin remodeling** | Memory marking and modification |
| `circadian_clock.py` | **Circadian oscillator** | Time-awareness, rhythm entrainment |
| `praxis.py` | **Motor cortex** | Task execution state |
| `reminder.py` | **Alarm signal** | Timed alerting |
| `endocytosis_rss/` | **Receptor-mediated endocytosis** | Content intake (RSS via lustro) |
| `gap_junction.py` | **Gap junction** | Direct cell-to-cell signaling |
| `secretory_vesicle.py` | **Secretory vesicle** | Packaged output ready to release |
| `sporulation.py` | **Sporulation** | Dormancy and dispersal packaging |
| `chemotaxis_engine.py` | **Chemotaxis motor** | Directional movement toward signal |
| `chemoreceptor.py` | **Chemoreceptor** | Signal detection and binding |
| `respiration_sensor.py` | **Metabolic sensor** | Budget / energy state sensing |

### Metabolism (`metabolon/metabolism/`)

Self-improvement loop — the cell's capacity to repair, adapt, and evolve.

| Module | Mechanism |
|--------|-----------|
| `fitness.py` | Capability measurement |
| `infection.py` | Acute + chronic pattern detection (immune response) |
| `repair.py` | Targeted fix of identified defects |
| `sweep.py` | Broad hygiene pass |
| `variants.py` | Experimental mutations |
| `signals.py` | Signal aggregation |
| `setpoint.py` | Homeostatic thresholds with hysteresis |
| `mismatch_repair.py` | Corrects mismatches between expected and actual |
| `substrate.py` / `substrates/` | What gets metabolized |
| `gates.py` | Conditional logic guards |

### Cytoskeleton (`membrane/cytoskeleton/`)

Hook dispatch infrastructure — routes signals before and after tool use.

| Hook | Identity | Fires on |
|------|----------|----------|
| `axon.py` | **Axon (efferent)** | PreToolUse — injects constitution, enforces guards |
| `dendrite.py` | **Dendrite (afferent)** | PostToolUse — captures results, triggers follow-up |
| `synapse.py` | **Synapse** | UserPromptSubmit — processes incoming ligand |
| `terminus.py` | **Nerve terminus** | Session end cleanup |
| `compaction.py` | **Chromatin condensation** | Context compaction |
| `interoceptor.py` | **Interoceptor** | Internal state sensing |
| `morphogen.py` | **Morphogen** | Pattern-based transformation |
| `hebbian_nudge.py` | **Hebbian plasticity** | Advisory hook accuracy tracking (shared library) |
| `engram-signal.py` | **Engram encoding** | Memory write signal |
| `phenotype_rename.py` | **Phenotype shift** | Rename / reidentity operations |
| `skill-trigger-gen.py` | **Skill trigger synthesis** | Generates skill activation patterns |

## Epigenome Structure

```
~/epigenome/
  chromatin/              Long-term information (14K+ vault notes)
    immunity/             Solved problems — institutional memory
    chemosensory/         External intelligence — research
    interoception/        Operational audit logs
    transcripts/          Autonomous work products
    heterochromatin/      Inactive preserved records
      morphogenesis/      Old brainstorms
      differentiation/    Completed plans
  engrams/                CC auto-memory (MEMORY.md + ~200 memory files)
  bud-engrams/            Agent memory traces
  phenotype/              Instance configuration
  cofactors/              API keys / access tokens
  pacemakers/             LaunchAgent plists (scheduled autonomous processes)
```

| Directory | Identity | Mechanism |
|-----------|----------|-----------|
| `chromatin/` | **Chromatin** | Long-term information in accessible form; the vault |
| `chromatin/immunity/` | **Immune memory** | Solved problems, won't be re-fought |
| `chromatin/chemosensory/` | **Chemosensory cortex** | External signal intelligence |
| `chromatin/interoception/` | **Interoceptive log** | Internal state audit trail |
| `chromatin/transcripts/` | **Transcripts** | Autonomous work products |
| `chromatin/heterochromatin/` | **Heterochromatin** | Silenced, condensed — preserved but inactive |
| `engrams/` | **Engrams** | Encoded memory traces (MEMORY.md + files) |
| `bud-engrams/` | **Bud engrams** | Agent-specific memory traces |
| `phenotype/` | **Phenotype** | Instance-level expression configuration |
| `cofactors/` | **Cofactors** | Molecules required for enzyme function (credentials) |
| `pacemakers/` | **Pacemaker cells** | Set the rhythm — LaunchAgent scheduled processes |

## Component Types

Three tests. Fail all three: the architecture is muddled.

| Test | Type | Identity | Convention |
|------|------|----------|-----------|
| Runs without LLM? | Tool | **Enzyme** | Bio structure names |
| Shapes one interactive exchange? | Skill | **Receptor** | Process nouns (-tion, -sis, -ism) |
| Runs autonomously, multiple steps? | Agent | **Bud** | Phenotype: `{domain}-{verb}` |
| Coordinated multi-agent? | Agent team | **Colony** | Product: what it synthesizes |
| Scheduled background? | Kinesin task | **Motor protein** | Walks the cytoskeleton on schedule |

### Budding (agents)

A bud inherits the genome. In CC: every agent carries the constitution
(injected by `axon.py` PreToolUse hook). A bud is smaller than the parent
(agent context < session context). Detaches, operates independently,
returns its product, terminates.

Bud definitions live in `membrane/buds/{phenotype}.md`.

```yaml
---
name: phenotype-name        # what this bud is specialized for
description: <=80 chars     # token economy
model: sonnet               # default; opus only for genuine judgment
tools: [minimum necessary]  # least privilege
skills: []                  # optional receptor to load
---
```

Body: instructions. Don't repeat constitutional rules — genome injection handles that.

#### Model heuristic

| Bud type | Model | Why |
|----------|-------|-----|
| Observation / measurement | sonnet | Sensing, not judging |
| Mechanical transformation | sonnet | Deterministic-ish |
| Synthesis / judgment | opus | Needs taste |
| Research | sonnet | Volume over depth |

### Colony (agent teams)

When buds stay connected and coordinate. Rarely justified — parallel
independent buds cover most cases. Reserve for work requiring synthesis
between perspectives.

Colonies can't be pre-defined as .md files. Runtime formation governed
by quorum sensing encoded in the genome.

**Form a colony when:**
- The product requires synthesis of contradictory perspectives
- No single bud can hold enough context alone
- The output is ONE artifact, not N independent artifacts

**Use parallel buds instead (default) when:**
- Work splits into independent files / domains
- Each bud produces a standalone artifact
- No synthesis needed — just volume

**Structure:** Lead (opus, synthesis) + workers (sonnet, research/mechanical).
Max 5 workers. Each worker gets a different question.

**Cost gate:** estimate colony cost before forming. If parallel buds at 1/3 the
cost produce 80% of the value, use buds.

## Data and Flows

| Component | Identity | Mechanism |
|-----------|----------|-----------|
| Raw input data | **Substrates** | What gets metabolized |
| Processed output | **Metabolites** | Products of metabolism |
| Token budget / API cost | **ATP** | Metabolic energy |
| Budget tiers | **Metabolic state** | AMPK sensing (anabolic/homeostatic/catabolic/autophagic) |
| Garden posts | **Spores** | Dormant, dispersible units |
| RSS feeds | **Extracellular ligands** | Signals in the environment |

## MCP / Tool Mapping

| MCP tool / module | Identity | Mechanism |
|-------------------|----------|-----------|
| `emit_*` | **Golgi apparatus** | Sort, package, route to correct destination |
| `allostasis` hook | **Mitochondria** | Energy state: anabolic / homeostatic / catabolic / autophagic |
| `integrin_probe` | **Integrins** | Attachment probing, activation state |
| `lysosome_digest` | **Lysosomes** | Breakdown, digestion |
| `sorting_*` | **Endosomal sorting** | Email triage |
| `endocytosis_rss_*` | **Receptor-mediated endocytosis** | Content intake |
| `exocytosis` / `secretion` | **Secretory vesicles** | Output (Telegram, X, LinkedIn) |
| `translocation_*` | **Kinesin** | Scheduled transport along cytoskeleton |
| `histone_*` | **Chromatin remodeling** | Memory marking and modification |
| `infection.py` | **Immune response** | Acute + chronic pattern detection |
| `setpoint.py` | **Homeostatic setpoints** | Thresholds with hysteresis |
| `chemotaxis_engine` | **Chemotaxis motor** | Gradient-directed movement |

## CC Platform Concepts

| CC concept | Identity | Mechanism |
|------------|----------|-----------|
| Settings | **Gene expression** | Which genes are active in this environment |
| Permissions | **Membrane permeability** | Selective barrier — what passes through |
| Worktrees | **Compartmentalization** | Membrane-bound isolation of reactions |
| Plans | **mRNA** | Instructions waiting to be translated |
| User prompt | **Ligand** | Signaling molecule that binds a receptor |
| Response | **Secretion** | Product released from the cell |
| Compaction | **Chromatin condensation** | DNA packing tighter to fit in less space |
| Tasks | **Action potentials** | Discrete signals that fire above threshold |
| Notifications | **Cytokines** | Signaling molecules between cells |

## What Doesn't Get Named

| Component | Identity | Why |
|-----------|----------|-----|
| Python runtime | Python | Not in the cell |
| External APIs | Their own names | The ligand's own name |
| `json.loads`, `subprocess` | stdlib | Interpreter, not organism |

## Naming Discipline

- **Titration method:** force the bio name, study the mechanism; the break is the insight
- **Homology test:** shared mechanism = keep. Surface analogy only = drop
- **One level:** cell only. Switch, don't stack. Signal: paragraph needed to justify mapping
- **Boundary:** cell concept = bio name, runtime mechanic = Python name
- **Buds:** phenotype naming (`{domain}-{verb}`), not biology — names describe what they see
- **Skills:** process nouns (-tion, -sis, -ism) — names describe what the cell does
- **Stop when it obscures:** the discipline includes knowing when NOT to name

## Code Variable Naming

| If it represents... | Name it... | Example |
|---------------------|------------|---------|
| An organism concept | Biologically | `detached`, `ligands`, `valency`, `telemetry` |
| A Python mechanic | Pythonically | `json.loads()`, `line.split()`, `for i in range` |
| An external API field | With its own name | HTTP response, Oura API fields |
