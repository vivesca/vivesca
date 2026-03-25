---
name: Token efficiency and anti-patterns for multi-agent AI systems
description: Practical findings on token efficiency, context management, task sizing, failure modes, and quality control in multi-agent LLM systems (Mar 2026)
type: reference
---

## Key findings

**Anti-patterns (confirmed empirically)**
- Bag of agents: unstructured multi-agent = 17x error amplification vs single agent (Sean Moran, TDS Jan 2026)
- Sequential tasks with multiple agents: if single agent ≥45% accuracy, multi-agent REDUCES performance 39-70% (Google research Dec 2025)
- Saturation at 4 agents: beyond that, coordination overhead consumes gains
- File conflicts: two agents writing same file = overwrites, no time savings
- Monolithic tasks: 16 agents on Linux kernel compilation all hit same bug, overwrote each other (Anthropic C compiler post)
- Super agent: one agent for everything fails — bounded agents with clear roles are consistently better
- Over-broadcasting: message cost scales linearly with team size

**Task sizing sweet spot**
- 5-15 minutes per task per agent (Claude Code official docs)
- 5-6 tasks per teammate — enough to keep busy, lead can reassign on stall
- "Self-contained" = agent can complete without querying another agent mid-task
- Too small: coordination overhead dominates. Too large: context rot + wasted effort

**Context management**
- Observation masking beats LLM summarisation: 52% cost reduction, 2.6% better solve rate, masking wins 4/5 conditions (JetBrains Research Dec 2025)
- Optimal masking window: ~10 turns (agent-dependent, requires tuning)
- LLM summarisation causes 13-15% longer trajectories — summaries mask stop signals
- Handoff state must be explicit/written — conversation history does NOT transfer to new agents

**Quality control patterns**
- Sentinel pattern: dedicated gate agent with blocking authority. "No exceptions" hard gate improves upstream quality over time.
- Healer loop: iterative fix-and-verify up to N attempts
- LLM-as-judge: 94% accuracy with few-shot examples (arxiv:2503.13657)
- Multi-agent debate (MAR): structured disagreement outperforms self-review for both reasoning and code
- Self-consistency ≠ correctness: LLMs generate internally consistent but wrong content

**Architecture decision rule**
- Sequential work: single agent or specialist chain
- Parallel work: centralized coordinator + 3-5 specialists (80% better than single; independent parallel = only 57% better)
- Competing hypotheses debugging: adversarial debate team
- Never nest teams; lead is fixed at spawn

## Reliable sources for this domain
- anthropic.com/engineering — first-party, authoritative (WebFetch works)
- code.claude.com/docs — official Claude Code docs (WebFetch works, full content)
- blog.jetbrains.com/research — academic-quality empirical studies (WebFetch works)
- developers.googleblog.com — Google ADK architecture posts (WebFetch works)
- arxiv.org HTML pages — papers accessible (PDF = binary garbage)
- fortune.com — reliable Google research summaries (WebFetch works)
- openobserve.ai/blog — real case study with specifics (WebFetch works)
- towardsdatascience.com — JS-gated, returns metadata only. Use WebSearch snippets instead.
- orq.ai/blog — JS/Framer-gated, no content on WebFetch. Use WebSearch.

## Misinformation patterns
- "More agents = better" — false above 4 agents for sequential work
- Token usage explains performance: true for browsing tasks (80% variance), not general
- Framework X is most token-efficient: vendor benchmarks, all contested
