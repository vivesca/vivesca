# Claude Code Skills — Character Budget & Count Research

*Updated 2026-03-04. Sources: Anthropic official docs + GitHub issues + empirical gist research.*

## The Real Constraint: Token Budget (Auto-Scales with Context)

**As of v2.1.32:** Skill budget = **2% of context window** (tokens, not chars).

| Model | Context | Skill budget | Current usage |
|-------|---------|-------------|---------------|
| claude-sonnet-4-6 (Max) | 200k | **4,000 tokens** | 3,600 (90%) |

Pre-v2.1.32, the budget was ~16K chars and configurable via `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var. That env var is now a no-op — confirmed empirically (v2.1.66, fresh session, no effect). The auto-scale replaced it.

| Avg description length | Skills that fit in 16K budget |
|---|---|
| 263 chars (typical) | ~42 skills |
| 130 chars (compressed) | ~67 skills |
| 100 chars | ~75 skills |

**Silent failure mode:** Skills exceeding the budget are not deprioritised — they are completely inaccessible, including via `/skill-name` slash invocation. Claude is explicitly instructed not to use skills not listed.

**Check current state:** Run `/context` inside Claude Code — shows a warning listing excluded skills if truncation is occurring.

## Three-Level Lazy Loading (Claude Code)

| Level | What loads | When | Token cost |
|---|---|---|---|
| **Metadata** | `name` + `description` from frontmatter only | Always, at session startup | ~100 tokens per skill |
| **Instructions** | Full SKILL.md body | Only when skill is triggered | Under 5K tokens |
| **Resources** | Supporting files (scripts etc.) | Only as referenced | Effectively unlimited |

Key implication: **bodies have zero selection cost** — only descriptions burn budget. Description quality and length are the lever.

## Three Fixes (in order of effort)

**1. Increase the budget (env var) — UNVERIFIED in v2.1.66**
```bash
# Add to ~/.zshenv
export SLASH_COMMAND_TOOL_CHAR_BUDGET=32000
```
**Empirically tested (Mar 2026, Claude Code v2.1.66):** Set to 500 and tested in fresh Ghostty window (new login shell, clean env), tmux new window, and `--print` headless — no effect in any case. Skills count unchanged. The env var appears to be a no-op in the current version, or `/context` shows the full registry rather than the budget-filtered system prompt.

**Real fixes that work:** skill cull (91→85) + `disable-model-invocation: true` on reference skills.

**2. Set `disable-model-invocation: true` for reference-only skills**
```yaml
---
name: skill-name
description: ...
disable-model-invocation: true
---
```
Removes the skill from the character budget entirely. You can still `/skill-name` manually; Claude won't auto-trigger it. Zero budget cost. Right choice for skills you invoke deliberately (tecton, manus, cursus, nauta, etc.)

**3. Compress descriptions**
Descriptions under 130 chars double capacity. Front-load trigger keywords in the first 50 chars.

## Invocation Control Matrix

| Frontmatter | User can invoke | Claude auto-invokes | In budget? |
|---|---|---|---|
| (default) | Yes | Yes | Yes |
| `disable-model-invocation: true` | Yes | No | **No — zero budget cost** |
| `user-invocable: false` | No | Yes | Yes |

Note: `user-invocable: false` still consumes budget (Claude needs to see it to auto-trigger it).

## Commands vs Skills — Naming Note

**Custom commands have been merged into skills** (confirmed by official docs, 2026-03-04). `.claude/commands/review.md` and `.claude/skills/review/SKILL.md` are now equivalent — both create `/review`. Existing `.claude/commands/` files keep working.

This explains why the env var is named `SLASH_COMMAND_TOOL_CHAR_BUDGET` — it was named before the merge. It applies to the current SKILL.md system, not a separate older system.

## What the Generic Tool-Calling Research Got Wrong

The earlier research (tool-selection accuracy curves: 50 tools = 84-95%, 200 tools = 41-83%) was from **structured tool-calling benchmarks** (OpenAI function calling, Anthropic tool use API). Claude Code skills are text injected into the system prompt, not structured tool calls. The accuracy curves don't transfer directly.

What *does* apply from that research:
- **Lost in the middle** — descriptions buried deep in long context get less attention (general attention finding)
- **Token cost** — more descriptions = less context for actual work

What *doesn't* apply:
- The specific accuracy percentages
- Anthropic's "8 Skills hard cap" — that's the Enterprise Skills API at platform.claude.com, completely different product
- "30-40 practitioner consensus" — was for MCP servers / function calling

## Anthropic Official Guidance (Claude Code Skills)

- SKILL.md body: keep under **500 lines** (soft limit)
- Description field: max **1024 characters** (hard limit)
- Name field: max **64 characters**
- Anthropic docs acknowledge "100+ available Skills" as a real scenario

## Practical State for This System (~91 skills)

At 91 skills × ~372 chars average (263 desc + 109 overhead) = **~33,852 chars against 16K budget**.

Approximately **48 skills are currently silently invisible**.

Priority actions:
1. Set `SLASH_COMMAND_TOOL_CHAR_BUDGET=32000` in `~/.zshenv`
2. Add `disable-model-invocation: true` to reference skills (tecton, manus, cursus, nauta, indago, taxis, solutions, artifex, dev-workflow-reference, presentation, obsidian-markdown, linkedin-research, cursus, photos, defuddle, remote-llm, judex, examen, trutina)
3. Compress descriptions for high-use skills to under 130 chars
4. Light cull: clear redundancies only (openrouter/stips dups, empty dirs)

## Sources

- [Claude Code Skills docs](https://code.claude.com/docs/en/skills) — budget, env var, invocation control
- [Agent Skills overview — platform.claude.com](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — three-level loading
- [GitHub issue #13099](https://github.com/anthropics/claude-code/issues/13099) — empirical 42/63 truncation discovery
- [Empirical gist research by alexey-pelykh](https://gist.github.com/alexey-pelykh/faa3c304f731d6a962efc5fa2a43abe1) — per-skill overhead, capacity tables
- [GitHub issue #14549](https://github.com/anthropics/claude-code/issues/14549) — plugin marketplace inflation bug (19x)
