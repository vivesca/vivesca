---
name: what-if
description: Pick a random architectural decision in vivesca, explore the alternative path.
model: sonnet
tools: ["Bash", "Read", "Grep", "Glob"]
---

Adversarial design probe. Challenge one architectural decision in vivesca.

1. Read ~/germline/genotype.md and ~/germline/DESIGN.md (if exists)
2. Inventory key architectural decisions by reading:
   - ~/germline/membrane/buds/ — agent approach
   - ~/germline/membrane/cytoskeleton/ — hook consolidation
   - ~/germline/membrane/receptors/ — receptor pattern
   - Any README or design docs

3. Pick ONE decision at random (or the most load-bearing one if invoked with a topic)
   Examples:
   - "What if agents were functions instead of LLM calls?"
   - "What if hooks were replaced by event sourcing?"
   - "What if all memory lived in a database instead of markdown?"
   - "What if the MCP server didn't exist and everything was CLI?"

4. For the chosen decision, explore the alternative:
   - What would the system look like?
   - What would be better? What would be worse?
   - What does the original choice optimize for that the alternative sacrifices?
   - Does the original choice still make sense given current usage?

Output: the decision, the alternative, the honest trade-off analysis, and a verdict.
One architectural decision, fully examined. Not a list.
