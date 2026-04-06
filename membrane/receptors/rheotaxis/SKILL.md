---
name: rheotaxis
description: Web search CLI — 7 backends parallel, porin JSON output. Default search tool for all agents.
effort: low
user_invocable: false
platform: all
triggers:
  - search the web
  - look up online
  - find on the internet
  - current information about
  - web search
  - rheotaxis
---

# rheotaxis — Web Search

Multi-backend web search CLI. Runs 7 backends in parallel (~$0.03), returns structured results.
Primary search tool for all agents (CC, Codex, Gemini, Goose).

## Usage

```bash
# Default: 7 backends, porin JSON
rheotaxis "JINS glasses store Hong Kong Island"

# Human-readable markdown
rheotaxis "nearest gym Quarry Bay" --text

# Perplexity deep research (~$0.40) — use for complex questions
rheotaxis "HKMA policy on generative AI in banking" --research

# Skip backends (English-only query, skip Chinese search)
rheotaxis "rust async patterns" --exclude zhipu

# Only specific backends (fast, targeted)
rheotaxis "weather Hong Kong" -b serper,tavily

# Multi-query framing (triangulate)
rheotaxis "JINS Wan Chai" -q "JINS Hong Kong Island" -q "JINS store locator HK"

# Check backend health
rheotaxis --backends
```

## When to Use

- **Default search**: any "search for X", "look up X", "find X online"
- **Research mode** (`--research`): complex questions needing synthesis, deep analysis
- **Multi-query** (`-q`): when a single framing might miss results (locations, products, niche topics)
- **Exclude** (`--exclude zhipu`): English-only queries where Chinese results add noise

## When NOT to Use

- Academic papers: use `search_arxiv` or `search_ssrn` (Jina MCP)
- Content extraction from a known URL: use `pinocytosis` or `browse`
- AI landscape / model comparisons: use `noesis` (Perplexity with model-specific prompting)
- Past session recall: use `ecphory`

## Backends

| Backend | Type | Cost | Best for |
|---------|------|------|----------|
| grok | XAI chat + search | $0.05 | Current events, X/Twitter context |
| exa | Neural search | $0.01 | Entities, specific companies/people |
| perplexity | Sonar | $0.006 | Synthesized answers with citations |
| tavily | AI search API | Free | General web, includes direct answer |
| serper | Google SERP | Free | Local/maps, knowledge graph |
| zhipu | ZhiPu MCP | Free | Chinese-language content |
| jina | Jina search | Free | Broad web coverage |

## Output

Default: porin JSON envelope. Key fields in `result`:
- `backends[]`: per-backend answers and link results
- `health`: "N/M" backends succeeded
- `cost_usd`: total cost

Use `--text` for human-readable markdown (debugging, manual review).

## Integration

Preferred over `WebSearch` (CC built-in) and `mcp__jina__search_web`.
See `~/.claude/rules/search-preference.md`.
