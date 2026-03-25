# LLM Agent Cost: The Quadratic Problem

**Source:** "Expensively Quadratic: The LLM Agent Cost Curve" (blog.exe.dev, Feb 2026)

## The Problem

Agent costs aren't linear — they compound. Each loop iteration re-reads the full conversation history from cache. Cost is roughly `tokens × number of calls`, not just `tokens`.

## Key Numbers (Anthropic pricing)

- Input: $5/M tokens
- Cache write: $6.25/M (1.25x)
- Cache read: $0.50/M (0.1x)
- Output: $25/M (5x)

**Threshold:** At just 20,000 tokens, cache reads already dominate total cost.

**Real example:** One feature implementation conversation cost $12.93. Cache reads were 87% of total cost by conversation's end.

**At scale:** Analysis of 250 conversations confirmed cache reads dominate across the board.

## Mitigations

1. **Fewer total calls** — batch tool outputs into single responses rather than spreading across multiple
2. **Sub-agents** — delegate iteration outside the main context window (fresh, smaller windows)
3. **Fresh conversations** — restarting can be cheaper than continuing, despite feeling wasteful
4. **Tool design** — return large outputs in single calls, not spread across many

## Relevance

Validates `/compact` discipline — proactive compaction at turn 3-4 is cost-optimal, not just a context hygiene habit. The math shows waiting until turn 8+ (when auto-prompted) means you've already paid the quadratic penalty for several rounds.

Also useful for Capco client conversations about agent deployment costs at scale.
