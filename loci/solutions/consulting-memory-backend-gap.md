# Why Nobody Has Answered "Which AI Memory Backend?" — LRN-20260313-001

## The Gap

No independent, practitioner-level answer exists for "which AI agent memory backend should I recommend to enterprise clients?" As of Mar 2026:

- **Vendor benchmarks** (Mem0, Zep, Letta, Cognee) are all self-serving — each uses baselines that make themselves look best. Zep published a rebuttal showing Mem0's benchmark had implementation bugs.
- **Academic benchmarks** (MemoryAgentBench ICLR 2026, AMA-Bench) use synthetic data only, and cover 2-3 commercial backends max. Zep/Graphiti and Letta appear in zero academic benchmarks.
- **No in-situ study exists** — nobody has run multiple backends under real workload for any duration.

## Why the Gap Exists

1. **PhD incentive mismatch** — comparison papers without a novel system don't get top-venue credit
2. **Timing** — most frameworks only became installable mid-2025
3. **Ops barrier** — running 10 backends needs real infra + API keys, not "1 GPU in a notebook"
4. **Consulting firms won't publish** — the answer is the deliverable ($200K engagement)
5. **Cloud vendors won't publish** — Google/Anthropic/OpenAI build competing memory layers

## Consulting Implications

- The practitioner who has independently tested multiple backends has genuine differentiation
- "It depends" is currently the only honest answer — the mnemon experiment aims to turn it into "it depends on X, and here's the data"
- Most valuable finding may be: "a well-maintained markdown file gets you 90% of the way"

## Key References

- Full landscape: `ai-agent-memory-landscape-2026.md`
- MemoryAgentBench (ICLR 2026): arxiv:2507.05257
- Zep's Mem0 rebuttal: blog.getzep.com/lies-damn-lies-statistics
- Agent Memory Paper List: github.com/Shichun-Liu/Agent-Memory-Paper-List
