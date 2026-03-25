# ADR-001: Semantic Search vs. Keyword Search

**Status:** Accepted
**Date:** 2026-01-24
**Context:** Banking FAQ chatbot replacement for iFLYTEK system

---

## Context and Problem Statement

The current iFLYTEK keyword-based chatbot cannot answer "SWIFT code" queries because it uses simple keyword matching. The information exists in the knowledge base (in a question about "remittance templates"), but semantic gaps between query terms and FAQ content prevent matches.

**Example failure case**:
- **User query**: "What is the SWIFT code?"
- **Existing FAQ**: "How do I fill out international remittance templates?" (answer contains SWIFT code information)
- **Current result**: No match (keyword mismatch)
- **Expected result**: Match based on semantic understanding

## Decision

Use **semantic search with vector embeddings (BGE-M3)** rather than improving keyword-based search.

### Approach
1. Convert all FAQ Q&A pairs to 1024-dim vector embeddings (BGE-M3 model)
2. Store embeddings in NumPy .npz files (language-partitioned)
3. User query → embed query → semantic search → return top match FAQ answer
4. Hybrid retrieval: 85% semantic + 15% lexical for EN, 75% semantic + 25% lexical for TC/SC

## Considered Alternatives

### Alternative 1: Enhanced Keyword Search (Elasticsearch with synonyms)
**Pros**: Simpler, faster, no ML dependencies
**Cons**:
- Requires manual synonym dictionaries (high maintenance for banking terminology)
- Cannot handle paraphrased queries ("How do I get the bank identifier code?")
- Still fails on semantic gaps (SWIFT code ≈ remittance templates)

**Why rejected**: Fundamental limitation - cannot capture semantic relationships between domain concepts.

### Alternative 2: Hybrid Search (Keywords + Semantic)
**Pros**: Best of both worlds - exact matches + semantic understanding
**Cons**: More complexity, requires tuning weight parameters per language
**Why deferred, not rejected**: We *are* using hybrid search, but semantic-first (75-85% weight). Can increase lexical weight if needed.

### Alternative 3: Full RAG with LLM Generation
**Pros**: Most flexible, can synthesize answers from multiple FAQs
**Cons**:
- User requirement: No LLM-generated responses (banking compliance)
- Hallucination risk unacceptable in banking context
- Latency and cost concerns

**Why rejected**: Violates core requirement (exact FAQ content only).

## Rationale

### Why Semantic Search Solves the SWIFT Code Problem
- Embeddings capture meaning, not just keywords
- "SWIFT code" query will match "remittance templates" FAQ based on semantic similarity
- Handles synonyms automatically (SWIFT code = BIC code = bank identifier code)
- Works across languages (EN/TC/SC) with multilingual model (BGE-M3)

### Why BGE-M3 Model
- **Multilingual**: Supports English, Traditional Chinese, Simplified Chinese
- **Performance**: 63.0 MTEB score (competitive with commercial models)
- **Cost**: Free (open-source) vs. $0.10-0.13/1M tokens for Cohere/OpenAI
- **Deployment**: Available via OpenRouter API or self-hosted

### Why Hybrid Retrieval (Not Pure Semantic)
From institutional learning (`docs/solutions/tc-sc-retrieval-quality-lag.md`):
- Pure semantic search underperformed on Chinese queries (TC/SC accuracy 0.68-0.72)
- Adding lexical reranking improved to 0.85-0.89 (comparable to EN)
- Lexical component helps with exact term matches (FPS, eDDA, SWIFT)

## Consequences

### Positive
- Solves domain terminology problem (SWIFT code, FPS, eDDA queries)
- Handles query variations and paraphrasing
- Multilingual support with single model
- No manual synonym maintenance

### Negative
- Requires ML infrastructure (embedding generation, vector storage)
- Latency higher than keyword search (200-400ms embedding + 5-10ms search vs. 5-10ms pure keyword)
- Model updates require re-embedding entire FAQ corpus
- Debugging "why did this match?" harder than keyword search

### Risks and Mitigations
| Risk | Mitigation |
|------|------------|
| Embedding quality degrades on banking jargon | Monitor accuracy per language, fine-tune if <80% |
| Latency exceeds 2s p95 target | ONNX optimization (if self-hosted), or OpenRouter API (if acceptable latency) |
| Model bias or unexpected matches | Comprehensive test suite with banking terminology |
| Vendor lock-in (OpenRouter API) | BGE-M3 is OSS - can self-host if needed |

## Validation

### Success Criteria
- ✅ "SWIFT code" queries match remittance FAQ (top-1, confidence >0.65)
- ✅ TC/SC accuracy comparable to EN (>0.85 top-1 accuracy)
- ✅ Response time <2s p95 (embedding + search + PII redaction)
- ✅ No synonym dictionary maintenance required

### Test Cases
1. "What is the SWIFT code?" → Matches remittance FAQ
2. "告訴我SWIFT code" (Tell me SWIFT code) → Matches remittance FAQ (TC)
3. "SWIFT代碼是什麼" (What is SWIFT code) → Matches remittance FAQ (SC)
4. "點樣轉數快?" (How to use FPS?) → Matches FPS FAQ (Cantonese)

## References

- **Brainstorm**: `docs/brainstorms/2026-01-24-faq-semantic-search-brainstorm.md`
- **Institutional learning**: `docs/solutions/logic-errors/tc-sc-retrieval-quality-lag.md`
- **Research findings**: `docs/research/semantic-search-findings.md`
- **BGE-M3 paper**: [FlagEmbedding: Massive Text Embedding Benchmark](https://arxiv.org/abs/2310.07554)
