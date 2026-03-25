# Async Agent Orchestration Research (Mar 2026)

## Key Sources
- **temporal.io/blog/orchestrating-ambient-agents-with-temporal** — WebFetch works; best source for ambient/session-independent pattern. Explains Schedules + Signals + Queries + Workflow Handles architecture clearly.
- **temporal.io/blog/announcing-openai-agents-sdk-integration** — WebFetch works. Public Preview Sep 2025. Best practitioner source for Temporal + OpenAI SDK durability.
- **docs.temporal.io/ai-cookbook/** — WebFetch works; code-level detail on OpenAI Agents SDK Python integration.
- **docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-long-run.html** — WebFetch works; clean architecture extract. `/ping` endpoint pattern documented.
- **inngest.com/ai + inngest.com/blog/** — WebFetch works. AgentKit documented. Good for serverless / low-ops comparisons.
- **news.ycombinator.com/item?id=46948533** — HN "Everyone's building async agents" thread. WebFetch works; rich practitioner opinions. Key quote: "The supervision protocol is the product, not the async dispatch."
- **github.com/proliferate-ai/proliferate** — WebFetch works via GitHub page; 235 stars, MIT, cron/webhook/Sentry triggers.
- **github.com/ColeMurray/background-agents** — 537 stars (2 weeks, Jan 2026); Modal sandboxes + Cloudflare Workers + GitHub OAuth UI.
- **mckinsey.com/capabilities/operations/our-insights/the-paradigm-shift-how-agentic-ai-is-redefining-banking-operations** — WebFetch sometimes works; best via WebSearch summaries. 200–2,000% productivity in KYC/AML.

## Key Settled Facts (Cross-Referenced)
- **Personal "hot queue" for reasoning agents = open problem** — no off-the-shelf solution as of Mar 2026. Coding task background dispatch is partially solved (Jules, Codex Cloud, Proliferate); production enterprise is solved (Temporal, Bedrock AgentCore); personal ambient reasoning is not.
- **Temporal is the gold standard for durable production orchestration.** Event-sourced history = crash-safe + auditable. Workflow Handles = cross-session result retrieval. OpenAI Agents SDK integration = Public Preview Sep 2025.
- **Three patterns from HN:** (1) fire-and-forget + webhook (most common, most products only ship this), (2) structured checkpointing (Temporal's model), (3) interrupt-driven human escalation (rarest).
- **AWS Bedrock AgentCore Runtime:** Ping-based health + task ID tracking. 15-min idle timeout. Good FS/enterprise fit on AWS.
- **Inngest:** Best for serverless/low-ops. AgentKit sub-library. Open-source core.
- **None of Anthropic/OpenAI/Google has a general-purpose cross-session agent state primitive.** Claude Code background tasks are intra-session only. Jules (Google) and Codex Cloud are coding-specific.

## Common Misinformation
- "Claude Code supports background agents" — true intra-session only. NOT cross-session persistence.
- "Async agent" is ambiguous — many products claim it but only ship fire-and-forget pattern 1. Ask: "does the caller block?" and "how do you retrieve results next session?"
- Temporal is sometimes described as "ETL/workflow" — it is general durable execution, not ETL-specific. AutoGen/LangGraph do NOT solve durability.

## Banking Use Cases (Confirmed)
AML/KYC re-screening (overnight batch), trade reconciliation (real-time ambient), loan underwriting (graph/hierarchical multi-agent), regulatory data validation. Santander/Mastercard completed first live AI-agent payment (Mar 2026). Banks: HSBC, Citi, UBS, DBS, ING — confirmed 20–40% cost reduction.

## Full Research
- Summary: /Users/terry/docs/solutions/async-agent-orchestration-landscape.md
- Full: /Users/terry/docs/solutions/research/2026-03-09-async-persistent-AI-agent-orchestration-session-independent-background-dispatch-2025.md
