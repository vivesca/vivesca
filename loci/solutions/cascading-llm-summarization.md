# Cascading LLM Summarization

Pattern for distilling large corpora through layered LLM processing. Built and validated on the Waking Up transcript corpus (1,314 transcripts, 5M tokens, 54 teachers).

## Architecture

```
Raw content (5M tokens)
  → Layer 1: Per-item digests (~130K tokens total)
    → Layer 2: Per-group guides (reads digests, not raw)
      → Layer 3: Cross-corpus themes (reads digests)
      → Layer 4: Specialized extraction (reads digests)
```

**Key insight:** Each layer reads the *previous layer's output*, never the raw source. This compresses the input dramatically — Layer 2+ operates on ~130K tokens instead of 5M.

## Patterns

### Idempotency via content detection
Check for output markers in the file itself (`\n## Digest\n` in content) rather than maintaining external state (database, sidecar files). Zero infrastructure, survives manual edits, works across sessions. Re-running skips already-processed items by default; `--force` flag to regenerate.

### Two-pass chunking for large collections
When a single group has >50 items (e.g. Jonah Primo: 212 transcripts), chunk into groups of ~50, summarize each chunk, then synthesize from chunk summaries. Avoids quality degradation from overwhelming the context window with too many items at once.

### LLM JSON trailing comma fix
LLMs trained on both JSON and JavaScript frequently emit trailing commas (`[1, 2,]`). Python's `json.loads()` rejects these. One-line fix:
```python
text = re.sub(r",\s*([}\]])", r"\1", text)
data = json.loads(text)
```
Apply to **all** LLM JSON parsing pipelines. Validated across 1,314+ Gemini calls — this specific pattern caused the only failure in the entire corpus run.

### Tradition/category dedup as hardcoded mapping
67 raw labels → 12 canonical groups via a simple `dict[str, str]`. No NLP, no fuzzy matching — just manual curation. For domain-specific taxonomies with <100 labels, a hardcoded dict is faster to build, easier to debug, and more reliable than any automated approach.

### Two-phase theme extraction
Phase A: Send all compact summaries to LLM, ask for theme list with transcript assignments (analytical/clustering task).
Phase B: For each theme, send only the relevant digests and generate a rich synthesis note (generative/writing task).
Splitting analysis from generation produces better results than trying to do both in one call.

## Cost Profile (Gemini 3 Flash free tier)

| Layer | Items | Tokens in | Tokens out | Cost | Time |
|-------|-------|-----------|------------|------|------|
| Digests | 1,314 | ~5M | ~500K | $0 | 18 min (c=5) |
| Guides | 60 | ~200K | ~120K | ~$0.50 | 12 min |
| Themes | 15 | ~150K | ~60K | ~$0.10 | 5 min |
| Practice | 1 | ~80K | ~8K | ~$0.05 | 1 min |
| **Total** | | | | **~$0.65** | **~36 min** |

## When to use this pattern

- Corpus too large for single-context synthesis (>100K tokens)
- Need both per-item detail AND cross-item synthesis
- Items share a common structure (transcripts, articles, reviews, docs)
- Output goes to a file-based system (vault, docs, wiki)
