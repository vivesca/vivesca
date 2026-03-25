---
title: Claude Code Extension Mechanisms — When to Use What
date: 2026-02-18
tags: [claude-code, architecture, skills, subagents, hooks, mcp, plugins, decision-framework]
---

# Claude Code Extension Mechanisms

Six ways to extend Claude Code. Each has a sweet spot. Using the wrong one wastes tokens or adds friction.

## Quick Reference

| Mechanism | Runs in | Triggered by | Inherits CLAUDE.md | Persistent state | Token cost |
|---|---|---|---|---|---|
| **Main context** | Main conversation | User message | Yes | No (session only) | Opus tokens |
| **Skill** | Main conversation | `/skill-name` | Yes | No | Opus tokens (prompt injected) |
| **Subagent** | Isolated context | Auto-delegation or explicit | No | Optional (memory) | ~40 tok idle + invocation model |
| **Hook** | External process | Lifecycle event | N/A (shell script) | N/A | Zero LLM tokens |
| **MCP server** | External process | Tool call | N/A (protocol) | Server-side | Per-call tokens |
| **Plugin** | Mixed (agents + tools) | Various | Agents: No; Tools: via main | Plugin-defined | Varies |

## Decision Flowchart

```
Is this enforcing a rule that MUST NOT be bypassed?
  YES → Hook (hard gate, can't be ignored)
  NO ↓

Is this connecting to an external system/API?
  YES → MCP server (structured protocol, reusable across tools)
  NO ↓

Is the output noisy/verbose AND benefits from isolation?
  YES ↓
  Does it also accumulate knowledge over time?
    YES → Subagent with memory
    NO  → Subagent without memory (or just Task tool ad-hoc)
  NO ↓

Does it need persona, vault context, or conversation history?
  YES ↓
  Is it a repeatable workflow with specific steps?
    YES → Skill (reusable prompt in main context)
    NO  → Main context (just do it)
  NO ↓

Can it run on a cheaper model to save tokens?
  YES → Subagent with model routing
  NO  → Main context
```

## When to Use Each

### Main Context (default)

**Use for:** Interactive work, iterative drafts, anything needing persona/vault/conversation history.

- Inherits full CLAUDE.md, persona (Jeeves), behavioral rules
- Access to conversation history and prior context
- Interactive back-and-forth with user
- Highest token cost (opus) but richest context

**Examples:** Drafting messages, career discussions, vault management, daily/weekly routines, any task where you'd say "but also consider X from earlier."

### Skills (`~/skills/`)

**Use for:** Repeatable workflows that run in main context with specific steps.

- Prompt injected into main conversation (inherits everything)
- User-invocable via `/skill-name`
- Can be preloaded into subagents via `skills:` field
- No isolation — output stays in main context
- Shared across tools via skill-sync (Claude Code + OpenCode)

**Good fit when:**
- Multi-step workflow with specific instructions (morning briefing, weekly review)
- Needs vault context or persona (message drafting, meeting prep)
- Needs conversation history (wrap, daily log)
- Reused frequently enough to warrant a named command

**Bad fit when:**
- Output is noisy/verbose (use subagent instead)
- Needs to accumulate knowledge across sessions (use subagent with memory)
- Just a simple prompt (don't create a skill for "summarize this")

**Examples:** `/morning`, `/daily`, `/weekly`, `/todo`, `/consilium`, `/meeting-prep`, `/delegate`

### Subagents (`~/.claude/agents/`)

**Use for:** Isolated tasks where context separation, memory, or model routing provides clear value.

- Runs in own context window (doesn't bloat main conversation)
- Does NOT inherit CLAUDE.md, persona, or conversation history
- Optional persistent memory across sessions
- Model routing (haiku/sonnet/opus)
- Tool restrictions (read-only reviewers, no web access, etc.)
- Auto-delegated based on description, or invoked explicitly

**Good fit when ≥2 of:**
1. Isolated context — noisy output you don't want in main conversation
2. Persistent memory — accumulates patterns over time
3. Model routing — cheaper model suffices
4. Tool restrictions — agent should be limited
5. Behavioral isolation — agent needs to be adversarial/different from main Claude

**Bad fit when:**
- Task needs persona/vault/conversation (use main context or skill)
- Task is interactive/iterative (subagents can't ask user questions in background)
- Generic role that Claude already knows (don't create "python expert" agent)
- Duplicates existing skill (if `/palaestra` works, don't make a GARP agent)

**Kill rule:** ≥2x/week for ≥4 weeks, or delete. Review monthly.

**Examples:** reviewer, security-reviewer, scout, researcher, skeptical-partner

### Hooks (`~/.claude/hooks/`)

**Use for:** Hard enforcement that can't be bypassed. Automatic actions on lifecycle events.

- Shell scripts triggered by lifecycle events (PreToolUse, PostToolUse, UserPromptSubmit, Stop, etc.)
- Run OUTSIDE the LLM — zero token cost
- Can block actions (exit code 2), inject context (stdout), or silently act
- Hooks > CLAUDE.md for enforcement (hard gate vs soft guidance)
- Can be scoped to specific tools via matcher

**Good fit when:**
- Rule MUST be enforced (bash-guard blocking rm -rf, blocking npm in pnpm projects)
- Automatic formatting/linting after edits (prettier, ruff, rustfmt)
- Injecting reminders on every prompt (auto-learning reminder)
- Pre-flight checks before actions
- Session lifecycle management (pre-compact, session-end)

**Bad fit when:**
- You want the LLM to reason about the rule (use CLAUDE.md instead)
- The action needs LLM intelligence (hooks are dumb scripts)
- The rule has nuanced exceptions (hooks are binary: allow/block)

**Examples:** bash-guard.js (PreToolUse), post-edit-format.js (PostToolUse), auto-learning.sh (UserPromptSubmit), session-end-reminder.js (Stop)

### MCP Servers

**Use for:** Connecting Claude to external systems via structured protocol.

- Expose tools, resources, and prompts via Model Context Protocol
- Run as separate processes (stdio or HTTP transport)
- Reusable across different AI tools (Claude Code, Cursor, etc.)
- Structured input/output via JSON-RPC

**Good fit when:**
- Connecting to an external API/service (database, SaaS, etc.)
- Tool needs to be reusable across multiple AI coding tools
- Complex tool that benefits from server-side state management
- You want a shared tool ecosystem (Context7 for docs)

**Bad fit when:**
- Simple one-off integration (just use Bash or WebFetch)
- The tool is specific to Claude Code workflows (use skill or hook)
- You're wrapping a CLI that already works via Bash

**Examples:** Context7 (documentation), Compound Engineering tools

### Plugins

**Use for:** Packaged bundles of agents + tools + skills from third parties.

- Installed from marketplace or local directory
- Can include subagents, MCP servers, skills, and hooks
- Lowest priority for name conflicts (custom agents override plugin agents)

**Good fit when:**
- Third-party provides a well-maintained workflow package
- You want a complete system (CE provides plan→work→review→compound)
- The plugin's agents/tools are better than what you'd build yourself

**Bad fit when:**
- You only need one piece of the plugin (cherry-pick the pattern instead)
- The plugin adds many agents you won't use (bloats system prompt)
- You need to customize the agents heavily (fork or write your own)

**Examples:** Compound Engineering (review pipeline + solutions KB), rust-analyzer LSP

## Architecture: How They Layer

```
┌─────────────────────────────────────────┐
│  CLAUDE.md + MEMORY.md (always loaded)  │  Rules + gotchas
├─────────────────────────────────────────┤
│  Hooks (lifecycle gates)                │  Hard enforcement, zero tokens
├─────────────────────────────────────────┤
│  Main Context (opus)                    │  Interactive, persona, vault
│  ├── Skills (injected prompts)          │  Repeatable workflows
│  └── MCP Tools (protocol calls)        │  External system access
├─────────────────────────────────────────┤
│  Subagents (isolated)                   │  Noisy tasks, memory, cheaper models
│  └── Plugin Agents (packaged)          │  Third-party bundles
└─────────────────────────────────────────┘
```

**Information flows down, not up:** Subagents don't see CLAUDE.md or conversation history. Skills see everything. Hooks see tool inputs but not conversation context.

## Anti-Patterns

- **Skill for something that should be a hook** — if it MUST happen every time (formatting, validation), don't rely on Claude remembering to invoke a skill. Use a hook.
- **Subagent for something that needs persona** — it won't have Jeeves, vault context, or conversation history. Run in main context.
- **Hook for something that needs LLM reasoning** — hooks are shell scripts. They can pattern-match, not think.
- **MCP server for a simple CLI wrapper** — if `gog gmail search` works via Bash, don't build an MCP server around it.
- **Plugin when you only use 20% of it** — extract the patterns you need into custom agents/skills.
- **Generic role agent** — "Python expert" or "Senior architect" agents add nothing Claude doesn't already know. Only create agents with specific behavioral properties (adversarial, memory-accumulating, cheap).
- **Too many of anything** — every extension adds cognitive overhead ("where does this live?"). Fewer, sharper tools > many overlapping ones.

## Current Setup (Feb 2026)

| Type | Count | Location |
|---|---|---|
| Skills | ~40 | `~/skills/` → `~/.claude/skills/` |
| Subagents | 5 | `~/agent-config/claude/agents/` → `~/.claude/agents/` |
| Hooks | 10 | `~/agent-config/claude/hooks/` → `~/.claude/hooks/` |
| MCP servers | 1 | Context7 (via CE plugin) |
| Plugins | 2 | Compound Engineering, rust-analyzer LSP |

## References

- Subagent details: `claude-code-custom-subagents-guide.md` (same directory)
- Official docs: https://code.claude.com/docs/en/sub-agents
- Skills docs: https://code.claude.com/docs/en/skills
- Hooks docs: https://code.claude.com/docs/en/hooks
- MCP docs: https://code.claude.com/docs/en/mcp
- Plugins docs: https://code.claude.com/docs/en/plugins
