---
module: tests/conftest.py, pytest.ini
date: 2026-01-26
category: testing-patterns
symptoms:
  - "Test suite taking over 2 minutes. Slow feedback loop during development."
root_cause: "Every test case triggered live OpenRouter API calls for embeddings and classification. Heavy FAQ indices were reloaded for every function-scoped fixture."
solution: "Implemented persistent JSON caches for embeddings/LLM results. Changed index fixtures to session scope."
severity: high
tags: [pytest, caching, llm, embeddings, performance, mock]
---

# Persistent Test Caching: 40x Speedup for LLM Applications

## Problem

The test suite was taking over 2 minutes, creating a slow feedback loop during development. Every test run was making live network calls to the OpenRouter API for embeddings and LLM intent classification/reranking. Additionally, heavy FAQ indices were being re-loaded from disk for every single test case.

## Investigation Attempts

1. **Sequential Execution**: Running 200+ tests sequentially with live API calls was causing timeouts in the local development environment.
2. **Durations Analysis**: `pytest --durations=10` confirmed that the majority of time was spent in `EmbeddingClient.embed` and `ResponseRouter.route` (LLM calls).

## Root Cause

Every test case triggered live OpenRouter API calls for embeddings and classification. Furthermore, heavy FAQ indices were reloaded for every function-scoped fixture instead of being cached across the session.

## Solution

Implemented persistent JSON caches for embeddings/LLM results and changed index fixtures to session scope. This was achieved through a three-tier optimization in `tests/conftest.py`:

### 1. Salted Persistent JSON Caching
Used `pytest`'s `monkeypatch` to intercept all LLM and Embedding calls. The cache filename includes a **content-based salt** (hash of `faq_data.json` and core services).

- **Benefit:** If you change the FAQ data or prompt logic, the cache automatically invalidates.
- **Manual Bypass:** Run `pytest --no-cache` or set `TEST_USE_CACHE=false` to ignore all caches.

### 2. Live API Health Check
Created `tests/test_live_api.py` with a `@pytest.mark.live` marker.
- **Benefit:** Prevents "network blindness." Run `pytest -m live --no-cache` to explicitly verify that the OpenRouter API is reachable and responding correctly.

### 3. Session Isolation Fixture
Added an `autouse` fixture that resets `router.session_manager.sessions` before every test.
- **Benefit:** Prevents state leakage (like chat history or audience preferences) between independent tests while still allowing the heavy FAQ index to remain loaded in memory once per session.

### 4. Session-Scoped Fixtures
Elevated the `retriever` and `router` fixtures to `session` scope to avoid redundant I/O.

## Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Total Tests** | 208 | 208 | - |
| **Execution Time** | > 120s (Timeout) | **5.6s** | **~40x** |
| **API Cost** | ~$0.05 / run | **$0.00** | **Free** |
| **Network Dependency** | Required | **Optional** | Offline-friendly |

## Prevention & Drawbacks

- **Stale Cache**: If prompts or FAQ data change, the cache must be manually cleared (`rm data/eval/test_*.json`).
- **State Leakage**: Session-scoped fixtures mean state (like chat history) can bleed between tests if not carefully managed. Always clear session state in tests that depend on it.
- **Recommendation**: Run a "live" test (without cache) before significant releases to verify API compatibility.

## See Also

- [Demo Confidence Test Suite Design](./demo-confidence-test-suite-design.md)
- [Parallel LLM Reranking Eval Speedup](../performance-issues/parallel-llm-reranking-eval-speedup.md)
