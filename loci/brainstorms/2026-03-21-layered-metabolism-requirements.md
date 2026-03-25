---
date: 2026-03-21
topic: layered-metabolism
---

# Layered Metabolism: Beyond Tool Descriptions

## Problem Frame

Vivesca's metabolism currently optimizes only tool descriptions — one unit type in one metabolic layer. But the system loads many other text fragments (prompts, resources, memory files, reference docs) that consume tokens (ATP) and influence LLM behaviour. These fragments accumulate without selection pressure. The biology metaphor — tokens as energy, text as genome, metabolism as energy management — structurally applies to all loaded text, not just tool descriptions.

## Requirements

- R1. The metabolism engine supports multiple unit types, each with its own parallel pipeline (signal adapter, variant store, fitness function, promotion gate).
- R2. **Active layer expansion:** prompt templates and resource descriptions gain their own metabolism pipelines alongside the existing tool description pipeline.
- R3. Each unit type collects signals via a type-specific adapter. Adapters use proxy signals initially, designed to be replaceable with better attribution mechanisms later.
- R4. **Prompt signal proxy:** track post-prompt outcomes — subsequent tool call results, user corrections, session quality after prompt use.
- R5. **Resource signal proxy:** track post-read actions — productive action following a read vs confusion, retry, or abandonment.
- R6. All unit types have full mutation autonomy (no human approval for safe dimensions). Selection handles quality, consistent with the living system philosophy.
- R7. The founding text (v0) serves as a constitutional constraint for all unit types — the LLM judge has veto power when mutations drift from founding intent.

## Success Criteria

- Prompt templates and resource descriptions are under metabolic pressure — signals collected, fitness computed, mutations proposed and promoted.
- The system detects low-fitness prompts/resources and improves them autonomously.
- The architecture cleanly separates unit types so the storage layer can be added later without rearchitecting the active layer.
- No regression in existing tool description metabolism.

## Scope Boundaries

- **Active layer only.** Storage layer (memory files, reference docs) is explicitly deferred until active layer proves out.
- **Basal layer deferred.** CLAUDE.md and always-loaded context cannot be A/B tested — no metabolism for these in v1.
- **No cross-layer interactions.** Each pipeline is independent. Cross-layer fitness coupling is a future concern.
- **No cross-unit coupling.** Co-invocation and interference analysis between prompts and tools is deferred.
- **No network features.** No inter-agent signal sharing or horizontal gene transfer.

## Key Decisions

- **Layered metabolism over unified abstraction:** Different metabolic layers (basal, active, storage, growth) have genuinely different signal mechanisms. Trying to unify them prematurely risks a leaky abstraction. Extend layer by layer, following the signal clarity gradient.
- **Parallel pipelines over generalised machinery:** Each unit type gets its own store/fitness/gate infrastructure rather than sharing generalised machinery. Cleaner separation, easier to evolve independently, avoids coupling between unit types that have different mutation surfaces.
- **Full autonomy from day one:** Prompt and resource mutations don't require human approval. This is consistent with the founding design ("full autonomy on safe dimensions") and avoids creating a human bottleneck that would prevent the system from actually living.
- **Proxy signals, upgradeable:** Start with directionally correct proxy signals rather than solving perfect attribution. Design the signal adapter interface so better mechanisms can replace proxies without touching fitness/mutation/gate code.

## Dependencies / Assumptions

- Assumes the core metabolism loop (signal → fitness → mutation → gate → promotion) is wired end-to-end for tool descriptions before this work begins. This extension builds on a working pipeline, not a stub.
- Prompt templates and resource descriptions are currently static files. The metabolism needs read/write access to them, same as tool description variants.

## Outstanding Questions

### Deferred to Planning

- [Affects R3][Needs research] What is the exact proxy signal schema for prompts? How to attribute "post-prompt outcome" when multiple tool calls follow a prompt invocation?
- [Affects R3][Needs research] What is the exact proxy signal schema for resources? How to distinguish "productive read" from "read followed by confusion"?
- [Affects R2][Technical] Mutation operator for prompt templates — section-level? Paragraph-level? Prompts are structured and longer than 80-char descriptions; the mutation surface is qualitatively different.
- [Affects R2][Technical] VariantStore format for prompts — longer text may need different storage/diff strategy than single-line descriptions.
- [Affects R1][Technical] Sequencing relative to core pipeline wiring — does this ship as part of the same milestone or as a follow-on?
- [Affects R7][Technical] Constitutional constraint for prompts — v0 veto semantics when the founding text is multi-paragraph rather than one line.

## Metabolic Layers (Vision)

For context on future direction. Only the active layer is in scope for this work.

| Layer | Biology | Vivesca | Signal | Status |
|-------|---------|---------|--------|--------|
| **Basal** | Always-on expenditure | CLAUDE.md, always-loaded rules | Can't A/B test | Deferred |
| **Active** | Task-specific energy | Tools, prompts, resources, skills | Invocation → outcome | **v1: expand** |
| **Storage** | Fat/glycogen reserves | Memory files, reference docs | Recall × usefulness | Deferred |
| **Growth** | Building new structures | New tools, skills, docs | Adoption rate | Deferred |

## Next Steps

→ `/ce:plan` for structured implementation planning
