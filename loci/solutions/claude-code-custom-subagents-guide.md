---
title: When to Create Custom Subagents vs Skills vs Main Context
date: 2026-02-18
tags: [claude-code, subagents, architecture, decision-framework]
---

# Custom Subagents: When and Why

## When Subagents Beat Main Context

Create a subagent only when **at least two** of these properties provide clear value:

1. **Isolated context** — the task produces noisy/verbose output (web searches, test runs, large file reads) that would bloat main conversation
2. **Persistent memory** — the agent accumulates patterns over time that improve its work (blind spots, codebase conventions, source preferences)
3. **Model routing** — the task can run on a cheaper model (haiku for lookups, sonnet for review) saving opus tokens
4. **Tool restrictions** — the agent should be read-only or limited (reviewers don't need Write)

**For the full decision framework (skills vs agents vs hooks vs MCP vs plugins), see `claude-code-extension-mechanisms.md`.**

## Kill Rule

From consilium council (5-model consensus):
> Don't create a new subagent unless you'll use it ≥2x/week for ≥4 weeks. Delete any that misses for 2 consecutive weeks.

## Setup Notes

- **Storage:** `~/.claude/agents/` (user-level, all projects) or `.claude/agents/` (project-level)
- **Symlink to agent-config:** `~/.claude/agents/` → `~/agent-config/claude/agents/` for git backup
- **Agent memory:** `~/.claude/agent-memory/` → `~/agent-config/claude/agent-memory/` for git backup
- **Memory scope:** `user` (cross-project) is the default. Use `project` or `local` only for codebase-specific knowledge
- **Format:** Markdown with YAML frontmatter (name, description, tools, model, memory)
- **Idle cost:** ~40 tokens per agent in system prompt (description only). Full prompt loads only on invocation.

## Anti-Patterns

- **Generic role templates** (e.g., VoltAgent's 127 agents) — boilerplate checklists that Claude already knows. No value over a well-phrased prompt.
- **Client/NDA data in agent memory** — compliance risk. Keep client context in Obsidian, pipe ad-hoc.
- **Agents that duplicate existing skills** — if `/meeting-prep` or `/palaestra` works in main context, an agent adds overhead without value.
- **Agents needing persona/behavioral instructions** — subagents don't inherit CLAUDE.md. If the task needs "Jeeves" or specific communication style, run in main context.
- **Too many agents** — each adds idle tokens + cognitive overhead of "which agent handles this?" Keep under 7.

## What Worked (Current Setup)

| Agent | Why it's a subagent |
|---|---|
| reviewer | Memory (learns patterns), isolation (review output), cheaper model |
| security-reviewer | Memory (accumulates security patterns), isolation, tool-restricted |
| scout | Model routing (haiku), isolation (verbose lookups) |
| researcher | Isolation (noisy web searches), memory (source preferences) |
| skeptical-partner | Isolation (stays adversarial — main Claude softens), memory (tracks blind spots) |

## References

- Official docs: https://code.claude.com/docs/en/sub-agents
- Agent Teams (experimental): https://code.claude.com/docs/en/agent-teams
- VoltAgent collection (templates, not tools): https://github.com/VoltAgent/awesome-claude-code-subagents
- Consilium transcript: ~/notes/Councils/LLM Council - Subagent Ideas - 2026-02-18.md
