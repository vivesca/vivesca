---
name: Human Memory Science for AI Agents Research (Mar 2026)
description: Comprehensive mapping of cognitive science memory mechanisms to AI agent architectures; covers all major memory systems, forgetting, consolidation, retrieval, schemas, metamemory, with specific AI implementation status per mechanism
type: reference
---

# Human Memory Science for AI Agents Research (Mar 2026)

## Output Location
Full synthesis: `/Users/terry/docs/solutions/human-memory-science-for-agents.md`

## Key Bridge Papers (most useful for this domain)

- **arxiv:2512.23343** "AI Meets Brain: Unified Survey" (Dec 2025) — best neuroscience→agents bridge. 57 pages. Has taxonomy, storage formats, consolidation paradigms, forgetting strategies, retrieval mechanisms.
- **arxiv:2504.15965** "From Human Memory to AI Memory" (Apr 2025) — maps all 5 forgetting types + consolidation to specific AI systems. WebFetch works (HTML version).
- **arxiv:2512.13564** "Memory in the Age of AI Agents" (Tsinghua) — canonical taxonomy. Inside-trail/cross-trail × semantic/episodic/procedural.
- **arxiv:2505.00675** "Rethinking Memory in AI" — operations framework: consolidate/index/update/forget/retrieve/compress.
- **arxiv:2502.06975** "Episodic Memory is the Missing Piece" — argues structural absence of episodic memory in current agents.
- **arxiv:2509.13235** "Scenario-Driven Cognitive Approach" — COLMA architecture, six capabilities.
- **arxiv:2508.15294** "Multiple Memory Systems for Long-term Memory" — dual retrieval/contextual units inspired by Tulving + encoding specificity.

## Source Reliability

- HTML arxiv pages (arxiv.org/html/...) — WebFetch works well, returns full paper content
- PDF arxiv pages — WebFetch returns binary garbage, do NOT use
- Semantic Scholar PDF links — same issue, use HTML or abstract pages
- PMC (pmc.ncbi.nlm.nih.gov) — WebFetch works, returns full article text

## Key Facts Established

### Gaps in Current AI Agent Memory Systems (all confirmed as of Mar 2026)
1. **Reconstruction vs retrieval** — no system does reconstructive memory (fill gaps from schema + mark inferred portions)
2. **Retrieval-induced forgetting (RIF)** — no system suppresses competitor memories when a target is retrieved
3. **Context-at-encoding storage** — no system stores the task context present when a memory was encoded
4. **Prospective memory** — almost no agent memory research addresses intention memory (triggering by context cues)
5. **Source monitoring** — Graphiti has ingestion metadata; none distinguish "agent observed" vs "user told" vs "inferred"
6. **Pre-retrieval FOK estimation** — no system estimates probability of hit before issuing retrieval query
7. **Spaced strengthening** — MemoryBank has decay but not deliberate scheduled re-access for important memories
8. **Schema-deviation storage** — no system stores only what deviates from schema-typical values
9. **Two learning rates** — no production system separates fast episodic capture from slow semantic consolidation explicitly

### Implementations Per Mechanism
- **Ebbinghaus decay:** MemoryBank (best), SAGE, MEMORYLLM (capacity bounding)
- **Reflection/consolidation:** Generative Agents (threshold-triggered), A-Mem (dynamic note evolution)
- **Multi-factor retrieval:** Generative Agents (recency + importance + relevance), HippoRAG (spreading activation on KG)
- **Graph-based spreading activation:** HippoRAG (explicit hippocampal model), Graphiti, A-Mem
- **Procedural schema:** Agent Workflow Memory, Buffer of Thoughts (thought templates), skill libraries
- **Metamemory:** Reflexion (post-hoc self-evaluation), RMM (retrospective + RL), Retroformer (failure memory)
- **Forgetting as active operation:** MemOS (explicit forgetting policies), MemoryBank (time-based deletion)

### Cognitive Architecture Reference
- **ACT-R:** Best mathematical model — activation = base-level + spreading activation from current goal context. Validated against human RT distributions. Closest to formal model of retrieval probability.
- **SOAR:** Separates episodic + semantic memory explicitly. Episodic store allows querying "what happened in situations like this?" — best symbolic AI analogue.

## Methodology That Worked

1. Start with survey papers (arxiv:2512.23343, arxiv:2512.13564) for taxonomy scaffolding
2. Then drill into mechanism-specific papers (arxiv:2504.15965 for forgetting, arxiv:2502.06975 for episodic gap)
3. WebSearch for specific mechanism + "AI agent" + year to find implementations
4. WebFetch HTML versions of arxiv papers (not PDF)
5. PMC for human neuroscience papers (PubMed Central — full text accessible)

## Misinformation Patterns Noted

- "Spreading activation" is frequently referenced in AI papers but rarely implemented — most systems use flat cosine similarity, not network propagation. HippoRAG is a genuine exception.
- "Episodic memory" in AI papers often just means "conversation history log" — not Tulving's definition (temporal-spatial indexed, reconstructive, hippocampus-dependent)
- Vendor claims about "human-like memory" almost always mean "we store conversation history" — not mechanism-level implementation
