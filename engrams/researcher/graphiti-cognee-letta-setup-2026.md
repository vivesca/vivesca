---
name: Graphiti / Cognee / Letta practical setup research (Mar 2026)
description: PyPI versions, local LLM support, backends, install commands, MCP servers for all three temporal memory / knowledge graph libraries
type: reference
---

## Graphiti (getzep/graphiti)
- **PyPI:** `graphiti-core` v0.28.2 (released Mar 11, 2026) — latest is security fix (Cypher injection hardening)
- **Python:** >=3.10, <4
- **Install:** `pip install graphiti-core` (base: requires Neo4j or Kuzu)
- **Kuzu extra:** `pip install graphiti-core[kuzu]` — embedded, no separate server, single-file DB
- **Other extras:** `falkordb`, `neptune`, `neo4j-opensearch`, `anthropic`, `groq`, `google-genai`, `sentence-transformers`, `voyageai`
- **Kuzu driver code:** `from graphiti_core.driver.kuzu_driver import KuzuDriver; KuzuDriver(db='/path/to/file.kuzu')` — defaults to `:memory:` if env var `KUZU_DB` not set
- **Neo4j minimum:** Neo4j 5.26+; bolt://localhost:7687; also needs APOC plugin
- **LLM:** OpenAI by default. Ollama works via `OpenAIGenericClient` (NOT `OpenAIClient` — Ollama lacks /v1/responses endpoint). `LLMConfig(api_key="ollama", model="deepseek-r1:7b", base_url="http://localhost:11434/v1")`. Docs warn: avoid small models, they fail JSON extraction.
- **Embeddings:** OpenAI (default), Voyage AI, sentence-transformers (`pip install graphiti-core[sentence-transformers]`), Gemini. Ollama embeddings work via OpenAI-compatible endpoint (no dedicated extra needed).
- **MCP server:** Official MCP is in the `mcp_server/` dir of the monorepo. Tagged release `mcp-v1.0.2` (Mar 11, 2026). No standalone PyPI package from Zep — run from source or use community packages. Community options: `montesmakes.graphiti-memory` on PyPI (`uvx montesmakes.graphiti-memory`), `graphiti-memory` on PyPI.
- **help.getzep.com:** WebFetch works well on specific doc pages. Use direct sub-page URLs.
- **GitHub rate limit 429 on WebFetch** — hit it on mcp_server/README.md. Use WebSearch for MCP README content.

## Cognee (topoteretes/cognee)
- **PyPI:** `cognee` v0.5.4 (released Mar 10, 2026)
- **Python:** >=3.10, <3.14
- **Install base:** `pip install cognee` — defaults to SQLite + LanceDB + Kuzu locally (no Neo4j required by default)
- **Ollama extras:** `pip install "cognee[ollama]"` + `pip install "cognee[baml]"` (BAML needed for structured output framework with local LLMs)
- **Fully local stack:** SQLite (relational) + LanceDB (vector) + KuzuDB (graph) + Ollama (LLM + embeddings) — zero cloud keys
- **Env vars for full local:** `LLM_PROVIDER=ollama`, `LLM_MODEL`, `LLM_ENDPOINT=http://localhost:11434/v1`, `EMBEDDING_PROVIDER=ollama`, `EMBEDDING_MODEL`, `EMBEDDING_ENDPOINT=http://localhost:11434/api/embeddings`, `EMBEDDING_DIMENSIONS`, `DB_PROVIDER=sqlite`, `VECTOR_DB_PROVIDER=lancedb`, `GRAPH_DATABASE_PROVIDER=kuzu`
- **WARNING:** "If you configure only LLM or only embeddings, the other defaults to OpenAI" — must set both explicitly
- **STRUCTURED_OUTPUT_FRAMEWORK=BAML** required when using Ollama for LLMs
- **MCP server:** `cognee-mcp` package — lives at `cognee/cognee-mcp/` in the monorepo. Install from source with uv or via Docker. Claude Code MCP: `claude mcp add cognee-sse -t sse http://localhost:8000/sse`
- **docs.cognee.ai:** WebFetch works on specific pages. Default page returns sparse content — use sub-page URLs.

## Letta (letta-ai/letta, formerly MemGPT)
- **PyPI:** `letta` v0.16.6 (released Mar 4, 2026). Client SDK: `letta-client` (separate package)
- **Python:** >=3.11, <3.14
- **Architecture note:** Letta is a SERVER + client SDK model. You run a server (Docker or pip), then interact via REST API or Python SDK. It is NOT a drop-in memory module — it's a stateful agent runtime.
- **Pip install (no Docker):** `pip install letta` then `letta server` — starts at http://localhost:8283. Defaults to SQLite at `~/.letta/letta.db` + sqlite-vec for embeddings. WARNING: SQLite migrations between versions not officially supported; use Postgres for production.
- **Docker (recommended):** `docker run -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data -p 8283:8283 -e OPENAI_API_KEY=... letta/letta:latest` — uses Postgres by default
- **Ollama:** Set `OLLAMA_BASE_URL=http://host.docker.internal:11434/v1` (Docker macOS) or `http://localhost:11434/v1` (pip/Linux). Then specify `model="ollama/<model-tag>"` and `embedding="ollama/<embed-model>"` when creating agents.
- **REST API:** `http://localhost:8283/v1` — full OpenAPI spec. Client SDK: `pip install letta-client`
- **Memory model:** Agents have persistent "memory blocks" (label/value pairs in context window). No separate "store a fact" API — you add to blocks at agent creation or update via `client.agents.blocks.update()`. Archival (long-term) memory uses vector search internally.
- **Standalone memory service caveat:** Letta is NOT a library you call like `mem0.add()`. Every memory operation goes through a Letta agent. If you want pure memory storage without agent orchestration, Letta is overbuilt — use Mem0 instead.
- **MCP:** No official Letta MCP server found as of Mar 2026. REST API is the integration path.

## Source access patterns
- `pypi.org/project/<name>/` — WebFetch works cleanly, returns version, Python req, extras
- `help.getzep.com/graphiti/*` — WebFetch works on specific sub-pages
- `docs.letta.com/*` — WebFetch works on some pages; Docker guide returns good content; pip guide returns sparse. Use WebSearch to surface the right sub-page URL first.
- `docs.cognee.ai/*` — WebFetch works on sub-pages (overview, embedding-providers, quickstart)
- `github.com/getzep/graphiti/blob/main/*` — 429 rate limit hit; use WebSearch for content
- `github.com/topoteretes/cognee/releases` — WebFetch works
- `dev.to` Cognee articles — WebFetch works well, good practical examples
