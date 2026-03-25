# LRN-20260305-003 — Exa AI Evaluation

**Date:** 2026-03-05
**Context:** Evaluating Exa as replacement/complement to noesis/Perplexity stack.

## What Exa Does Differently

Exa is embeddings-first, not keyword-first. Queries are semantically encoded; results are retrieved by vector similarity across a crawled index trained for AI consumption (not human SERP optimisation). This gives it a qualitative edge on discovery-style queries ("find papers like this one", "companies matching these criteria") where phrasing variability defeats keyword search. Perplexity/noesis synthesises an answer from web results; Exa returns raw results with full page content available, giving the caller full control over how to use them.

## Exa Product Lines

### Exa Search (core API)
- Neural + keyword hybrid search; 1–100 results per call
- `$7/1,000 requests` (≈ **$0.007/query**) — essentially same as noesis search ($0.006)
- Full page content: +$1/1,000 pages (near-free)
- Latency: 100–1,200ms (fast tier <350ms P50)
- 1,000 free requests/month on free tier
- Benchmarks: 90.04% SimpleQA (vs Perplexity 88.70%, Tavily 93.3%, Exa Research 94.9%)

### Exa Deep / Agentic Search
- Agent-in-loop: iterative search across multiple pages before returning
- `$12/1,000 requests` ($0.012/query); +$3/1,000 with reasoning ($0.015)
- Latency: 4–30s per call
- Quality: 94.9% SimpleQA (highest of any API tested, 2025)
- Conceptual equivalent to noesis research but billed per query not per research session

### Exa Research (full pipeline)
- Agent search ops + page reads + reasoning tokens all billed separately
- Agent search: $5/1,000 ops; page reads: $5–10/1,000 pages; reasoning: $5/1M tokens
- For a typical deep research task (~20 search ops + ~10 page reads): ~$0.15–0.20/task
- Comparable to noesis research ($0.40) but modular — cheaper for focused tasks

### Exa Websets
- Structured entity-list generation: companies, people, papers matching criteria
- Not a search replacement — designed for lead gen / market mapping
- Pricing: Free (1K credits/25 results), Core $49/mo (8K credits), Pro $449/mo (100K credits)
- 10 credits per matched result; large websets (1,000+ items) can take up to 1 hour
- **Use case:** building prospect lists, sourcing candidates, market mapping — not ad hoc research

## Comparison vs noesis Stack

| Dimension | noesis search ($0.006) | Exa Search ($0.007) | Exa Research ($0.015–0.20) | noesis research ($0.40) |
|---|---|---|---|---|
| Quick cited lookups | Synthesised answer + citations | Raw results (no synthesis) | Overkill | Overkill |
| Deep research | Shallow | Shallow | 94.9% accuracy, modular cost | Full synthesis, easier UX |
| HK/Chinese queries | Perplexity index, English-dominant | Auto-language filtering (quality unknown for Chinese) | Same caveat | Perplexity index |
| Rate limits | ~Perplexity cap (30 QPS) | 100s QPS | 100s QPS | ~Perplexity cap |
| Results format | Synthesised prose | Raw URLs + content | Structured findings | Synthesised prose |

## HK/Chinese Coverage — Caution Flag

Exa's language-filtering changelog confirms "English, Spanish, French, or any other language" with Chinese implied but not explicitly validated. No third-party benchmarks found for CJK coverage specifically. The noesis/Perplexity stack uses the same underlying index but returns synthesised answers that mask coverage gaps. For HK local queries (OpenRice, HK01, Sundaykiss, LIHKG), both stacks likely perform similarly poorly via API — the winning strategy remains "search in Chinese first" regardless of provider.

## Community Signals

- Praised for "Find Similar" feature — feed one result, get 20 more like it (impossible with keyword search)
- Criticised for pricing complexity and cost at scale
- Documentation still maturing vs Perplexity/Tavily
- Multi-API stacks (Serper volume + Tavily quality + Exa research) are the production pattern — not single-provider

## Recommendation: TEST for deep research; SKIP for quick lookups; SKIP Websets

**Quick cited lookups:** Skip Exa. noesis search ($0.006) returns synthesised answers with citations — Exa returns raw URLs needing post-processing. Same cost, worse UX for this use case.

**Deep research:** Test Exa Research as a complement when noesis research ($0.40) feels like overkill. Exa Research is modular (~$0.15–0.20/task) and hits 94.9% SimpleQA. Candidate for a new middle tier: noesis search → Exa Research → noesis research.

**Websets:** Skip. Lead-gen / market-mapping product. Not relevant to the current research workflow.

**Proposed revised stack:**
- WebSearch (free) → noesis search ($0.006, cited synthesis) → **Exa Research ($0.015–0.20, modular depth)** → noesis research ($0.40, full synthesis)

## Sources

- [Exa Pricing](https://exa.ai/pricing) — official pricing page
- [Exa vs Perplexity](https://exa.ai/versus/perplexity) — official comparison
- [Tavily vs Exa vs Perplexity vs YOU.com comparison](https://www.humai.blog/tavily-vs-exa-vs-perplexity-vs-you-com-the-complete-ai-search-api-comparison-2025/) — SimpleQA benchmarks + latency data
- [Exa Websets FAQ](https://exa.ai/docs/websets/faq) — official Websets docs
- [Exa language filtering changelog](https://exa.ai/docs/changelog/language-filtering-default) — CJK coverage context
- [Introducing Exa Research blog](https://exa.ai/blog/introducing-exa-research) — agentic pipeline details (404 — used search summary)
- [Exa Websets reviews — opentools.ai](https://opentools.ai/tools/exa-websets)
