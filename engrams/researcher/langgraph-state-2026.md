---
name: LangGraph & LangChain State (March 2026)
description: Current state of LangGraph 1.x and LangChain 1.x as of Mar 2026 — API, dependencies, competition, enterprise adoption, security, practitioner sentiment
type: reference
---

## Versions & Releases
- LangGraph 1.0 GA: October 2025 (some sources say Nov 2025 — same release wave). Current: v1.1.2 (Mar 12 2026).
- LangChain 1.0 GA: October 2025.
- Both pledged no breaking changes until 2.0.
- Pre-1.0 history was chaotic (pre-2025 criticism is largely stale).
- Python >=3.10 required (3.9 dropped at EOL Oct 2025).

## LangGraph 1.0 API Changes
- Core graph primitives (state, nodes, edges) unchanged from pre-1.0 — upgrade is safe.
- `create_react_agent` from langgraph.prebuilt DEPRECATED → replaced by LangChain's `create_agent`.
- Durable execution, checkpointing, HITL, streaming: all first-class and stable.
- LangGraph 1.1 added version="v2" opt-in streaming with full type safety.

## LangChain 1.0 Changes
- New `create_agent` abstraction (wraps LangGraph under the hood).
- Middleware system for HITL, PII redaction, summarization.
- Legacy functionality → `langchain-classic` package.
- Reduced surface area — the 2023-2024 "abstraction hell" criticism was addressed.
- From 1.0: the ONLY way to define agents in LangChain is `create_agent` (no more AgentExecutor).

## Relationship Between LangGraph and LangChain
- LangGraph is standalone: `pip install langgraph` — does NOT require full `langchain` package.
- BUT: `langgraph` pulls in `langchain-core` as a dependency (the shared base abstraction layer). Cannot avoid `langchain-core`.
- Full `langchain` package is NOT required. You can use LangGraph with zero LangChain imports.
- LangChain agents run on LangGraph internally — composable upward and downward.
- 26.3K GitHub stars (Mar 2026).

## LangGraph Platform / Deployment (renamed LangSmith Deployment Oct 2025)
- LangGraph Platform was renamed to LangSmith Deployment as of October 2025.
- Pricing: LangSmith Plus $39/seat/month, includes 1 free dev deployment.
- Node execution billing: ~$0.001 per node executed on cloud.
- Self-hosting: only via Enterprise custom pricing — NOT free.
- ~400 companies using LangGraph Platform in production (vendor claim).
- Available on AWS Marketplace.

## LangSmith (Observability)
- Completely OPTIONAL — LangGraph works without it.
- Free Developer tier: 5K traces/month, 1 seat, 14-day retention.
- Plus: $39/seat/month, 10K traces/month, 400-day retention, unlimited seats.
- Enterprise: custom, self-hostable, SSO/RBAC.
- The debugging story (step-by-step traces with token counts, replay from UI) is a genuine differentiator vs alternatives.

## Security Issues (2025)
- CVE-2025-64439: RCE in langgraph-checkpoint via JsonPlusSerializer deserialization. CVSS 7.4.
  Fixed in langgraph-checkpoint==3.0.0. Requires untrusted data to be persisted into checkpoints.
- CVE-2025-68664: Critical LangChain Core vulnerability via serialization injection (12 vulnerable flows).
- Enterprise red flag: if agent checkpoints process user-supplied data, patch immediately.

## Practitioner Sentiment (2025-2026)
- Consensus: LangGraph is the most production-mature framework for complex stateful multi-agent systems.
- The "death by abstraction" 2023-2024 critique applies less now — core API is stable and readable.
- Learning curve is real: need solid OOP + graph mental model upfront.
- Common gotcha: infinite loops with unmanaged sub-agents; token burn from poorly bounded cycles.
- Debugging advantage: state is always inspectable ("at any point I can see exactly what's in PipelineState").
- LangSmith traces are considered best-in-class for agent observability.
- Vendor lock-in concern persists: LangGraph Platform pricing model vs self-hosting trade-off.

## Competition Landscape (2026)
| Framework | Verdict |
|-----------|---------|
| **CrewAI** | Best time-to-production for linear workflows. 40% faster deploy than LangGraph for standard cases. Role-based syntax readable by non-engineers. Weakness: arbitrary graph structures awkward. |
| **AutoGen / AG2** | Best for conversational multi-party agents. BUT: Microsoft shifted to maintenance mode in favor of broader MS Agent Framework. |
| **Pydantic AI** | V1 released Sept 2025. Type-safe, Python-native. Newer but catching up fast. Preferred by teams valuing strict typing. |
| **Mastra** | TypeScript-first. Replit used it to go from 80% → 96% task success. Marsh McLennan deployed to 75K employees. Batteries-included, opinionated. |
| **Bare Python** | Still the escape hatch. Teams that removed LangGraph saw 40% latency reduction (1 measured case). Valid for simple/batch workflows. |
| **LangGraph** | Most battle-tested for production stateful systems with cycles, branching, parallel execution. Best debugging (LangSmith). Steeper learning curve. |

- The "mix and match" approach is common in production — strongest teams don't pick one framework.

## Enterprise / Financial Services Adoption (Confirmed)
- **BlackRock**: LangGraph orchestrating Aladdin AI agents. 50+ engineering teams via plugin registry. Managing $11T in assets.
- **JPMorgan**: "Ask David" (Ask David) — multi-agent investment research system. 95% reduction in research task time.
- **LinkedIn**: AI Hiring Agent on LangGraph.
- **Uber**: Unit test generation agents.
- **Cisco, Klarna**: Production LangGraph Platform users.
- **Captide**: Investment research / equity modeling agents on LangGraph Platform + LangSmith.
- Note: JPMorgan and BlackRock citations come from LangChain conference recap (Interrupt 2025) — treat as confirmed vendor presentations, not independent case studies.

## The March 2026 "Should a Capco client use LangGraph?" Answer
Use it when: complex stateful workflows, cycles/branching, parallel execution, HITL required, multi-agent with engineering team, need production observability.
Skip it when: linear pipeline, batch/scheduled, simple RAG, time-to-prototype matters most, non-engineering stakeholders write agent definitions.

## Key Sources
- blog.langchain.com/langchain-langgraph-1dot0/ (official 1.0 announcement)
- changelog.langchain.com (release log)
- pypi.org/project/langgraph/ (v1.1.2, Mar 12 2026)
- github.com/langchain-ai/langgraph (26.3K stars)
- nvd.nist.gov/vuln/detail/CVE-2025-68664 (LangChain Core vuln)
- resolvedsecurity.com/vulnerability-catalog/CVE-2025-64439 (LangGraph RCE)
- blog.langchain.com/interrupt-2025-recap/ (enterprise case studies)
- langchain.com/pricing-langgraph-platform (pricing)
