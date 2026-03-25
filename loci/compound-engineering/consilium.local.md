---
review_agents: [kieran-python-reviewer, code-simplicity-reviewer, security-sentinel, performance-oracle, architecture-strategist]
plan_review_agents: [kieran-python-reviewer, code-simplicity-reviewer]
---

# Review Context

## Project Overview
Consilium is a multi-model LLM deliberation CLI. It queries 5+ frontier models (GPT-5.2-pro, Gemini-3-pro, Grok-4, DeepSeek-R1, GLM-5) via OpenRouter API, runs structured debate formats, and synthesises a verdict with Claude Opus 4.6 as judge.

## Architecture
- **Single-package CLI** installed via `uv tool install`. Entry point: `consilium/cli.py` → `main()`.
- **Mode modules**: `council.py`, `quick.py`, `discuss.py`, `redteam.py`, `solo.py`, `oxford.py` — each exports a `run_*()` function returning `SessionResult(transcript, cost, duration)`.
- **Shared core**: `models.py` (API queries, model configs, async parallel), `prompts.py` (all prompt constants).
- **No database, no auth, no server** — pure CLI, stateless except `~/.consilium/sessions/` transcript files and `history.jsonl`.

## Key Patterns
- All external API calls go through `query_model()` or `query_model_async()` in `models.py` — never direct `httpx` elsewhere.
- Thinking models (Opus, GPT-5.2, Gemini-3, etc.) use non-streaming path with higher token limits and timeouts.
- Google AI Studio fallback for Gemini models when OpenRouter fails.
- Socratic mode is folded into `discuss.py` via `style="socratic"` parameter — not a separate module.
- Auto-routing: Opus classifies question difficulty → routes to quick (simple) or council (moderate/complex).

## Security Notes
- API keys from env vars only (`OPENROUTER_API_KEY`, `GOOGLE_API_KEY`). Never logged or saved.
- `sanitize_speaker_content()` strips prompt injection markers from model responses before feeding to judge.
- Session transcripts saved locally only. `--share` uploads to secret GitHub Gist via `gh` CLI.

## Performance Considerations
- Parallel async queries via `run_parallel()` with `asyncio.gather()` — main latency driver is slowest model.
- Classification step adds ~5-10s overhead on every auto-routed invocation (Opus thinking model).
- Streaming for non-thinking models reduces perceived latency.

## What Reviewers Should Know
- This is a personal tool, not production SaaS. Optimise for correctness and usability over enterprise patterns.
- Cost tracking is approximate (OpenRouter `usage.cost` field). No need for penny-precise accounting.
- The `LiveWriter` stdout tee is intentionally simple — no need for full logging framework.
- Error messages from models start with `[Error:` or `[No response` — these are returned as strings, not raised as exceptions, because partial results are useful.
