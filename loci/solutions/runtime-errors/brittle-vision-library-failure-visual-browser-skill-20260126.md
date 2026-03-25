---
module: visual-browser
date: 2026-01-26
problem_type: library-failure
component: browser-use-integration
symptoms:
  - "`browser-use` library failing with `error='items'`"
  - "Pydantic validation errors during schema parsing"
  - "OpenRouter model ID mismatch for Gemini 3 Flash"
root_cause: "Brittle abstraction in the `browser-use` library (v0.11.4) and strict schema requirements causing failures with OpenRouter's wrappers"
severity: high
tags:
  - browser-automation
  - playwright
  - openrouter
  - gemini-3-flash
  - agentic-browsing
---

# Brittle Vision Library Failure in Visual Browser Skill

## Problem Symptom
The `visual-browser` skill, initially implemented using the high-level `browser-use` library, consistently failed with a cryptic `error='items'` message. Further investigation revealed Pydantic validation errors when attempting to parse the structured output from models via OpenRouter. Additionally, the new **Gemini 3 Flash** model failed to load due to a model ID mismatch (`google/gemini-3-flash` vs the required `google/gemini-3-flash-preview`).

## Investigation Steps
1.  **Library Test:** Attempted to run `browser-use` with Gemini 2.0 Flash, Gemini 3 Flash, Claude 3.5 Sonnet, and GPT-4o.
2.  **Schema Failure:** All models failed with the same `error='items'` output, indicating the failure was within the library's internal orchestration/parsing logic rather than the models themselves.
3.  **Model ID Audit:** Discovered that OpenRouter requires the `-preview` suffix for Gemini 3 models as of early 2026.
4.  **Backend Proxying:** Attempted to use `LLMProxy` objects to "lie" to the library about the provider (e.g., setting `provider='openai'`), but the library's strict Pydantic models blocked these attributes.

## Root Cause
The `browser-use` library (v0.11.4) has a brittle dependency on specific LangChain and Pydantic schema formats. When used with OpenRouter's API wrappers, the slight differences in returned JSON structures cause the library's "item" parser to fail, rendering the high-level abstraction unusable for this multi-provider environment.

## Working Solution
Implemented a **custom lightweight Playwright loop** that calls the OpenRouter API directly. This provides total control over the vision-reasoning loop and eliminates the library-induced schema errors.

### Implementation Example (`browse.py`)
```python
async def query_gemini(screenshot_b64, task, history):
    payload = {
        "model": "google/gemini-3-flash-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
                ]
            }
        ]
    }
    # Direct httpx call bypassing brittle library parsers
    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, headers=headers, json=payload)
        # Process raw JSON content...
```

## Prevention Strategies
- **Prefer Direct Loops:** For high-reliability agentic browsing, use pure Playwright scripts instead of high-level brittle wrappers.
- **Stable Model IDs:** Always verify the latest OpenRouter model IDs (e.g., using `curl`) before hardcoding.
- **Decouple Reasoning:** Use **Gemini 3 Flash** for the visual analysis and spatial reasoning as it is currently the most cost-effective and fastest vision model (3x faster than 2.5 Pro).

## Related Documentation
- [Stable UI Selectors for Agent Browser](../testing-patterns/stable-ui-selectors-agent-browser.md)
- [Agent Browser Skill vs Subagent Confusion](agent-browser-skill-vs-subagent-confusion-20260126.md)
