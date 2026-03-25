# Human Memory Science for AI Agent Architects
*Researched: March 2026 | Sources: cognitive neuroscience, 2024–2026 agent memory papers*

> **Purpose:** Actionable mapping of human memory mechanisms to AI agent design. Each section states the mechanism, what it implies for agent architecture, and whether it has been implemented — and where.

---

## 0. The Reference Stack

The best bridge papers (cross-reference these throughout):

| Paper | What it covers |
|---|---|
| arxiv:2512.23343 "AI Meets Brain" (Dec 2025) | Unified survey: neuroscience → LLMs → agents. 57 pages. Taxonomy + storage + retrieval. |
| arxiv:2504.15965 "From Human Memory to AI Memory" (Apr 2025) | Maps all five forgetting types + consolidation to specific AI systems |
| arxiv:2512.13564 "Memory in the Age of AI Agents" (Tsinghua, Dec 2025) | Taxonomy: semantic/episodic/procedural × inside-trail/cross-trail |
| arxiv:2505.00675 "Rethinking Memory in AI" (May 2025) | Operations framework: consolidation, indexing, updating, forgetting, retrieval, compression |
| arxiv:2509.13235 "Scenario-Driven Cognitive Approach" (Sep 2025) | COLMA architecture; six cognitive capabilities required |
| arxiv:2502.06975 "Episodic Memory is the Missing Piece" (Feb 2025) | Argues episodic is structurally absent from current LLM agents |

---

## 1. The Major Memory Systems

### What Cognitive Science Says

Human memory is not one thing. The field has converged on at least five functionally distinct systems that operate in parallel and interact:

**Working Memory (Baddeley model)**
- Capacity: ~4 "chunks" (not 7±2 — that was based on items, not chunks; Cowan 2001)
- Duration: ~15–20 seconds without rehearsal
- Components: phonological loop (verbal rehearsal), visuospatial sketchpad (spatial/visual), episodic buffer (links to LTM), central executive (attentional controller)
- Key function: active manipulation of information, not mere holding. It is the workspace for reasoning.

**Episodic Memory (Tulving)**
- Stores "what happened where and when" — temporally indexed, context-bound, autobiographical
- Critically depends on the hippocampus for encoding and retrieval
- Supports "mental time travel" — re-experiencing past events and pre-experiencing future ones
- Unique property: each retrieval *reconstructs* the memory, not replays it (memories are reassembled from fragments, not read off a tape)

**Semantic Memory**
- Stores facts, concepts, meanings — decontextualised (you know Paris is in France but not *when you learned it*)
- Distributed across neocortex (temporal, frontal areas), not hippocampus-dependent
- Builds up through repeated exposure; individual episodes are "averaged out"

**Procedural Memory (Implicit)**
- Skills, habits, motor programs — "how to" knowledge
- Encoded in basal ganglia and cerebellum; highly resistant to forgetting
- Not accessible to conscious introspection: you cannot verbally describe how you ride a bike well enough to teach from the description alone

**Prospective Memory**
- "Memory for intentions" — remembering to do something at a future time or event
- Two types: *time-based* (remember to take medication at 8am) and *event-based* (remember to pass on the message when you see Sarah)
- Event-based is more reliable because the cue triggers the intention without deliberate monitoring

### How They Interact

The standard model: episodic memories get consolidated into semantic memory over time via hippocampal-neocortical replay. Working memory acts as the interface between incoming perception, LTM retrieval, and current reasoning. Procedural memory is largely separate — skills become automatic and exit working memory entirely (a key feature, not a bug).

**The stability-plasticity dilemma:** hippocampus = fast, specific, easily overwritten (plastic). Neocortex = slow, distributed, stable. The brain solves catastrophic forgetting by using the hippocampus as a fast buffer that gradually writes to neocortex via sleep replay.

### AI Agent Mapping and Implementations

| Human system | AI analogue | Implemented where |
|---|---|---|
| Working memory | Context window | Universal — every LLM |
| Episodic memory | Interaction trajectory store | MemGPT/Letta (recall storage), A-Mem (note network), Park et al. Generative Agents |
| Semantic memory | Knowledge base / vector store / model weights | Mem0 (extracted facts), LangMem (semantic type), model parameters |
| Procedural memory | System prompt / tool definitions / agent policies | LangMem (procedural type that modifies system prompt), SOAR production rules |
| Prospective memory | Task queue / calendar / reminder systems | Almost entirely absent from agent memory research — a genuine gap |

**The episodic gap (arxiv:2502.06975):** Current LLM agents lack true episodic memory. The argument: agents need "what-where-when" encoded trajectories that can be retrieved by partial cue and mentally replayed to support planning. Current systems either store flat logs (no structure for cue-based recall) or extracted facts (episodic detail is lost). MemGPT/Letta is closest but treats recall storage as a database, not a reconstructive system.

**ACT-R's implementation** is the most computationally precise: declarative memory chunks have activation levels (base-level + spreading activation from current goal context). Retrieval probability is a function of this activation. Procedural memory is production rules that fire to transform working memory. ACT-R has predicted human RT distributions in hundreds of experiments — it is the most validated cognitive architecture.

**SOAR's implementation:** Separates declarative into semantic (general facts) and episodic (experiential records) memory. Episodic store lets agents explicitly query "what happened in situations like this?" — the closest symbolic AI system to true episodic retrieval.

---

## 2. Forgetting Mechanisms

### What Cognitive Science Says

Forgetting is not failure — it is adaptive information management. Five distinct mechanisms:

**1. Encoding failure**
Information was never properly stored. Attention gating at encoding determines what reaches memory. "Shallow processing" (surface features) → weak encoding. "Deep processing" (meaning, elaboration) → strong encoding. Levels of Processing theory (Craik & Lockhart 1972).

**2. Decay / Ebbinghaus forgetting curve**
Retention = e^(-t/S) where t is time and S is memory strength. The curve is logarithmic — rapid initial loss, slower later. Strength can be reset by review. The key insight: decay rate is not fixed; it depends on prior retrieval history (the spacing effect — reviewed memories have slower decay).

**3. Interference**
- *Proactive interference:* old memories disrupt recall of new ones
- *Retroactive interference:* new learning disrupts recall of old memories
- Interference is *cue competition*: multiple memories compete for the same retrieval cue

**4. Retrieval-Induced Forgetting (RIF)**
Actively retrieving one memory from a set *suppresses* the competing memories in that set. Mechanism: inhibitory control actively suppresses competing traces to reduce interference. This is adaptive — it keeps the retrieved memory accessible while reducing noise from related alternatives. The human brain treats memory management as active suppression, not passive decay.

**5. Motivated forgetting**
Emotionally aversive memories can be actively suppressed (Freudian motivated forgetting has empirical support in fMRI studies showing hippocampal suppression via prefrontal control).

### Actionable Design Principles

- **Forgetting should be an explicit operation, not a side effect.** Most agent systems treat memory as append-only. The brain treats it as dynamically managed.
- **Decay should be strength-based and access-modulated,** not purely time-based. Information accessed recently should decay more slowly.
- **Cue competition should inform retrieval design.** When many memories compete for the same query, retrieved memories should be "boosted" relative to non-retrieved ones — this is RIF's mechanism applied to vector store management.
- **Privacy and compliance require active forgetting.** GDPR-style "right to be forgotten" maps directly to motivated forgetting.

### Implementations

**MemoryBank (Zhong et al., 2024):** Ebbinghaus forgetting curve explicitly implemented. Memory strength tracks elapsed time since last access. Exponential decay model. Low-strength memories are deprioritised or deleted. Closest existing AI implementation of Ebbinghaus mechanics.

**SAGE (mentioned in arxiv:2512.23343):** Adaptively eliminates low-value information based on forgetting curve parameters to reduce cognitive load.

**MEMORYLLM:** Fixed-size memory pool in latent space — forces forgetting by bounding capacity. Analogous to limited-capacity working memory. New memories must displace old ones.

**MemOS (arxiv:2507.03724):** Explicit forgetting policies as part of memory lifecycle management alongside conflict detection, deduplication, versioning.

**Not implemented anywhere (gap):** Retrieval-induced forgetting — actively suppressing competitor memories when a target is retrieved. This would require vector stores to track which memories "competed" for each query and downweight them. No production system does this.

---

## 3. Consolidation

### What Cognitive Science Says

Consolidation is the process by which memories are stabilised and transformed from fragile, hippocampus-dependent traces into stable, neocortex-distributed representations.

**Synaptic consolidation** (hours timescale): Protein synthesis-dependent stabilisation of synaptic changes at the site of encoding.

**Systems consolidation** (weeks to years timescale): Gradual transfer from hippocampus to neocortex via repeated reactivation. The hippocampus "teaches" the cortex by replaying compressed event representations during sleep (slow-wave sleep: sharp-wave ripples in hippocampus coordinate with cortical slow oscillations). Over time, cortical representations become hippocampus-independent — this is why old semantic memories survive hippocampal damage but recent episodic memories do not (HM case, anterograde amnesia).

**Sleep replay is not verbatim.** It is schematic: the hippocampus replays the *structure* of an episode, not every sensory detail. The replay is fast (compressed ~20x during sharp-wave ripples). It preferentially replays emotionally salient or contextually novel experiences.

**Schema assimilation:** New memories that fit existing schemas consolidate *faster* (Tse et al., 2007 in rats — new paired associates learned in one trial when existing schema is present). The schema provides a cortical scaffold that the hippocampus hooks into rapidly. This is why prior knowledge dramatically accelerates new learning.

**Complementary Learning Systems (CLS) theory:** The learning architecture that emerges: hippocampus (fast, sparse, pattern-separated encoding) + neocortex (slow, distributed, overlapping representations). Different learning rates at different timescales, coordinated by sleep.

### Actionable Design Principles

- **Batch consolidation during "downtime" is more biologically accurate than continuous consolidation.** The brain uses sleep (offline periods) to reorganise memory, not live write-through.
- **Consolidation should be compressive and schematic,** not verbatim archival. Extract structure and patterns, not raw logs.
- **Emotionally/relevance-weighted consolidation:** replay and strengthen high-importance memories preferentially.
- **Schema-accelerated encoding:** new memories that match existing schema structures should be encoded faster and with less redundancy.
- **Two learning rates:** fast (in-context) and slow (consolidated long-term) should be explicitly separated in architecture.

### Implementations

**Generative Agents (Park et al., 2023) reflection mechanism:** Agents periodically review their memory stream and generate higher-level insights ("reflections") that are stored back as new memories. This is the closest to hippocampal → cortical consolidation: episodic detail → semantic abstraction. The reflection runs on a threshold (accumulated "importance" score triggers a reflection pass), analogous to sleep's role in consolidation.

**A-Mem (NeurIPS 2025):** Zettelkasten-inspired. Each memory note has content + links to related notes. When a new note is created, existing notes can be updated (evolved) based on the new connection. This is dynamic consolidation — not just archival, but integrating new information into the existing knowledge graph.

**Hierarchical memory trees (Chen et al.):** Recursive upward summarisation — raw events → episode summaries → day summaries → theme summaries. Structure mirrors the hippocampal replay process that extracts schema from episodic experience.

**MemGPT/Letta:** The explicit "main context / archival storage" separation maps to working memory / long-term memory, but consolidation (the *process* of moving things between them) is under agent control via function calls. The agent must decide to "archive" a memory — there is no automatic consolidation.

**Not implemented (gap):** Schema-accelerated encoding. No system checks whether new information matches existing schemas and encodes it preferentially. Also missing: two-learning-rate architecture — most systems have a single retrieval-and-insert pipeline with no distinction between fast episodic capture and slow semantic consolidation.

---

## 4. Retrieval

### What Cognitive Science Says

Retrieval is not passive lookup — it is active reconstruction. The brain reinstates the neural pattern present at encoding and fills in gaps using inference and schema. This is why memories are fallible (false memories) but also flexible (useful for novel situations).

**Encoding specificity principle (Tulving & Thompson 1973):** The best retrieval cue is one that matches the context at encoding. Memory that was encoded in a specific emotional, physiological, or contextual state is better retrieved in that same state (state-dependent learning).

**Context-dependent retrieval:** Godden & Baddeley (1975) — divers learned word lists underwater or on land, recalled better in the same environment. The principle applies to internal states (mood-congruent memory), environmental context, and cognitive context.

**Spreading activation (Collins & Loftus 1975):** Memory is a semantic network. Activating one node spreads activation to associated nodes. A concept "primes" related concepts, making them more accessible. Retrieval involves propagating activation through the network from the cue until a threshold is reached.

**Content-addressable memory:** Memories are retrieved by *content* (partial cues, features, meaning) rather than by address (location). Any feature of a memory can serve as a retrieval cue — this is why you can retrieve a memory from a smell, a word, a visual fragment.

**Tip-of-the-tongue (TOT) state:** Partial retrieval — the person knows the memory exists, knows some of its attributes, but cannot complete retrieval. Evidence that retrieval is multi-stage: initial match → activation → completion. The intermediate state is accessible to monitoring.

### Actionable Design Principles

- **Encode context with memories, not just content.** The task context, agent state, and conversational context at encoding should be stored alongside the memory and used as retrieval cues.
- **Multi-factor retrieval is more human-like than pure semantic similarity.** Temporal recency, access frequency, contextual overlap, and semantic similarity should all contribute to retrieval ranking.
- **Graph traversal (spreading activation) outperforms flat vector search for relational queries.** The mechanism is different: vectors find semantically similar items; graphs propagate activation and find *connected* items.
- **Partial cue recovery:** systems should be able to retrieve partial matches and signal the confidence/completeness of retrieval (metamemory — covered in Section 6).

### Implementations

**Generative Agents retrieval score:** recency + importance + relevance combined linearly. Explicit multi-factor retrieval. This is the most direct implementation of non-uniform retrieval weighting.

**HippoRAG (Zhang et al., 2024):** Explicitly models hippocampal indexing. Knowledge graph construction where entities are nodes and relations are edges. Query → entity extraction → spreading activation across the graph → retrieval. Named after the hippocampus's role in associative memory. Outperforms vector-only RAG on multi-hop reasoning tasks.

**Graphiti (Zep):** Bi-temporal knowledge graph. Each fact has two timestamps: when it was true in the world, and when it was ingested. Queries can target specific time windows. This is closest to the episodic "what-where-when" structure.

**A-Mem:** Retrieval uses keyword + semantic + link traversal — spreading activation through the Zettelkasten note network. When a note is retrieved, its linked notes become accessible candidates.

**Encoding specificity — not implemented:** No production system stores the task context at encoding time and uses it for retrieval matching. This is a genuine gap. The closest approximation: Graphiti stores the conversation in which a fact was learned (ingestion timestamp + source), but not the full cognitive context.

**State-dependent retrieval — not implemented:** No system adjusts retrieval based on the agent's current task state matching the encoding state.

---

## 5. Schemas and Chunking

### What Cognitive Science Says

**Chunking (Miller 1956, revised by Cowan 2001):** Working memory is limited not in number of items but in number of *chunks* — meaningful units that have been bound together by prior learning. Expert chess players see board positions as ~4 chunks (attack configurations, pawn structures) where novices see 28 individual pieces. Chunking is how expertise compresses information.

**Schema (Bartlett 1932, updated):** A schema is an organized knowledge structure — a template for a category of experience. Schemas guide both encoding (new information is interpreted in terms of existing schemas) and retrieval (gaps are filled by schema-typical values). The classic demonstration: Bartlett's "War of the Ghosts" — participants remembered the story but "normalised" it to match their cultural schemas.

**Expert chunking in practice:**
- Chess masters encode positions as 50,000–100,000 chunks acquired over ~10 years (de Groot, Chase & Simon)
- The chunks are stored in long-term memory and serve as rapid pattern recognition: the expert sees "danger" in a position immediately because the pattern matches a stored chunk, then deliberate search is applied to verify
- This is why experts are fast at recognition and slow to explain — the recognition is chunked and pre-conscious

**Script theory (Schank & Abelson 1977):** Schemas for event sequences (restaurant script: enter → seated → menu → order → eat → pay → leave). Scripts allow efficient encoding of typical experiences (only deviations from script need to be stored).

**Schema assimilation vs accommodation (Piaget):** New information either fits an existing schema (assimilation, fast, low encoding cost) or requires schema modification (accommodation, slow, high cognitive cost). Expertise is largely a database of schemas refined by accommodation events.

### Actionable Design Principles

- **Memory entries should be schema-tagged.** When a new memory is encoded, check if it fits an existing schema. If yes, store only the deviation. If no, initiate schema formation.
- **Retrieval should be pattern-completion,** not just lookup. Given a partial description, complete it using schema-typical values (with appropriate uncertainty flagging).
- **Task templates are procedural schemas.** Agent workflow libraries should evolve from repeated episodes (chunked) rather than be manually specified.
- **Compression ratio scales with expertise.** A newly deployed agent has no schemas — everything is novel. As patterns accumulate, the same information should require less storage (chunking compression).

### Implementations

**Buffer of Thoughts (2024):** Explicitly implements thought templates. When a task is completed, the reasoning chain is abstracted and stored as a "template" that can be retrieved for future similar tasks. This is schema formation from episodic experience.

**Agent Workflow Memory:** Agents select from stored "workflows" — reusable structured procedures. Workflows are induced from successful trajectories. Direct implementation of procedural schema.

**Generative Agents reflection:** High-level insights extracted from episodes are a form of schema formation — recurring patterns are noticed and stored as general principles.

**A-Mem note linking:** When memories are linked across time, the links encode relational schemas. The Zettelkasten approach explicitly values atomic notes connected by meaningful relationships over hierarchical organisation.

**MemoryOS (BAI-LAB, EMNLP 2025):** Personalised AI with memory organised in a hierarchical graph structure: task–concept–fact paths. The task level is effectively a schema/script layer — events are organised around task structures.

**Skill libraries (Wang et al.):** Executable code + semantic vector keys. Generalised skills learned from episodes. The most direct implementation of procedural schema — the agent builds a library of reusable skill-chunks.

**Not implemented:** Schema-deviation storage (only storing what differs from schema-typical). Also missing: explicit schema accommodation — detecting when a schema is violated and updating it. Most systems treat memories as independent entries, not as updates to an existing schema network.

---

## 6. Metamemory

### What Cognitive Science Says

Metamemory is the ability to monitor and evaluate one's own memory — knowing what you know, how well you know it, and how to retrieve it.

**Judgments of Learning (JOLs):** After studying an item, people make predictions about whether they will remember it later. These are reasonably calibrated — they influence study time allocation.

**Feeling of Knowing (FOK):** Before attempting recall, people can judge whether they will be able to retrieve a target. FOKs are reliable enough to guide search strategies: "I know it, let me keep trying" vs "I don't know it, no point searching."

**Tip-of-the-Tongue (TOT):** The intermediate state where a memory is partially accessible — you know you know it, you can retrieve attributes (the word starts with "M", it's a famous Italian tenor), but cannot complete retrieval. TOTs demonstrate that memory monitoring is continuous, not binary.

**Confidence calibration:** Well-calibrated metamemory means confidence tracks accuracy. Overconfident individuals retrieve wrong memories with high confidence — a failure mode. Underconfident individuals fail to retrieve correct memories because they abandon search too early.

**Source monitoring (Johnson et al.):** Not just "what do I know" but "where did I learn it." Source monitoring errors produce false memories (attributing something you read to something you experienced). The brain tags memories with their provenance — this allows distinguishing personal experience from hearsay.

**Metamemory's function:** It saves computational resources. Without metamemory, the brain would always engage full retrieval and always be uncertain. With it, it can choose when to search, how long to search, and when to give up and say "I don't know."

### Actionable Design Principles

- **Agents should have FOK-like pre-retrieval confidence scores.** Before a full vector search, estimate probability that relevant memory exists. Skip the search if probability is below threshold.
- **Confidence should be calibrated to retrieval quality,** not semantic similarity score. High cosine similarity does not imply accurate memory; the agent should know the difference.
- **Source tagging is essential.** Every stored memory should record its provenance: observed vs inferred vs told by user vs extracted from document. Source confusions in agents produce the same failure mode as human false memories — confident wrong answers.
- **Graceful degradation:** agents should be able to say "I have partial information about this" (TOT equivalent) rather than binary know/don't-know. This enables the calling agent to decide whether to request clarification.
- **Memory evaluation as a first-class operation.** Reflexion (Shinn et al., 2023) implements a form of metamemory: the agent evaluates past actions and stores linguistic self-assessments. This is post-hoc metamemory — evaluate after the fact rather than at the moment of retrieval.

### Implementations

**Reflexion (Shinn et al., 2023):** Closest to applied metamemory. The agent generates verbal self-critiques of past performance and stores them as long-term memory. These critiques modify future behavior. Metamemory as running self-assessment rather than real-time monitoring.

**RMM (Retrospective Memory Management):** Combines retrospective reflection with RL-based retrieval optimisation. The agent learns, over time, which types of memories are worth retrieving for which tasks — a trainable metamemory signal.

**Retroformer:** Uses failure trajectories as long-term memory that guides decision-making. The "failure memory" is explicitly tracked — an asymmetric memory emphasis on errors, which matches human metamemory (we remember our mistakes disproportionately).

**BGC-KC (Tan et al., 2024):** Studies systematic bias in LLMs toward internal (parametric) knowledge over retrieved external knowledge. This is a miscalibration problem: the model's metamemory about its own internal knowledge is overconfident, and its trust of retrieved memories is too low. No agent system has corrected for this.

**Not implemented:** Pre-retrieval FOK scoring. No production system estimates whether a memory will be found before issuing the retrieval query. Source monitoring is partial — Graphiti stores ingestion metadata, but no system systematically distinguishes "agent observed this directly" from "user reported this" from "inferred from prior conversation." Calibrated confidence on retrieval output (distinct from similarity score) is absent.

---

## 7. Cross-Cutting Principles: What AI Has Missed

These are the most actionable gaps between what human memory science knows and what agent memory systems do.

### 7.1 Reconstruction vs Retrieval

Human memories are **reconstructed**, not retrieved. Each recall reassembles a memory from fragments + schema priors + current context. This is why memory is adaptive (good for generalisation) but also fallible (false memories).

**Current AI gap:** All vector store approaches treat retrieval as lookup — you get back what was stored. A reconstructive memory would: retrieve the closest matching fragments, use schema priors to fill gaps, flag the filled-in portions as inferred. This would support better generalisation (using partial matches) at the cost of introducing potential confabulation — which is actually acceptable if the confabulation is flagged.

### 7.2 The Spacing Effect

Memories reviewed at expanding intervals are retained better than massed review (Ebbinghaus, confirmed across hundreds of studies). The optimal schedule follows a power law: review at 1 day, 3 days, 1 week, 2 weeks, 1 month.

**Current AI gap:** MemoryBank implements decay but not *spaced strengthening* — the deliberate scheduling of re-access to keep important memories alive. For long-lived agents, a background process that periodically "reviews" important memories (retrieves and re-embeds them) would implement this.

### 7.3 Context at Encoding

The most powerful retrieval cue is the context present at encoding. Current systems store content; they should also store:
- The task the agent was performing when it encoded the memory
- The immediately prior context (what the conversation was about)
- Any emotional/priority signals that marked the event as salient

### 7.4 Active Forgetting as Curation

RIF — retrieval-induced forgetting — means the brain actively suppresses memories that compete with frequently retrieved ones. This keeps the most-used knowledge highly accessible while letting less-used associations decay. No agent system implements this competition-based suppression.

**Proposed implementation:** Track which memories competed in each retrieval query (returned in top-k but not selected). Apply a small negative weight update to those competitors. Over many retrievals, frequently-competing-but-not-selected memories decay, reducing retrieval noise.

### 7.5 Prospective Memory

The brain has dedicated mechanisms for remembering intentions — not just what happened, but what needs to happen. Event-based prospective memory (triggered by context cues) is more reliable than time-based.

**Current AI gap:** Most agent frameworks treat task queues as separate from memory. A unified prospective memory system would store intentions alongside episodic memories and activate them when the triggering context is detected — the way a human who "meant to call Sarah" recalls the intention when they see Sarah's name.

### 7.6 Metamemory Calibration

The single most actionable human mechanism not in agent systems: **pre-retrieval confidence estimation** combined with **source attribution**. Before searching memory: estimate probability of hit. After retrieving: flag source quality and confidence. This allows downstream reasoning to weight retrieved memories appropriately.

---

## 8. Architecture Implications: A Design Pattern

Mapping the mechanisms above to a layered agent memory architecture:

```
Layer 0: Sensory Buffer (context window)
  - Duration: current interaction only
  - Human analogue: sensory memory + working memory
  - Mechanism: attention gating for what to consolidate

Layer 1: Episodic Store (interaction log + trajectory store)
  - Duration: medium-term (weeks)
  - Human analogue: hippocampal episodic memory
  - Mechanisms: decay by access recency + importance,
    context tagging at encoding, source attribution
  - Retrieval: multi-factor (recency + relevance + context match)

Layer 2: Semantic Store (extracted knowledge / fact base)
  - Duration: long-term (persistent)
  - Human analogue: neocortical semantic memory
  - Mechanisms: consolidation from Layer 1 via LLM extraction,
    schema-matching to reduce redundancy, graph structure for spreading activation
  - Retrieval: graph traversal + vector similarity hybrid

Layer 3: Procedural Store (skill library / agent policies)
  - Duration: persistent (updated rarely)
  - Human analogue: basal ganglia procedural memory
  - Mechanisms: extracted from successful trajectories,
    stored as (situation → action) templates
  - Retrieval: pattern-match on current task state

Layer 4: Prospective Store (intention queue)
  - Duration: until executed
  - Human analogue: prospective memory
  - Mechanisms: event-based triggers, context-activated
  - Retrieval: triggered by context match, not explicit query

Metamemory Layer (cross-cutting):
  - Source tags on all memories
  - Confidence calibration separate from similarity scores
  - Pre-retrieval FOK estimation
  - Post-retrieval self-evaluation (Reflexion pattern)
```

---

## 9. Which Systems Come Closest

Ranking by degree of biological fidelity across the mechanisms covered:

| System | Forgetting | Consolidation | Multi-factor retrieval | Schema/chunking | Metamemory |
|---|---|---|---|---|---|
| **ACT-R** | Decay + interference | Implicit (activation strengthening) | Activation-based (mathematical) | Chunk activation | Partial (subsymbolic) |
| **SOAR** | Limited | Limited | Limited | Production rules as schemas | Limited |
| **Generative Agents** | None | Reflection mechanism | Recency + importance + relevance | Reflection as schema formation | None |
| **A-Mem** | None | Dynamic note evolution | Multi-factor + graph traversal | Link network as schemas | None |
| **MemoryBank** | Ebbinghaus decay | Summarisation | Limited | Limited | None |
| **Graphiti/Zep** | Limited | Graph construction | Temporal + semantic | Graph structure | Source metadata only |
| **Letta/MemGPT** | Agent-controlled | Agent-controlled | Agent-controlled | None explicit | None |
| **Mem0** | None | LLM extraction | Vector similarity only | Limited | None |
| **Reflexion** | None | None | None | None | Yes (self-evaluation) |
| **MemOS** | Explicit forgetting policies | Lifecycle management | Priority-driven | Task-concept-fact hierarchy | Limited |

**No current system scores well across all columns.** The most complete biological analogue for agent use would need: Generative Agents (consolidation) + MemoryBank (forgetting) + Graphiti (temporal retrieval) + Reflexion (metamemory) + A-Mem (dynamic schema evolution).

---

## Key Sources

1. [AI Meets Brain: Unified Survey (arxiv:2512.23343)](https://arxiv.org/html/2512.23343v1)
2. [From Human Memory to AI Memory (arxiv:2504.15965)](https://arxiv.org/html/2504.15965v1)
3. [Memory in the Age of AI Agents — Tsinghua (arxiv:2512.13564)](https://arxiv.org/abs/2512.13564)
4. [Rethinking Memory in AI — Operations Framework (arxiv:2505.00675)](https://arxiv.org/html/2505.00675v1)
5. [Episodic Memory is the Missing Piece (arxiv:2502.06975)](https://arxiv.org/abs/2502.06975)
6. [A-Mem: Agentic Memory (NeurIPS 2025, arxiv:2502.12110)](https://arxiv.org/abs/2502.12110)
7. [MemOS: Memory OS for AI System (arxiv:2507.03724)](https://arxiv.org/abs/2507.03724)
8. [Scenario-Driven Cognitive Approach to AI Memory (arxiv:2509.13235)](https://arxiv.org/html/2509.13235)
9. [Multiple Memory Systems for Long-term Memory (arxiv:2508.15294)](https://arxiv.org/html/2508.15294v1)
10. [HippoRAG — hippocampal indexing in RAG systems](https://arxiv.org/abs/2405.14831)
11. [Retrieval-Induced Forgetting — Anderson et al., Nature Neuroscience 2015](https://www.nature.com/articles/nn.3973)
12. [Human-like Forgetting Curves in DNNs (arxiv:2506.12034)](https://arxiv.org/html/2506.12034v2)
13. [MemoryBank: Ebbinghaus Implementation (Semantic Scholar)](https://www.semanticscholar.org/paper/MemoryBank:-Enhancing-Large-Language-Models-with-Zhong-Guo/c3a59e1e405e7c28319e5a1c5b5241f9b340cf63)
14. [Analysis and Comparison of ACT-R and SOAR (arxiv:2201.09305)](https://arxiv.org/abs/2201.09305)
15. [Tip-of-Tongue Metamemory Study (Journal of Cognition, 2024)](https://journalofcognition.org/articles/10.5334/joc.442)
