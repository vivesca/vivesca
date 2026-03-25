---
date: 2026-03-21
topic: vivesca-enhancements
focus: open-ended
---

# Ideation: Vivesca Enhancements

## Codebase Context

Vivesca v0.2 — living MCP server (FastMCP 3, Python 3.11+) with metabolism engine for continuous tool optimization. 24 tools across 7 domain modules, 4 resources, 3 prompts, 71 tests. Persistent HTTP process via LaunchAgent.

Core architecture: tool descriptions as versioned genomes (markdown in VariantStore), signal collection via FastMCP Middleware, fitness = success_rate × (1/log₂(avg_tokens + 2)), hot path (metaprompt repair on errors) and cold path (weekly DE sweep), dual-gate promotion (deterministic + LLM judge), git branches as sandbox.

Metabolism engine implemented (9 commits, 21 Mar 2026) but not wired end-to-end — sweep CLI is a stub.

## Ranked Ideas

### 1. Close the Metabolism Loop
**Description:** Wire the pipeline end-to-end: signal → fitness → candidate selection → mutation → gate → promotion. The `sweep` CLI is a stub. `repair.py`, `sweep.py`, and `gates.py` are never imported by `server.py`. `promote()` is never called in production.
**Rationale:** Foundational gap. Every other enhancement assumes the loop exists. Without it, vivesca is a signal collector with dormant evolution machinery.
**Downsides:** Largest single piece of work. Requires decisions about triggering, async bridging, and error handling.
**Confidence:** 95%
**Complexity:** High
**Status:** Unexplored

### 2. Signal Quality Pipeline
**Description:** Three interlocking fixes: (a) Error taxonomy router — classify errors before routing to repair; only description misfires trigger haiku. (b) Correction signal injection — `Outcome.correction` and `Outcome.reinvocation` are dead code; add mechanism to emit them. (c) Binary health registry — pre-flight check at startup, `Outcome.unavailable` for missing CLIs.
**Rationale:** Without signal quality, metabolism optimises the wrong lever. A missing binary generates error signals that trigger description repair — wasting LLM calls and corrupting fitness.
**Downsides:** Three coordinated changes touching signals, middleware, fitness, and repair routing.
**Confidence:** 90%
**Complexity:** Medium
**Status:** Unexplored

### 3. Evolutionary Safety Net
**Description:** Three mechanisms: (a) Founding description as constitutional constraint — pass v0 to LLM judge with veto power. (b) Variant lineage tracking — record parent ID, mutation method, triggering signal, pre-mutation fitness. (c) Mutation rollback — auto-revert on fitness regression.
**Rationale:** Autonomy is only safe if evolution is bounded, observable, and reversible. Without these, a runaway mutation on a safety-critical tool could optimise away a constraint.
**Downsides:** Adds monitoring state and a background coroutine. Constitutional check adds LLM call to every promotion.
**Confidence:** 85%
**Complexity:** Medium-High
**Status:** Unexplored

### 4. Deterministic Hot-Path Repair
**Description:** Classify failure modes with regex/keyword match before calling haiku. Known patterns (wrong argument format, timezone, missing field) get slot substitutions. LLM repair becomes fallthrough for novel errors only.
**Rationale:** Repair cost drops from O(every error) to O(novel errors). Same failure, same fix — no reason to pay for LLM on the 10th occurrence.
**Downsides:** Pattern library requires curation. Risk of over-fitting to current failures.
**Confidence:** 75%
**Complexity:** Low-Medium
**Status:** Unexplored

### 5. Signal Temporal Dynamics
**Description:** Half-life decay on historical fitness signals. Dormancy detection — skip zero-signal tools from mutation candidates. Warm-up discount on first K signals after dormancy.
**Rationale:** Stale signals dominate averages. Evolution should track current usage patterns.
**Downsides:** Requires choosing decay constant. May discard stable historical signal.
**Confidence:** 80%
**Complexity:** Low
**Status:** Unexplored

### 6. Cross-Tool Fitness Coupling
**Description:** Track co-invocation patterns. Compute pairwise coupling strength. When mutating one member of a high-coupling pair, include partner's description as context. Prevents semantic convergence between similar tools.
**Rationale:** Tools compete for selection in the same system prompt. Individual fitness doesn't capture interference. Epistasis — gene-gene interaction — is structural biology, not decorative.
**Downsides:** Most complex idea. Requires session sequencing. Signal volume may be too low initially.
**Confidence:** 65%
**Complexity:** High
**Status:** Unexplored

## Additional Direction: Layered Metabolism (Explored)

Brainstormed and planned separately. Extends metabolism beyond tool descriptions to prompt templates and resource descriptions. See:
- Brainstorm: `docs/brainstorms/2026-03-21-layered-metabolism-requirements.md`
- Plan: `docs/plans/2026-03-21-001-feat-layered-metabolism-active-layer-expansion-plan.md`

Key finding: FastMCP Middleware already has `on_get_prompt` and `on_read_resource` hooks. Signal collection works the same way for all unit types.

## Rejection Summary

| # | Idea | Reason Rejected |
|---|------|-----------------|
| 1 | Async signal collector | Just do it — well-understood pattern, not worth brainstorming |
| 2 | Async metabolism bridge | asyncio.to_thread wrappers — implement during pipeline wiring |
| 3 | Description char budget gate | One-line gate fix, implement alongside pipeline wiring |
| 4 | Resource lifecycle verification | Nice-to-have, low leverage on core system |
| 5 | Latency as fitness dimension | Clean extension, fold into pipeline wiring |
| 6 | Variant shadow-testing | Dual gate sufficient initially; replay harness premature |
| 7 | Invert sweep trigger | Implementation detail of #1 |
| 8 | Tool budget visibility resource | Useful but orthogonal |
| 9 | Invocation drought / extinction | Dormancy detection in #5 covers pragmatic case |
| 10 | Epigenetic fitness lanes | Signal volume too low to partition |
| 11 | Reverse metabolism | Meta-interesting but premature |
| 12 | Junk DNA / variant graveyard | Non-problem at current scale (5 variants × 24 tools) |
| 13 | Allometric fitness | Premature until uniform function proven wrong |
| 14 | Adaptive description compression | 80-char rule already tight |
| 15 | Description syntax as learnable schema | Sample size too small |
| 16 | Cross-session variant inheritance | Premature convergence only matters once system converges |
| 17 | Schema mutation | Good v2 surface expansion; premature now |
| 18 | Horizontal gene transfer | Network infra doesn't exist |
| 19 | Inter-agent signal donation | Network-dependent, future direction |
| 20 | Signal log compaction | Months from mattering |
| 21 | Adversarial fitness injection | Synthetic signals risk poisoning real data |
| 22 | Metabolism rate as health signal | Subsumed by lineage tracking in #3 |
| 23 | Session-boundary enrichment | Fold into pipeline wiring |

## Session Log

- 2026-03-21: Initial ideation — 48 raw candidates from 6 parallel agents (pain, unmet needs, inversion, reframe, leverage, edge cases), deduped to ~30, 6 survivors + 23 rejected. Layered metabolism direction brainstormed and planned separately.
