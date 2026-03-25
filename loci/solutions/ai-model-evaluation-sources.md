# AI Model Evaluation Sources

Where to look when comparing frontier models. Each source has different strengths and failure modes.

## Leaderboards

| Source | What It Measures | Strengths | Weaknesses |
|--------|-----------------|-----------|------------|
| **Arena (arena.ai)** | Human preference (blind A/B Elo) | Ecological validity, hard to game | Style bias, slow vote accumulation, tech-skewed voters |
| **Artificial Analysis** | Automated benchmarks + infra metrics | Reproducible, provider-level, pricing | Benchmark contamination possible, doesn't capture conversational quality |
| **LiveBench** (livebench.ai) | Auto-generated monthly questions | Contamination-proof (new questions monthly) | Narrow task coverage |
| **SEAL** (Scale AI) | Private held-out evals | Can't train on what you can't see | Less public, enterprise-focused |
| **SWE-rebench** (swe-rebench.com) | Cost/problem + resolve rate | Only public source for cost-per-task | Benchmark harness specific, not production |
| **Terminal-Bench** (tbench.ai) | Multi-step agentic CLI tasks (229 tasks) | Directly measures terminal agent capability (compiling, server setup, chained commands) | Young benchmark, smaller task set |
| **Aider** (aider.chat/docs/leaderboards) | Code editing cost/quality | Practical coding proxy | Single tool's harness |
| **HAL SWE-bench Mini** (hal.cs.princeton.edu) | Controlled 50-task cost/accuracy | More controlled than full SWE-bench | Small sample |

## Sniff-Test for Unknown Benchmarks

Before trusting a new leaderboard, check:

1. **Published methodology?** Real benchmarks have papers, open eval harnesses, or at minimum detailed methodology pages. No paper = no accountability.
2. **Community scrutiny?** If nobody is arguing about it, nobody is using it. Search for discussions, citations, critiques.
3. **Results surprise anyone?** If rankings perfectly match a vendor's marketing narrative, it's probably marketing. Legitimate benchmarks produce at least some counterintuitive results.
4. **Name squatting?** Check whether the site borrows the name of a reputable benchmark. Example: `apex-testing.org` (unverified coding benchmark) vs APEX from Mercor (published knowledge-work benchmark with arxiv paper).
5. **Who runs it?** Anonymous or untraceable operators = red flag. Established benchmarks have institutional backing or known researchers.

### Known Unverified / Suspicious Sources

| Source | Red Flags |
|--------|-----------|
| **apex-testing.org** | No community discussion, no published methodology, name-squats on Mercor's APEX, suspiciously clean results (Feb 2026) |

## Key Gotchas

- **Arena Elo scores shift daily** as votes accumulate. New models (< 1 week) are unreliable.
- **Vendor-reported benchmarks are not third-party benchmarks.** Qwen 3.5, Seed 2.0 — self-reported. Flag as `[vendor-reported]`.
- **"Thinking" variants are listed separately** on Arena — check both.
- **Verbosity inflates effective cost.** Sonnet 4.6 = 4.8x tokens vs 4.5 on agentic tasks (GDPval-AA). Opus 4.6 adaptive = 4.8x median. MiniMax M2.5 = 3.7x median.
- **Per-token pricing ≠ per-task cost.** SWE-rebench: $0.23/resolved (MiniMax) vs $6.62/resolved (Claude Code) on same benchmark.

## Enterprise Cost Sources

- **Deloitte** — "Token FinOps" framework: real-time monitoring, chargebacks, ROI thresholds
- **Bessemer** — AI pricing playbook: token → workflow → outcome pricing evolution
- **Adam Holter** — Agentic workflows increased per-task tokens 10-100x since Dec 2023

## When to Use What

- "Which model do users prefer?" → Arena
- "Which scores highest on standardised tasks?" → AA, LiveBench
- "What will it actually cost per task?" → SWE-rebench, Aider
- "Is this model contaminated?" → LiveBench, SEAL
- "What should I use for MY workflow?" → Run your own 10-prompt eval
