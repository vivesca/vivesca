---
name: redarguo
description: "One-line adversarial challenge via a different LLM. Use PROACTIVELY before committing to decisions, sending client deliverables, publishing LinkedIn posts, or locking strategies. NOT for garden posts or reversible actions. Invoke when stakes are high and agreement feels too easy."
user_invocable: true
---

# Redarguo — Echo Chamber Breaker

One-line strongest counterargument from a different LLM. Designed to add minimal, targeted friction at decision points.

## When to Invoke (Proactively)

Invoke `/redarguo` without being asked when:
- Terry is about to **commit** to a decision (job, strategy, investment)
- Drafting **client-facing** or **LinkedIn** content
- A consilium returned unanimous agreement (suspiciously easy)
- Terry says "I'm sure" or "obviously" about something non-factual

Do NOT invoke for:
- Garden posts (low stakes, weekly cull handles quality)
- Reversible actions (email filters, skill edits, vault notes)
- Factual questions with verifiable answers
- Creative flow / ideation mode

## How It Works

```bash
# Pipe the claim or decision to a different model via OpenRouter
echo "<claim or decision summary>" | redarguo
```

Output format — exactly one line:
> 🔴 **Weakest point:** <the strongest counterargument in one sentence>

If the redarguo can't find a meaningful challenge, it says:
> 🟢 **No strong counter.** This holds up.

## Usage

```bash
# Challenge a decision
redarguo "Taking Capco at 93K over MTR at 120K because consulting compounds"

# Challenge a draft
redarguo "$(cat ~/notes/Writing/Blog/Published/some-post.md)"

# In-session: Claude pipes the relevant context automatically
```

## In-Session Use

When invoking proactively, Claude should:
1. Summarise the claim/decision in one sentence
2. Run `redarguo "<summary>"`
3. Present the one-line result
4. Let Terry decide whether it changes anything
5. Move on — don't discuss the redarguo's point unless Terry wants to
