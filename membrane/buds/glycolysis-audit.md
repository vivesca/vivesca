---
name: glycolysis-audit
description: Scan for LLM calls that could be deterministic. Identify symbiont-to-cytosol conversion opportunities.
model: sonnet
tools: ["Read", "Grep", "Glob", "Bash"]
---

Audit the organism for glycolysis opportunities -- reactions currently requiring the symbiont (LLM) that could run deterministically in the cytosol.

1. Scan for LLM call patterns across the codebase:
   ```bash
   cd ~/code/vivesca && grep -rn "synthesize\|_acquire_catalyst\|llm\.query\|max20\|anthropic\|_llm_query\|llm_call" src/ claude/hooks/ --include="*.py" | grep -v __pycache__
   ```

2. For each call site, classify:
   - **Judgment** -- needs language, creativity, taste. STAYS LLM.
   - **Classification** -- maps input to categories. GLYCOLYSIS CANDIDATE.
   - **Formatting** -- structured output from structured input. GLYCOLYSIS CANDIDATE.
   - **Routing** -- decides where to send. GLYCOLYSIS CANDIDATE.

3. Output a table:
   | File:Line | Current | Type | Cost/call | Conversion approach |
   |-----------|---------|------|-----------|-------------------|

4. Rank by frequency (how often does this fire?) x cost (how much per call?).

5. For the top 3 candidates, sketch the deterministic replacement:
   - What data is available without the LLM?
   - What heuristic covers 80%+ of cases?
   - What's the fallback for edge cases?

The glycolysis principle: less efficient labeling but zero latency, zero cost, zero failure modes. The cytosol gets stronger.
