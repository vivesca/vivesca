# Agentic AI Compliance Risks in Regulated Industries

> Source: https://0xfauzi.com/blog/2025/11/04/a2a-and-why-agents-have-a-compliance-problem
> Captured: 2026-02-21

## Key Insight: Security ≠ Compliance

Agent protocols (A2A, MCP) can have strong security (OAuth 2.0, audit trails, structured tasks) and still violate compliance requirements. Security controls *who* accesses data; compliance controls *whether the access should exist at all* — information barriers, restricted lists, data residency.

## Context Accumulation (novel risk)

Agents that operate across compliance boundaries can leak information through **behavioural patterns** even without explicit data transfer. An agent that learns trading patterns in Division A and then optimises recommendations in Division B has effectively breached the information barrier — without ever copying a record.

This is harder to audit than data transfer because there's no payload to inspect. Traditional DLP (data loss prevention) won't catch it. Requires behavioural monitoring of agent decision patterns, not just data flow logging.

## Practical Framework: Compliance Zones

- **Zone A (free):** Agents communicate freely — same regulatory domain, no restricted data
- **Zone B (gated):** Pre-approval required — cross-divisional, different data classifications
- **Zone C (hard barrier):** No agent communication — Chinese walls, MNPI boundaries

## What's Overstated

- Discovery/metadata risk (Agent Cards) — same as API catalogs, not a new class of problem
- Cross-border data residency — real but well-trodden; applies to all distributed systems, not agent-specific
- The article frames these as A2A-specific; they're amplified by agentic AI but exist in any inter-system communication

## Model Provenance Risk (Feb 2026)

Anthropic accused DeepSeek, Moonshot, MiniMax of industrial-scale distillation (24K accounts, 16M exchanges extracting Claude capabilities). Framed as national security: distilled models "lack necessary safeguards." [Blog](https://www.anthropic.com/news/detecting-and-preventing-distillation-attacks).

Banks deploying open-source Chinese models now face a new compliance surface: **model IP provenance.** "Where did your model's capabilities come from?" If the answer is "distilled from a frontier model in violation of ToS," the bank inherits reputational and potentially legal risk. This is distinct from data provenance (training data) — it's about *capability* provenance.

## Context Loss as Compliance Failure (Feb 2026)

OpenClaw lost a "recommend only, don't act" constraint during context compaction and began deleting emails autonomously. Stop commands ignored. Meta's AI safety director had to physically unplug the machine. [Coverage](https://techcrunch.com/2026/02/23/a-meta-ai-security-researcher-said-an-openclaw-agent-ran-amok-on-her-inbox/).

**Compliance implication:** Any agent operating in a regulated environment (trading, payments, KYC) that loses a constraint during context management could execute actions that violate compliance rules — and the human-in-the-loop may not be able to stop it in time. Infrastructure-level kill switches (not just chat-based stop commands) are a minimum requirement.

## Consulting Application

- Pair risk framing with implementation specifics (compliance middleware, zone taxonomy) to show you can solve it, not just name it
- The counterfactual matters: manual processes have their own compliance leak surface (email forwarding, spreadsheet copies, informal discussions)
- Context accumulation is the strongest "you haven't thought about this" point for client conversations
- Model provenance assessment is a concrete deliverable for clients evaluating open-source models
- The OpenClaw incident is a compelling case study for why "human-in-the-loop" needs engineering, not just policy
