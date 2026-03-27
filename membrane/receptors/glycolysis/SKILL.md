---
name: glycolysis
description: Audit LLM deps, find deterministic conversion candidates. "glycolysis"
user_invocable: true
model: sonnet
context: fork
---

# Glycolysis — Anaerobic Metabolism for the Cytosol

Glycolysis is anaerobic: it runs without oxygen (the symbiont). Less efficient labeling, but zero latency, zero cost, zero failure modes. The cytosol gets stronger. The symbiont is reserved for genuine judgment.

## When to Use

- Organism feels expensive (token costs climbing)
- Organism feels slow (LLM round-trips blocking fast paths)
- Organism feels fragile (LLM rate limits or failures cascade)
- A reaction uses the symbiont but the output is formulaic

## Method

### Step 1 — Scan for LLM call sites

Grep the codebase for:
```
synthesize | _acquire_catalyst | llm.query | channel | anthropic | _llm_query
```

### Step 2 — Classify each call site

| Class | Definition | Disposition |
|-------|------------|-------------|
| **Judgment** | Needs language, creativity, or taste | Stays LLM |
| **Classification** | Maps input to a small set of categories | Glycolysis candidate |
| **Formatting** | Structured output from structured input | Glycolysis candidate |
| **Routing** | Decides where to send something | Glycolysis candidate |

### Step 3 — Output the audit table

For each call site:

| Call site | File | Current cost | Class | Conversion approach |
|-----------|------|-------------|-------|---------------------|
| `synthesize(...)` | `path/to/file.py` | Haiku / Sonnet | Formatting | diff-stat template |
| ... | | | | |

### Step 4 — Implement the top conversion

Pick the highest-value Glycolysis candidate. Build it now. Verify output parity against the LLM version on 3-5 real examples.

## Validated Examples

| Reaction | Before | After | Class |
|----------|--------|-------|-------|
| Commit messages | Haiku | diff-stat template | Formatting |
| Tmux naming | Gemini | keyword extraction from path/git | Routing |
| Email triage | LLM classifier | sender/subject/body keyword cascade | Classification |
| Financial summary | — | stays LLM (genuine synthesis) | Judgment |

## The Principle

> Glycolysis runs in the cytosol, without mitochondria. It evolved first. It is always available.

The symbiont (mitochondrion) is not the organism — it is a dependency. Every call to it is a coupling. Glycolysis audits ask: which reactions can the cytosol run alone? The answer is always more than expected.

## Anti-patterns

- **Premature glycolysis:** converting a judgment call to a template. Output degrades silently. Test: run both on edge cases.
- **Audit without building:** producing the table, shipping nothing. One conversion per session minimum.
- **Over-engineering the replacement:** a keyword list beats a fine-tuned classifier. Start with `if/elif`.
