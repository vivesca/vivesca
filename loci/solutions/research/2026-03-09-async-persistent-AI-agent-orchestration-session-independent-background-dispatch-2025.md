# Async / Persistent AI Agent Orchestration: Session-Independent Background Dispatch
*Research date: 2026-03-09 | Researcher agent*

---

## Research Questions

1. What frameworks/tools exist for session-independent agent dispatch? (Temporal, Inngest, Modal, Celery, Prefect, etc.) — which are AI-native vs repurposed infra?
2. What have Anthropic, OpenAI, Google shipped for async/background agents in 2025?
3. What open-source projects specifically target "personal AI agent scheduler" or "unattended agent runs"? GitHub stars, activity level.
4. Is there a clean solution for: dispatch reasoning agent → close session → retrieve results next session? If yes, what is it?
5. What are practitioners building in this space right now (X/Twitter, HN)?

---

## Q1: Framework Landscape — AI-Native vs Repurposed Infra

### Temporal (temporal.io) — Repurposed general infra, but now AI-native positioned

**What it is:** Durable execution platform based on event-sourced workflow history. Workflows survive crashes, LLM rate limits, network failures, and restarts by replaying from the last persisted event.

**How it solves session-independent dispatch:**
- Temporal Schedules trigger workflows at regular intervals entirely independent of any user session
- Each agent invocation is an Activity; orchestration runs as a Workflow
- Workflow Handles allow cross-session result retrieval by ID — poll or query any workflow from any process
- Signals enable async state updates to running workflows without session coupling
- Queries expose current workflow state to external callers

**AI-specific additions (2025):**
- **OpenAI Agents SDK integration** — Public Preview launched Sep 2025. Wraps OpenAI agent loops inside Temporal Workflows. Automatic retries and state checkpointing. Every agent invocation = a Temporal Activity. Works with any OpenAI-powered agent with minimal code changes.
- **Ambient agents pattern** — documented: cron-triggered workflows with 25s intervals; each cycle analyses conditions, takes autonomous action; exposes Signals/Queries for human interaction; durable MCP tool backing for auditability.
- **Multi-agent architectures** — blog post on multi-agent patterns: each agent is a long-running workflow; inter-agent coordination via Signals; complete event history for observability and compliance.

**Status:** Open-source core (Apache 2). Temporal Cloud (managed). Production-grade. Used at scale by Stripe, Airbnb, Netflix.

**Sources:**
- https://temporal.io/blog/orchestrating-ambient-agents-with-temporal
- https://temporal.io/blog/announcing-openai-agents-sdk-integration
- https://docs.temporal.io/ai-cookbook/openai-agents-sdk-python
- https://www.infoq.com/news/2025/09/temporal-aiagent/

---

### Inngest (inngest.com) — Serverless-first, AI-native oriented

**What it is:** Durable workflow orchestration via `step.run` pattern. Functions composed of Trigger + Flow Control + Steps. Runs anywhere (edge, serverless, traditional).

**How it solves session-independent dispatch:**
- Trigger from API calls, webhooks, cron schedules — fully independent of initiating session
- `step.run` provides automatic retries, recovery, and state management
- AgentKit sub-library for multi-agent systems with dependency management and failure handling
- `step.ai.wrap` wraps any AI SDK call for reliable execution with built-in retries and observability

**Architecture:** Event-driven. Functions dispatch Inngest events via API, which trigger workers anywhere. No persistent connection needed.

**GitHub:** github.com/inngest/inngest — 10K+ stars, actively maintained.

**Sources:**
- https://www.inngest.com/ai
- https://www.inngest.com/blog/semi-autonomous-ai-agents
- https://agentkit.inngest.com/overview

---

### AWS Bedrock AgentCore Runtime — Managed cloud, FS-enterprise ready

**What it is:** AWS-managed runtime for AI agents with native async support.

**How it solves session-independent dispatch:**
- Immediate response pattern: ACK user immediately, run agent in background
- `/ping` health endpoint: `{"status": "HealthyBusy"}` vs `{"status": "Healthy"}` — clients poll for completion
- Session reuse: same session can be invoked multiple times across different caller sessions; context persists incrementally
- Unified API: callers use same endpoint for sync and async — runtime handles the difference

**Architecture:** Task ID–based tracking. Custom ping handlers. Sessions auto-terminate after 15 minutes of idle.

**Enterprise fit:** SOC 2, IAM, existing AWS audit trail. No separate infra to operate. Directly relevant for banks on AWS.

**Source:** https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-long-run.html

---

### Celery / Prefect / Airflow — Repurposed data-infra, not AI-native

These are message queue / workflow tools that predate LLM agents:

- **Celery:** Distributed task queue. Executes arbitrary Python functions. Works for agent dispatch but has no AI-native abstractions — no retries on LLM rate limits, no built-in observability for agent reasoning loops. Low-ceremony but low-guard.
- **Prefect:** Workflow management with rich UI and failure handling. Better than Celery for observability. Not AI-specific; no agent-loop abstractions. Can wrap agent invocations as Prefect flows. Better fit for ETL-like agent pipelines than dynamic reasoning loops.
- **Airflow:** DAG-based. Too rigid for non-deterministic agent workflows. Not a fit.

**Verdict:** Celery/Prefect work as low-tech dispatch mechanisms but require significant wrapping to handle LLM-specific concerns (rate limits, non-determinism, token recovery).

---

### Modal (modal.com) — Cloud compute, not orchestration

Modal provides serverless GPU compute on demand. Used *under* orchestration layers (Proliferate uses Modal sandboxes). Not itself an orchestration solution for session-independent agent dispatch. Relevant if agents need heavy compute (fine-tuning, multi-GPU inference) launched asynchronously.

---

## Q2: What Anthropic, OpenAI, Google Shipped in 2025

### Anthropic

- **Claude Code Agent Teams** (Claude Opus 4.6): Sub-agent swarms with shared context across parallel sessions. Dispatch multiple Claude agents as a team; team lead orchestrates. Not session-independent — still requires the initiating Claude Code session to be active.
- **Claude Code background tasks** (`run_in_background: true`): Sub-agents run in background within a session. Not cross-session — output files in `/private/tmp/` are ephemeral.
- **MCP + AAIF:** Donated MCP to Linux Foundation (Dec 2025). AAIF consortium (Anthropic, OpenAI, Block). MCP enables agent→tool connections but not agent persistence itself.
- **Agent Skills open standard:** Opened the Skills architecture. Skills are stateless invocations, not persistent state.

**Gap:** Anthropic has no native cross-session agent state or background dispatch primitive as of early 2026. Claude Code's background tasks are intra-session only.

### OpenAI

- **Operator** (Jan 2025): Browser-based agent for Pro users. Interactive, not background.
- **OpenAI Agents SDK** (2025): Framework for building multi-agent systems. Integrates with Temporal (Public Preview Sep 2025) for durable execution — this is the production path for session-independent dispatch with OpenAI agents.
- **Codex Cloud** (2025): Cloud-based async coding agent. Dispatches from web UI; works while user is away. Closest to "close browser, come back later" UX for coding tasks.
- **Responses API:** Standard for building agent logic. Stateless — caller manages state.

### Google

- **Gemini Jules** (2025): Async coding agent integrated with GitHub. Dispatched from issue/PR; works in background; results delivered via PR. Best consumer-facing async UX currently available for code tasks.
- **A2A (Agent-to-Agent) protocol:** Standard for agent-to-agent communication. Orthogonal to session persistence — addresses inter-agent messaging, not state durability.
- **Antigravity (internal):** Asynchronous task dispatch mentioned in developer reports (RedMonk 2025). Not a public product.

**Synthesis:** None of the three labs have shipped a general-purpose "fire and forget, retrieve later" primitive. The pattern is assembled from: their SDKs + Temporal/Inngest/Bedrock for durability + file/DB storage for result retrieval.

---

## Q3: Open-Source "Personal Agent Scheduler" Projects

| Project | Stars | License | Key capability | Maturity |
|---|---|---|---|---|
| Background Agents (ColeMurray) | 537 (2 weeks, Jan 2026) | Open | Modal sandboxes, GitHub OAuth UI, Ramp-inspired | Very early |
| Proliferate | 235 | MIT | cron/webhook/Sentry triggers, cloud sandboxes, multiplayer | Early/active |
| OpenCode Scheduler | Unknown | Unknown | OS-native schedulers (launchd/systemd), Claude Code–compatible | Early |
| Cairn | Unknown | Unknown | End-to-end software engineering from GitHub repos | Early |
| Shadow (ishaan1013) | Unknown | Unknown | Background coding agent + real-time web interface | Experimental |
| OpenFang | Unknown | Unknown | Agent OS: 24/7 schedules, knowledge graphs, RBAC | Early |
| OpenCode Background Agents (kdcokenny) | Unknown | Unknown | Claude Code–style background agents with context persistence | Experimental |

**Pattern:** All are coding-task–focused. None address the "personal reasoning agent that runs research/analysis unattended and surfaces structured output next session" use case. That remains open.

---

## Q4: Is There a Clean Solution for "Dispatch → Close → Retrieve"?

**Short answer: No clean off-the-shelf solution for personal/ambient reasoning agents. Yes for coding-task agents.**

### What exists for coding tasks:
- **Gemini Jules:** Dispatch from GitHub issue; Jules works overnight; result = PR. Genuinely session-independent. But narrowly scoped to code.
- **Proliferate / Background Agents:** Same pattern — dispatch, sandbox runs, result = PR or diff. Still code-focused.
- **Temporal + OpenAI SDK:** Full durability + result retrieval via Workflow Handle. Requires infrastructure setup (Temporal server or Cloud) + integration work.

### What does NOT exist cleanly:
- "Queue a research brief, close Claude Code, come back tomorrow and get a structured synthesis." No product ships this. The closest workaround: cron job → bash script → Claude API call → write output to file → read file next session. Entirely manual plumbing.
- Personal AI agent scheduler with: (a) queue management, (b) natural-language result packaging, (c) session re-injection on next open. Gap confirmed by HN thread 46948533.

### The three implementation patterns (from HN consensus):
1. Fire-and-forget + completion webhook — most common, most products ship this only
2. Structured checkpointing + intermediate state inspection — Temporal's model
3. Interrupt-driven escalation to humans mid-execution — human-in-the-loop; rarest, hardest

**Key practitioner insight (HN 46948533):** "The supervision protocol is the product, not the async dispatch." The queue is trivial; the hard parts are: result packaging, context re-injection, and deciding when to interrupt.

---

## Q5: Practitioner Signal (X/HN, Feb-Mar 2026)

**HN "Everyone's building async agents" thread (46948533, Feb 2026):**
- Consensus: "async" = caller does not block, not when agent runs
- "Background job" is more honest terminology
- Most implementations are pattern 1 only (fire-and-forget)
- Jules (Google) and Codex Cloud (OpenAI) cited as reference UX implementations

**HN "Why we built our own background agent" (46589842):**
- Teams building internal background agent infra because off-the-shelf doesn't fit
- Common complaint: existing tools optimised for ETL, not reasoning loops
- Ramp's "Inspect" tool cited as a practical internal pattern (now open-sourced as Background Agents)

**X/Twitter signal (2025-2026):**
- "Ambient agents" framing from Temporal is gaining traction
- Temporal + OpenAI SDK integration widely shared in agent developer communities
- "Session-independent" phrasing not yet standardised — also seen as "persistent agents", "always-on agents", "background agents"

---

## Enterprise/Banking Demand (Confirmed Use Cases)

From McKinsey, Deloitte, Oracle, and actual deployments (HSBC, Citi, DBS, Santander):

1. **Overnight AML/KYC re-screening** — ideal background agent use case. Run unattended, produce exception reports. Sequential workflow pattern for auditability.
2. **Real-time trade reconciliation** — agents reconcile trades continuously; flag discrepancies. Always-on ambient pattern.
3. **Regulatory data validation** — agents validate submissions, flag risk thresholds. Temporal's event history = compliance audit trail.
4. **Loan underwriting pipeline** — graph/hierarchical pattern: supervisor + specialist agents (credit, fraud, risk). Long-running (hours), must survive API failures.
5. **Live payment execution** — Santander + Mastercard completed Europe's first AI-agent–executed live payment (Mar 2026). Proof of end-to-end agentic transactions.

**Business impact confirmed (multiple banks):** 20–40% cost reduction, 10–30% revenue uplift. McKinsey: 200–2,000% productivity gains in KYC/AML compliance via end-to-end agentic workflows.

**Gartner warning:** 40% of agentic AI projects cancelled by end-2027 due to escalating costs and misaligned value. Primary cause: inadequate durability + governance from the start.

---

## Summary Assessment

| Dimension | Verdict |
|---|---|
| Personal "hot queue" for reasoning agents | Open problem — no clean solution |
| Coding task background dispatch | Partially solved (Jules, Codex Cloud, Proliferate) |
| Production enterprise async orchestration | Solved (Temporal, Bedrock AgentCore, Inngest) |
| FS/banking governance layer | Not AI-native yet — assembled from orchestration + human-in-the-loop wrappers |
| Personal result re-injection next session | Open — no product ships this cleanly |

---

## All Sources

- https://temporal.io/blog/orchestrating-ambient-agents-with-temporal
- https://temporal.io/blog/announcing-openai-agents-sdk-integration
- https://temporal.io/blog/using-multi-agent-architectures-with-temporal
- https://temporal.io/blog/build-resilient-agentic-ai-with-temporal
- https://docs.temporal.io/ai-cookbook/openai-agents-sdk-python
- https://www.infoq.com/news/2025/09/temporal-aiagent/
- https://www.inngest.com/ai
- https://www.inngest.com/blog/semi-autonomous-ai-agents
- https://agentkit.inngest.com/overview
- https://github.com/inngest/inngest
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-long-run.html
- https://github.com/proliferate-ai/proliferate
- https://github.com/ColeMurray/background-agents
- https://backgroundagents.dev
- https://github.com/different-ai/opencode-scheduler
- https://github.com/cairn-dev/cairn
- https://github.com/RightNow-AI/openfang
- https://news.ycombinator.com/item?id=46948533
- https://news.ycombinator.com/item?id=46589842
- https://www.mckinsey.com/capabilities/operations/our-insights/the-paradigm-shift-how-agentic-ai-is-redefining-banking-operations
- https://www.deloitte.com/us/en/insights/industry/financial-services/agentic-ai-banking.html
- https://www.mastercard.com/news/europe/en/newsroom/press-releases/en/2026/santander-and-mastercard-complete-europe-s-first-live-end-to-end-payment-executed-by-an-ai-agent/
- https://www.oracle.com/financial-services/banking/future-banking/
- https://www.prosus.com/news-insights/2026/state-of-ai-agents-2026-autonomy-is-here
- https://intuitionlabs.ai/articles/agentic-ai-temporal-orchestration
- https://claudefa.st/blog/guide/agents/async-workflows
- https://dev.to/akki907/temporal-workflow-orchestration-building-reliable-agentic-ai-systems-3bpm
