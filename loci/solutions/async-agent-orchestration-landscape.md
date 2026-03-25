# Async / Persistent AI Agent Orchestration — Landscape Summary
*Research date: 2026-03-09*

## Gap Assessment: Is the "Personal Hot Queue" a Solved Problem?

**Partially solved at the infrastructure layer; largely unsolved at the personal/ambient layer.**

Enterprise infra (Temporal, AWS Bedrock AgentCore, Inngest) solves durable dispatch at scale. But the specific pattern of "I queue a reasoning task from my terminal, close the session, and pick up structured results next time I open Claude" has no clean off-the-shelf answer as of early 2026. The closest approximations are cobbled from cron + file output + a polling wrapper. The Hacker News consensus (thread 46948533, Feb 2026): "the supervision protocol is the product, not the async dispatch" — meaning the hard part is *result handoff and context re-injection*, not the queue itself.

## Top 3 Tools Worth Evaluating

### 1. Temporal (temporal.io) — Best for production-grade durable agents
- Durable execution via event-sourced workflow history. Agent survives crashes, rate limits, restarts.
- **Public Preview: OpenAI Agents SDK integration** (Sep 2025) — wraps OpenAI agent loops as Temporal workflows with automatic retries and state checkpointing.
- Pattern: `Schedule → Workflow (agent loop) → Signal/Query for result retrieval` — fully session-independent.
- Ambient agents pattern documented: cron-triggered workflows, signals for async updates, Workflow Handle for cross-session result polling.
- Self-hosted or Temporal Cloud. Open-source core (Apache 2). Source: temporal.io/blog/orchestrating-ambient-agents-with-temporal

### 2. Inngest (inngest.com) — Best for serverless / low-ops personal use
- `step.run` pattern for durable multi-step functions. Runs anywhere (edge, serverless, traditional).
- Triggers: API calls, webhooks, cron schedules.
- AgentKit sub-library specifically for multi-agent orchestration with built-in retries and observability.
- Lower ops overhead than Temporal — no separate server to run. Better fit for personal/small-team use.
- Open-source core (github.com/inngest/inngest, ~10K+ stars). Source: inngest.com/ai, inngest.com/docs

### 3. AWS Bedrock AgentCore Runtime — Best for FS/enterprise with AWS stack
- Native async pattern: immediate ACK + background processing, `/ping` health endpoint for status polling.
- Session reuse across invocations — context persists across calls without re-sending.
- Managed AWS service: no infra to operate. Compliance-friendly (SOC 2, existing AWS IAM/audit trail).
- Directly relevant for HK banks already on AWS. Source: docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-long-run.html

## Notable Open-Source Projects (Personal / Unattended)

- **Proliferate** (github.com/proliferate-ai/proliferate, 235 stars, MIT) — background agent with cron/webhook/Sentry/Linear triggers; cloud sandboxes; multiplayer steering.
- **Background Agents** (github.com/ColeMurray/background-agents, 537 stars in first 2 weeks, Jan 2026) — Modal sandboxes + Cloudflare Workers + GitHub OAuth monitoring UI. Directly inspired by Ramp's internal "Inspect" tool.
- **OpenCode Scheduler** (github.com/different-ai/opencode-scheduler) — Claude Code-compatible; uses OS-native schedulers (launchd/systemd); designed for recurring unattended runs.
- **Cairn** (github.com/cairn-dev/cairn) — end-to-end software engineering background agent directly from GitHub repos.

## What Practitioners Are Building (X/HN Signal, Feb-Mar 2026)

- Three implementation patterns dominate: (1) fire-and-forget + webhook, (2) structured checkpointing + intermediate state inspection, (3) interrupt-driven human escalation. Most products only ship pattern 1.
- Term "async agent" is contested — "background job" considered more honest. The real differentiation is *whether the caller blocks*, not when the agent executes.
- Claude Code async (sub-agent swarms) and Gemini Jules are the consumer-facing reference implementations. Neither solves cross-session result retrieval cleanly for personal use.

## Capco Consulting Angle: What Banks Need Here

Banks are the natural enterprise buyer for this capability. Confirmed use cases from McKinsey/Deloitte/Oracle research (2025-2026):

1. **Overnight regulatory batch agents** — AML/KYC re-screening, regulatory data validation, threshold monitoring. Run unattended, produce structured exception reports for morning review.
2. **Multi-agent trade reconciliation** — sequential workflows (regulated processes require accuracy + audit trace over speed). Temporal's event history directly addresses compliance audit requirements.
3. **Credit underwriting pipelines** — graph/hierarchical agent patterns: supervisor + specialist agents (credit, fraud, risk). Long-running (minutes to hours), must survive LLM rate limits and API failures.
4. **Compliance monitoring loops** — ambient agents pattern: continuously run, signal humans only on exception. Santander/Mastercard live payment agent (Mar 2026) is the first public proof of end-to-end agentic payments.

**The consulting pitch:** Banks are building these patterns on ad-hoc infra (custom queues, home-grown orchestrators). The gap is not in AI capability but in *production-grade durability + governance*. Temporal + Bedrock AgentCore + human-in-the-loop controls is the enterprise-ready stack. Capco's AI governance accelerator framework maps directly onto the supervision layer these systems need.

**Gartner red flag to lead with:** 40% of agentic AI projects will be cancelled by end-2027 due to escalating costs and misaligned value. The fix is durable orchestration + tight ROI instrumentation from day one — not better models.

## Sources Consulted
- temporal.io/blog/orchestrating-ambient-agents-with-temporal
- temporal.io/blog/announcing-openai-agents-sdk-integration
- docs.temporal.io/ai-cookbook/openai-agents-sdk-python
- infoq.com/news/2025/09/temporal-aiagent/
- docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-long-run.html
- inngest.com/ai + inngest.com/blog/semi-autonomous-ai-agents
- github.com/proliferate-ai/proliferate
- github.com/ColeMurray/background-agents
- github.com/different-ai/opencode-scheduler
- news.ycombinator.com/item?id=46948533 (HN: "Everyone's building async agents...")
- news.ycombinator.com/item?id=46589842 (HN: "Why we built our own background agent")
- mckinsey.com/capabilities/operations/our-insights/the-paradigm-shift-how-agentic-ai-is-redefining-banking-operations
- deloitte.com/us/en/insights/industry/financial-services/agentic-ai-banking.html
- prosus.com/news-insights/2026/state-of-ai-agents-2026-autonomy-is-here
