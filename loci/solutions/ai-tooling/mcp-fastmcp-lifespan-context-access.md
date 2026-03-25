---
module: Oghma
date: 2026-02-06
problem_type: runtime_error
component: mcp_server
symptoms:
  - "'Context' object is not subscriptable"
  - "MCP tool calls fail with AttributeError"
  - "Lifespan-yielded dict not accessible from tool handlers"
root_cause: wrong_api
resolution_type: config_change
severity: high
tags: [mcp, fastmcp, lifespan, context, python]
---

# MCP FastMCP Lifespan Context Access (v1.26.0)

## Problem

When using FastMCP's lifespan pattern to share state (e.g., database connections) with tool handlers, the yielded dict is NOT directly accessible via `mcp.get_context()["key"]`. The Context object is a Pydantic BaseModel, not a dict.

## Wrong (common mistake)

```python
@asynccontextmanager
async def lifespan(_: FastMCP):
    storage = Storage(read_only=True)
    yield {"storage": storage}

mcp = FastMCP("MyServer", lifespan=lifespan)

def _get_storage():
    return mcp.get_context()["storage"]  # TypeError: 'Context' object is not subscriptable
```

## Correct

```python
def _get_lifespan_context() -> dict[str, Any]:
    ctx = mcp.get_context()
    return ctx.request_context.lifespan_context

def _get_storage():
    return _get_lifespan_context()["storage"]  # Works
```

The access chain is: `Context` → `.request_context` (RequestContext dataclass) → `.lifespan_context` (the dict you yielded).

## Testing

Tests should monkeypatch `_get_lifespan_context` (or `_get_storage` directly), NOT `mcp.get_context`:

```python
# Wrong — returns plain dict, doesn't match real Context object
monkeypatch.setattr(mcp_server.mcp, "get_context", lambda: {"storage": fake})

# Right — patches the helper that extracts from Context
monkeypatch.setattr(mcp_server, "_get_lifespan_context", lambda: {"storage": fake})
```

## Why This Happens

MCP SDK v1.26.0 changed Context to a Pydantic BaseModel. The lifespan dict is buried under `request_context.lifespan_context`. The FastMCP docs show the lifespan pattern but don't clearly show how to ACCESS the yielded values from tool handlers.

## Prevention

- Always create a `_get_lifespan_context()` helper — single point of access
- Test with the real Context object path, not dict shortcuts
- When upgrading MCP SDK versions, check if Context API changed
