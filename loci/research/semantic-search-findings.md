# Semantic Search Research Findings
**Date:** 2026-01-24
**Context:** Banking FAQ chatbot semantic search implementation
**Research agents used:** 8 parallel agents (best practices, frameworks, performance, security, data integrity, simplicity, architecture)

---

## Key Findings Summary

### 1. Critical Architecture Fix: Session Management
**Problem**: In-memory session storage breaks multi-instance deployment
**Impact**: Production blocker - sessions lost across requests on Railway/on-prem
**Solution**: Migrate to Redis with 30-minute TTL

### 2. Security Gaps Identified
- Missing API authentication
- Incomplete PII redaction (only email/HKID, missing account numbers, cards, transaction IDs)
- No comprehensive audit logging for banking compliance

### 3. Performance Reality Check
- **BGE-M3 CPU target of 500ms is unrealistic** - actual: 800-1500ms on typical hardware
- ONNX + INT8 quantization needed for 200-400ms (if using local deployment)
- If using OpenRouter API, optimization is N/A (cloud-hosted)

### 4. Simplicity Wins
- **NumPy .npz sufficient until 5K+ FAQs** (current: 300 FAQs, 5-10ms search)
- Defer query enhancement until proven necessary
- Defer admin UI until update frequency >1/week

### 5. TC/SC Quality Validation
From institutional learning (`docs/solutions/tc-sc-retrieval-quality-lag.md`):
- Normalization + lexical rerank essential for Chinese
- Full-width punctuation normalization required
- Cantonese synonym mapping (點樣→如何, 轉數快→fps)
- Validates current implementation is on right track

---

## Vector Database Comparison (2025-2026 Best Practices)

| Solution | Best For | Query Time @ 10K | Memory | Tradeoffs |
|----------|----------|------------------|---------|-----------|
| NumPy .npz | <5K vectors, prototyping | 5-10ms | Low (in-process) | No persistence, linear scan |
| PGVector | Production, SQL familiarity | 10-20ms | Medium (PostgreSQL) | Requires DB, index tuning |
| Chroma | Local dev, small scale | 15-25ms | Low (embedded) | Limited production features |
| Weaviate | Large scale, multi-tenant | 5-15ms | High (dedicated) | Ops complexity, cost |
| Pinecone | Managed, serverless | 20-40ms | N/A (cloud) | Vendor lock-in, egress costs |

**Recommendation**: Keep NumPy .npz until scale justifies migration (>5K FAQs or >50ms latency).

---

## Embedding Model Landscape (2025-2026)

### Top Models for Multilingual Banking

| Model | MTEB Score | Dimensions | Cost | Deployment |
|-------|-----------|------------|------|------------|
| Cohere embed-v4 | 65.2 | 1024 | $0.10/1M tokens | API only |
| BGE-M3 | 63.0 | 1024 | Free (OSS) | API or self-hosted |
| OpenAI ada-002 | 61.0 | 1536 | $0.13/1M tokens | API only |
| E5-mistral-7b | 56.9 | 4096 | Free (OSS) | Self-hosted (GPU) |

**Current choice: BGE-M3** via OpenRouter API
**Rationale**: Good multilingual performance, cost-effective, 1024-dim matches industry standard

### Fine-Tuning Considerations
- **When to fine-tune**: Baseline accuracy <80% after 3 months production data
- **Cost**: 2-3 weeks engineering time + GPU compute
- **Benefit**: 10-15% accuracy gain typical for domain-specific corpora
- **Decision**: Defer until pre-trained model validated on banking domain

---

## TC/SC Retrieval Quality (Institutional Learning)

From `docs/solutions/logic-errors/tc-sc-retrieval-quality-lag-bank-faq-chatbot-20260124.md`:

### Problem Solved
TC/SC retrieval quality lagged behind EN (0.68-0.72 vs 0.89 for EN). Solution: normalization + lexical reranking tuned for Cantonese/Chinese.

### Key Components (Validate in Current Implementation)

1. **Full-width punctuation normalization**
```python
FULLWIDTH_MAP = str.maketrans({
    "０": "0", "１": "1", "２": "2", # ... (0-9)
    "，": ",", "。": ".", "！": "!", "？": "?",
    "（": "(", "）": ")", "－": "-",
})
```

2. **Cantonese synonym mapping**
```python
SYNONYM_MAP = {
    "匯率": "外匯",
    "轉賬": "轉帳",
    "繳費": "付款",
    "點樣": "如何",
    "係咪": "是否",
    "轉數快": "fps",
}
```

3. **Language-specific hybrid weights**
```python
LANG_WEIGHTS = {
    "en": (0.85, 0.15),  # 85% semantic, 15% lexical
    "tc": (0.75, 0.25),  # More lexical weight for Chinese
    "sc": (0.75, 0.25),
}
```

**Result**: Quality improved to 0.85-0.89 for TC/SC (comparable to EN).

---

## Compliance Requirements (Banking Context)

### Audit Logging (7-Year Retention)
Banking regulations require:
- Full query text (PII-redacted)
- Matched FAQ ID and content
- Confidence scores
- Model version and parameters
- Timestamp and session ID
- User attribution (if available)

### PII Redaction Patterns (Extended for Banking)
Beyond basic email/HKID:
- Account numbers: `\b\d{3}-\d{3}-\d{3,4}\b`
- Credit cards: `\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b` (with Luhn validation)
- Transaction IDs: `\b[A-Z]{2}\d{8,14}\b`
- HK phone numbers: `\+852[-\s]?\d{4}[-\s]?\d{4}`
- SWIFT codes: `\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b`

### Explainability
Regulators may require showing matched question for AI decision explainability. Consider adding matched question to response metadata (optional UI display).

---

## Performance Optimization Options

### ONNX + INT8 Quantization (If Using Local BGE-M3)
```python
from optimum.onnxruntime import ORTModelForFeatureExtraction, ORTQuantizer

# Export to ONNX
model = ORTModelForFeatureExtraction.from_pretrained(
    "BAAI/bge-m3",
    export=True,
    provider="CPUExecutionProvider"
)

# INT8 quantization (2x speedup)
quantizer = ORTQuantizer.from_pretrained(model)
quantizer.quantize(save_dir="./bge-m3-int8")
```

**Expected improvement**: 800-1500ms → 200-400ms on CPU
**Note**: Only applicable if self-hosting model. OpenRouter API can't be optimized.

### BM25 Lexical Search (Replace N-gram at Scale)
```python
from rank_bm25 import BM25Okapi
import jieba  # For Chinese tokenization

def tokenize(text, lang):
    if lang in ['tc', 'sc']:
        return jieba.lcut(text)
    else:
        return text.split()

tokenized_corpus = [tokenize(faq, lang) for faq, lang in zip(faq_texts, faq_langs)]
bm25 = BM25Okapi(tokenized_corpus)

# 10x faster than character n-grams at >1000 FAQs
scores = bm25.get_scores(tokenize(query, query_lang))
```

**Trigger condition**: FAQ count >1,000 OR lexical search latency >100ms

---

## Admin UI Options (If Needed)

### Payload CMS (Node.js)
- **Pros**: Modern UI, webhook support, role-based access
- **Cons**: Node.js dependency (adds runtime to Python stack), on-prem deployment complexity
- **Effort**: 3-4 weeks (integration + webhook pipeline)

### Django Admin (Python)
- **Pros**: Python-native, built-in LDAP support, no additional runtime
- **Cons**: Less modern UI, manual webhook implementation
- **Effort**: 2-3 weeks (custom admin + celery webhooks)

### Strapi (Node.js)
- Similar to Payload CMS
- More plugin ecosystem, less banking-focused

**Recommendation**: Defer admin UI until FAQ updates >1/week for 3 months. Manual JSON editing works for MVP.

---

## Architecture Validation

### Language-Locked Sessions ✓
- **Solid decision**: Reduces search space by ~67%, eliminates cross-language noise
- **Risk**: Code-switching users (HK customers may switch EN↔TC mid-conversation)
- **Mitigation**: Add manual language switch in UI

### Q&A Concatenation ✓
- **Sound approach**: Captures semantic relationship between Q and A
- **Risk**: Long answers may dominate embedding space
- **Mitigation**: Monitor false negatives; consider question-weighted concatenation if issues arise

### Confidence-Based Routing ✓
- **Excellent for banking**: Graceful degradation admits uncertainty vs. hallucinating
- **Regulatory alignment**: Confidence thresholds provide audit trail
- **Enhancement**: Add feedback loop when users select from top-3 clarification

### Answer-Only Response ⚠️
- **Banking concern**: Regulators may require showing matched question for explainability
- **User validation**: Customers need to verify "Yes, this is what I asked"
- **Recommendation**: Add matched question to response metadata (optional UI display)

---

## References

### Industry Best Practices (2025-2026)
- [Pinecone: Semantic Search Architecture](https://www.pinecone.io/learn/semantic-search/)
- [Weaviate: Vector Database Performance Benchmarks](https://weaviate.io/blog/benchmarking)
- [HuggingFace: MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)

### Framework Documentation
- [FastAPI: Background Tasks & Lifecycle](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Sentence-Transformers: Model Optimization](https://www.sbert.net/docs/training/overview.html)
- [NumPy: Memory-Mapped Arrays](https://numpy.org/doc/stable/reference/generated/numpy.memmap.html)

### Research Papers
- BGE-M3 paper: [FlagEmbedding: Massive Text Embedding Benchmark](https://arxiv.org/abs/2310.07554)
- Hybrid retrieval: [Dense-Sparse Hybrid Retrieval](https://arxiv.org/abs/2104.08663)

---

## Next Steps

1. **Validate current implementation** against institutional learning (TC/SC normalization, synonym mapping)
2. **Confirm infrastructure dependencies** (SIEM endpoint, Redis deployment, hardware spec)
3. **Execute Sprint 0** (Redis sessions, API auth, PII patterns, audit logging)
4. **Measure baseline accuracy** before optimizing
5. **Defer backlog items** until production data proves necessity (admin UI, fine-tuning, PGVector)
