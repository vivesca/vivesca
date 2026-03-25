---
module: AI Tooling
date: 2026-02-05
problem_type: best_practice
component: delegation
symptoms:
  - "User has competing priorities but wants feature work to progress"
  - "Complex task requires research before implementation"
  - "Need to ship without blocking user's high-priority tasks"
root_cause: mental_model_error
resolution_type: process_change
severity: medium
tags: [orchestration, delegation, background-agents, codex, opencode, necto, async-work]
related_files:
  - ~/oghma/docs/plans/2026-02-05-feat-mcp-server-plan.md
  - ~/oghma/src/oghma/mcp_server.py
---

# Orchestration pattern for shipping features while user is busy

## Problem

User wants feature work to progress but has competing high-priority tasks (BGV docs, resignation letter, interview prep). How to ship without blocking them or requiring constant attention?

## Context: Oghma MCP Server Session

The Oghma project (personal memory system) had MVP complete with 4,498 memories. User wanted v2 feature (MCP server for tool access) but had immediate priorities that couldn't wait.

## The Orchestration Pattern

### Phase 1: Non-Blocking Planning

Launch a **background Task agent** to research and write the plan:

```
Task: Research MCP server patterns and write implementation plan
- Review existing MCP servers (filesystem, memory, etc.)
- Analyze Oghma's current architecture
- Write plan to ~/oghma/docs/plans/2026-02-05-feat-mcp-server-plan.md
```

User can continue with other work. Plan arrives when ready.

### Phase 2: Match Complexity to Tool

Once plan is approved, **delegate to the right tier**:

| Task Type | Delegate To | Why |
|-----------|-------------|-----|
| Complex implementation (MCP server, architecture) | **Codex** | GPT-5.3 Codex handles hard engineering |
| Simple config/glue (MCP config files) | **OpenCode** | GLM-5 (or GLM-4.7 fallback) is free and sufficient |
| Judgment calls (review, user decisions) | **Claude Code** | Stays in main conversation |

### Phase 3: Codex for Heavy Lifting

For the MCP server implementation:

```bash
codex exec --skip-git-repo-check "
Implement MCP server for Oghma memory system.

Goal: Expose memory operations as MCP tools.
Plan: [reference the plan file]
Boundaries: Read-only storage mode, no destructive operations without flag.

Done when:
- mcp_server.py implements all tools from plan
- Tests pass
- Can run with: uv run python -m oghma.mcp_server
"
```

Codex shipped:
- `mcp_server.py` with full tool suite
- Read-only storage mode for safety
- 143 tests passing

### Phase 4: OpenCode for Routine Tasks

For MCP config propagation:

```bash
OPENCODE_HOME=~/.opencode-lean opencode run -m zhipuai-coding-plan/glm-4.7 \
  --title "Add Oghma MCP config" \
  "Add Oghma MCP server config to ~/.claude/mcp.json"
```

### Phase 5: Sync Across Tools

Use **necto** to propagate config to all AI tools:

```bash
necto --full
```

This ensures Claude Code, Codex, and OpenCode all have access to the new MCP server.

## Key Insights

1. **Background agents for planning = non-blocking**. User approves the result, not the process.

2. **Match task complexity to tool tier**:
   - Codex for hard/architectural work (paid but smarter)
   - OpenCode for routine/bulk work (free and unlimited)
   - Claude Code for orchestration and user interaction

3. **necto ensures consistency**. All three AI tools get the same MCP config.

4. **User focuses on high-priority**. Feature ships in parallel with their urgent tasks.

## When to Use This Pattern

- User has competing priorities but wants progress
- Task has distinct planning and implementation phases
- Implementation is complex enough to warrant Codex
- Result needs to work across multiple AI tools

## Anti-Patterns to Avoid

- Asking user to "check in" repeatedly during implementation
- Using Codex for simple tasks (waste of paid tier)
- Using OpenCode for complex architecture (will fail or produce poor code)
- Forgetting to sync MCP config (tools won't have access)

## Decision Flow

```
User wants feature but is busy
    │
    ├─ Launch background Task agent for planning
    │   └─ Write plan to docs/plans/
    │
    ├─ User approves plan (async, when convenient)
    │
    ├─ Is implementation complex?
    │   ├─ Yes → Codex (architecture, multi-file, tests)
    │   └─ No → OpenCode (config, simple changes)
    │
    ├─ Need config sync?
    │   └─ Yes → necto to propagate across tools
    │
    └─ Report completion to user
```

## Applies To

- MCP server development
- Any feature requiring research + implementation
- Multi-day work while user has other priorities
- Work that benefits from "think first, then build"
