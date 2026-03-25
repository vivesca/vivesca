# Subagent Isolation for Token-Heavy Tool Outputs

## Problem

Skills/workflows that run tools returning 10K+ tokens of raw data (chat history, large file reads, search results) bloat the main context window. The raw data is only needed for synthesis — keeping it in context wastes tokens for the rest of the conversation.

## Solution

Delegate the heavy read + synthesis to a subagent (haiku for cost). Raw data stays in the subagent's context; only the concise summary (~30 lines) returns to main context.

```
Task tool (subagent_type: "general-purpose", model: "haiku"):
  "Run <heavy-command>, then synthesize a concise summary. Keep output under 30 lines."
```

## When to Use

- Chat history scans (`chat_history.py --full` → 30KB+ on busy days)
- Large file analysis where you only need key findings
- Multi-file search results that need collation
- Any tool output where raw > 5K tokens but synthesis < 500 tokens

## Applied In

- `/daily` skill — history scan delegated to haiku subagent (Feb 2026)
