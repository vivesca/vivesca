---
name: llm-routing
description: Reference for choosing between LLM tools (ask-llms, llm-council, remote-llm). Consult before querying multiple models.
user_invocable: false
---

# LLM Routing

Decision guide for when to use which LLM querying tool.

## Tool Selection

| Tool | Use When | Models | Cost |
|------|----------|--------|------|
| `/ask-llms` | Quick comparison, parallel queries | 3-5 via OpenRouter | Low |
| `/llm-council` | Important decisions, deliberation needed | 5 frontier + judge | High |
| `/remote-llm` | Proprietary code, can't share directly | Qwen3 at work | Free |

## Decision Tree

```
Is this about proprietary/work code?
  └── YES → /remote-llm (craft prompt for local LLM)
  └── NO ↓

Is this an important decision with trade-offs?
  └── YES → /llm-council (5 models deliberate)
  └── NO ↓

Do you need multiple perspectives quickly?
  └── YES → /ask-llms (parallel queries)
  └── NO → Just use Claude directly
```

## /ask-llms

**Purpose:** Quick parallel queries to multiple models via OpenRouter.

**Best for:**
- Comparing model outputs on same prompt
- Getting diverse perspectives without deliberation
- Draft review from multiple viewpoints
- Quick "second opinion" checks

**Flags:**
- `--cheap` — Use cheaper models (for low-stakes queries)
- No flag — Use frontier models (for important messages)

**Example:**
```
/ask-llms "Should I follow up with this recruiter now or wait?"
```

## /llm-council

**Purpose:** 5 frontier models deliberate sequentially, each seeing previous responses, then judge synthesizes.

**Best for:**
- Career decisions (job offers, timing, strategy)
- Important outreach messages
- When you want consensus, not just comparison
- Complex trade-offs with no clear answer

**Models:** Opus 4.5, GPT-5.2, Gemini 3 Pro, Grok 4, Kimi K2.5

**Example:**
```
/llm-council "I have an offer at $93K from Capco. Should I accept or negotiate?"
```

## /remote-llm

**Purpose:** Craft prompts for Terry to run on local/work LLMs when code can't be shared.

**Best for:**
- Proprietary bank code
- Work systems Terry can't paste
- Anything requiring Qwen3 at CITIC

**Output:** A well-structured prompt Terry can copy to the work LLM.

## Environment Setup

```bash
# Required for ask-llms and llm-council
export OPENROUTER_API_KEY=...

# For some models in council
export GOOGLE_API_KEY=...
export MOONSHOT_API_KEY=...
```

## Cost Awareness

| Tool | Approximate Cost |
|------|------------------|
| `/ask-llms --cheap` | ~$0.01-0.05 |
| `/ask-llms` | ~$0.10-0.30 |
| `/llm-council` | ~$0.50-1.00 |
| `/remote-llm` | Free (local) |

## Coding Tools (Claude Code vs OpenCode)

Separate from querying multiple LLMs — this is about which coding assistant to use.

| Tool | SWE-bench | Cost | Best For |
|------|-----------|------|----------|
| **Claude Code (Opus 4.5)** | 80.9% | ~$3/M tokens | Complex multi-file, highest accuracy |
| **OpenCode + GLM-5** | 73.8% | **Unlimited** | New tasks, bilingual, quota conservation |
| **OpenCode + Gemini 3 Flash** | 78.0% | ~$0.50/M | Speed when GLM unavailable |

### When to Switch to OpenCode

**Stay in Claude Code** if context is already built — switch costs (re-explaining, re-reading) usually exceed savings.

**Suggest OpenCode (GLM-5)** when:
- New task without existing Claude Code context
- Weekly Claude Code quota running high (>70%)
- Bilingual projects (TC/SC/EN) — GLM's multilingual edge

### GLM-5 Notes

- Terry has unlimited quota via Coding Max (valid to 2027-01-28)
- SWE-bench Multilingual: 66.7% — strong for bilingual
- Preserved Thinking: keeps reasoning across agentic turns

### Quota Conservation

When Claude Code usage is high:
- Default to OpenCode for new tasks
- Shorter responses, fewer exploratory reads
- Skip optional verification unless critical

## Related Skills

- `/ask-llms` — Parallel queries implementation
- `/llm-council` — Deliberation implementation
- `/remote-llm` — Local LLM prompt crafting
- `/delegate` — Delegate tasks to OpenCode/Codex
