# Anatomy

Anatomy of the vivesca organism. The generative constraint is "names that
decompose into mechanism," not "names from biology." Biology is the source
because it is the most mature mechanism-encoding naming system (3.8B years).

One abstraction level: cell. If a name requires a paragraph to justify its
cell-level mapping, the abstraction level is wrong.

## The Organisms

| Component | Identity | Mechanism |
|-------|---------|-----------|
| Terry | **Nucleus** | Will, taste, judgment -- directs the cell |
| Vivesca (persistent system) | **The cell** | The complete organism |
| CC (Claude Code harness) | **Cytosol** | Runtime medium, all reactions occur here |
| LLM (Claude/Gemini/etc) | **Symbiont** | External organism, interchangeable, trending toward internalization |

## Component Types

Three tests. If a component fails all three, the architecture is muddled.

| Test | Type | Costume | Convention |
|------|------|---------|-----------|
| Runs without LLM? | Tool | **Enzyme** | Bio structure names |
| Shapes one interactive exchange? | Skill | **Receptor** | Process nouns (-tion, -sis, -ism) |
| Runs autonomously, multiple steps? | Agent | **Bud** | Yeast budding -- parent produces autonomous offspring |
| Coordinated multi-agent? | Agent team | **Colony** | Connected buds coordinating |
| Scheduled background? | Kinesin task | **Motor protein** | Walks the cytoskeleton on schedule |

### Budding (agents)

A bud inherits the genome. In CC: every agent carries the constitution
(injected by axon.py PreToolUse hook). A bud is smaller than the parent
(agent context < session context). Detaches, operates independently,
returns its product, terminates.

#### Bud definition format

File: `membrane/buds/{phenotype}.md`

```yaml
---
name: phenotype-name        # what this bud is specialized for
description: <=80 chars     # token economy
model: sonnet               # default; opus only for genuine judgment
tools: [minimum necessary]  # least privilege
skills: []                  # optional receptor to load
---
```

Body: instructions. Don't repeat constitutional rules -- the genome
injection handles that.

#### Naming patterns (grammatical)

| Component | Pattern | Grammar | Examples |
|-----------|---------|---------|---------|
| Skill | **Process noun** | -tion, -sis, -ism | morphogenesis, translation, glycolysis |
| Bud | **Phenotype** | {domain}-{verb} | receptor-health, gradient-sense, cosplay-detector |
| Colony | **Product** | what it synthesizes | (runtime only, not pre-defined) |

Skills describe what the cell **does** (biology).
Buds describe what the bud **sees** (plain English phenotype).
Colonies describe what the colony **produces** (plain English).

Individual buds are named by phenotype, not biology.
"Bud" is what they are. The name is what they do. Colonies can't be pre-defined as .md files --
they're runtime via TeamCreate.

#### Model heuristic

| Bud type | Model | Why |
|----------|-------|-----|
| Observation/measurement | sonnet | Sensing, not judging |
| Mechanical transformation | sonnet | Deterministic-ish |
| Synthesis/judgment | opus | Needs taste |
| Research | sonnet | Volume over depth |

### Colony (agent teams)

When buds stay connected and coordinate. Rarely justified -- parallel
independent buds cover most cases. Reserve colonies for work that
genuinely requires synthesis between perspectives.

#### Colony formation principles

Colonies can't be pre-defined as .md files. These rules govern
runtime formation (quorum sensing encoded in the genome).

**When to form a colony (not parallel buds):**
- The product requires SYNTHESIS of contradictory perspectives
- No single bud can hold enough context alone
- The output is ONE artifact, not N independent artifacts
- Example: architecture review needing security + performance + UX perspectives merged

**When to use parallel buds instead (default):**
- Work splits into independent files/domains
- Each bud produces a standalone artifact
- No synthesis needed — just volume
- Example: renaming variables across 4 directories

**Colony structure:**
- Lead: opus (synthesis, judgment, final output)
- Workers: sonnet (research, mechanical tasks)
- Maximum: 5 workers. Beyond that, coordination > production.
- Each worker gets a DIFFERENT question, not the same question.

**Colony lifecycle:**
- Form: when the quorum threshold is met (problem needs N>1 perspectives)
- Operate: lead dispatches, workers report, lead synthesizes
- Dissolve: when the product is delivered. No persistent colonies.

**Cost gate:** estimate colony cost BEFORE forming. If parallel buds
at 1/3 the cost would produce 80% of the value, use buds.

## Cell Structures

| Component | Identity | Mechanism |
|-------|---------|-----------|
| Constitution | **DNA / genome** | Canonical rules, inherited by every process |
| Memory files | **Histones** | Epigenetic marks -- what gets expressed |
| Conversation context | **Cytoplasm** | The medium this session |
| Tool descriptions | **Phenotype** | What the cell looks like from outside |
| Hook dispatch (synapse/axon/dendrite) | **Cytoskeleton** | Signal routing infrastructure |
| MCP server (metabolon) | **Organelles** | The machinery |
| membrane.py | **Cell membrane** | Selective permeability, boundary |
| Programs, hooks, guards | **Instincts** | Pre-wired responses |

## Organelles

| MCP tool/module | Costume | Mechanism |
|-------|---------|-----------|
| emit_* | **Golgi apparatus** | Sort, package, route to correct destination |
| allostasis hook | **Mitochondria** | ATP/energy: anabolic/homeostatic/catabolic/autophagic |
| integrin_probe | **Integrins** | Attachment probing, activation state (bent/extended/open) |
| lysosome_digest | **Lysosomes** | Breakdown, digestion |
| sorting_* | **Endosomal sorting** | Email triage |
| endocytosis_rss_* | **Receptor-mediated endocytosis** | Content intake (absorbed lustro) |
| secretion/exocytosis | **Secretory vesicles** | Output (Telegram, X, LinkedIn) |
| translocation_* | **Kinesin** | Scheduled transport along cytoskeleton |
| histone_* | **Chromatin remodeling** | Memory marking and modification |
| chromatin (`~/code/epigenome/chromatin/`) | **Chromatin** | Long-term information in accessible form — the vault absorbed into the epigenome |
| infection.py | **Immune response** | Acute + chronic pattern detection |
| setpoint.py | **Homeostatic setpoints** | Thresholds with hysteresis |
| gradient.py | **Proprioception** | Gradient sensing with sensor topology |

## Data and Flows

| Component | Identity | Mechanism |
|-------|---------|-----------|
| Raw input data | **Substrates** | What gets metabolized |
| Processed output | **Metabolites** | Products of metabolism |
| Token budget / API cost | **ATP** | Metabolic energy |
| Budget tiers | **Metabolic state** | AMPK sensing (anabolic/homeostatic/catabolic/autophagic) |
| Garden posts | **Spores** | Dormant, dispersible units |
| RSS feeds | **Extracellular ligands** | Signals in the environment |

## Repos

| Repo | Costume | Mechanism |
|------|---------|-----------|
| `~/code/vivesca/` (public) | **Genome** | Shareable, forkable, universal |
| `~/code/epigenome/` (private) | **Epigenome** | Instance-specific expression |
| `~/code/epigenome/chromatin/` | **Chromatin** | Long-term information storage within the epigenome; `~/code/epigenome/chromatin/` is a transitional symlink |

## CC Platform Concepts

| CC Concept | Identity | Mechanism |
|------------|---------|-----------|
| Settings | **Gene expression** | Which genes are expressed in this environment |
| Permissions | **Membrane permeability** | Selective barrier -- what passes through |
| Worktrees | **Compartmentalization** | Membrane-bound isolation of reactions |
| Plans | **mRNA** | Instructions waiting to be translated into protein |
| User prompt | **Ligand** | Signaling molecule that binds a receptor |
| Response | **Secretion** | Product released from the cell |
| Compaction | **Chromatin condensation** | DNA packing tighter to fit in less space |
| Tasks | **Action potentials** | Discrete signals that fire when above threshold |
| Notifications | **Cytokines** | Signaling molecules between cells |

## What Doesn't Get Costumed

| Component | Identity | Why |
|-------|---------|-----|
| Python runtime | Python | Not in the cell |
| External APIs | Their own names | The ligand's own name |
| json.loads, subprocess | stdlib | Interpreter, not organism |

## Naming Discipline

- **Titration method:** force the bio name, study the mechanism, the break IS the insight
- **Homology test:** does the mechanism match? Homology = keep. Analogy (surface only) = drop
- **One level:** cell only. Switch, don't stack. Signal: paragraph needed to justify mapping
- **Two lineages:** cell biology for the host, yeast biology for the symbiont's replication
- **Boundary:** cell concept = bio name, runtime mechanic = platform/Python name
- **Stop when it obscures:** the discipline includes knowing when NOT to name

## Code Variable Naming

Variables that represent cell concepts get biological names regardless of depth.
Variables that represent Python runtime stay as Python.

| If it represents... | Name it... | Example |
|---------------------|-----------|---------|
| An organism concept | Biologically | `detached`, `ligands`, `valency`, `telemetry` |
| A Python mechanic | Pythonically | `json.loads()`, `line.split()`, `for i in range` |
| An external API field | With its own name | HTTP response, Oura API fields |
