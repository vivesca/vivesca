# GPT-5.4-Pro Responses API Latency

**ERR-20260307-001** — Discovered while fixing consilium `--council` hang.

## The Problem

`consilium --council` was hanging indefinitely. Root cause: multiple compounding issues in `api.rs`.

## Discoveries (empirically verified 2026-03-07)

### 1. max_output_tokens floor of 4096 is REQUIRED

GPT-5.4-Pro via the Responses API (`https://api.openai.com/v1/responses`) stalls (returns empty body after 90s+) if `max_output_tokens < ~3000`. With 4096, it completes. With 1500 or 2500, the request hangs and curl `--max-time 90` gets no response.

The model actually uses ~335 tokens (133 reasoning + 202 text) for a typical 120-word structured response. The token budget just needs to be high enough for the model to allocate its reasoning buffer.

**Fix:** Keep `max_tokens = max_tokens.max(4096)` in `query_openai` for thinking models.

### 2. Structured prompts make GPT-5.4-Pro slow regardless of max_output_tokens

Simple prompt + 1500 tokens → 9.9s
Simple prompt + 4096 tokens → 7s
Council blind prompt (14 lines, 4 structured items) + 4096 tokens → 67-81s
Council blind prompt + 3000 tokens → 81s
Council blind prompt + 1500 tokens → stall >90s

The prompt structure (multi-point enumeration, explicit instructions) triggers heavy reasoning even for "What is 2+2?". This is a fundamental GPT-5.4-Pro characteristic with "medium" effort on the Responses API, not something we can tune away.

### 3. `max_tokens.max(16000)` (old floor) caused 295s responses

The previous floor of 16,000 tokens was causing OpenRouter to generate extremely long responses. Fixed to 4096 across all provider functions.

### 4. Per-task wall-clock timeout is essential in parallel phases

`run_parallel` has no outer timeout by default — if any model stalls, the whole blind phase blocks. Fixed by wrapping each `tokio::spawn` with `tokio::time::timeout(wall_timeout, ...)`.

### 5. Debate rounds also need wall-clock caps

Sequential `query_model_async` calls in council debate rounds have no timeout beyond the per-request 120s × 3 retries = 360s max. Added `tokio::time::timeout(120s)` wrapper in council.rs.

## Performance Characteristics (2026-03-07 baseline)

| Phase | Models OK | Time |
|-------|-----------|------|
| Blind phase (90s wall cap) | GPT-5.4-Pro sometimes (67-90s), others <30s | ~90s |
| Debate round (120s wall cap per model) | GPT-5.4-Pro usually times out, Kimi-K2.5 usually times out | 120s per timeout |
| Full `--council` | 2-3/5 models active | 7-9 minutes |

## Summary of Fixes Applied

```
api.rs:
  - max_tokens.max(16000) → max_tokens.max(4096) for all provider functions
  - Added GLM-5 reasoning_content vs reasoning field fix in query_bigmodel
  - Added default "medium" reasoning effort for GPT-5.4-Pro in query_openai
  - Added tokio::time::timeout per-task in run_parallel and run_parallel_with_different_messages
  - query_model_with_fallback: timeout_secs = timeout_secs.min(120.0) for thinking models

council.rs:
  - Blind phase timeout capped at timeout.min(90.0)
  - Xpol phase timeout capped at timeout.min(90.0)
  - Debate round wrapped with tokio::time::timeout(120s)
```

## Recommendation

GPT-5.4-Pro via the Responses API is consistently 67-120s+ per call in council context. It's viable but slow. If faster council runs are needed, override M1:
```bash
CONSILIUM_MODEL_M1="google/gemini-2.5-flash" consilium --council "..."
```
