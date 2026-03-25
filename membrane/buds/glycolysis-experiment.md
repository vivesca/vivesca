---
name: glycolysis-experiment
description: Take the top glycolysis candidate and actually convert it. Measure before/after cost and latency.
model: sonnet
tools: ["Read", "Grep", "Glob", "Bash", "Edit", "Write"]
---

Experiment: convert one LLM dependency to deterministic and measure the result.

1. Run the glycolysis audit first:
   ```bash
   cd ~/code/vivesca && grep -rn "synthesize\|_acquire_catalyst\|llm\.query\|max20\|anthropic" src/ claude/hooks/ --include="*.py" | grep -v __pycache__
   ```

2. Classify each as Judgment/Classification/Formatting/Routing

3. Pick the TOP candidate (highest frequency x lowest complexity)

4. Build the deterministic replacement:
   - What data is available without the LLM?
   - What heuristic covers 80%+ of cases?
   - Keep LLM as fallback for edge cases

5. Implement the conversion (edit the file)

6. Run tests: `cd ~/code/vivesca && uv run pytest tests/ -x -q --tb=short --ignore=tests/test_moneo.py`

7. Measure (estimate):
   - Before: ~$X per call, ~Yms latency
   - After: $0, ~Zms latency
   - Coverage: N% of cases handled deterministically

8. Report the conversion and metrics

This agent DOES make changes (unlike the audit agent which only reports).
One conversion per run. Small, safe, testable.
