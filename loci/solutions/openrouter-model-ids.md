# OpenRouter Model ID Gotcha

## Problem

Anthropic model IDs use date suffixes (e.g., `claude-sonnet-4-20250514`). OpenRouter does **not** — their IDs are just `anthropic/claude-sonnet-4`.

Using the Anthropic-style ID on OpenRouter returns:
```
Error code: 400 - 'anthropic/claude-sonnet-4-20250514 is not a valid model ID'
```

## Impact

In Meridian, this caused the gap analysis to silently fail — every finding returned "Gap" with "Error during analysis" in the reasoning field and 0 provenance. The catch block masked the real error.

## Fix

Check valid model IDs: `curl -sS https://openrouter.ai/api/v1/models | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data'] if 'claude' in m['id']]"`

Current valid Claude IDs on OpenRouter (Feb 2026):
- `anthropic/claude-sonnet-4` (not `claude-sonnet-4-20250514`)
- `anthropic/claude-sonnet-4.5`
- `anthropic/claude-sonnet-4.6`
- `anthropic/claude-3.7-sonnet`

## Rule

When configuring OpenRouter, always verify the model ID against their `/models` endpoint. Don't assume Anthropic's naming convention carries over.

*Discovered: 2026-02-24, Meridian project*
