# vivesca

An information metabolism engine. Every text fragment loaded into an LLM's context window is energy — tokens consumed, output influenced, budget spent. Vivesca applies continuous selection pressure so that energy is never wasted.

MCP server is one interface. The metabolism is the identity.

<!-- mcp-name: org.vivesca/vivesca -->

## Install

```bash
uv add vivesca
```

## What it provides

- **25 tools** across 8 domains — messaging, search, calendar, memory, browser, health, metabolism
- **Structured output** — every tool returns Pydantic models with `outputSchema`
- **Metabolism engine** — signal collection, fitness computation, variant evolution, promotion gates
- **4 resources** — budget, calendar, search log, memory stats
- **3 prompts** — research, draft message, morning brief

## Hypothesis

Should LLM systems manage their own context? Vivesca tests whether they should, and how.

**Claim:** Every text fragment in an LLM's context is energy under selection pressure. Continuous metabolism — governed by taste, not just metrics — outperforms manual optimization.

**Predictions:**
- Frequency-based pruning creates fragile systems (constitutive knowledge looks unused but is load-bearing)
- Taste-based fitness outperforms pure token efficiency metrics
- Systems that metabolize all loaded text outperform systems that optimize only some

**Status:** Hypothesis with one implementation, zero external validation. The signals accumulating now are the first real data.

## Philosophy

Tokens are energy. Text is mass. Taste decides how to spend it. The rest is plumbing.

Read the trilogy:
1. [The Missing Metabolism](https://terryli.hm/posts/the-missing-metabolism) — tools need evolution
2. [Taste Is the Metabolism](https://terryli.hm/posts/taste-is-the-metabolism) — taste is the organizing principle
3. [Everything Is Energy](https://terryli.hm/posts/everything-is-energy) — one equation

[vivesca.org](https://vivesca.org)
