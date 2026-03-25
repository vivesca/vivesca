---
name: AI Model Releases — Early 2026 (Jan–Mar)
description: OpenAI and Google/DeepMind model releases, capabilities, pricing, and technical shifts in Q1 2026
type: reference
---

## OpenAI — Q1 2026

### Model Lineage (all GPT-5 series; o-series retired)
- GPT-5.3-Codex (Feb 5 2026): Agentic coding model. 25% faster than 5.2-Codex. First model partially self-created via early internal version.
- GPT-5.3-Codex-Spark: Lighter variant (fewer details confirmed).
- GPT-5.4 (Mar 5 2026): Unified frontier model — absorbs coding (5.3-Codex level), reasoning, computer use, long-context, agentic tool use. 1.05M token context window. 1M in API/Codex.
- GPT-5.4 Thinking: Reasoning variant (served as ChatGPT default for Plus/Team/Pro).
- GPT-5.4 Pro: Highest capability tier. $30/$180 per M input/output.
- GPT-5.4 standard: $2.50/$15.00 per M input/output. Cached input: $1.25/M. Long-context surcharge at 272K+ tokens.

### Key capabilities (GPT-5.4)
- Native computer use (first in general-purpose GPT model) — mouse/keyboard commands via screenshots, Playwright
- 33% fewer factual errors vs 5.2; 18% fewer hallucinations overall
- OSWorld-Verified and WebArena Verified record scores
- 83% on GDPval knowledge work test
- Tool search mechanism: 47% token cost reduction in tool-heavy workflows

### o-series fate
- o4-mini retired Feb 13 2026. GPT-4o, GPT-4.1, GPT-4.1 mini also retired. GPT-5.1 retired Mar 11 2026.
- No new standalone "o-series" reasoning model announced in Q1 2026. Reasoning integrated into GPT-5.x Thinking variants.

## Google / Gemini — Q1 2026

### Timeline
- Gemini 3 family launched Nov 18 2025 (base release)
- Gemini 3 Deep Think: Jan/Feb 2026 updates (major reasoning mode)
- Gemini 3 Deep Think (Feb 12 2026 update): 84.6% on ARC-AGI-2 (ARC Prize verified)
- Gemini 3.1 Pro: Feb 19 2026
- Gemini 3.1 Flash-Lite: Mar 3 2026 (developer preview)

### Model family
- Gemini 3 Pro / 3.1 Pro: Flagship. 1M token context. MoE architecture. Three-tier thinking system (Low/Medium/High). Real-time RAG via Google Search index.
- Gemini 3 Flash: Speed-optimized; default in Gemini app.
- Gemini 3.1 Flash-Lite: $0.25/$1.50 per M input/output = 1/8th price of Pro. 2.5x faster TTFT, 45% faster output vs Gemini 2.5 Flash.
- Gemini 3 Deep Think: Reasoning mode (not separate model). Available to AI Ultra subscribers.

### Key benchmarks (Gemini 3 Deep Think)
- ARC-AGI-2: 84.6% (Feb update); earlier Jan version scored 45.1%
- ARC-AGI-1: ~96% (near-saturated)
- Codeforces Elo: 3455
- IMO 2025: Gold-medal level
- Humanity's Last Exam: top-tier performance (specific % not confirmed in sources)

### Architecture notes (3.1 Pro)
- Transformer-based MoE
- Native multimodal: text, images, video, audio, code
- Integrated RAG (Google Search index) — reduces factual hallucinations 30%
- Three-tier thinking compute modulation
- 65,536 output token limit

## Google DeepMind Research — Aletheia (Feb 2026)
- Announced Feb 2026; paper: arxiv:2602.10177 ("Towards Autonomous Mathematics Research")
- Second paper: arxiv:2602.21201 (Aletheia tackles FirstProof autonomously)
- Architecture: Generator → Verifier → Reviser agentic loop; powered by advanced Gemini Deep Think
- FirstProof challenge: solved 6/10 open PhD-level math problems autonomously, no human help, under real deadline
- Erdős Conjectures: solved 4 open questions from 700-problem dataset
- Authored paper (Feng26) with zero human intervention (arithmetic geometry — structure constants/eigenweights)
- IMO-ProofBench Advanced: ~91.9%

## Anthropic — Q1 2026 (context)
- Opus 4.6: Feb 5 2026. 1M context. 14.5hr task horizon (longest of any model at release).
- Sonnet 4.6: Feb 17 2026. Same price as 4.5. Better computer use, coding.
- Claude Cowork: Jan 2026 research preview (GUI version of Claude Code for non-technical users).
- Claude 5 ("Fennec" codename): rumored Feb/Mar 2026; unconfirmed as of Mar 14.

## Technical Paradigm Shifts (early 2026)
- Three distinct scaling laws now recognized: pretraining, post-training, test-time (inference-time compute).
- Test-time scaling = dominant efficiency lever: 20s think time ≈ 100,000x more training compute.
- o1→o3 progression happened in 3 months (vs 1-2 year pretraining cycles) — demonstrates new velocity.
- Data saturation concern: public text data ceiling may arrive 2026.
- Industry moving to "efficient + frontier" tiered strategy (smaller specialist + massive general).

## Source reliability notes
- openai.com/index/* pages: return 403 on WebFetch — use WebSearch result snippets.
- blog.google/* pages: JS-gated — similar issue. Use VentureBeat, MarkTechPost, simonwillison.net as proxies.
- artificialanalysis.ai: reliable for benchmark cross-referencing.
- simonwillison.net: excellent for Google model releases, WebFetch works well.
- Pricing data cross-checked: openrouter.ai + pricepertoken.com + official API docs.
