---
name: elencho
description: Parallel AI research — runs query through all search tools (Grok, Exa, noesis), synthesises agreements and disagreements. For factual research, not opinions.
user_invocable: false
platform: all
triggers:
  - elencho
  - parallel research
  - multi-tool research
  - cross-check sources
---

# elencho — Parallel AI Research Orchestrator

Run a research query through ALL available AI tools in parallel, then synthesise — highlighting agreements, disagreements, and unique findings.

**Absorbed into vivesca** (2026-04-03). Available as:
- MCP tool: `mcp__vivesca__elencho` (query, mode=cheap|full)
- CLI: `cd ~/code/elencho && uv run elencho "query"` (original, with rich output)
- Enzyme: `~/germline/metabolon/enzymes/elencho.py`

Principle: **redundancy is insurance.** Running all tools costs ~$0.07 (cheap) / ~$0.50 (full) but catches errors any single tool would miss.

## Commands

```bash
# Standard research (all tools including noesis research ~$0.40)
elencho "What is the HKMA policy on generative AI?"

# Cheap mode — skip noesis research (saves ~$0.40, total ~$0.07)
elencho --cheap "quick question about Python packaging"

# Save to file
elencho "HKMA AI guidelines" -o output.md
```

## Tools Used

| Tool | Cost | Latency | What it's good at |
|------|------|---------|-------------------|
| Grok | ~$0.05 | ~30-45s | Recency, web search, X/Twitter |
| Exa | ~$0.01 | ~2-5s | Paper/source discovery |
| Noesis search | ~$0.006 | ~6-10s | Cited search results |
| Noesis research | ~$0.40 | ~180s | Deep comprehensive research (skipped with --cheap) |
| WebSearch | free | — | Skipped when called from Claude Code (nested session issue) |

## Output

Markdown report with:
- **Consensus** — what all tools agree on (high confidence)
- **Disagreements** — where tools conflict (flag for review)
- **Unique findings** — what only one tool found (unverified)
- **Confidence level** — overall assessment
- **Citations** — ranked by cross-tool agreement
- **Tool performance** — latency, cost, status per tool

## When to Use

- Any research where you want multiple perspectives
- Consulting research where accuracy matters
- Calibrating tool reliability on a new domain
- When a single tool gave a surprising answer — verify with all tools

## When NOT to Use

- Simple factual lookups (just use Grok or noesis search directly)
- X/Twitter specific search (use `grok --x-only`)
- Time-critical queries where 30s+ latency is too much

## Architecture

- Python CLI at `~/code/elencho/` (synced to soma 2026-04-03)
- Each tool is an async module in `src/elencho/tools/`
- `asyncio.gather()` runs all tools in parallel
- Synthesis via OpenRouter API (Claude Sonnet) using `OPENROUTER_API_KEY` from keychain
- All tool failures are graceful — never crashes the pipeline

## Gotchas

- **WebSearch stub**: Can't run nested Claude Code sessions. Grok covers web search.
- **noesis research is slow**: 2-3 minutes. Use `--cheap` for quick queries.
- **OpenRouter key required**: Reads from keychain (`openrouter-api-key`) or `OPENROUTER_API_KEY` env var.
- **Synthesis cost**: ~$0.01-0.02 per synthesis via OpenRouter (Claude Sonnet).
- **Running from outside Claude Code**: WebSearch could potentially work via `claude --print` if not nested.

## Calls

- `grok` — web search + X/Twitter
- `exauro` — neural search / paper discovery (archived at `effectors/.archive/exauro`)
- `noesis` — cited search + deep research (external tool, not installed locally)
- `stips` — OpenRouter credits check (external tool, not installed locally)
