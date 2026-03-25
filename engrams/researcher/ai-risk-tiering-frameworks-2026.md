---
name: AI Risk Tiering Frameworks — Banking (Early 2026)
description: Survey of regulatory and industry AI risk tiering frameworks relevant to financial services, for use in bank AI governance consulting deliverables
type: reference
---

## Regulatory Frameworks

### EU AI Act (4-tier)
- Source: trail-ml.com, advisense.com, EBA factsheet Nov 2025
- Tiers: Unacceptable (prohibited) → High → Limited → Minimal
- High-risk banking use cases: credit scoring, creditworthiness assessment (confirmed by EBA), fraud detection, customer profiling, transaction monitoring
- High-risk AI definition: must be both an AI system AND fall within Annex III sectors (access to essential services/credit = banking's primary exposure)
- Governance for high-risk: conformity assessment, risk management system, data governance, technical documentation, human oversight, accuracy/robustness, post-market monitoring, registration in EU registry
- AI system definition test: 7 elements — machine-based, autonomous, adaptable, objective-driven, inference capable, output-generating, environment-influencing
- Key banking distinction: pure logistic regression with fixed coefficients = NOT AI system; ML models (RF, GB, NN) with adaptability = AI system
- Compliance timeline: Feb 2025 (prohibited uses); Aug 2026 (high-risk compliance)

### MAS AI Risk Management Guidelines (Nov 2025 consultation)
- Source: stephensonharwood.com, mas.gov.sg
- NOT a discrete tier system — uses materiality-based proportionality
- Risk materiality assessment dimensions: impact, complexity, reliance
- Core pillars: AI lifecycle controls, competence requirements, technology infrastructure, change management
- Governance: board-level oversight, risk culture, framework alignment with existing risk management
- 12-month transition period once finalized (~mid-2026 effective)
- FEAT principles (Fairness, Ethics, Accountability, Transparency) remain underlying foundation

### NIST AI RMF 1.0 (expanded 2024-2025)
- Source: nist.gov, ispartnersllc.com
- NOT prescriptive tiers — 4 functions: GOVERN, MAP, MEASURE, MANAGE (19 categories, 72 subcategories)
- Organizations create their own tiered profiles: "rigorous governance for high-risk, streamlined for low-risk"
- 2025 expansion: generative AI, supply chain, new attack models
- Strength: flexible, extensible. Weakness: no mandatory tiers means no enforceability.

### HKMA AI Guidance (2024)
- Source: mayerbrown.com, gibsondunn.com (JS-gated), kpmg.com/cn
- No formal tier system published as of early 2026
- Risk-based approach: "proportionate to the risks involved" but no published tier criteria
- Key 2024 circulars: GenAI customer-facing applications (principles-based); AI for AML/TF monitoring (Sep 2024)
- Board accountability: dedicated AI oversight committees required
- HKMA designated AI governance a "strategic supervisory priority" for 2026
- HKMA GenAI Sandbox++ in progress — real-world use case learning may generate future tiering guidance
- Cross-sector reference: HK Policy Statement on Responsible AI (Oct 2024) — risk-based, principles-only, no tiers

### US Treasury FS AI RMF (Feb 2026)
- Source: home.treasury.gov, finsights.cooley.com
- NIST AI RMF adapted for financial services
- Structure: 230 control objectives + AI adoption stage questionnaire
- Maturity-based staging: controls scale with adoption stage, not just risk level
- 100+ institutions participated in development
- Strength: most operationally specific framework for FS. Weakness: maturity-based staging conflates capability with risk.

## Industry Frameworks

### Microsoft Responsible AI Standard v2
- Source: verifywise.ai, microsoft.com, maginative.com
- Three review categories: General → Sensitive Use → Limited Access Use
- Sensitive Use triggers: consequential impact on individual's legal status or life opportunities
- Review gate: Sensitive Uses and Emerging Technologies team; 396 cases reviewed in 2024 (77% GenAI)
- Impact Assessment required before development, updated annually
- Annual transparency report published; 2025 added Frontier Governance Framework for frontier models
- Strength: operationally embedded in development workflow. Weakness: internal framework, not publicly auditable.

### Deloitte Gen AI Risk Framework
- Source: deloitte.com
- 4 risk categories (not tiers): Enterprise Risks, Gen AI Capability Risks, Adversarial AI Risks, Marketplace Risks
- Explicitly intersectional — not a hierarchy
- Banking-specific finding: fraud losses projected $40B by 2027 (up from $12.3B in 2023)
- No formal tier criteria published; framework is risk-type taxonomy, not severity tiering

### KPMG Trusted AI Framework
- Source: kpmg.com (US and CN)
- 5 pillars: AI Strategy & Risk Appetite, Governance Structure, Policies & Standards, Model Risk Management, Third-Party Risk Management
- "Risk Tiering to accelerate innovation within risk-weighted guardrails" — mentioned but not detailed publicly
- HK-specific: directly aligned to HKMA 2024 guidance
- Strength: explicitly connects to board-level accountability. Weakness: framework detail is client-gated.

### McKinsey AI Risk Governance
- Source: mckinsey.com
- 6×6 framework: 6 risk categories × 6 business contexts (matrix approach)
- Risk categories include: fairness impairment, data privacy, third-party, performance/explainability, regulatory, reputational
- For banking: model risk management function as natural home for AI risk assessment
- 2025 addition: agentic AI risk taxonomy update
- Practical recommendation: update MRM standards for gen-AI-specific risks (handling changing inputs, multi-step interactions)
- Strength: cross-risk matrix prevents siloing. Weakness: no published tier criteria.

### ISO/IEC 42001:2023 + 42005:2025
- Source: schellman.com, aarc-360.com
- NOT a tier system — management system standard (certifiable)
- 38 controls covering risk assessment, impact assessment, lifecycle oversight
- ISO 42005 (Apr 2025): companion standard for AI system impact assessments on groups/society
- Strength: internationally certifiable, aligns with ISO 27001 pattern organizations already use. Weakness: no tier enforcement.

### BIS/BCBS Supervisory Approach
- Source: banking.vision, bis.org publications
- AI as ICT risk under DORA (BaFin Dec 2025 classification confirmed)
- 3-pillar governance: Strategic (board), Organizational (3LoD), Operational (lifecycle)
- Supervisory priority: integration depth and operational criticality over technical autonomy
- "Degrees of autonomy are technically relevant but not a supervisory priority" — integration risk is
- FSB monitoring AI adoption since 2025 — systemic risk lens, not use-case lens

## What Makes a Framework Actionable vs. Checkbox

Cross-source synthesis (guidehouse.com, banking.vision, obsidiansecurity.com):

**Useful frameworks have:**
1. Tier-linked gate criteria — tier determines WHAT you must do before deploying (not just how much documentation)
2. Embedded in SDLC — risk assessment happens at intake, not post-deployment audit
3. Shared artifacts — model cards, bias tests, red-team results built into workflow
4. Operational metrics — time to risk assessment, control test pass rates, explainability coverage
5. Escalation paths — clear "who decides what" when a use case is borderline
6. Integration with existing risk frameworks (MRM, DORA, GDPR) — parallel governance fails

**Checkbox frameworks produce:**
- One-time compliance documentation
- Post-deployment risk assessments
- Governance committees with no kill authority
- Tier labels with no differentiated governance requirements

## Source Reliability Notes
- EBA factsheet (Nov 2025): most authoritative on EU AI Act banking mapping
- advisense.com: best technical breakdown of AI Act credit model classification
- guidehouse.com: best practical governance framework (Guidehouse 2026 article)
- banking.vision: best BaFin/DORA integration explanation
- kpmg.com/cn (HK Banking Report 2025): best HKMA-aligned framework
- BIS PDFs return binary — use search result summaries instead
- Microsoft RAI Standard PDF returns binary — use search summaries
- Gibson Dunn, Hauzen LLP pages are JS-gated — return CSS/empty
