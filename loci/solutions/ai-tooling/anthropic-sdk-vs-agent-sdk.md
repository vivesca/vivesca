# Anthropic SDK vs Claude Agent SDK — When to Use Which

**Date:** 2026-02-20
**Context:** Deciding SDK for aegis-gov (AI governance intake agent)

## The Two SDKs

- **`anthropic`** (standard) — Stable. Direct Messages API wrapper. Tool use via JSON Schema dicts + manual dispatch loop. `messages.parse()` for Pydantic structured output.
- **`claude-agent-sdk`** (v0.1.38, Alpha, Feb 2026) — Wraps Claude Code CLI as Python library. Custom tools implemented as in-process MCP servers. Designed for coding agents (file system, bash, web).

## Decision Rule

| Your tools are... | Use |
|---|---|
| Pure Python business logic (score, route, classify) | `anthropic` (standard) |
| File system, bash, web browsing, code editing | `claude-agent-sdk` |
| Mix of both | Start with standard, add Agent SDK only if file/bash tools dominate |

## Why Standard SDK Won for aegis-gov

- 6 tools, all pure Python functions (get_submission, score_dimensions, route_case, etc.)
- Need surgical control over tool dispatch for vulnerable vs hardened mode switching
- `ask_clarifying_question` blocks on stdin — need to intercept for automated red-team
- Agent loop is ~30 lines — framework overhead exceeds value
- Agent SDK adds MCP abstraction for no benefit when tools are in-process functions

## The Agent Loop (30 lines)

```python
while True:
    response = client.messages.create(model=..., messages=messages, tools=tools)
    messages.append({"role": "assistant", "content": response.content})
    if response.stop_reason == "end_turn":
        break
    tool_results = [dispatch(b.name, b.input) for b in response.content if b.type == "tool_use"]
    messages.append({"role": "user", "content": tool_results})
```

## Also Considered and Rejected

- **LangChain/LangGraph:** Framework abstraction hides behavior you need to see for red-teaming. Adds dependency complexity. Agent loop is too simple to justify.
- **OpenRouter:** Existing pattern in consilium/bank-faq-chatbot. Valid option but direct Anthropic SDK has better tool_use support and structured output.
