---
name: Claude Agent Patterns 2026
description: Claude Code agent teams, subagents, Agent SDK patterns, model selection, and community production patterns — researched March 2026
type: reference
---

## Key Facts

- **Agent Teams release:** Feb 5, 2026 with Opus 4.6. Experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` required. v2.1.32+.
- **Split panes NOT supported in Ghostty** — only in-process mode works. tmux or iTerm2 required for split panes.
- **Subagent file format:** YAML frontmatter + Markdown body in `.claude/agents/` (project) or `~/.claude/agents/` (user)
- **Task tool renamed to Agent** in v2.1.63 — check both `"Task"` and `"Agent"` in tool_use blocks for compatibility
- **Subagents cannot spawn subagents** — no nesting; design around with skills or chaining from main conversation
- **Subagents do NOT inherit:** parent conversation history, parent skills, parent system prompt
- **Subagents DO inherit:** CLAUDE.md (all hierarchy), MCP servers, permission settings (from lead at spawn time)

## Performance Data (Anthropic Internal)
- Opus 4 lead + Sonnet 4 subagents: **+90.2% over single-agent Opus 4** on internal research eval
- Token cost: multi-agent system ~15x more tokens than single chat
- Token budget explains 80% of BrowseComp performance variance

## Model Selection Hierarchy (Validated Pattern)
| Role | Model | Rationale |
|---|---|---|
| Lead / orchestrator | Opus 4.6 | Deep reasoning for decomposition, synthesis |
| Standard subagents | Sonnet 4.6 | Balanced; 1M context |
| High-frequency workers | Haiku 4.5 | "90% of Sonnet agentic capability" at 3x cost savings |
| Security / architecture review | Opus 4.6 | High-stakes justifies cost |
| Built-in Explore/Plan | Haiku | Fast, read-only, latency-sensitive |

wshobson/agents (112 agents, 72 plugins) validates this empirically with four-tier assignment.

## Key Subagent Patterns
1. **Competing hypotheses debug** — explicitly adversarial teammates try to disprove each other; surviving theory has higher reliability
2. **Parallel code review lenses** — security / performance / test coverage as independent agents
3. **Spec-driven DAG** — Explorer → Proposer → Spec Writer → Designer → Task Planner → Implementer → Verifier → Archiver (agent-teams-lite)
4. **Progressive disclosure plugins** — skills load contextually, not all upfront (wshobson/agents pattern)

## Top Anti-Patterns
- Over-parallelizing small tasks (coordination overhead dominates)
- Vague dispatch prompts (fresh context = cannot ask clarifying questions)
- Lead implementing instead of delegating (use Shift+Tab delegate mode)
- Same-file parallel edits (causes overwrites)
- Broadcasting frequently (token cost scales with team size)
- Not using TeammateIdle/TaskCompleted hooks for quality gates

## AGENTS.md vs CLAUDE.md
- AGENTS.md = cross-tool standard (Claude Code, Cursor, Gemini CLI, OpenCode)
- CLAUDE.md = Claude-specific rules (slash commands, hooks, skills invocation)
- Both can coexist; put shared build/test/convention info in AGENTS.md

## Sources That Work Well
- code.claude.com/docs/en/agent-teams — full official docs, WebFetch works
- code.claude.com/docs/en/sub-agents — full official docs, WebFetch works
- platform.claude.com/docs/en/agent-sdk/subagents — SDK reference, WebFetch works
- anthropic.com/engineering/multi-agent-research-system — engineering blog, WebFetch works
- addyosmani.com/blog/claude-code-agent-teams/ — practical patterns, WebFetch works
- github.com/wshobson/agents — community library, WebFetch works (returns README)
- claudefa.st/blog/* — community guides, WebFetch works
- claudelog.com/mechanics/* — model selection guides, WebFetch works

## Source Gotchas
- medium.com articles: WebFetch 403 in most cases — use WebSearch snippets only
- anthropic.com/news/* main release pages: sometimes 403 — use VentureBeat/simonwillison as proxies
