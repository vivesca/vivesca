---
module: GLOBAL
date: 2026-02-06
problem_type: workflow_issue
component: delegation
symptoms:
  - "OpenCode times out investigating library source code"
  - "Delegate gets stuck reading pip package internals instead of making changes"
  - "Task requires understanding external API that delegate can't access"
root_cause: tool_limitation
resolution_type: process_change
severity: low
tags: [opencode, delegation, library-internals, mcp, fastmcp]
---

# OpenCode Struggles with External Library Internals

## Problem

When delegating a fix that requires understanding an external library's API (e.g., MCP SDK's Context object), OpenCode/GLM-4.7 gets stuck exploring the library source code in site-packages. It reads file after file trying to understand the API surface, burns through its context, and times out without making changes.

## When This Happens

- Fix requires knowing how a library's API changed between versions
- The correct API isn't obvious from the existing code or error messages
- Library has complex inheritance (e.g., Pydantic BaseModel subclasses)

## Solution

Do the API investigation yourself (in Claude Code), then delegate with **explicit instructions**:

```
# Bad delegation prompt:
"Fix the Context access error in mcp_server.py"

# Good delegation prompt:
"In mcp_server.py line 23, change mcp.get_context()['storage'] to
mcp.get_context().request_context.lifespan_context['storage'].
The Context object is a Pydantic BaseModel, not a dict."
```

## Rule of Thumb

- **Delegate:** File changes, test writing, refactoring — where the task is mechanical
- **Don't delegate:** API investigation, library version differences — where judgment and exploration are needed
- **Hybrid:** Investigate the API yourself, then delegate the implementation with explicit instructions
