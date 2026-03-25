---
name: AI Agent Memory Benchmarks — Academic Literature Survey
description: Comprehensive map of existing academic benchmarks comparing AI agent memory systems; identifies what exists, what's missing, and novelty gap for a 10-backend empirical survey
type: reference
---

# AI Agent Memory Benchmarks — Literature Survey (Mar 2026)

## What Exists

### 1. Survey Papers (no empirical comparison of backends)
- **arxiv:2512.13564** "Memory in the Age of AI Agents" (Dec 2025) — taxonomy survey, covers benchmarks and open-source frameworks. No head-to-head backend eval. Companion GitHub: Shichun-Liu/Agent-Memory-Paper-List.
- **TechRxiv** "Memory in LLM-based Multi-agent Systems" — survey on mechanisms, not empirical.

### 2. Benchmark Datasets (evaluate memory *tasks*, not frameworks)
- **LoCoMo** (Snap Research, 2024) — long-turn dialogues, 16K–26K tokens, synthetic personas. Gold standard but recognized as too short/simple.
- **LongMemEval** (Wu et al., ICLR 2025) — 5 memory abilities, avg 115K tokens, more temporal reasoning. GitHub: xiaowu0162/LongMemEval.
- **MemoryAgentBench / ICLR 2026** (arxiv:2507.05257, Hu/Wang/McAuley) — 4 competencies (retrieval, test-time learning, long-range understanding, conflict resolution), 10+ datasets. **INCLUDES Mem0 and Cognee as evaluated systems, plus MemGPT, GraphRAG, HippoRAG-v2, BM25, embedding RAG, long-context models.** Notably missing: Zep, Graphiti, Letta, LangMem. Primarily synthetic. Independent academic work.
- **AMA-Bench** (arxiv:2602.22769, Feb 2026) — agentic trajectory memory (not conversational). Tests MemGPT, MemoryBank, MemoRAG, SimpleMem, RAG systems, long-context models. ~15 methods total. Independent academic. Key finding: existing memory systems often underperform vs long-context baselines on agentic tasks.
- **MemBench** (Tan et al. 2025) — factual vs reflective memory levels.
- **ConvoMem** (arxiv:2511.10523) — reveals long-context beats RAG (70–82% vs 30–45%) for <150-turn histories. Tests Mem0 explicitly.
- **GoodAI LTM Benchmark** (NeurIPS 2024) — conversational LTM with distraction segments. Vendor-produced (GoodAI). Tests MemGPT, GPT-4, Claude. Synthetic-but-realistic.

### 3. Vendor-Produced Evaluations (contested, single-benchmark focus)
- **Mem0 paper** (arxiv:2504.19413) — tests on LoCoMo vs 6 categories of baselines. Vendor-authored. Claims 26% accuracy over OpenAI memory. Baseline = "OpenAI memory" not Zep/Letta/Cognee.
- **Zep paper** (arxiv:2501.13956) — tests on DMR + LongMemEval vs MemGPT + RAG baselines only. Vendor-authored. Claims 10% over Mem0 on LongMemEval (after correcting Mem0's implementation errors). Contested by Mem0.
- **Letta blog benchmark** — tests Letta filesystem vs Mem0 graph on LoCoMo. 74.0% vs 68.5%. Vendor-produced.
- **Cognee eval page** — tests Cognee vs Mem0, Graphiti, LightRAG on 24 HotPotQA questions. Vendor-produced. 45 repeated runs.
- **MemR3** (arxiv:2512.20237, Dec 2025) — proposes MemR3 retrieval controller, tests on LoCoMo with baselines: A-Mem, LangMem, Mem0, Self-RAG, RAG, Zep (backend). Independent academic. Does NOT compare Cognee, Letta, Graphiti full stack.

### 4. Framework-Proposing Papers (each compares against prior SOTA, not cross-framework)
- **MemGPT** (arxiv:2310.08560, Oct 2023) — OS-inspired hierarchy. Tested vs GPT-4 full-context on MSC dataset.
- **A-Mem** (arxiv:2502.12110, NeurIPS 2025) — Zettelkasten-style. Tests vs Mem0, LangMem + others. LoCoMo + task benchmarks.

## What Is Missing (The Gap)

### Critical absences in the literature:
1. **No independent academic paper compares ≥5 production memory backends side-by-side on the same benchmark.** The closest is MemoryAgentBench (Mem0 + Cognee + MemGPT) — but it omits Zep, Graphiti, Letta, LangMem entirely.
2. **No real/in-situ workload study.** All benchmarks are synthetic (LoCoMo, LongMemEval, MemoryAgentBench) or semi-synthetic (GoodAI LTM). No longitudinal deployment study with real users exists.
3. **No experience report.** Zero "experience report" style papers in the systems/SRE tradition comparing these frameworks in production contexts.
4. **Latency/cost/ops not benchmarked academically.** Vendor claims on token reduction (Mem0: 90%, Zep: 90%) and latency (Zep: p95 0.6s) are each measured against different baselines, not each other.
5. **Backend diversity is narrow.** Even the broadest academic benchmark (AMA-Bench at ~15 methods) focuses on algorithmic approaches (RAG variants, summarization, LTM agents) rather than the specific library ecosystem (Mem0 vs Zep vs Cognee vs LangMem as installable packages).
6. **Graph vs vector vs hybrid architectures** not isolated as independent variables across backends.
7. **No multi-task/multi-domain evaluation.** All existing evals use 1–2 benchmark datasets. No paper covers conversational + agentic + code + document tasks within one framework comparison.

## Novelty Assessment for a 10-Backend Empirical Survey

**A 10-backend empirical survey would be clearly novel IF it:**
- Includes: Mem0, Zep/Graphiti, Letta, LangMem, Cognee, A-Mem, MemoryOS, Memobase, Memary, GoodAI LTM Agent (or similar 10th)
- Uses ≥2 benchmarks (LoCoMo + LongMemEval at minimum; ideally + AMA-Bench tasks)
- Measures: accuracy, latency (p50/p95), token cost, setup complexity, cold-start vs warm retrieval
- Is authored independently (not by any framework's team)
- Includes real or near-real workload component (even a small-n user study)

**The vendor benchmark wars (Mem0 vs Zep vs Letta) have created demand but no authoritative independent arbiter.** MemoryAgentBench (ICLR 2026) is the closest to a credible independent evaluation but covers only 2–3 of the 10 frameworks practitioners actually use.

## Key Sources for Further Work

- arxiv:2507.05257 — MemoryAgentBench (most comprehensive independent eval, though framework-incomplete)
- arxiv:2602.22769 — AMA-Bench (broadest method count, agentic focus)
- arxiv:2512.13564 — Survey (best taxonomy paper)
- arxiv:2501.13956 — Zep paper (vendor, temporal KG details)
- arxiv:2504.19413 — Mem0 paper (vendor, production architecture)
- blog.getzep.com/lies-damn-lies-statistics — Zep's rebuttal of Mem0 benchmark (methodology critique, useful for understanding what "correct" evaluation looks like)
- letta.com/blog/benchmarking-ai-agent-memory — Letta's vendor benchmark
- github.com/HUST-AI-HYZ/MemoryAgentBench — code + dataset
- github.com/Shichun-Liu/Agent-Memory-Paper-List — paper list (up to date as of early 2026)
- github.com/DEEP-PolyU/Awesome-GraphMemory — graph-memory specific paper list

## Misinformation Patterns in This Space
- All vendor "X% improvement" claims use different baselines — cross-vendor comparison via cherry-picked numbers is unreliable.
- LoCoMo is recognized in the community as too simple (Zep prefers LongMemEval; AMA-Bench explicitly criticizes dialogue-centric benchmarks for agentic tasks).
- "Production-ready" claims are all vendor-sourced; no independent deployment study exists.
