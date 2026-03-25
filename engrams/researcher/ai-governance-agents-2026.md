---
name: AI Governance for Agents — Risk & Regulatory Research (Mar 2026)
description: Comprehensive research on MRM, audit trails, regulatory guidance, threat taxonomies, governance frameworks, autonomy levels, and responsible AI for agentic systems. Specifically covering GARP RAI exam topics and FS consulting context.
type: reference
---

## GARP RAI Exam Structure

- 5 modules: (1) AI + Risk Intro, (2) Tools & Techniques, (3) Risks & Risk Factors, (4) Responsible & Ethical AI, (5) Data & AI Model Governance
- 80 questions, 4 hours, 100-130h prep
- Agentic AI is NOT a distinct module — surfaces in Modules 3 (agent risks), 4 (guardrails, constitutional AI), 5 (MRM for dynamic models, audit trails)
- Registration open for April 2026 exam
- Source: https://www.garp.org/rai

## SR 11-7 and Agentic AI

**Where it holds:** Sound governance, independent validation, effective challenge remain valid foundations.
**Three critical gaps (GARP analysis, Feb 2026):**
1. Static assumption: SR 11-7 assumes "simplified, relatively static" models — agents autonomously recalibrate; periodic validation misses material behavioral changes
2. Third-party concentration: No mechanism for correlated systemic risk from shared LLM vendors across institutions
3. Explainability thresholds: No adequacy standard defined for opaque LLM reasoning

**Path forward:** Targeted refinement (not replacement). Complement periodic validation with continuous monitoring + use-based controls.
Source: https://www.garp.org/risk-intelligence/operational/sr-11-7-age-agentic-ai-260227

## Regulatory Guidance — Agent-Specific Statements

**US:** No agent-specific guidance; SR 11-7 applies by OCC confirmation (2025 bulletin). Deregulatory posture.
**UK:** DRCF Oct 2025 Call for Views on Agentic AI. Findings published Jan 2026. No agent-specific legislation planned — outcome-focused, risk-based approach. FCA: no new rules; Consumer Duty + SM&CR apply to agent outputs. PRA SS1/23 covers agents.
  - Source: https://www.drcf.org.uk/news-and-events/news/call-for-views-agentic-ai-and-regulatory-challenges
  - Source: https://iapp.org/news/a/uk-drcf-highlights-risk-based-approach-to-agentic-ai
**EU:** Hard deadline Aug 2, 2026. Credit scoring and AML agents = high-risk; require conformity assessment, "automatic logging," human oversight mechanisms.
**HK:** GenAI Sandbox++ (Mar 2026) explicitly covers agentic AI governance embedding in 3 lines of defence + "AI vs AI" frameworks.
**SG:** MAS AIRG (consultation closed Jan 2026) explicitly covers "complex AI, including GenAI and AI agents." Final guidelines + 12-month transition → compliance ~late 2026/2027.
  - Source: https://kpmg.com/sg/en/services/advisory/alerts/mas-guidelines-artificial-intelligence-risk-management-airg-2025.html
**BIS:** 10-action framework for AI governance (Jan 2025). Not agent-specific. Three-lines-of-defence model applies.
  - Source: https://bankingjournal.aba.com/2025/01/bis-drafts-guidance-for-central-banks-on-ai-adoption/
**IIF-EY 2025 survey:** 54% G-SIBs piloting agents; 100% planning. Top governance priorities: compliance (73%), performance monitoring (71%).
  - Source: https://www.iif.com/Publications/ID/6322/2025-IIF-EY-Annual-Survey-Report-on-AI-Use-in-Financial-Services

## Agent-Specific Threat Taxonomies

**OWASP Top 10 for Agentic Applications (Dec 2025):**
Key threats: prompt injection (#1, in 73% of production deployments), goal hijacking, tool misuse, identity/privilege abuse, memory poisoning, unauthorized action execution.
- Source: https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/

**OWASP Multi-Agentic System Threat Modeling Guide (2025):**
Agent-to-agent collusion, competitive exploitation, trust boundary failures in orchestrated systems.
- Source: https://genai.owasp.org/resource/multi-agentic-system-threat-modeling-guide-v1-0/

**MAESTRO Framework (CSA, Feb 2025):**
7-layer: foundation model → agent memory → agent reasoning → tool/API interface → multi-agent communication → orchestration → deployment environment. Companion to OWASP ASI.
- Source: https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro

**MITRE ATLAS (Oct 2025 update):**
Added 14 new agentic AI techniques (Zenity Labs collaboration). Total: 15 tactics, 66+ techniques. ~70% map to existing security controls.
- Source: https://atlas.mitre.org/

**Six multi-agent failure modes (arxiv:2508.05687):**
Cascading failures, inter-agent communication failures, monoculture collapse, conformity bias, deficient theory of mind, mixed motive dynamics.
"A collection of safe agents does not guarantee a safe collection of agents."

## Audit Trail Standards

**OpenTelemetry GenAI Semantic Conventions v1.37+:**
Defined attributes: gen_ai.request.model, gen_ai.usage.input_tokens, gen_ai.usage.output_tokens, gen_ai.provider.name. Agent-level semantic conventions (Tasks, Actions, Agents, Teams, Memory operations) in active development.
- Source: https://opentelemetry.io/blog/2025/ai-agent-observability/

**EU AI Act requirement:** "Automatic logging" is named requirement for high-risk systems — agent action traces are in scope.

**FS regulatory requirement baseline:** UTC timestamps, agent ID + version, tool calls + parameters, output + reasoning trace, human approval gates traversed.

**Key tooling:** Datadog AI Agent Monitoring (DASH 2025), LangSmith (free 5K traces/month), Langfuse (open source/self-hostable), agent gateways with OTel instrumentation.

## Agent Autonomy Levels (Knight Columbia Institute, 2025)

L1=Operator (user full control), L2=Collaborator (shared planning), L3=Consultant (agent autonomous, user guides), L4=Approver (user approves consequential actions), L5=Observer (fully autonomous, emergency off-switch only).
**FS consensus:** L4 maximum; L3 for routine workflows. L5 not yet in FS production.
**Autonomy certificates:** Proposed third-party-issued digital credentials specifying max authorized autonomy level.
- Source: https://knightcolumbia.org/content/levels-of-autonomy-for-ai-agents-1

**Agentic Trust Framework (CSA, Feb 2026):**
4 maturity levels: Bounded → Supervised → Delegated → Autonomous. Promotion requires 5 gates: performance, security validation, business value, clean incident record, governance sign-off.
- Source: https://cloudsecurityalliance.org/blog/2026/02/02/the-agentic-trust-framework-zero-trust-governance-for-ai-agents

## Governance Frameworks

**NIST AI RMF:** Govern / Map / Measure / Manage. 2025 updates emphasize model provenance, data integrity, third-party assessment.
  - Source: https://www.nist.gov/itl/ai-risk-management-framework

**ISO 42001 (Dec 2023):** 38 controls, 9 governance areas. PDCA methodology. Overlaps with EU AI Act requirements on data governance, transparency, human oversight.
  - Source: https://www.deloitte.com/us/en/services/consulting/articles/iso-42001-standard-ai-governance-risk-management.html

**BIS 10-action framework (Jan 2025):** Interdisciplinary AI committee, risk profile, inventory, controls assessment, monitoring, incident reporting, workforce skills, ongoing review.

**Governance-as-a-Service (arxiv:2508.18765):** Runtime proxy filtering agent actions on programmable rules — non-invasive, policy-as-code enforcement.

**PwC multi-agent validation:** Agent-level (separate model ID per agent) + system-level (integrated system model ID for emergent risks). Reuse rule: new context = incremental risk assessment.

**KPMG 4-pillar evolved MRM:** Risk-Based Governance + Development + Validation Frameworks + Ongoing Monitoring.

## Responsible AI / Guardrails

**Constitutional AI (Anthropic, Jan 2026 model spec):**
4-tier priority hierarchy: safety > ethics > regulatory compliance > helpfulness.
7 absolute prohibitions (hardcoded). Remaining behaviors softcoded — operator/user can adjust within constitutional limits.
Mirrors EU AI Act structure — intentional.

**Anthropic RSP v3.0 (Feb 24, 2026):**
ASL-3 activated May 2025 (chemical/biological threats). Mandatory Frontier Safety Roadmaps + periodic Risk Reports q3-q6.
Notable: v3.0 removes prior commitment to pause training if safety controls are outpaced.
- Source: https://www.anthropic.com/news/responsible-scaling-policy-v3

**OpenAI Preparedness Framework v2 (April 15, 2025):**
Explicitly addresses agentic capabilities as risk category. Capabilities Reports + Safety Advisory Group + Board oversight. Introduced Research Categories for pre-tracked emerging capabilities.
- Source: https://openai.com/index/updating-our-preparedness-framework/

**HITL patterns:** Full HITL (irreversible high-stakes), exception-based HITL (production standard, triggered by confidence/anomaly/blast-radius), supervisory HITL (monitoring + emergency off-switch).

**Kill switches:** Phase rollouts across 3 rings with automatic kill switches on error-rate thresholds. Graceful degradation (fall back to human-routed workflow, not silent failure).

## 2025 AI Agent Index Key Findings (arxiv:2602.17753)

Documented 30 deployed agents. Critical governance gaps:
- 25/30: no internal safety testing disclosure
- 23/30: no third-party testing info
- Only 4 publish agent-specific system cards (ChatGPT Agent, Claude Code, Gemini 2.5, OpenAI Codex)
- Enterprise platforms: mostly optional guardrail modules, minimal disclosed built-in protections
- Model concentration: nearly all depend on GPT/Claude/Gemini — single points of failure
- Accountability diffusion: no single entity bears clear responsibility across provider/orchestrator/deployer chain

## Agent Red Teaming

What's different vs static model testing: multi-step attack chains, tool access abuse, memory poisoning, inter-agent manipulation, indirect prompt injection (instructions in content agent reads), goal drift over extended operation, sandboxing escapes.

**EU AI Act:** Mandates adversarial testing for high-risk systems (Aug 2, 2026 deadline).

**Microsoft Azure AI Foundry:** Released automated AI Red Teaming Agent in 2025 — first major automated tool for agent-specific red teaming.

**AIVSS:** OWASP's AI Vulnerability Scoring System for agentic AI, aligned with CVSS principles.
- Source: https://aivss.owasp.org/

## WebFetch Source Reliability Notes

- garp.org article pages: works well
- opentelemetry.io/blog: works
- knightcolumbia.org: works
- iapp.org/news: works
- arxiv.org/html/: works (HTML versions only — PDFs are binary garbage)
- BIS PDFs (bis.org/*.pdf): binary — use bankingjournal.aba.com or regulationtomorrow.com summaries
- IIF PDFs (iif.com/LinkClick): binary — use EY newsroom press release page instead
- mckinsey.com/capabilities/risk: timeout
- genai.owasp.org resource pages: JS-gated; WebFetch returns CSS only — use WebSearch snippets
- MAS.gov.sg main pages: JS-gated; use KPMG/law firm summaries
