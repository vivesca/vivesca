---
name: Persona & Role Prompting in Multi-Agent LLMs — Research Landscape
description: Key papers, findings, and gaps on whether role/persona prompting helps or hurts in single-agent and multi-agent LLM settings (2024–2026)
type: reference
---

## Key papers

- **Zheng et al. (EMNLP 2024 Findings)** — arxiv:2311.10054 — core negative result: 162 roles, 9 models, 2410 MMLU questions; no statistically significant improvement over baseline; domain-aligned roles (coefficient 0.004) negligible
- **Hu & Collier (ACL 2024)** — "Quantifying the Persona Effect" — aclanthology.org/2024.acl-long.554 — persona explains small share of variance; modest shifts but small effect size
- **"Conformity, Confabulation, Impersonation" (C3NLP@ACL 2024)** — arxiv:2405.03862 — persona collapse in multi-agent; debate instructions worsen inconstancy; conformity = biggest failure mode
- **"From Single to Societal" (2025)** — arxiv:2511.11789 — demographic persona diversity → in-group favoritism, not independent perspectives; biases persist across LLMs and group sizes
- **"Dynamic Role Assignment for Multi-Agent Debate" (2025)** — arxiv:2601.17152 — Zhang et al. (Amazon AGI + NYU); best positive result: dynamically assigned roles +74.8% over uniform, +29.7% over random on GPQA/MathVision/RealWorldQA
- **"Understanding Agent Scaling via Diversity" (2026)** — arxiv:2602.03794 — "effective channels" framework; 2 diverse agents = 16 homogeneous; model + prompt diversity is the mechanism (not persona/role diversity specifically)
- **"Why Do Multi-Agent LLM Systems Fail?" (2025)** — arxiv:2503.13657 — Cemri et al.; role failures = 0.5% of failures; spec issues = 41.77%; improving role prompts alone yields only +9.4%
- **"Talk Isn't Always Cheap" (2025)** — arxiv:2509.05396 — model diversity in debate can backfire; sycophantic conformity propagates weaker agent errors to stronger agents
- **Mixture-of-Agents (2024)** — arxiv:2406.04692 — heterogeneous model mixes beat homogeneous ensembles; best positive result for model diversity
- **"Rethinking MoA" (2025)** — openreview.net/forum?id=ioprnwVrDH — challenges MoA benefit; weaker agents hurt stronger agents in debate settings
- **SPP (NAACL 2024)** — arxiv:2307.05300 — single LLM multi-persona self-collaboration; works only in GPT-4, not weaker models

## Key gaps (open as of Mar 2026)

1. No study combines model diversity + persona diversity to test interaction effect
2. No CrewAI role/backstory/goal ablation study published
3. Zheng et al. not replicated in multi-agent configuration
4. No domain-expert compliance/legal review persona study (all existing work: generic benchmarks)
5. Dynamic role assignment (Zhang et al.) not tested in enterprise/professional tasks

## Source reliability notes

- aclanthology.org pages: WebFetch works for HTML pages; PDFs return binary
- arxiv.org HTML pages (arxiv.org/html/...): WebFetch works cleanly
- arxiv.org/abs/... pages: WebFetch works for abstracts
- researchgate.net: partial content only via WebFetch
- ACL/EMNLP proceedings PDFs: return binary — use HTML or abs pages

## Summary verdict

Persona prompting = null or negative single-agent effect. In multi-agent: introduces conformity/bias failure modes that undermine the diversity goal. Model diversity = strong positive effect. Dynamic capability-aware role assignment = strong positive effect. Static human-declared persona roles = weak to null.

## Output

Full vault note: `/Users/terry/epigenome/chromatin/Persona vs Procedure in Multi-Agent Systems - Research.md`
