# Docima Backend Gotchas

> LRN-20260317-001: Operational findings from benchmarking 10 AI agent memory backends.

## Working Backends (7/10)

### markdown (baseline)
- Pure keyword matching, zero dependencies. 79% recall.
- Word-overlap scoring (split query into words, match any). Not substring.

### langmem (LangGraph InMemoryStore)
- Best framework backend: 89% recall, 13ms query, 400ms ingest.
- Uses SQLite for persistence + sentence-transformers for embeddings.
- Sweet spot: nearly raw-DB recall at framework convenience.

### sqlite-vec, pgvector, neo4j (raw vector DBs)
- All hit 100% recall. Backend choice doesn't matter — embedding model does the work.
- Ingest is slow (~28s for 53 facts) because each fact requires an API embedding call.
- pgvector needs Docker (`ankane/pgvector`), neo4j needs Docker (`neo4j:5`).

### memoryscope
- TF-IDF keyword scoring, JSON file storage. 68% recall.
- CJK-aware tokenisation. No external dependencies.

### mem0
- **Bug fixed (Mar 2026):** `client.search()` returns `{'results': [...]}` but backend iterated over dict keys, not the results list. Each "result" was the string `'results'`, mapped to empty Memory.
- Consolidates facts during ingestion (53→32). 57% recall after fix.
- 700s ingest for 53 facts — each add() calls LLM for entity extraction + dedup.
- Qdrant dimension mismatch: old collections persist with wrong dims. `rm -rf ~/.local/share/docima/mem0/` to fix.
- `embedding_model_dims` must be set in BOTH embedder config AND vector_store config.

## Blocked Backends (3/10)

### graphiti — Architectural Mismatch
- **Root cause:** `add_episode()` silently fails because graphiti internally calls OpenAI SDK directly (not the configured LLM client) for entity deduplication and community detection. With no valid `OPENAI_API_KEY`, these calls 429 and the exception is swallowed.
- Setting `OPENAI_API_KEY` to OpenRouter key + `OPENAI_BASE_URL` to OpenRouter doesn't work — graphiti's internal pipeline expects specific OpenAI model behaviour.
- Even when add works, `search()` queries graph edges (entity→relationship→entity), not text chunks. Single-sentence facts don't produce meaningful entity graphs.
- **Verdict:** Graphiti is designed for conversation-length inputs and OpenAI's ecosystem. Not compatible with docima's single-fact benchmark pattern or non-OpenAI LLMs without significant patching.

### cognee — Python 3.13 Incompatibility
- **Root cause:** `sqlalchemy.exc.StatementError: 'str' object has no attribute 'hex'` — cognee's SQLAlchemy ORM expects UUID objects but passes strings on Python 3.13.
- Also: SQLite database locking under concurrent access when cognifying 53 facts.
- Also: `prune_data()` + `prune_system()` in `clear()` breaks subsequent `cognify()`. Fixed by making `clear()` a no-op and using fresh temp dirs.
- Also: Gemini models trigger `ContentPolicyFilterError` on structured output via litellm's instructor integration. DeepSeek V3.2 via OpenRouter works for LLM, but the UUID bug blocks before we get there.
- **Verdict:** Wait for cognee to support Python 3.13 or test on Python 3.12.

### letta — External Service Down
- **Root cause:** `letta-free` hosted embedding endpoint returns 404. The Docker container only has `letta-free` model available — can't configure custom embeddings.
- Agent creation works (`model='letta/letta-free'`), but `passages.create()` fails with 500 when trying to embed the text.
- **Verdict:** External dependency. Will work when Letta fixes their endpoint. No local workaround without deeper Docker configuration.

## Benchmark Harness Lessons

- **`clear()` is dangerous for framework backends.** Mem0/cognee/graphiti all break when `clear()` is called before re-ingestion. Use fresh temp dirs instead.
- **`finalize()` hook needed for batch-processing backends.** Cognee requires `cognify()` between add and query. Added `finalize()` to the backend interface.
- **Exact string matching fails for framework backends.** Mem0 consolidates facts, graphiti extracts entities. Token-overlap matching (Jaccard on word sets) handles this.
- **Framework backends are 25-100x slower.** 700-800s vs 28s for raw vector DBs. Each fact requires LLM API calls.
- **Silent exception swallowing is the #1 debugging obstacle.** Graphiti's `except: pass` on `add_episode()` hid the real error for hours. Always log exceptions.

## Model Configuration

Standardised setup (Mar 2026):
- **Embeddings:** Gemini embedding-001 (MTEB #1, free, 3072 dims) via `docima.embeddings`
- **LLM (entity extraction):** DeepSeek V3.2 via OpenRouter ($0.32/M tokens, intelligence 42)
- **Exception:** Cognee needs gpt-4o-mini for structured output (Gemini triggers content policy filter)
- **Default embedding override:** `--embed-model` flag or `DOCIMA_EMBED_MODEL` env var
