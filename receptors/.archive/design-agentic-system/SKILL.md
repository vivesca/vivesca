---
name: design-agentic-system
description: "Design agentic AI systems for enterprise/banking clients. Use when advising on AI architecture, scoping agent projects, or creating design deliverables."
user_invocable: true
---

# Design Agentic System

Structured framework for designing agentic AI systems, calibrated for banking/financial services clients.

## When to Use

- Client asks "should we build an AI agent for X?"
- Scoping a new agentic system project
- Creating architecture deliverables for steering committees
- Evaluating vendor agentic solutions

## Quick Start

Terry has 3 years building AI/ML in banking (CITIC Bank International — AML models, GenAI chatbot, HKMA GenAI Sandbox). Use this domain experience to ground recommendations.

Ask the user:
1. **What problem?** (customer service, operations, research, etc.)
2. **What stage?** (POC, Pilot, Production)
3. **What constraints?** (regulatory, data, budget, timeline)

Then work through the phases below, adjusting depth to stage.

---

## Phase 0: Triage (5 min)

**Purpose:** Determine if an agentic approach makes sense before investing design effort.

### Questions to Answer

| Question | Red Flag |
|----------|----------|
| Is the task well-defined enough for rules/workflow? | If yes → consider deterministic automation first |
| Does the client have clean, consistent data? | Fragmented knowledge base → recommend data cleanup before agents |
| What's the regulatory environment? | HKMA/MAS/FCA → heavier compliance scaffolding |
| What's the blast radius of errors? | Financial transactions → higher safety requirements |
| Is there executive sponsorship? | No sponsor → POC dies regardless of quality |

### Output

**Go / Conditional / No-Go** recommendation with 2-3 sentence rationale.

If No-Go, recommend alternatives (workflow automation, RAG without agency, human-assisted AI).

---

## Phase 1: Requirements

### Problem Scoping

- **Problem type:** Assistant, Automation, Research, Decision Support
- **Users:** Internal staff, customers, or both?
- **Volume:** Transactions/queries per day? Peak load scenarios?
- **Success criteria:** What measurable outcome defines success?

### Constraints Matrix

| Constraint | Client Answer | Design Implication |
|------------|---------------|-------------------|
| Latency tolerance | | Sync vs async, model size |
| Cost ceiling | | Model selection, caching strategy |
| Data residency | | Cloud region, on-prem requirements |
| Human oversight | | Approval workflows, escalation triggers |
| Audit requirements | | Logging depth, retention period |

### Failure Economics (Banking-Critical)

Don't just model happy path. Answer:

1. **What happens when the agent fails?** (Error rate assumption: 5-20%)
2. **Who handles failures?** (Junior ops? Senior compliance? Specialists?)
3. **What's the FTE cost of the failure path?**

> If 20% of queries need senior compliance officers to reverse-engineer AI reasoning, net operational cost may *increase*. Model this explicitly.

### Abuse & Threat Model

For customer-facing agents:

- **Prompt injection:** Can users manipulate the agent into unauthorized actions?
- **Social engineering:** Can users exploit "helpfulness" to get exceptions/approvals?
- **Data exfiltration:** Can users extract training data or other customers' info?

**Output:** Risk register with likelihood/impact ratings.

---

## Phase 2: Architecture Selection

### Agent Topology

| Pattern | When to Use | Trade-off |
|---------|-------------|-----------|
| **Single agent** | Simple tasks, clear scope | Lower complexity, limited capability |
| **Router + specialists** | Multiple distinct task types | Better accuracy, more moving parts |
| **Multi-agent collaboration** | Complex reasoning, verification needed | Highest capability, hardest to debug |
| **Human-in-the-loop** | High-stakes decisions | Safest, slowest |

### Orchestration Pattern

| Pattern | Description | Best For |
|---------|-------------|----------|
| **ReAct** | Reason → Act → Observe loop | General-purpose, exploratory |
| **Plan-then-Execute** | Full plan upfront, then execute | Predictable multi-step tasks |
| **Hierarchical** | Manager agent delegates to workers | Complex workflows, parallel execution |

### Model Selection

| Factor | Consideration |
|--------|--------------|
| **Capability** | Does it need frontier reasoning or is smaller sufficient? |
| **Cost** | $/1K tokens × expected volume |
| **Latency** | Streaming? Batch? Real-time? |
| **Vendor lock-in** | Switching cost if provider changes pricing/terms |
| **Data handling** | Where does data go? Acceptable for this client? |

---

## Phase 3: Component Design

### 3.1 Knowledge & Memory

Translate technical terms for stakeholders:

| Technical | Business Term | Purpose |
|-----------|--------------|---------|
| Semantic memory | Knowledge Base | Static reference (policies, FAQs, docs) |
| Episodic memory | Audit Trail | Conversation history, decisions made |
| Working memory | Session Context | Current task state |

**Key decisions:**
- What's in the knowledge base? Who maintains it?
- How long is conversation history retained?
- How is context passed between sessions?

### 3.2 Tool/Action Space

List every action the agent can take. For each:

| Tool | Description | Risk Level | Controls |
|------|-------------|------------|----------|
| `search_knowledge_base` | Query internal docs | Low | None |
| `lookup_customer` | Retrieve customer record | Medium | Logging |
| `update_account` | Modify account settings | High | Maker-checker, limits |
| `transfer_funds` | Move money | Critical | Dual approval, hard caps |

**Banking controls to consider:**
- RBAC/entitlements per tool
- Maker-checker for state changes
- Hard limits (transaction caps, allowlisted endpoints)
- Velocity limits (max actions per minute)

### 3.3 Safety & Guardrails

**Input guardrails:**
- Prompt injection detection
- PII filtering
- Out-of-scope detection

**Output guardrails:**
- Response validation against policy
- Confidence thresholds for escalation
- Prohibited content filtering

**"Helpful vs Hardened" Analysis** (for customer-facing agents):

> Agents optimized for helpfulness become social engineering targets. If the agent can waive fees, approve exceptions, or escalate access, model the attack surface.

| Capability | Abuse Scenario | Mitigation |
|------------|---------------|------------|
| Fee waiver | Customer claims false hardship | Approval limits, pattern detection |
| Account changes | Social engineering via urgency | Verification steps, cooling period |
| Information access | Phishing for other customers' data | Strict scoping, no cross-account queries |

### 3.4 Records & Evidence Layer

**Production requirement for regulated environments.** POCs can defer but must prove path to compliance.

| Element | POC | Production |
|---------|-----|------------|
| Conversation logs | Basic logging | WORM storage, retention policy |
| Tool call audit | Log actions | Full request/response, timestamps |
| Rationale capture | Optional | Required for explainability |
| PII handling | Minimal | Redaction rules, access controls |
| Surveillance hooks | N/A | Integration with eComms monitoring |

### 3.5 Transactional Integrity

**For agents that modify state (accounts, records, transactions):**

- **Idempotency:** All state-changing tools must handle retries safely
- **Compensating transactions:** Define rollback for each action
- **Error propagation:** Does failure stop immediately or attempt recovery?

> Banking systems have ACID properties. Agentic frameworks don't. Bridge this gap explicitly.

---

## Phase 4: Trade-off Analysis

### Standard Trade-offs

| Trade-off | Lever A | Lever B |
|-----------|---------|---------|
| Cost vs Capability | Smaller/cheaper models | Frontier models |
| Autonomy vs Control | More automation | More human checkpoints |
| Latency vs Accuracy | Fast, cached responses | Slower, deliberate reasoning |
| Flexibility vs Safety | Broader tool access | Constrained action space |

### Banking-Specific Trade-offs

| Trade-off | Consideration |
|-----------|--------------|
| **Speed vs Compliance** | Can you prove audit trail to regulators? |
| **Vendor vs Build** | Lock-in risk vs time-to-market |
| **Sandbox vs Production** | Innovation speed vs MRM readiness |

### Scalability Stress Test

Model performance under 10x normal load:
- Latency degradation?
- Cost spike?
- Fallback strategy? (Queue? Rule-based backup? Human overflow?)

---

## Phase 5: Outputs

### Artifact Depth by Stage

| Stage | Artifacts |
|-------|-----------|
| **POC** | 1-page architecture sketch, risk summary, success criteria |
| **Pilot** | Architecture diagram, decision matrix, escalation workflow, basic audit plan |
| **Production** | Full design doc, MRM package, records retention schedule, abuse playbook, FTE projections |

### Standard Deliverables

1. **Architecture Diagram** — Components, data flows, integration points
2. **Decision Matrix** — Key choices with rationale
3. **Risk Register** — Identified risks with mitigations
4. **Escalation Workflow** — When and how humans get involved
5. **ROI Projection** — Expected volume, error rates, FTE impact, 12-month cost model

### Optional (Production)

- Abuse scenario playbook
- Records retention schedule
- Surveillance integration spec
- Disaster recovery / rollback procedures

---

## Anti-Patterns to Flag

| Anti-Pattern | Problem | Alternative |
|--------------|---------|-------------|
| "Just add an agent" | No clear problem definition | Start with Phase 0 triage |
| Autonomous financial actions | Unacceptable risk | Human-in-the-loop for money movement |
| Training on customer data | Privacy/regulatory issues | Retrieval over fine-tuning |
| Single point of failure | Agent down = service down | Fallback to rules/humans |
| Ignoring failure path | Happy-path-only design | Model failure economics explicitly |
| Premature optimization | Over-engineering for POC | Match depth to stage |

---

## Quick Reference: Vocabulary Translation

When presenting to compliance/risk stakeholders:

| Technical | Say Instead |
|-----------|-------------|
| Episodic memory | Audit trail / conversation history |
| Semantic memory | Knowledge base |
| Working memory | Session context |
| Tool use | Authorized actions |
| Prompt injection | Input manipulation attack |
| Hallucination | Fabricated response |
| ReAct loop | Iterative reasoning |
| Multi-agent | Specialist coordination |

---

## See Also

- [[OpenClaw Design Analysis]] — Personal agent design patterns
- [[AI Coding Best Practices]] — Implementation patterns
