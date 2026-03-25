---
name: Multi-Agent LLM Orchestration Patterns for Quality (Mar 2026)
description: Empirical findings on what actually works for maximizing LLM output quality via multi-agent patterns — debate, refinement, competition, MoA, judge design, frameworks
type: reference
---

## Key papers

- **Mixture-of-Agents (MoA)** — arxiv:2406.04692, ICLR 2025 Spotlight — heterogeneous 6 models outperform 6 identical models (61.3% vs 56.7% AlpacaEval); 3 layers optimal; first aggregation step = biggest quality jump; 65.1% AlpacaEval vs GPT-4o 57.5%.
- **Understanding Agent Scaling via Diversity** — arxiv:2602.03794 — "effective channels" K* framework; 2 diverse agents = 16 homogeneous agents; diversity is the mechanism, not raw count.
- **MAD Scaling Challenges** — ICLR Blogposts 2025 — d2jud02ci9yv69.cloudfront.net/2025-04-28-mad-159/blog/mad/ — default MAD frameworks fail to consistently beat self-consistency (SC 82.13% vs MAD 74.73% on MMLU); SC scales better with tokens than MAD.
- **Multi-Agent Debate Adaptive Stability** — arxiv:2510.12697, NeurIPS 2025 — debate for judges converges in 2–8 rounds; adaptive KS-test stopping = same accuracy as fixed 10 rounds; gains most pronounced on hard tasks (LLMBar, TruthfulQA), modest on easy ones.
- **Talk Isn't Always Cheap** — arxiv:2509.05396 — weaker agent in debate group causes 5–12pp degradation; sycophantic conformity propagates; agents flip correct → incorrect answers across rounds.
- **Why Do Multi-Agent LLM Systems Fail?** — arxiv:2503.13657 — 14 failure modes in 3 categories; inter-agent coordination = primary cause; prompt fixes yield only ~14% improvement; structural changes needed.
- **Towards a Science of Scaling Agent Systems** — arxiv:2512.08296 — capability saturation at ~45% single-agent baseline; beyond that, coordination yields diminishing/negative returns; centralized coordination contains error propagation 4.4x vs independent 17.2x; power-law scaling T = 2.72 × (n+0.5)^1.724; hard ceiling at 3–4 agents under fixed compute.
- **MultiAgentBench** — arxiv:2503.01935, ACL 2025 — graph-mesh topology best overall; cognitive planning +3% milestone rate; gpt-4o-mini reaches highest task score across models.
- **More Agents Is All You Need** — arxiv:2402.05120 — sampling-and-voting ("Agent Forest") scales monotonically with N; harder tasks benefit more; orthogonal to other improvements.
- **Efficient Agents** — arxiv:2508.02694 — Best-of-N diminishing returns immediate: N=1 53.33%, N=2 54.55%, N=4 53.94% (accuracy DROPS); token cost rises 34%. Recommends N=1; BoN is inefficient for agent settings.
- **Justice or Prejudice** — arxiv:2410.02736 — 12 judge biases quantified; position bias severe with 3+ options; self-enhancement bias ChatGPT 8.91% error vs GPT-4-Turbo 1.16%; CoT adds ~7% robustness; answer randomization mitigates position bias.
- **Panel of LLM Evaluators (PoLL)** — arxiv:2404.18796 — multi-model panel reduces intra-model bias; 7x cheaper than single large judge; outperforms single large judge.
- **Agent-as-Judge vs LLM-as-Judge** — arxiv:2508.02994 — agent judge disagrees with human 0.3% vs LLM judge 31% on code evaluation; multi-agent ChatEval improves human correlation 10–16% over single-agent.
- **Multi-Agent LLM for Incident Response** — arxiv:2511.15755 — 100% actionable recommendations vs 1.7% single-agent; 80x specificity, 140x correctness; 348 controlled trials; zero quality variance.
- **CONSENSAGENT** — ACL 2025 Findings — sycophancy mitigation in multi-agent consensus.

## Core empirical consensus (Mar 2026)

1. **Model diversity >> agent count.** 2 diverse models > 16 homogeneous (arxiv:2602.03794). The mechanism is uncorrelated errors, not more deliberation.
2. **MAD (multi-agent debate) mostly fails to beat self-consistency** at matched compute. SC scales better with token budget. MAD degrades on conformity. Only exception: debate for *judging* (not generation) shows consistent gains (NeurIPS 2025, arxiv:2510.12697).
3. **GAN-style refinement (evaluator-optimizer)** works when: (a) external feedback is grounded, (b) criteria are explicit, (c) task is open-ended creative/writing. Fails on reasoning (Huang et al.: models can't self-correct reasoning without external signal).
4. **Best-of-N / tournament wins on token efficiency** for simple reasoning tasks. Marginal diminishing returns start immediately. BoN worse than refinement for complex creative tasks.
5. **Topology matters more than count.** Centralized: +80.8% on parallelizable tasks; sequential reasoning degrades -39-70% across ALL multi-agent variants (arxiv:2512.08296). Never add agents to sequential reasoning chains.
6. **Capability threshold at ~45%.** If single-agent already exceeds 45% on task, adding coordination overhead yields negative returns.
7. **3–4 agents is the practical ceiling** under fixed compute. Communication overhead eats reasoning budget beyond that.
8. **Sycophancy cascade is the primary multi-agent failure mode.** Stronger agents get dragged down by weaker agents. Homogeneous model groups face monoculture collapse.

## Judge design findings

- Use different model family from generation model (prevents self-enhancement bias)
- Panel of small models > single large model (cheaper, less intra-model bias)
- Binary/3-point scales more reliable than 5-point or numeric
- CoT + rubric = best single-judge setup
- Randomize answer order to counter position bias
- Agent-as-judge for process evaluation (code, multi-turn), LLM-as-judge for output evaluation
- Adaptive stopping (KS test) eliminates wasted debate rounds

## Framework production state (Mar 2026)

- LangGraph: best for complex stateful; production at BlackRock, JPMorgan, LinkedIn
- CrewAI: fastest for linear role-based workflows
- AutoGen/AG2: maintenance mode (Microsoft shifted focus)
- OpenAI Agents SDK: handoffs + agents-as-tools patterns; official 2025
- Google ADK: 8 patterns documented; sequential → add complexity principle

## Frontier-specific evidence (Mar 2026 research pass)

### arxiv:2512.08296 — the only academic paper testing real frontier models in multi-agent settings
- Models tested: OpenAI (GPT-5-nano/mini/full), Google (Gemini 2.0 Flash, 2.5 Flash, 2.5 Pro), Anthropic (Claude Sonnet 3.7, 4.0, 4.5)
- **Anthropic models diverge from the rest:** Heterogeneous mixing in centralized architecture helps Claude (low-cap orchestrator + high-cap subagents = 0.42 vs homogeneous 0.32, +31%), but *hurts* OpenAI and Gemini.
- **Decentralized mixing helps all families:** Decentralized mixed-capability nearly matches or beats homogeneous high-capability across all three families.
- 45% capability threshold confirmed at frontier scale (which model crosses it depends on task; not explicitly named).
- Out-of-sample validation on GPT-5.2 (per search snippet — not confirmed in paper HTML directly; treat as uncertain).

### Anthropic "How we built our multi-agent research system" (Jun 2025)
- URL: anthropic.com/engineering/multi-agent-research-system
- Multi-agent (Opus 4 lead + Sonnet 4 subagents) outperformed single Opus 4 by 90.2% on **Anthropic's internal research eval** (not a public benchmark).
- Token usage explains 80% of BrowseComp performance variance — upgrading model > doubling token budget.
- Parallelization reduced research completion time by up to 90%.
- The 90.2% figure is *Anthropic's proprietary eval* — not independently reproducible.

### Carlini C compiler experiment (Feb 2026)
- URL: anthropic.com/engineering/building-c-compiler
- 16 Claude Opus 4.6 agents, ~2000 sessions, $20K, built 100K-line Rust C compiler.
- 99% GCC torture test pass rate. Limitation: "reached the limits of Opus's abilities."
- **No comparison to fewer agents or single agent.** Coordination insight: lock-based parallelism; monolithic tasks defeat parallelization (all agents hit same bug).
- Specialized agent roles (documentation, quality, performance) worked. Implicit goal management failed.

### SWE-bench leaderboard (real frontier multi-agent evidence)
- Top performers mix Claude + o4-mini or Claude + GPT-4o for orchestration/execution split.
- "No single architecture consistently achieves state-of-the-art." Single-agent and multi-agent systems coexist at top.
- Scaffold matters as much as model: same model + different scaffold = dramatically different scores.

### Incident response paper (arxiv:2511.15755) — CAUTION
- Claims 100% actionable rate, 80x specificity — but used **TinyLlama 1.1B 4-bit quantized**. Not frontier. Phase 2 with GPT-5.2/Claude Sonnet planned but unpublished.

### Karpathy LLM Council
- URL: github.com/karpathy/llm-council
- Uses frontier models (GPT-5.1, Gemini 3 Pro, Claude Sonnet 4.5, Grok 4). "99% vibe coded as a fun Saturday hack." **Zero empirical benchmarks published.**

### Rethinking MoA (arxiv:2502.00674)
- Tested almost entirely on open-source models (Qwen, WizardLM, Mixtral). GPT-4o appeared only as aggregator in one MT-Bench supplement.
- Self-MoA (same top model, multiple samples) beats mixed-model MoA — reinforces cheap-model findings but **not a frontier-specific test.**

### Key structural gap confirmed
- No published paper does a controlled A/B of frontier-only multi-agent vs frontier single-agent across multiple task types.
- All "frontier" claims from AI labs (Anthropic 90.2%, Opus 4.5 orchestrating Sonnet) use **internal evaluations** not publicly reproducible benchmarks.
- MAD literature: all tested on GPT-4o-mini, Llama, Claude-haiku. Deliberate.

## Chinese lab research — blind spot filled (Mar 2026)

### Latent-space communication — the genuinely novel finding
Three papers, all with Chinese lab co-authorship, propose bypassing natural language entirely for inter-agent communication. These have no equivalent in English-language literature:

1. **Interlat** (arxiv:2511.09149) — Zhejiang U / Alibaba / NTU / SJTU. Agents share last hidden states instead of tokens. ALFWorld benchmark: +3.3pp accuracy (70.48% vs 67.14%) over fine-tuned CoT. Compression to 8 tokens maintains performance while delivering 24x latency reduction (9.19s → 0.20s). Currently requires same-architecture models (limitation).

2. **LatentMAS** (arxiv:2511.20639) — training-free framework, pure latent collaboration via shared latent working memory. 9 benchmarks (math, commonsense, code): up to +14.6% accuracy, 70.8–83.7% token reduction, 4–4.3x faster inference. **No additional training required** — this is the most immediately applicable.

3. **Thought Communication** (arxiv:2510.20733) — NeurIPS 2025 Spotlight. Formal latent variable model; proves shared+private thoughts identifiable nonparametrically. Synthetic + real-world benchmarks validated. Authors: Yujia Zheng et al.

4. **Cache-to-Cache (C2C)** (arxiv:2510.03215) — Tsinghua University. Fuses KV-cache directly between models via learned neural projector. 6.4–14.2% accuracy gain over individual models; 3.1–5.4% over text communication; 2.5x latency speedup. Requires same-family models currently.

**Implication for existing findings:** The English-language literature assumes text is the only inter-agent communication medium. These papers suggest the communication bottleneck (sycophancy, information loss, latency) may be solvable architecturally — not just via prompting or topology changes.

### Chinese frontier model agentic benchmarks

- **Kimi K2** (Moonshot AI, arxiv:2507.20534) — 1T parameter MoE, 32B active. Stable across 200–300 sequential tool calls. Tau2-Bench: 66.1. BrowseComp: 60.2 (beats GPT-5's 54.9). HLE with tools: 44.9% (beats GPT-5's 41.7). SWE-Bench Verified: 65.8.
- **Kimi K2.5** (Jan 2026) — multimodal + vision upgrade; agentic tasks from video demonstrations.

- **GLM-5** (Zhipu/Z.ai, arxiv:2602.15763, Feb 11 2026) — 744B MoE, 44B active. BrowseComp: 75.9 (hierarchical context mgmt) — #1 all models. Tau2-Bench: 89.7. Vending-Bench 2: $4,432 final balance (#1 open-source). Intelligence Index v4.0: 50 (first open-weights to reach this). Technical innovation: fully async RL framework, token-in-token-out (TITO) alignment, 10,000+ verifiable training scenarios.

- **DeepSeek V3.2** (Dec 2025, arxiv:2512.02556) — first model to integrate thinking directly into tool-use. Agent training data: 1,800+ synthetic environments, 85K+ complex prompts. RL on this data improves Tau2-Bench, MCP-Mark, MCP-Universe. DeepSeek-V3.2-Speciale outperforms GPT-5 on IMO/IOI/ICPC 2025.

- **Qwen3** (Alibaba, May 2025 technical report, arxiv:2505.09388) — 235B-A22B. BFCL v3: 70.8 (outperforms Gemini 2.5 Pro, OpenAI o1). Hybrid thinking/non-thinking mode. Most downloaded model family globally (700M+ HuggingFace downloads by Jan 2026).
  - **Qwen3.5** followup: BFCL-V4: 72.2 (122B-A10B).

- **Baidu ERNIE 5.0 / Xinxiang** (Nov 2025) — "general super agent" platform with multi-agent architecture. LMArena: 1,460 (#1 Chinese model, #8 global). Multi-agent product "Oreate" covers doc/slide/image/video/podcast in one pipeline.

- **ByteDance UI-TARS-1.5** (Apr 2025) — open-source GUI agent, SOTA on 7+ GUI benchmarks. "Think-then-act" RL strategy. Beats GPT-4o, Claude, Gemini on PC/Mac agent benchmarks. UI-TARS-2 (Sep 2025): ~60% human-level in game environments.

- **ByteDance AGILE** — RL-based agent framework, end-to-end. 13B model outperforms GPT-4 Agent on ProductQA (+7.4% accuracy); 7B model reaches 85.2% on MedMCQA (vs GPT-4 MedPrompt 79.1%). Key differentiator: active expert help-seeking.

- **Tencent C3-Bench** (github.com/Tencent-Hunyuan/C3-Benchmark, ICLR 2026) — multi-tasking agent benchmark, 49 mainstream agents tested, covering tool dependencies, hidden info, dynamic decision paths. Peer-reviewed; vendor-created but open-source with academic publication.

### Key Chinese lab contributions to the field (synthesis)

1. **Latent communication research** — uniquely Chinese-lab territory. No Western lab has published comparable work. This is the most structurally novel finding: changes the fundamental assumption about inter-agent communication medium.

2. **Scale of agentic training data synthesis** — DeepSeek's 1,800 environments / 85K prompts pipeline and GLM-5's 10,000+ verifiable scenarios are larger than anything reported in English-language literature.

3. **Sequential tool-call stability** — Kimi K2's 200-300 call stability is a specific capability claim not benchmarked in Western lit. Addresses a known failure mode.

4. **Benchmark ecosystem** — Chinese labs have built their own benchmarks (C3-Bench, MCP-Atlas, MCP-Mark, MCP-Universe, Tau2-Bench variants) which are now being adopted internationally. BrowseComp and Tau2-Bench appear in both Chinese and Western model evaluations.

### What Chinese research does NOT contradict
- The English-language finding that text-based MAD (debate) fails to beat self-consistency — confirmed implicitly by the Chinese labs' pivot to latent communication instead.
- Model diversity >> agent count — consistent; latent-space communication papers still use heterogeneous architectures.
- 3–4 agent ceiling under fixed compute — no Chinese paper contradicts this; AGILE and GLM-5 focus on single-agent improvement, not large ensembles.

### Source reliability notes — Chinese sources
- zhuanlan.zhihu.com: 403 on WebFetch consistently. Use WebSearch snippets.
- infoq.cn: 451 (geo-blocked). Use WebSearch summaries.
- arxiv HTML pages with Chinese authors: work normally.
- csdn.net/blog: 403. Use WebSearch.
- developer.aliyun.com: works.
- seed.bytedance.com: works.
- github.com/Tencent-Hunyuan: works.
- 36kr.com: often JS-gated; use English-language summaries.

## Source reliability notes (general)

- arxiv HTML pages work well
- d2jud02ci9yv69.cloudfront.net (ICLR blog) works
- arxiv.org abstract pages: work but limited detail
- WebSearch often unavailable during session — retry with different phrasing
- ZenML production blog: WebFetch works (1200 deployments data)
- analyticsvidhya.com: WebFetch works for Karpathy content
- anthropic.com/engineering/* pages: WebFetch works, returns full content
- anthropic.com/news/* pages: WebFetch works
- swebench.com: WebFetch works
