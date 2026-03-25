# Agentic AI Research Gaps for Consulting — LRN-20260313-002

## Context

Map of the agentic AI stack with research gap assessment. Oriented toward: what can a practitioner-consultant credibly research and publish that academics and big firms won't?

## The Stack

### 1. Reasoning Engine (LLM)
- **Benchmarked:** Heavily (MMLU, HumanEval, GPQA, etc.)
- **Gap:** None for consulting — this is commoditised research
- **Consulting angle:** Model selection guidance (which LLM for which task), cost-performance tradeoffs

### 2. Tool Use
- **Benchmarked:** Moderate (BFCL, ToolBench, API-Bank)
- **Gap:** Getting crowded, diminishing returns on new benchmarks
- **Consulting angle:** Enterprise tool integration patterns, error handling in production

### 3. Memory ← ACTIVE (mnemon)
- **Benchmarked:** Barely — vendor self-benchmarks only, no independent practitioner comparison
- **Gap:** Wide open. No in-situ study, no production-oriented comparison, no enterprise-grade evaluation
- **Why gap persists:** Integration problem (not algorithmic), hard to standardise, enterprise scale not reproducible in labs, grad students can't write "I tried 10 pip installs" papers
- **Consulting angle:** "Which backend for enterprise?" is a $200K engagement question with no public answer

### 4. Planning / Multi-step Decomposition
- **Benchmarked:** Task-specific (SWE-bench for coding, WebArena for web tasks)
- **Gap:** No general planning benchmark. No comparison of planning strategies (ReAct vs plan-then-execute vs tree-of-thought) under enterprise constraints (latency, cost, reliability)
- **Consulting angle:** Planning strategy selection for regulated environments. "How do you audit an agent's planning?"

### 5. Evaluation / Judging Agent Output
- **Benchmarked:** Early (AgentBench, GAIA)
- **Gap:** Wide open. How to evaluate agent output quality in production when ground truth doesn't exist? LLM-as-judge is the default but poorly understood
- **Consulting angle:** Evaluation frameworks for regulated industries (MRM, SR 11-7). Directly maps to GARP RAI credential. "How does model risk management apply to agents?"
- **Synergy:** evals-skills plugin already in toolkit

### 6. Multi-Agent Coordination
- **Benchmarked:** Almost none
- **Gap:** Very open. When to use multi-agent? How to prevent cascading errors? How to audit multi-agent decisions?
- **Consulting angle:** Governance frameworks for multi-agent systems in banking. HKMA/MAS haven't addressed this yet.

### 7. Safety / Control / Alignment for Autonomous Agents
- **Benchmarked:** Theoretical papers, few practical benchmarks
- **Gap:** Huge gap between academic alignment research and "how do I safely deploy an agent that can send emails?"
- **Consulting angle:** Practical agent guardrails for FS. Permission models, human-in-the-loop design, audit trails.

### 8. Human-Agent Interaction / UX
- **Benchmarked:** Almost none
- **Gap:** Massively undervalued. How should humans work with AI agents? Autonomy calibration, trust, override patterns, skill/hook systems
- **Consulting angle:** Terry's daily Claude Code workflow IS a case study. The skill system, hooks architecture, autonomy levels — this is original practitioner research.

## Priority for Consulting Career

| Area | Novelty | Consulting Value | Effort | Priority |
|------|---------|-----------------|--------|----------|
| Memory (mnemon) | High | High | Medium (building) | **1 — in progress** |
| Evaluation/MRM for agents | High | Very High | Medium | **2 — natural next** |
| Human-agent interaction | Very High | High | Low (documenting existing practice) | **3 — garden post series** |
| Planning audit | Medium | High | High | 4 — future |
| Multi-agent governance | High | Medium (premature) | High | 5 — future |
| Safety/control practical | Medium | High | Medium | 6 — future |

## Key Insight

The research areas with the widest gaps are exactly the ones where enterprise needs diverge from academic incentives. Memory, evaluation, and human-agent interaction are all integration/systems/UX problems — not algorithmic problems. ML venues reward algorithms. This structural mismatch creates a durable consulting niche for practitioners who do the messy work.

## Related
- `consulting-memory-backend-gap.md` — deep dive on memory specifically
- `ai-agent-memory-landscape-2026.md` — framework landscape
- `memory/project_mnemon_goals.md` — mnemon goal tensions
- `memory/feedback_why_gap_exists.md` — structural gap analysis framework
