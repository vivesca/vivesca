# Code Mode MCP Pattern

> Source: https://blog.cloudflare.com/code-mode-mcp/ (Feb 2025)

## Problem

Large APIs (100+ endpoints) are impractical to expose as individual MCP tools. Cloudflare's full API would consume 1.17M tokens as tool definitions — more than any model's context window.

## Pattern

Replace N tools with **two meta-tools**:

1. **`search(code)`** — Agent writes JS to query the OpenAPI spec, filtering thousands of endpoints to the relevant few. The full spec never enters the model's context.
2. **`execute(code)`** — Agent writes JS to make authenticated API calls, handle pagination, compose multiple requests, and extract only needed data.

Both run inside sandboxed V8 isolates (no filesystem, no env vars).

## Result

- ~2,500 endpoints accessible for ~1,000 tokens (99.9% reduction)
- Token cost stays flat as the API grows
- OAuth scoping limits agent to user-granted permissions
- Model uses its code-writing ability instead of burning context on schemas

## When to Use

- Wrapping a large API (100+ endpoints) as an MCP server
- API has an OpenAPI/Swagger spec available
- Endpoints follow consistent patterns (REST CRUD)
- You'd otherwise need dozens of tool definitions

## When NOT to Use

- Small APIs (< 20 endpoints) — just define the tools directly
- APIs without a machine-readable spec
- When you need tight input validation per-tool (Zod schemas on each tool give better guardrails)
- When the model needs hand-crafted tool descriptions to understand domain concepts

## Key Insight

The model is already good at writing code. Instead of pre-digesting an API into tool definitions (burning context), let it write code against the spec at runtime (burning compute). Trade context tokens for inference tokens.
