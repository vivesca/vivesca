# Claude Model Selection Guide

*Last updated: 2026-03-12. Sources verified from Anthropic announcements + independent benchmarks + pondus live data. Official benchmark table from anthropic.com/news/claude-sonnet-4-6 (Feb 17, 2026) added 2026-03-12.*

## TL;DR (updated 2026-03-12)

**Default: Opus 4.6 for in-session work; delegate coding to Codex/Gemini/OpenCode.** The delegation-first architecture changes the calculus: in-session work is orchestration, judgment, and discussion — not heavy agentic coding. Chatbot Arena Elo gap (43 points: 1503 vs 1460) shows Opus is meaningfully better at human-preference tasks. Artificial Analysis Intelligence Index gap at Max tier is only 1 point (53 vs 52) — near-tied on raw capability. The Arena gap is the more relevant signal for conversational/judgment work. Quota stays healthy as long as coding execution is delegated (Max20 weekly at ~28% in March 2026 with Sonnet-only; Opus is heavier but manageable if not doing agentic coding in-session). Drop to Sonnet when weekly % > 70% or doing long agentic tool-call loops in-session.

**Previous recommendation (pre-Mar 2026):** Sonnet as default. Revised based on: (1) delegation discipline reducing in-session token burn, (2) Arena Elo gap favouring Opus for judgment/discussion, (3) noesis deep research confirming hybrid routing with Opus for planning/analysis phases.

## Benchmarks (Sonnet 4.6 vs Opus 4.6)

Sources: Anthropic system card (Feb 17, 2026), digitalapplied.com, vellum.ai, officechai.com, Artificial Analysis

| Benchmark | Sonnet 4.6 | Opus 4.6 | Verdict |
|---|---|---|---|
| SWE-bench Verified (coding) | 79.6% | 80.8% | Near-tied (-1.2pp) |
| OSWorld-Verified (computer use) | 72.5% | 72.7% | Near-tied (-0.2pp) |
| GDPval-AA Elo (office tasks) | **1,633** | 1,606 | **Sonnet wins +27 Elo** |
| ARC-AGI-2 (abstract reasoning) | 58.3% | **68.8%** | Opus +10.5pp |
| Humanity's Last Exam (no tools) | 33.2%† | **40.0%** | Opus +6.8pp |
| Humanity's Last Exam (with tools) | 49.0% | **53.0%** | Opus +4pp |
| GPQA Diamond (standard eval) | 74.1% | **91.3%** | Opus +17pp |
| GPQA Diamond (adaptive thinking) | 89.9% | **91.3%** | Near-tied (-1.4pp) |
| MMLU-Pro | 79.1% | **81.2%** | Opus +2.1pp |
| MATH-500 | 97.8% | **97.6%** | Sonnet (marginal) |
| Terminal-Bench 2.0 (agentic terminal) | 59.1% | **65.4%** | Opus +6pp |
| BrowseComp (hard web research) | 74.7% | **84.0%** | Opus +9pp |
| BigLaw Bench (legal) | — | **90.2%** | Opus |
| AA Intelligence Index (max reasoning) | 52 (rank 5) | **53 (rank 4)** | Near-tied (-1pt). Gemini 3.1 Pro (57) + GPT-5.4 (57) both beat Opus here — see Non-Claude section. |
| AA Intelligence Index (standard) | 44 (rank 15) | **46 (rank 13)** | Near-tied (-2pt) |
| Chatbot Arena Elo | 1460 (rank 16) | **1503 (rank 1)** | Opus +43 Elo. Gemini 3.1 Pro scores only 1316 on same benchmark. |
| SEAL overall | — | **67.3 (rank 2)** | Opus |
| Finance Agent v1.1 | **63.3%** | 60.1% | Sonnet wins |
| MCP-Atlas Scaled Tool Use | **61.3%** | 59.5% | Sonnet wins |
| τ²-bench Retail | 91.7% | 91.9% | Near-tied (-0.2pp) |
| τ²-bench Telecom | 97.9% | **99.3%** | Opus +1.4pp |
| MRCR v2 at 1M tokens (recall) | ~18.5%† | **76.0%** | Opus decisive |
| MMMLU (multilingual) | 89.3% | **91.1%** | Opus +1.8pp |
| HumanEval | 92.1% | — | (Opus not published) |

†MRCR figure is Sonnet 4.5; Sonnet 4.6 number not published.
‡HLE without-tools Sonnet: 33.2% is from Anthropic official benchmark table (thinking/adaptive mode). Earlier third-party sources cited 19.1% (likely non-thinking eval). Use 33.2% for apples-to-apples comparisons with Opus 40.0% (also thinking mode).

**GPQA discrepancy explained:** 74.1% = standard (non-thinking) eval from Anthropic's official benchmark table. 89.9% = adaptive thinking / max effort configuration. Both are real; use the right one for comparison context. Opus 91.3% is also with thinking. Gap collapses from 17pp → 1.4pp when both use thinking mode.

**ARC-AGI-2 clarification:** Some early sources cited 75.2% for Opus — this was an error. Vellum.ai (cross-referencing system card) confirms 68.8%. Sonnet 58.3%.

**Pricing (API, confirmed platform.claude.com, Mar 2026)**:
- Sonnet 4.6: $3/$15 per Mtok (input/output)
- Opus 4.6: $5/$25 per Mtok — **NOT $15/$75** (that was Opus 4.1/Opus 4)
- Ratio: 1.67x for both input and output
- "5x cheaper" claims in press = comparing Sonnet 4.6 vs Opus 4.1. Incorrect for current Opus 4.6.

**Batch API pricing**: Sonnet $1.50/$7.50 · Opus $2.50/$12.50 per Mtok

**Pricing (1M context, confirmed official docs)**: kicks in when input > 200K tokens; charges ALL tokens at premium rate
- Sonnet 4.6: $6/$22.50 per Mtok
- Opus 4.6: $10/$37.50 per Mtok

**Opus 4.6 Fast Mode (research preview)**: $30/$150 per Mtok — 6x standard rate. Includes full 1M context at no additional long-context surcharge.

## Non-Claude Frontier Models (Delegation Targets)

Relevant for choosing Gemini CLI / Codex targets, not in-session model selection.

| Model | AA Index (max) | Arena Elo | Notes |
|---|---|---|---|
| **gemini-3.1-pro-preview** | **57 (rank 1)** | 1316 | Best on intelligence benchmarks. Free via CLI (`-m gemini-3.1-pro-preview`). LiveCodeBench Elo 2887 (unprecedented). AA gave Google **pre-release access** — caveat for consulting use. |
| **gpt-5.4 (xhigh)** | **57 (rank 2)** | 1485 | Tied with Gemini on AA index. Strong Arena performance. Via Codex or API. |
| gpt-5.3-codex (xhigh) | 54 | — | Codex's underlying model. |
| gemini-3-flash | 46 | 1474 | Fast, free, good for bulk/boilerplate. |

**Key insight — Intelligence Index vs Arena Elo:**
- AA Intelligence Index = raw ceiling at max effort. Gemini 3.1 and GPT-5.4 lead here (57 vs Opus 53).
- Chatbot Arena Elo = human preference in conversation. Opus 4.6 leads decisively (1503 vs Gemini's 1316).
- **Implication:** delegate execution (coding, algorithmic tasks) to Gemini 3.1 Pro free; keep judgment and in-session work on Opus. The two complement each other perfectly.

**Pre-release caveat:** AA evaluated Gemini 3.1 Pro Preview with Google-provided pre-release access. Treat the 57 AA index as directionally correct but not independently verified. Arena Elo (human preference, blind) is the more trustworthy signal for conversational quality comparisons.

## When to Use Opus

Escalate when the task involves:
- **Novel abstract reasoning** — no established pattern, ARC-AGI-2 class problems (+10pp gap)
- **Graduate-level scientific or legal analysis** (+17pp GPQA gap in standard mode; collapses to 1.4pp with max effort on both — but Opus max is still the right tool)
- **Agent Teams orchestration** — Opus-exclusive feature in Claude Code; can run parallel sub-agents at scale (Anthropic demo: built a working C compiler, 100K+ lines, across 3 CPU architectures)
- **Hard multi-step web research** — BrowseComp class (~2x better than Sonnet 4.5)
- **Sustained agentic terminal operations** (+6pp Terminal-Bench; Opus is "less likely to give up")
- **Large corpus in context > 256K** — Opus 4.6 has confirmed 76% MRCR recall at 1M tokens; Sonnet 4.6 MRCR at 1M is unpublished

## When Sonnet 4.6 Wins or Ties

- Routine coding, refactoring, tests
- Browser/GUI automation (GDPval lead)
- Office automation — documents, spreadsheets, structured data
- Math and financial modelling (89% benchmark)
- Multi-document knowledge work under 200K tokens
- High-volume or cost-sensitive agentic work

## Routing for Claude Code Max (Terry's Workload)

**Session default: Opus 4.6 + medium effort.** Coding is delegated (Codex/Gemini/OpenCode), so in-session Opus burn is orchestration and judgment only — manageable on Max20. Switch to Sonnet explicitly for the categories below.

Audited against actual vault usage (Feb 2026). Eight categories, ranked by frequency:

| Category | Examples | % of usage | Model | Effort |
|---|---|---|---|---|
| Life admin & scheduling | Physio, dental, insurance claims, BCT ORSO, financial reviews | ~20% | Sonnet | Medium |
| Career decisions | PILON negotiation, Capco positioning, job pipeline | ~15% | **Opus** | Medium (Max for `/consilium`) |
| Drafting | LinkedIn posts, emails (gog), WhatsApp messages | ~15% | Sonnet | Medium |
| Exam prep | GARP RAI quizzes, DBS interview prep, consulting drill | ~10% | Sonnet | Medium |
| AI news & article analysis | `/lustro`, `/digest`, article evaluation, summarization | ~10% | Sonnet | Medium |
| Dev/tooling | orchestration, skills, architecture, hard debug | ~15% | **Opus** | Medium (Max for hard arch/debug) |
| Research | Products, schools, investments, deep analysis | ~10% | **Opus** | Medium |
| Daily routines | `/morning`, `/daily`, `/wrap`, TODO management | ~5% | Sonnet | Medium |

**Don't switch per-task.** Switching friction costs more than the marginal savings on admin tasks. Opus handles everything — admin, drafting, wraps, exam prep, research, judgment.

**Switch to Sonnet** (`/model sonnet`) only when:
- Weekly % > 70% (check `/status` — this is the hard trigger)
- Running a subagent swarm or long agentic loop in-session where coding must happen in-session

**Opus + max effort** (switch effort slider) for:
- `/consilium` on hard decisions with many trade-offs
- Novel architectural design (no established pattern)
- PhD-level scientific or legal analysis
- Hard multi-step web research (BrowseComp class)
- Agent Teams orchestration
- Debugging that has failed 3+ times on medium effort

**Weekly pool budget guidance** (Max20, resets Friday 11am HKT):
- Delegation-first keeps Opus burn manageable — coding goes to Codex/Gemini, not Max20
- Monitor Monday evening — if past 50% "all models", tighten to Sonnet-default
- At 70%+ weekly, switch to Sonnet for everything except `/consilium`
- **Usage snapshots:** `usus log` / `usus history` — automated tracking in `~/.local/share/usus/history.jsonl`

## Claude Code Effort Slider

CC's `/model` UI shows: `◐ Medium effort (default) ← → to adjust`. Three levels: Low / Medium / Max.

**Effort ↔ AA benchmark variant mapping:**
- **Max effort** = "Adaptive Reasoning, Max Effort" = extended thinking at max `budget_tokens` = AA `(max)` variant
- **Medium effort** = standard configuration, no extended thinking by default = AA `standard` variant
- **Low effort** = reduced reasoning budget

**AA Intelligence Index by effort:**
| Effort | Sonnet 4.6 | Opus 4.6 | Gap |
|---|---|---|---|
| Max | 52 (rank 5) | 53 (rank 4) | **1pt** |
| Medium/Standard | 44 (rank 15) | 46 (rank 13) | **2pt** |

**At max effort, the gap narrows because extended thinking lets Sonnet close in on Opus's structural reasoning advantage. At medium effort, Opus's lead is proportionally larger.**

**GPQA at different effort levels:**
- Standard (no thinking): Sonnet 74.1%, Opus 91.3% → 17pp gap
- Adaptive thinking (max): Sonnet 89.9%, Opus 91.3% → 1.4pp gap

**CC effort recommendation:**
- **Opus + medium effort** = correct default for ~90% of in-session work (orchestration, judgment, drafting, analysis). Opus's reasoning advantage already kicks in at medium — no need for extended thinking for routine tasks.
- **Opus + max effort** = reserve for: `/consilium` on hard decisions, novel architecture with no prior art, PhD-level analysis, debugging after 3+ failures. Switch via effort slider, switch back after.
- **Sonnet + medium** = correct for subagents, long agentic tool-call loops, when weekly % > 70%. Faster, cheaper, near-parity for execution tasks.
- **Sonnet + max** = rarely warranted — if you need max effort reasoning, the Opus max option is only 1pt better but architecturally sounder for hard reasoning. Sonnet max burns more tokens (+28% output vs Opus at same tasks).

**Cost note:** Max effort on Opus at API = ~2-3x token consumption vs medium. On Max20, this comes from the weekly pool. Medium effort is the right default — max effort for hard problems only.

## Token Consumption Warning (Sonnet 4.6)

On GDPval-AA, Sonnet 4.6 used **~280M tokens vs Sonnet 4.5's 58M** — a 4.8x increase. In cost-per-task terms, this can make Sonnet 4.6 more expensive than Opus 4.6 for agentic workflows despite the lower headline rate.

**Artificial Analysis Intelligence Index findings (Feb 2026):**
- Sonnet 4.6 (max effort): 74M output tokens → $2,088 eval cost
- Opus 4.6 (max effort): 58M output tokens → $2,486 eval cost
- Sonnet uses **~28% more output tokens** than Opus for the same tasks
- Intelligence Index: Sonnet 51, Opus 53 (gap narrowed from 7 to 2 points)
- On Max plan, tokens = pool consumption — Sonnet's chattiness partially offsets its per-token savings
- **For non-agentic tasks** (reading, analysis, drafting): Sonnet is clearly cheaper — fewer tool calls, less thrashing
- **For heavy agentic tasks** (multi-file coding, complex automations): measure actual pool burn before assuming Sonnet saves budget

## Speed & Latency (Artificial Analysis, Mar 2026)

Source: artificialanalysis.ai/models/claude-sonnet-4-6

| Metric | Sonnet 4.6 (non-reasoning) | Sonnet 4.6 (adaptive max) | Notes |
|---|---|---|---|
| Output speed | 47.4 t/s | 57.8 t/s | Below avg for tier (median 55-68 t/s) |
| Time to first token | 0.89s | 0.72s | Competitive (median 1.2-1.4s) |
| Verbosity rank | #55/59 | — | Very verbose vs peers |

Best providers for speed: Amazon (73.3 t/s), Google/Azure (~55.8 t/s). Best latency: Google/Anthropic (0.73s).

Opus 4.6 speed data: not yet extracted from Artificial Analysis (check artificialanalysis.ai/models/claude-opus-4-6 directly).

## 1M Context Window — Caveats

**Availability**: Beta. On API requires tier 4 (confirmed platform.claude.com). Available for: Opus 4.6, Sonnet 4.6, Sonnet 4.5, Sonnet 4. On Max plan, check billing — may count against extra usage cap.

**Pricing is all-or-nothing**: Crossing 200K tokens in a single request triggers premium pricing on **all tokens** in that request — not just the excess.

| Model | Standard (≤200K) | Long context (>200K) |
|---|---|---|
| Sonnet 4.6 | $3/$15 | $6/$22.50 per Mtok |
| Opus 4.6 | $5/$25 | **$10/$37.50 per Mtok** |

**Recall quality at 1M tokens**:
- Opus 4.6: 76% MRCR v2 (8-needle retrieval) — confirmed
- Sonnet 4.6: number not published yet (was 18.5% for Sonnet 4.5)
- "Context rot" improvement in Opus 4.6: 50% degradation now starts at ~500K tokens instead of ~64K

**Better alternative**: Context compaction (auto-summarises older context) handles most long-conversation cases without triggering premium pricing. Available within the standard 200K window.

## Behavioural Notes

- Opus 4.6 reported as "less sycophantic" and "less likely to give up on a problem" (thezvi.substack)
- Opus 4.6 exhibited self-interested negotiation behaviours in Vending Bench evaluation (lying, price-fixing with competitors); Anthropic attributes this to game-context goal prompting — monitor for agentic deployments with external tool calls
- Sonnet 4.6 had early post-launch hallucinated function names / broken structured outputs; stabilised within days

## Sources

1. [Anthropic — Introducing Claude Sonnet 4.6](https://www.anthropic.com/news/claude-sonnet-4-6)
2. [DigitalApplied — Sonnet 4.6 Benchmarks & Pricing](https://www.digitalapplied.com/blog/claude-sonnet-4-6-benchmarks-pricing-guide)
3. [DigitalApplied — Opus 4.6 Benchmarks & Pricing](https://www.digitalapplied.com/blog/claude-opus-4-6-release-features-benchmarks-guide)
4. [Vellum.ai — Opus 4.6 Benchmarks](https://www.vellum.ai/blog/claude-opus-4-6-benchmarks)
5. [VentureBeat — Sonnet 4.6 matches flagship at 1/5 cost](https://venturebeat.com/technology/anthropics-sonnet-4-6-matches-flagship-ai-performance-at-one-fifth-the-cost)
6. [Latent Space AINews — Sonnet 4.6 token consumption anomaly](https://www.latent.space/p/ainews-claude-sonnet-46-clean-upgrade)
7. [rdworldonline — Opus 4.6 MRCR at 1M tokens](https://www.rdworldonline.com/claude-opus-4-6-targets-research-workflows-with-1m-token-context-window-improved-scientific-reasoning/)
8. [The New Stack — Agent Teams feature](https://thenewstack.io/anthropics-opus-4-6-is-a-step-change-for-the-enterprise/)
9. [thezvi — Opus 4.6 behavioural observations](https://thezvi.substack.com/p/claude-opus-46-escalates-things-quickly)
10. [Artificial Analysis — Sonnet 4.6 token consumption + Intelligence Index](https://artificialanalysis.ai/articles/sonnet-4-6-everything-you-need-to-know)
11. [Artificial Analysis on X — 28% more tokens than Opus](https://x.com/ArtificialAnlys/status/2024259812176121952)
12. [NxCode — Sonnet 4.6 vs Opus 4.6 Which to Choose](https://www.nxcode.io/resources/news/claude-sonnet-4-6-vs-opus-4-6-which-model-to-choose-2026)
13. [TechBrew — A Tale of Two Claudes (real-world tests)](https://www.techbrew.com/stories/2026/02/23/a-tale-of-two-claudes)
