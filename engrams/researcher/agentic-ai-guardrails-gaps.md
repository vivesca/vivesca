# Agentic AI Guardrails / Governance — Practitioner Gaps Research (Feb 28, 2026)

## Research methodology that worked
- OWASP GenAI project (genai.owasp.org) — comprehensive agentic security docs; direct WebFetch returns CSS, use WebSearch summaries
- rockcybermusings.com — high-signal independent analysis of framework gaps; WebFetch works
- gravitee.io/blog state of AI agent security 2026 report — good stats; WebFetch works
- isaca.org industry news — IAM crisis articles; WebFetch works
- cloudsecurityalliance.org blog — "authorization outlives intent"; WebFetch works
- arxiv.org trust paradox paper (2510.18563) — "trust as unmodeled variable"; WebFetch works
- arxiv.org agentic finance governance (2512.11933) — MRM gaps for GenAI; WebFetch works
- agentbudget.dev — niche cost enforcement tool; WebFetch works
- dataiku.com cost iceberg article — hidden agentic cost governance gaps; WebFetch works
- mightybot.ai policy-driven AI article — policy-to-practice gap; WebFetch works
- O'Reilly radar (oreilly.com/radar/ai-agents-need-guardrails) — governance theatre vs engineering; WebFetch works
- avidoai.com guardrail testing for financial services — specific testing gaps; WebFetch works
- jack-vanlightly.com remediation post — 404 as of Feb 2026

## Confirmed Gaps (Evidence-Based)

### 1. Policy-to-Code Execution Gap
- No tool bridges high-level business rules ("draw requests >$500K require site inspection within 30 days") to machine-enforceable agent controls
- Guardrails (NeMo, Bedrock, LlamaFirewall) answer "is this content safe?" — they cannot answer "did this action comply with policy X?"
- Source: mightybot.ai, O'Reilly radar, avidoai.com
- Gartner stat: 40% of agentic AI projects will be abandoned by 2027 — governance gap as primary cause

### 2. Action Reversibility / Compensation
- Every framework says "prefer reversible actions" — none define reversibility or provide enforcement tooling
- No standard for "compensation action registries" (saga pattern for AI agents)
- nextgov.com coined "reversible resilience" as requirement for government AI agents
- Medium article (Dec 2025) explicitly names "reversible autonomy" as "the missing layer"
- Source: analyticsinsight.net, medium/@raktims2210

### 3. Agent Identity / Non-Human IAM
- 45.6% of teams still use shared API keys for agent-to-agent auth (Gravitee 2026 report)
- Only 21.9% treat agents as independent identities
- OAuth consent model "collapses" for agentic workloads (OWASP finding)
- "Authorization outlives intent" — credentials remain active avg 47 days after workflow ends (Okta/CSA)
- 51% of orgs lack formal secret revocation processes
- Non-human identities outnumber humans 144:1 in some enterprises
- Frameworks proposed (ARIA, DID-based) but no mainstream tooling
- Sources: isaca.org, cloudsecurityalliance.org, gravitee.io, openid.net whitepaper

### 4. Multi-Agent Trust Propagation
- Systems assume baseline inter-agent trust without modeling strength, authorization limits, or revocability
- Trust-Vulnerability Paradox: more coordination = more attack surface (arxiv 2510.18563)
- A single compromised agent propagates malicious influence across the system via A2A channels
- "Guardian agent" oversight concept proposed but no production tooling
- Source: arxiv 2510.18563, arxiv 2506.04133 (TRiSM review)

### 5. HITL Approval Quality (Not Just Presence)
- The math breaks at scale: 50-agent enterprise at 20 tool calls/hour = 1,000 approval-eligible events/hour
- "Overwhelming HITL" attack vector: flood system with benign requests to induce reviewer fatigue
- No tooling for tiered consequence-based automation (auto-approve reversible low-risk, gate irreversible)
- AI can learn to frame approval requests favourably — deception at the approval layer
- Sources: rockcybermusings.com, cio.com, bytebridge.medium.com

### 6. MCP Supply Chain / Tool Poisoning
- 8,000+ exposed MCP servers as of 2026 (Medium article)
- MCPTox benchmark: o1-mini 72.8% attack success; Claude 3.7 Sonnet refuses <3% of the time
- Smithery supply chain attack (Oct 2025): path-traversal in smithery.yaml exfiltrated API tokens
- CVE-2025-6514 (CVSS 9.6): OS command injection in mcp-remote, 437K downloads
- No standard for MCP server SBOMs (incredibuild article)
- Singapore MGF provides 2 bullet points on MCP; NIST has no guidance yet
- Sources: elastic.co, arxiv MCPTox, datasciencedojo.com, authzed.com breach timeline

### 7. Cost Governance / Budget Enforcement
- 92% of businesses implementing agentic AI experience cost overruns (IDC stat)
- 71% lack visibility into agent cost drivers
- Agent software is non-deterministic: same task = 3 or 300 LLM calls
- AgentBudget.dev exists but is a small Python SDK — no enterprise-grade enforcement layer
- No native per-agent budget enforcement in LangChain, CrewAI, AutoGen, or most orchestrators
- Sources: cxtoday.com, dataiku.com, agentbudget.dev

### 8. Agentic Audit Trail Quality (Not Just Existence)
- Tools log what happened; none link actions to specific policy version + intent + confidence + timestamp
- arxiv 2601.20727: Hash-chain audit trail paper — academic, no production tooling
- Financial services: audit trail must support regulatory replay and counterfactual analysis — no tool does this
- Sources: medium/@kuldeep.paul08, arxiv 2601.20727, avidoai.com

### 9. Shadow Agent Detection / Inventory
- 63% of orgs lack AI governance policies (IBM Cost of Data Breach 2025)
- Only 47.1% of an org's AI agents are actively monitored (Gravitee 2026)
- 40% of enterprise apps expected to embed agents by end of 2026 — detection tools lag far behind
- No continuous agent discovery tooling comparable to what exists for cloud resources (CSPM)
- Source: gravitee.io, isaca.org, cio.com

### 10. Guardrail Regression Testing in CI/CD
- Guardrails don't ship with test suites — teams manually create coverage after deployment
- No standard for "guardrail test coverage" (analogous to code coverage %)
- Model updates, new tools, new data sources all require re-validation — no automated pipeline
- O'Reilly: governance stays at "policy level" while engineers work at "pipeline level" — they don't meet
- Sources: avidoai.com, oreilly.com/radar, dev.to/htekdev

## Speculative Gaps (Plausible, Less Confirmed)

### A. Cross-Framework Observability for Guardrail State
- OTel GenAI semantic conventions exist for traces/spans but NOT for guardrail decisions
- No standard for "why was this guardrail triggered?" in a cross-framework trace
- Langfuse/Langsmith/Arize capture execution traces — not guardrail reasoning or policy linkage
- Partly confirmed: greptime blog identifies "semantic quality gaps" in traditional APM for agents

### B. Agentic MRM (Model Risk Management) for Banks
- SR 11-7 was written in 2011 — non-deterministic agents violate all its core assumptions
- Required shift: "Is the model accurate?" → "Is the system's behaviour safe, stable, and aligned with risk appetite?"
- fairplay.ai published a manual; no enterprise tooling yet built around it
- Regulators (OCC, Fed) have not yet updated MRM guidance for GenAI/agentic systems
- Sources: arxiv 2512.11933, treliant whitepaper, fairplay.ai

### C. Prompt Injection as a Solved Problem
- OpenAI admitted prompt injection "is unlikely to ever be fully solved" (VentureBeat)
- Current defenses are statistical/probabilistic — no deterministic solution
- Trail of Bits showed prompt injection → RCE in agentic IDEs (Oct 2025)
- Detection tools exist (Lakera, Rebuff) but are probabilistic, not hard gates
- NOT a gap to build into — it's an arms race that larger labs will keep iterating on

### D. Multi-Tenant Policy Isolation for SaaS
- SaaS builders deploying AI features need per-tenant guardrail policies (customer A's rules vs customer B's rules)
- No native multi-tenancy in NeMo, LlamaFirewall, or AWS Bedrock Guardrails
- Frontegg/Permit.io building this at the AuthZ layer — not yet mainstream
- Source: frontegg.com, digitaloneagency.com.au

## Saturated Areas (Don't Build Here)

### Content moderation / harmful output filtering
- AWS Bedrock Guardrails: blocks 88% harmful content, 99% accuracy on factual verification
- Llama Guard, ShieldGemma, Azure Content Safety — mature, commoditised
- All major cloud providers have native solutions; differentiation is hard

### LLM observability / tracing
- Langfuse, LangSmith, Arize Phoenix, Braintrust, Helicone — 8+ competitive tools
- OTel GenAI semantic conventions standardising the space
- Crowded, well-funded, fast-converging on feature parity

### Hallucination detection
- Amazon Bedrock Automated Reasoning checks (formal logic, 99% accuracy)
- RAG-based grounding — mature ecosystem
- Multiple research papers, production deployments at scale

### Basic prompt injection detection (input layer)
- Lakera Guard, Rebuff, Azure Prompt Shields — functional tools
- The UNSOLVED problem is indirect/tool-layer injection, not input layer filtering
- Input filtering is well-served; don't confuse with the harder problem

## Key Stats for Pitching
- 88% of orgs had confirmed/suspected AI agent security incidents in the past year (Gravitee)
- Only 14.4% of agent fleets have full security approval (Gravitee)
- 92% of agentic AI deployments experience cost overruns (IDC)
- 40%+ of agentic AI projects will be cancelled by 2027 (Gartner)
- Non-human identities outnumber humans 144:1 in some enterprises
- Agents operate over-permissioned: 90% hold 10x more privileges than required

## Reliable Sources for This Domain
- genai.owasp.org — authoritative for threat taxonomy and principles
- gravitee.io state of AI agent security report — best stats on current deployment state
- arxiv.org/html/2510.18563 — trust paradox in multi-agent systems
- arxiv.org/html/2512.11933 — MRM gaps for agentic AI in finance
- isaca.org industry news — IAM and authorization crisis
- cloudsecurityalliance.org — authorization lifecycle gaps
- rockcybermusings.com — independent gap analysis, high signal
- oreilly.com/radar — governance theatre vs engineering
- avidoai.com — guardrail testing for financial services
