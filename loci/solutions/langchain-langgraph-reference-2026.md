---
id: LRN-20260314-001
title: "LangChain/LangGraph Reference — March 2026"
date: 2026-03-14
tags: [langchain, langgraph, ai-frameworks, consulting]
---

# LangChain / LangGraph Reference — March 2026

Client-ready reference for the current state of LangChain and LangGraph as of March 2026. Claude's training data cuts off May 2025 — this was researched via web search.

## Architecture Flip (the key insight)

```
Pre-1.0 (2023-2024):
  langchain = monolith (everything lived here)
      └── langgraph = optional add-on for "advanced" graph workflows

Post-1.0 (Oct 2025):
  langgraph = the engine (core orchestration primitive)
      └── langchain = convenience layer built ON TOP of langgraph
```

The dependency arrow flipped. LangChain's agents now run on LangGraph internally. `AgentExecutor` is gone — replaced by `create_agent` which is a LangGraph graph under the hood.

**Old advice ("start with LangChain, graduate to LangGraph") is backwards now.**

## Dependency Relationship

```
langchain (full package)
    ├── langchain-core  ← shared base (message types, runnables, tool interfaces)
    ├── agents now run on LangGraph internally
    └── langchain-classic  ← legacy compat (escape valve, not the path forward)

langgraph (standalone — does NOT require full langchain)
    ├── langchain-core  ← required, can't avoid (lightweight)
    ├── langgraph-checkpoint  ← persistence layer
    ├── langgraph-sdk
    └── langgraph-prebuilt
```

## Version Status

| Package | GA Date | Current Version | Stars |
|---------|---------|-----------------|-------|
| LangGraph | Oct 2025 | v1.1.2 (Mar 12, 2026) | 26.3K |
| LangChain | Oct 2025 | 1.0 | — |

Both have a stability pledge: no breaking changes until 2.0. First time this has been true — pre-1.0 history had breaking changes in minor releases.

## When to Recommend LangGraph

**Use LangGraph when:**
- Complex stateful workflows with cycles, conditional branching, or parallel agent execution
- Human-in-the-loop is a hard requirement (compliance review, approval gates)
- Long-running, resumable processes (multi-day workflows, async)
- Engineering team comfortable with graph/state-machine mental models
- Need production-grade observability (LangSmith integration is best-in-class)
- Platform-scale needs (BlackRock/JPMorgan pattern)

**Don't use LangGraph when:**
- Linear or batch pipeline, scheduled/cron — plain Python is faster and cheaper
- Non-engineers need to read/write agent definitions — CrewAI's role syntax wins
- Time-to-demo matters more than correctness — CrewAI again
- Data-sensitive on-prem constraint — LangSmith self-hosting requires Enterprise contract
- TypeScript team — Mastra is a better fit

**The framing:** "LangGraph is now the SAP of agent orchestration — powerful, battle-proven at enterprise scale, worth it if you're building a platform, but overkill for a single workflow. The question isn't 'is it production-ready?' (yes) — it's 'do you need a platform or a workflow?'"

## Competition Landscape (March 2026)

| Framework | Best For | Notes |
|-----------|----------|-------|
| **LangGraph** | Stateful, cyclic, complex multi-agent | Most battle-tested. Best observability. Steepest curve. |
| **CrewAI** | Linear multi-agent, fast prototyping | ~40% faster to deploy. Role-based syntax readable by non-engineers. |
| **PydanticAI** | Type-safe Python agents | v1 Sep 2025. Growing fast. No LangChain dependency. |
| **Mastra** | TypeScript teams | Replit: 80%→96% task success. Marsh McLennan: 75K employees. |
| **AutoGen / AG2** | Conversational multi-party debate | Microsoft shifted to maintenance mode. AG2 community fork active. |
| **Plain Python** | Batch/scheduled pipelines | Still the right answer for linear/cron workflows. |

Best production teams in 2026 mix frameworks — LangGraph for orchestration backbone, CrewAI for fast prototyping, bare Python for hot paths.

## Enterprise Adoption (FS-specific)

*Source: LangChain Interrupt 2025 conference — vendor-presented, not independently audited.*

- **BlackRock**: LangGraph orchestrating AI agents inside Aladdin ($11T AUM). 50+ engineering teams via plugin registry. Daily eval-driven dev with LangSmith.
- **JPMorgan**: "Ask David" multi-agent investment research. 95% reduction in research task time. LangGraph sub-agents for specialized data integration.
- **LinkedIn**: AI Hiring Agent on LangGraph.
- **Captide**: Investment research and equity modeling agents (smaller FinTech, independently verifiable).
- **Cisco, Uber, Klarna**: Non-FS large-scale production.

~400 companies using LangGraph Platform in production (vendor claim).

## Security — Two CVEs to Know

Both matter for FS client conversations:

1. **CVE-2025-64439** (CVSS 7.4): RCE in `langgraph-checkpoint` via `JsonPlusSerializer`. Untrusted user data in checkpoints → malicious deserialization. **Fixed in `langgraph-checkpoint==3.0.0`.** Patch immediately if on earlier version with user-controlled checkpoint data.

2. **CVE-2025-68664** (LangChain Core, Critical): 12 affected flows including event streaming, message history, logging.

**Talking point:** "LangGraph is production-ready, but two CVEs in 2025 — including an RCE — mean your model risk and security teams need to review the deployment before go-live. Standard vendor diligence, not a dealbreaker."

## LangSmith (Observability)

Optional but losing it means losing LangGraph's primary DX advantage.

| Tier | Price | Traces/month | Retention |
|------|-------|-------------|-----------|
| Developer (free) | $0 | 5,000 | 14 days |
| Plus | $39/seat/month | 10,000 base | 400 days |
| Enterprise | Custom | Custom | SSO/RBAC, self-hostable |

Features: step traces with token counts per node, replay failed runs, evaluation dashboards.

## LangGraph Platform (Deployment)

- Renamed: LangGraph Platform → **LangSmith Deployment** (Oct 2025)
- Pricing: $39/seat/month (Plus), ~$0.001/node executed on cloud
- Self-hosting: Enterprise plan only (NOT free) — important for on-prem FS clients
- Available on AWS Marketplace

## Sources

1. [LangChain & LangGraph 1.0 announcement](https://blog.langchain.com/langchain-langgraph-1dot0/)
2. [LangGraph on PyPI — v1.1.2](https://pypi.org/project/langgraph/)
3. [LangGraph on GitHub](https://github.com/langchain-ai/langgraph)
4. [LangGraph Platform pricing](https://www.langchain.com/pricing-langgraph-platform)
5. [CVE-2025-64439](https://www.resolvedsecurity.com/vulnerability-catalog/CVE-2025-64439)
6. [CVE-2025-68664](https://nvd.nist.gov/vuln/detail/CVE-2025-68664)
7. [HN: Agentic Frameworks in 2026](https://news.ycombinator.com/item?id=46509130)
8. [BlackRock production AI agents](https://blog.tmcnet.com/blog/rich-tehrani/ai/how-blackrock-orchestrates-11t-in-assets-with-production-ai-agents.html)
9. [JPMorgan "Ask David"](https://aibuilder.services/how-jp-morgan-built-an-ai-agent-for-investment-research-with-langgraph/)
10. [CrewAI vs LangGraph vs AutoGen — DataCamp](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)
11. [Open source agent frameworks compared 2026](https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared)
