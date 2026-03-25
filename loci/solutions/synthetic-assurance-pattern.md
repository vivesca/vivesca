# Synthetic Assurance: AI Faking Evidence of Human Understanding

## The Pattern

When organisations require humans to demonstrate understanding of AI-generated outputs (for compliance, audit, or governance), exhausted or time-pressed staff will use AI to generate those explanations — creating a closed loop where AI output is validated by AI-generated rationale, signed off by humans too tired to verify either.

## Origin

Identified by Gemini during a consilium red team session (Feb 18, 2026) stress-testing a consulting framework on AI adoption costs. Amplified by Grok into a systemic cascade.

## The Cascade

1. AI generates code/models/decisions (Cognitive Debt — nobody fully understands the output)
2. Governance requires human-authored documentation proving understanding (SR 11-7 model documentation, IFRS 9 expert judgment overlays, BCBS 239 data lineage)
3. Staff are exhausted from AI-concentrated decision load (AI Vampire effect)
4. Staff use GenAI to write the required documentation
5. Reviewers (also exhausted) approve without deep validation (Completion Theater)
6. Result: **Human-in-the-Loop control is destroyed** while appearing formally satisfied

## Why It's Dangerous

- It's invisible to standard governance checks — the documentation *exists* and *looks correct*
- It compounds: each cycle increases the gap between documented understanding and actual understanding
- It's self-reinforcing: the more governance demands "proof of understanding," the more staff use AI to produce that proof
- Detection requires comparing interview depth against documentation quality — few audit methodologies do this

## Regulatory Impact (Banking)

- **HKMA:** Destroys HITL control → MIC (Manager-in-Charge) regime failure
- **PRA/BoE:** SS1/23 model documentation integrity → supervisory findings
- **BCBS 239:** Principle 6 (adaptability) requires comprehensible data aggregation → lineage becomes fictional
- **IFRS 9:** Expert judgment overlays on ECL staging may be hallucinated → potential restatement
- **Conduct risk:** Section 72A (Banking Ordinance, HK) investigation into management fitness if discovered

## Detection Approaches

- Compare documentation quality against staff interview depth (do they understand what they documented?)
- Monitor for stylistic uniformity in model documentation (AI-generated text has detectable patterns)
- Track documentation production speed vs historical baselines (suspiciously fast = likely AI-generated)
- Cross-reference documented rationale against actual model behaviour (hallucinated explanations won't match)
- Audit prompt logs (if available) for documentation-generation queries

## Consulting Application

**Pitch line:** "Your people are using AI to fake the evidence that they understand AI. We detect this before your regulator does."

**Status:** Currently theoretical (Feb 2026). Watch for HKMA/PRA examination findings citing AI-generated model documentation or HITL control failures. Revisit upon first publicised regulatory action.

## Broader Applicability

This pattern isn't banking-specific. It applies anywhere governance requires human attestation of understanding:
- Medical AI: doctors using AI to write clinical justifications for AI-recommended treatments
- Legal: lawyers using AI to draft explanations of AI-generated contract analysis
- Education: students using AI to write reflections on AI-assisted assignments
- Any ISO/SOX/SOC2 environment requiring human sign-off on automated processes

The universal form: **any time you mandate human understanding as a control, and provide AI tools that can simulate understanding, the control will be gamed.**

## Related

- [[Research - Human Cost of AI Adoption]] — full framework
- [[LLM Council - Human Cost Framework Red Team - 2026-02-18]] — council transcript
- Spiridonov, ["The Quality Cost of the AI Vampire"](https://forge-quality.dev/articles/quality-cost-of-ai-vampire) — Completion Theater concept
