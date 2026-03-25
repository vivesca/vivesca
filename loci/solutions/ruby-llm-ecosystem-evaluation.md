# Ruby LLM Ecosystem Evaluation

*Evaluated: 2026-02-23*

## RubyLLM (github.com/crmne/ruby_llm)

Unified Ruby interface for 11 LLM providers, 1,150+ models. One API, swap providers by changing a string.

- **Stars:** 3,592 | **Version:** 1.12.1 | **Age:** ~13 months
- **Deps:** 5 runtime (Faraday, Marcel, Zeitwerk, event_stream_parser, ruby_llm-schema)
- **Maintainer:** Single (Carmine Paolino, CEO of Chat with Work)
- **Scope:** Intentionally narrow — provider abstraction, streaming, tools, Rails integration. Explicitly excludes RAG, prompt templates, vector DBs, multi-agent orchestration.

**Strengths:** Clean provider abstraction, Rails-native DSL (`acts_as_chat`, generators), fluent builder API, streaming first-class, 1,150-model registry with pricing/capabilities, battle-tested in production.

**Weaknesses:** Single maintainer (bus factor 1), 64 open issues (some critical), breaking changes between minors (v1.7→1.10 all needed upgrade generators), some providers thin (xAI/Perplexity = basic chat only).

**Verdict:** Adopt for Rails AI projects. Best-in-class for adding LLM features to existing Rails apps. Pin versions carefully.

## ruby_llm-skills (github.com/kieranklaassen/ruby_llm-skills)

Extension implementing Agent Skills spec (open standard used by Claude, Codex, Gemini).

- **Stars:** 24 | **Version:** 0.3.0 | **Age:** 39 days
- Progressive disclosure (metadata ~100 tokens, full instructions ~5K on demand)
- Flexible sources: filesystem, database, zip archives, composite
- Rails integration: Railtie, generator, convention (`app/skills/`)

**Verdict:** Watch, not adopt. Architecture is solid but too new (39 days, pre-v1.0). Revisit at v1.0.

## Ruby's Relevance for AI Work (2026)

**Still strong:** CRUD/internal tools, startups shipping fast, solo devs. Rails remains fastest idea→production for web apps.

**Lost ground:** AI/ML (Python owns completely), high-concurrency (Go/Rust), frontend-heavy (TypeScript/Next.js), new dev mindshare (shrinking hiring pool).

**Key insight:** RubyLLM is an HTTP API wrapper — you don't need Python to call LLM APIs. If the app is Rails and AI is a feature, Ruby is fine. If AI is the product (fine-tuning, embeddings pipelines, RAG, eval frameworks), Python is the only serious choice. The ecosystem gap is a chasm.

**For consulting (Capco context):** Python is the lingua franca. Ruby knowledge is nice-to-have for specific client engagements, not a strategic investment.
