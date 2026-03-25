# Agent Test Scenarios — HK FS Consulting

Multi-model deliberation outputs (consilium `--quick`) on realistic Capco/HSBC consulting scenarios.
Generated March 2026 using 5-model panel: Gemini 3.1 Pro, Claude Opus 4.6, Grok-4, Kimi K2.5, GLM-5.
(GPT-5.4-pro returned 403 — access-restricted at time of generation.)

## Scenarios

### proposal-architect.md
**HK retail bank: scoping an AI credit decisioning engagement**

Client framing: "a chatbot for loan officers." How to reframe, scope, de-risk, and propose.

Key insights:
- Pivot: "chatbot" → "AI-Powered Credit Underwriting Copilot" (decision support, not decision-maker)
- Two-track AI: predictive ML for scoring + generative AI for document synthesis/RAG
- Phase 1 PoC use cases: Policy Retrieval, Unstructured Data Summarization, Memo Generation
- HKMA instruments: 2019 High-Level Principles on AI, Aug 2023 GenAI Circular, SPM SA-2 (Model Risk)
- Three-horizon roadmap: Augmented Analyst (M1-4) → Intelligent Co-pilot (M5-9) → Supervised Autonomy (M10-15)
- HITL must be meaningful, not rubber-stamping; explainability is mandatory at individual loan level (SHAP/LIME)

Best for: Proposal structure, client reframing conversation, HKMA regulatory positioning.

---

### governance-sentinel.md
**HK bank: HKMA MRM controls for LLM credit application summarization**

What can go wrong, required controls, and oversight framework for an LLM deployed as "decision support."

Key insights:
- "Decision support is a governance fiction" — RMs will anchor on summaries within weeks; LLM is de facto in the decisioning chain regardless of label
- HKMA SA-2 model inventory: LLM summarization tool = a "model," must be registered and risk-rated (likely Medium-High)
- Prohibited Behaviours Register: explicitly what the model must never do, and must be tested not just documented
- 8-category validation framework: faithfulness, completeness, omission bias, hallucination, consistency, robustness, fairness, tone neutrality
- Data flow controls at each stage: classification, PII masking, inference logging, output filtering
- Cross-border transfer: PDPO Section 33 applies if cloud-hosted LLM infers offshore
- Three-lines-of-defence governance structure required; CRO sign-off given credit chain proximity

Best for: MRM framework design, HKMA exam/audit prep, risk committee presentations.

---

### eval-designer.md
**HK insurer: RAG evaluation framework for compliance Q&A system**

How to evaluate a RAG-based Q&A system answering IA/HKMA/SFC/PCPD compliance questions.

Key insights:
- Four-layer evaluation stack: Retrieval Relevance → Generation Fidelity → Answer Quality → Regulatory Defensibility
- Regulatory defensibility layer: "Would a compliance officer stake their practising certificate on this?"
- Hallucination rate: zero tolerance — one fabricated GL citation destroys trust permanently
- temporal_precision: 1.0 — zero tolerance for citing superseded/repealed provisions
- Cross-source recall: must retrieve from ALL relevant regulatory bodies (IA + HKMA + SFC + PCPD) for multi-jurisdictional queries
- Four difficulty tiers: factoid → scenario-based/multi-hop → adversarial/loophole → cross-lingual/colloquial
- Golden dataset: 300-500 triplets vetted by senior HK compliance officers; not generics, must be HK-specific

Best for: RAG system design, eval framework proposals, InsurTech/RegTech client work.

## Model Performance Notes (Mar 2026)

| Model | Strength | Weakness |
|-------|----------|----------|
| Claude Opus 4.6 | "Insight you didn't ask for" — named governance fiction, prohibited behaviours register, temporal precision risk | Occasionally over-structured |
| Gemini 3.1 Pro | Best structurer — concrete specs, numerical targets, difficulty tiers, slide-ready | Slightly less HK-specific than Opus |
| Grok-4 | Broad coverage, adds angles others miss (vendor mgmt, pricing model) | Generic — needs HK-specific overlays for client use |
| Kimi K2.5 / GLM-5 | Present but not dominant in these outputs | Coding-focused models, thinner on regulatory reasoning |

## Reuse

- Deliverable templates: Opus outputs from governance-sentinel.md (validation table, data flow diagram, governance structure) are client-ready
- Scenario bank: all 3 scenarios usable in `/consulting-prep` scenario practice mode
- Rerun: `consilium "..." --quick -o ~/docs/solutions/agent-tests/<name>.md` — use `--quick` for parallel batch (council mode rate-limits at 4+ concurrent)
