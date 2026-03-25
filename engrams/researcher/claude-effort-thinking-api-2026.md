---
name: Claude Effort Level & Extended Thinking API — How It Actually Works (Mar 2026)
description: Definitive breakdown of effort parameter, adaptive thinking, budget_tokens deprecation, and whether high effort is a floor or ceiling for thinking.
type: reference
---

## Core Architecture (as of Opus 4.6 / Sonnet 4.6, Mar 2026)

### Two separate control mechanisms

1. **`effort` parameter** — in `output_config.effort`: `"low"`, `"medium"`, `"high"` (default), `"max"` (Opus 4.6 only). Affects ALL tokens: text responses, tool calls, AND extended thinking.
2. **`thinking` parameter** — `{type: "adaptive"}` (recommended on Opus/Sonnet 4.6) or `{type: "enabled", budget_tokens: N}` (deprecated on 4.6 models). Separate from effort.

### budget_tokens status
- **Deprecated on Opus 4.6 and Sonnet 4.6.** Will be removed in a future release.
- Still accepted and functional — no immediate migration required.
- Replace with: `thinking: {type: "adaptive"}` + `output_config: {effort: "..."}`.

---

## The Floor vs Ceiling Question — Answered Definitively

**High effort is a CEILING, not a floor.**

The official docs state (Adaptive Thinking page):
> "In adaptive mode, thinking is optional for the model. Claude evaluates the complexity of each request and determines whether and how much to use extended thinking."

The key table from the Adaptive Thinking docs:

| Effort | Thinking behavior |
|--------|------------------|
| `max` | Claude **always** thinks with no constraints on thinking depth |
| `high` (default) | Claude **always** thinks |
| `medium` | Claude uses **moderate** thinking. May **skip** thinking for very simple queries |
| `low` | Claude **minimizes** thinking. Skips thinking for simple tasks |

**Critical nuance:** At `high` effort, the docs say Claude "almost always thinks" (effort page) and "always thinks" (adaptive thinking page). The slight contradiction suggests high effort is behaviorally very close to a floor for thinking — the model will think on essentially any non-trivial input. But it is described as a ceiling (maximum allocated budget), not a hard technical requirement to emit thinking tokens.

**From the effort docs:**
> "Effort is a behavioral signal, not a strict token budget. At lower effort levels, Claude will still think on sufficiently difficult problems, but it will think less than it would at higher effort levels for the same problem."

---

## Can the Model Short-Circuit at High Effort?

**At `high` effort:** Practically no — the docs say Claude "almost always thinks" at high. For trivially simple prompts (e.g., "What is the capital of France?") in `medium` effort, Claude may skip thinking. At `high`, it is likely to think even on simple tasks.

**At `medium` effort:** Yes — Claude may skip thinking for "very simple queries."

**At `low` effort:** Yes — Claude "minimizes thinking. Skips thinking for simple tasks."

The model cannot "choose" to short-circuit against the effort level. Effort is a behavioral signal sent to the model at inference time; the model complies with it as training-level instruction.

---

## What effortLevel in Claude Code Maps To

From Claude Code model-config docs:
- `effortLevel` in settings file: `"low"`, `"medium"`, `"high"` — persists across sessions.
- `/effort low|medium|high|max|auto` — session-level override.
- `CLAUDE_CODE_EFFORT_LEVEL` env var — takes precedence over settings.
- Opus 4.6 **defaults to `medium` effort** for Max and Team subscribers (not `high`!).
- Sonnet 4.6 **defaults to `high` effort**.

At the API level, `effortLevel` maps directly to `output_config.effort` in the API call. Claude Code also uses `thinking: {type: "adaptive"}` by default on Opus 4.6 / Sonnet 4.6.

To revert to old fixed `budget_tokens` behavior: `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1`. Then `MAX_THINKING_TOKENS` controls the budget.

---

## API Wire Format (current)

```json
{
  "model": "claude-opus-4-6",
  "max_tokens": 16000,
  "thinking": {"type": "adaptive"},
  "output_config": {"effort": "medium"},
  "messages": [...]
}
```

The `effort` parameter affects:
1. Text responses and explanations (verbosity, depth)
2. Tool calls (fewer + terser at low, more + verbose at high)
3. Extended thinking (whether it happens and how much)

---

## Effort Also Affects Non-Thinking Token Spend

This is often missed: effort is not just a thinking control. At lower effort:
- Fewer tool calls
- Terse confirmations
- No preamble before actions
- Shorter explanations

At higher effort:
- More tool calls
- Explains plan before acting
- Detailed summaries
- Comprehensive code comments

---

## Sources
- Effort docs: https://platform.claude.com/docs/en/build-with-claude/effort
- Adaptive thinking docs: https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking
- Claude Code model config: https://code.claude.com/docs/en/model-config
