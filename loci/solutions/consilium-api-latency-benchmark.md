# Consilium API Latency Benchmark

**Date:** 2026-03-04
**Location:** HK (Tailscale → Tokyo exit node)
**Method:** Parallel async httpx, prompt "Reply with exactly: ok", max_tokens=500

## Results

| Model | Direct API | Endpoint | OpenRouter | Winner |
|-------|-----------|----------|-----------|--------|
| GPT-5.2-Pro | 1.6s (Responses API) | api.openai.com/v1/responses | 4.0s | **OpenAI Responses API (+2.4s)** |
| Gemini-3.1-Pro | 8.3s | generativelanguage.googleapis.com | 5.0s | **OpenRouter (+3.3s)** |
| Grok-4 | 5.8s | api.x.ai | 13.0s | **xAI direct (+7.2s)** |
| Kimi-K2.5 | 2.7s | api.moonshot.ai | 2.6s | **Tied** |
| GLM-5 | 2.6s | api.z.ai | 9.8s | **z.ai direct (+7.2s)** |

## Key Findings

**GPT-5.2-Pro uses the Responses API:** `gpt-5.2-pro` returns HTTP 404 on `api.openai.com/v1/chat/completions` — it's a Responses API model. Fixed by switching `query_openai` to `POST /v1/responses` with `input`/`max_output_tokens` and parsing `output[].content[].text`. Native Responses API is 1.6s vs OR's 4.0s.

**Gemini is faster via OpenRouter:** Google AI Studio direct adds ~3.3s latency from HK. OpenRouter likely has closer routing to Google's infrastructure.

**Grok and GLM strongly prefer native:** xAI direct is 2.2× faster than OR; z.ai direct is 3.8× faster than OR.

**Kimi is a wash:** Either endpoint works, <0.1s difference.

## Consilium Config Changes Applied

- M1 (GPT): switched `query_openai` to Responses API (`/v1/responses`); restored `Some(("openai", "gpt-5.2-pro"))` native fallback
- M2 (Gemini): removed `Some(("google", ...))` fallback → `None` (OR only)
- M3 (Grok): kept `Some(("xai", "grok-4"))` native-first ✓
- M4 (Kimi): kept `Some(("moonshot", "kimi-k2.5"))` native-first ✓
- M5 (GLM): kept `Some(("zhipu", "glm-5"))` native-first via z.ai ✓

## Script

`/tmp/api_bench.py` — async httpx, parallel, tests both endpoints per model.

---

## LRN-20260308-001: GPT-5.4-Pro and Kimi Removed from Council

**Date:** 2026-03-08

### GPT-5.4-Pro — do not use in any council mode

Upgraded from `gpt-5.2-pro` to `gpt-5.4-pro` expecting higher reasoning quality. Discovered:

- `gpt-5.4-pro` uses **OpenAI Responses API** — fundamentally different from chat completions
- Real-world latency: **907 seconds** per call in `--quick` mode (not a typo)
- Even `--council` mode times out (90s blind cap, 120s debate cap) — model never contributes
- No benchmark data on pondus/artificial-analysis/arena to justify the wait
- Routing to OpenRouter doesn't help — the Responses API latency is inherent to the model

**Rule:** Never add a Responses API model to the council without first measuring real-world latency in `--quick` mode. Benchmark latency (`/v1/responses` endpoint TTR) ≠ council session latency (full reasoning output).

**Fix:** Reverted to `gpt-5.2-pro` (3.6s in quick mode). GPT-5.4-Pro removed from all rotation.

**Future:** If gpt-5.4-pro ever appears in pondus benchmarks with clear quality advantage, revisit — but only if latency issue is resolved. `pondus monitor` watching for it.

### Kimi-K2.5 — connection failures, no quality advantage

- Intermittent `Connection failed` errors from `api.moonshot.ai`
- OR routing equally slow (2.6s vs 2.7s direct — tied, no fallback benefit)
- No clear quality signal over DeepSeek-V3.2 in benchmarks

**Fix:** Replaced with `deepseek/deepseek-v3.2` (3.5s, arena rank 49, ELO 1421, reliable).

### Post-swap quick mode timing (2026-03-08)

| Model | Before | After |
|---|---|---|
| GPT | 907s | 3.6s |
| Kimi → DeepSeek | ~131s / conn fail | 3.5s |
| Total session | ~15 min | **6.4s** |

**Lesson:** Before adding any new model to the council, run `consilium --quick --quiet "name a color" > ~/tmp/consi-speedtest.txt` and check per-model timings in the output. If any model exceeds 60s, it doesn't belong in quick or council rotation.

## LRN-20260309-001 — Responses API models billed directly via OPENAI_API_KEY

GPT-5.4-Pro uses OpenAI's Responses API, which consilium called directly via `OPENAI_API_KEY` rather than routing through OpenRouter. This created a parallel billing stream invisible in OpenRouter spend tracking.

**Impact:** $92 in 4 days (Mar 4–7) before detection.

**Lessons:**
1. **Set a low OpenAI direct budget cap** ($20) — catches direct API spikes fast. Raising it to "stop the noise" delays detection.
2. **Before adding any model to the council:** check pricing via `pondus check <model>` — now shows OpenRouter pricing alongside benchmarks.
3. **Two spend streams to monitor:** OpenRouter (`stips`) + OpenAI direct (`platform.openai.com/usage`). Both need budget caps.
4. **Responses API ≠ Chat Completions API** — Responses API models don't route through OpenRouter; they burn the direct key.

---

## Critic model: Sonnet beats Opus for council critique (LRN-20260312-001)

Switched CRITIQUE_MODEL from Opus to Sonnet 4.6 based on benchmark evidence:
- GDPval-AA (office tasks): Sonnet +27 Elo over Opus
- GPQA gap collapses from 17pp → 1.4pp when both use thinking mode
- Critic role = adversarial judgment on a synthesis = office/knowledge work, not PhD science

Opus advantage concentrates in: novel abstract reasoning (+10pp ARC-AGI-2), PhD science (+17pp GPQA), hard web research (~2x BrowseComp). None of these apply to the critic role.

**Rule:** For any agentic sub-role, check GDPval-AA benchmark before defaulting to Opus. Intuition ("Opus is smarter") is not sufficient — benchmark the task type.
