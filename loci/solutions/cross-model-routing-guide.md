# Cross-Model Routing Guide

*Last updated: 2026-03-18 (default model revised). Based on Feb-Mar 2026 model landscape + hands-on testing + benchmark audit.*

Complements `claude-model-guide.md` (Claude-specific) and CLAUDE.md delegation patterns. This doc covers **when to route tasks to non-Claude models**.

## Model Landscape (Feb 2026)

| Model | Best At | Interface | Access | Notes |
|-------|---------|-----------|--------|-------|
| **Claude Opus 4.6** | Novel reasoning, orchestration, judgment, Agent Teams, long context >256K | Claude Code (native) | Max plan | **Our default (revised Mar 12).** Opus +43 Arena Elo; delegation-first keeps quota healthy. |
| **Claude Sonnet 4.6** | Routine coding, automation, office/knowledge work, subagent swarms | Claude Code (`/model sonnet`) | Max plan | Switch to when weekly % > 70%, or running long in-session agentic loops. |
| **GPT-5.3 Codex** | Pure code generation, debugging, testing | Codex CLI v0.104.0 | ChatGPT Pro ($200/mo) | Top SWE-bench Pro. First model hitting "high" cybersecurity risk. |
| **GPT-5.2 Thinking** | Reading comprehension, long-context, multimodal vision | OpenAI API | $1.75/$14/Mtok | xhigh reasoning effort. Best vision model (halves error rate on charts). |
| **GPT-5.2 Pro** | Research & knowledge work | ChatGPT Pro UI | $200/mo sub | Deep research agent. No CLI. |
| **Gemini 3.1 Pro** | Algorithmic coding, scientific reasoning, MCP/tool coordination | Gemini CLI v0.29.5 | AI Pro plan | AA Intelligence #1 (57). Best *programmer* (LiveCodeBench Elo 2887). Trails on agentic *developer* tasks (GDPval-AA). Verbose (57M vs 12M median tokens). $2/$12 Mtok (free on AI Pro). |
| **Gemini Deep Think** | Knowledge breadth, fact verification | Gemini API | AI Pro plan | Specialised reasoning variant. |
| **Grok 4.2** | AI news search, real-time info (X/Twitter data) | xAI API; community CLIs | SuperGrok $30/mo or API | Public beta Feb 17. Rapid learning (weekly updates). |
| **GPT-4.5** | EQ, collaborative communication | **DEPRECATED** | ChatGPT Pro "Legacy" only | API removed Jul 2025. Not automatable. |
| **GLM-5** | Search/browse tasks, tool-use, reasoning; bulk coding | `cg` (Claude Code backend); OpenCode (`opencode/glm-5`) | BigModel plan | BrowseComp 75.9 (SOTA all models), HLE w/ tools 50.4. Weak on multi-step chained coding (52.3 vs Claude 61.6). GLM-5 now primary OpenCode model (Mar 6 key refresh). |
| **GLM-4.7** | Bulk delegation fallback | OpenCode CLI | BigModel annual plan | Fallback if GLM-5 regresses. GLM-5 is now the primary OpenCode model (`opencode/glm-5` provider — Mar 2026). |

## Task Routing Table

**Default orchestrator: Claude Opus 4.6** (revised Mar 12, 2026 — see `claude-model-guide.md`). Delegation-first keeps quota healthy; Opus is for in-session judgment + orchestration only.

| Task Type | Primary | Escalation / Fallback | Notes |
|-----------|---------|----------------------|-------|
| **Orchestration, life admin, drafting, daily routines** | Claude Opus 4.6 | — | Default. Opus +43 Arena Elo for judgment/conversation. |
| **Complex decisions, `/consilium`** | Claude Opus 4.6 | `/model opus` + max effort | Switch to max effort for hard trade-offs. |
| **Routine coding** | Claude Opus 4.6 (in-session) | OpenCode (GLM-5) | Delegate bulk to OpenCode; Opus orchestrates. |
| **Hard coding — agentic (repo nav, test loops)** | GPT-5.3 Codex | **→ Opus** (`/model opus`) | Best *developer*. Terminal-Bench #1 (77.3%). |
| **Hard coding — algorithmic (self-contained logic)** | Gemini 3.1 Pro | GPT-5.3 Codex | Best *programmer*. LiveCodeBench #1 (Elo 2887). Free via CLI. |
| **Hard coding — in-session (3+ failures)** | **→ Opus + max effort** | GPT-5.3 Codex | Opus "less likely to give up." Switch back after. |
| **Scientific / formal reasoning** | Gemini 3.1 Pro | **→ Opus** (`/model opus`) | GPQA Diamond 94.3%, ARC-AGI-2 77.1%, SciCode 59%. |
| **Document analysis (long)** | GPT-5.2 Thinking | Claude Opus 4.6 | API available. Best for chart/diagram/screenshot interpretation. |
| **Deep research** | GPT-5.2 Pro | `pplx research` | Pro is ChatGPT UI only. Pplx for automated. |
| **Fact verification** | Gemini Deep Think | `pplx search` | Use when ground truth matters. |
| **AI news search** | Grok 4.2 | WebSearch → `pplx search` | Real-time X/Twitter advantage. |
| **Web search / browse tasks** | GLM-5 via `cg` | Claude Sonnet 4.6 | BrowseComp SOTA (75.9 vs Claude 64.8). Best for multi-hop evidence gathering. |
| **Tool-use heavy tasks** | GLM-5 via `cg` | Claude Sonnet 4.6 | Tool calling jumped 60.8→95.8 (GLM-4.7→5). Strong tool orchestration. |
| **Bulk/free delegation** | GLM-5 via OpenCode (`opencode/glm-5`) | Gemini CLI (auto) | Mar 6 key refresh restored GLM-5 as primary OpenCode model. Gemini for quality step-up. |
| **Agent Teams (parallel sub-agents)** | **→ Opus** (`/model opus`) | — | Opus-exclusive feature. Switch to Opus, run, switch back. |

## Search Cascade (updated)

```
General:     WebSearch (free) → pplx search ($0.006) → pplx research ($0.40)
AI-specific: Grok 4.2 (real-time X data) → WebSearch → pplx search
HK local:    Chinese query first → WebSearch → pplx search
```

## Gemini 3.1 Pro Routing Notes

**Programmer vs developer:** Gemini is a better *programmer* (algorithmic, self-contained logic). Codex is a better *developer* (codebase navigation, test loops, multi-file fixes). Decision heuristic: self-contained task → Gemini. Needs repo context → Codex.

**Use Gemini for:** Algorithmic coding, refactoring complex functions, scientific/quantitative reasoning, MCP/tool-heavy workflows, long-context code review (1M context), any mid-tier task too complex for GLM-5 but not worth Codex credits.

**Don't use Gemini for:** Agentic multi-file debugging (Codex wins on Terminal-Bench), expert office/financial tasks (Claude wins on GDPval-AA by 289 Elo), anything needing low latency (31s TTFT), tasks where verbosity burns context budget.

**Key benchmarks (verified vs Google model card + Artificial Analysis, Feb 25):**
- AA Intelligence Index: 57 (#1 of 114)
- LiveCodeBench Pro: Elo 2887 (#1 ever)
- SWE-Bench Verified: 80.6% (near-tied Opus 80.8%)
- SWE-Bench Pro: 54.2% (trails Codex 56.8%)
- Terminal-Bench 2.0: 68.5% (trails Codex 77.3%)
- GPQA Diamond: 94.3%, ARC-AGI-2: 77.1%, SciCode: 59%
- MCP Atlas: 69.2%
- GDPval-AA: 1317 Elo (vs Opus 1606 — significant gap on real-world agentic)

**Pricing:** $2/$12 per Mtok via API. Free on Google AI Pro plan ($20/mo). ~2.5x cheaper than Opus on input, ~2.1x on output (NOT "7.5x" as some blogs claim — that compares against stale Opus 4.5 pricing).

## GLM-5 Routing Notes

**Use `cg` for:** Multi-hop web research, browse-heavy tasks, tool-orchestration workflows, reasoning problems with tool access, Chinese-language tasks.

**Don't use `cg` for:** Multi-step chained coding (9pp behind Claude — error accumulation compounds across sequential edits), end-to-end frontend builds (ISR lags Claude by 13-14pp on HTML/Vue), long-horizon dev sessions.

**Benchmarks that matter:**
- BrowseComp 75.9 (SOTA, all models incl. closed) vs Claude 64.8
- HLE w/ tools 50.4 vs Claude 43.4, GPT-5.2 45.5
- SWE-rebench 42.1 vs Claude 43.8 (close — 1.7pp)
- Multi-step chained coding 52.3 vs Claude 61.6 (gap — error accumulation)
- Tool calling 95.8 (up from 60.8 on GLM-4.7)

**Pricing:** ~$0.80/$2.56 per Mtok (OpenRouter) — roughly 6x cheaper than Opus 4.6.

See [[GLM-5 Technical Report]] for full architecture and benchmark tables.

## Setup Status & TODOs

- [x] Codex CLI v0.104.0 — likely already routing to GPT-5.3 Codex
- [x] GLM-5 via `cg` — working as Claude Code backend; also primary OpenCode model via `opencode/glm-5` (Mar 6 key refresh)
- [x] Gemini CLI — `gemini-3.1-pro-preview` working via OAuth/AI Pro plan. Free-tier API key gets quota 0. Auto-routing selects 3.1 Pro for complex tasks. (Verified at v0.29.5 Feb 25; check `gemini --version` for current.)
- [x] Grok CLI — custom `~/bin/grok` script using xAI API. `grok "query"`, `grok --x-only "query"` for X/Twitter search.
- [ ] GPT-5.2 Thinking access — available via OpenAI API. Could route through OpenRouter or a lightweight script. Low priority unless document analysis volume increases.
- [x] GPT-4.5 — confirmed deprecated. Not worth pursuing.

## Source Post

Chinese tech blogger's Spring Festival 2026 project: 970-question eval across 18 dimensions, ~100 sub-dimensions. Cross-model adversarial question generation with iterative skill refinement. Rankings above are directionally aligned with independent benchmarks (SWE-bench, ARC-AGI-2, Arena).

Key methodological insight: evaluation quality is bounded by question-generating model quality. Cross-model adversarial generation (models quiz each other, then review) produces better benchmarks than single-model generation.
