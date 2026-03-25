---
name: ask-llms
description: Query multiple LLMs in parallel via OpenRouter and compare responses. "ask llms"
user_invocable: true
---

# Ask LLMs

Query multiple LLMs simultaneously via OpenRouter and display their responses side-by-side. For quick parallel comparisons — use `/llm-council` when you want models to actually debate and synthesize.

## When to Use

Use this skill when:
- Comparing how different LLMs answer the same question
- Need diverse perspectives on a problem or decision
- Want quick "second opinions" from multiple models
- Curious about model differences on a topic
- Quick feedback on outreach messages (see `/outreach` for style tips)

## Prerequisites

**OpenRouter API key** (required):
```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

## PII Masking

When questions contain personal information, mask before sending:

```bash
cd /Users/terry/skills/pii-mask
masked=$(uv run mask.py "Question with personal details...")

cd /Users/terry/skills/ask-llms
uv run council.py "$masked"
```

Preview: `uv run mask.py --dry-run "your question"` — see `/Users/terry/skills/pii-mask/SKILL.md`

## Instructions

### Step 1: Get the Question

Ask the user what question they want answered, or use the question they already provided.

### Step 2: Run the Query

**Expensive mode (default)** — frontier models with thinking:
```bash
cd /Users/terry/skills/ask-llms
uv run council.py "YOUR QUESTION HERE"
```

**Cheap mode** — fast and affordable:
```bash
uv run council.py "YOUR QUESTION HERE" --cheap
```

### Step 3: Present Results

The script outputs each model's response with clear separators. Highlight:
- Key differences between models
- Points of agreement
- Which response is most relevant to the user's situation

## Model Tiers

**Expensive (default)** — 2026 frontier models with thinking/reasoning:
- Claude Opus 4.5
- GPT-5.2
- Gemini 3 Pro
- Grok 4
- DeepSeek R1

**Cheap** (`--cheap` flag) — fast and affordable:
- Claude Sonnet 4.5
- GPT-4o
- Gemini Flash
- Grok 4.1 Fast
- DeepSeek V3.2

## Options

| Flag | Description |
|------|-------------|
| `--cheap` | Use cheaper/faster models |
| `--no-thinking` | Disable reasoning mode for expensive models |
| `--timeout N` | Timeout in seconds (default: 60 cheap, 180 expensive) |
| `--models "a,b,c"` | Override with custom models |

## Routing: Which LLM Tool?

> **Future:** This skill will fold into `/consilium --quick` mode. Until then, use this for parallel comparisons and `/consilium` for deliberation.

```
Is this about proprietary/work code?
  YES → /remote-llm (craft prompt for local LLM)
  NO ↓
Does the question have a single correct answer?
  YES → Web search or ask Claude directly
  NO ↓
Is this personal preference / physical / visual?
  YES → Try it in person, or ask Claude directly
  NO ↓
Are there genuine trade-offs requiring deliberation?
  YES → /consilium (full council, ~$0.50)
  NO ↓
Need multiple perspectives quickly?
  YES → /ask-llms (parallel queries, ~$0.10)
  NO → Just use Claude directly
```

| Tool | Use When | Cost |
|------|----------|------|
| `/ask-llms` | Quick comparison, parallel queries | $0.01-0.30 |
| `/consilium` | Important decisions, deliberation needed | $0.50-1.00 |
| `/remote-llm` | Proprietary code, can't share directly | Free |

### Coding Delegation (separate concern)

| Tool | Best For | Cost |
|------|----------|------|
| Claude Code (Opus) | Complex multi-file, planning, judgment | Subscription |
| OpenCode (GLM-5) | Routine coding, unlimited | Free |
| Codex (GPT-5.2) | Hard bugs, escalation | Paid |

Stay in Claude Code if context is already built. Suggest OpenCode for new tasks or when quota >70%.

## Files

- Script: `/Users/terry/skills/ask-llms/council.py`
- This skill: `/Users/terry/skills/ask-llms/SKILL.md`
