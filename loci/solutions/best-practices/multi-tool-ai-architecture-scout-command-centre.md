---
module: GLOBAL
date: 2026-02-07
problem_type: best_practice
component: ai_tools
symptoms:
  - "Unclear when to use which AI tool"
  - "Scout/cron output goes unread"
  - "Morning briefing requires manual trigger"
root_cause: missing_context
resolution_type: process_change
severity: low
tags: [ai-tools, openclaw, claude-code, architecture, delegation, cron]
related_files:
  - ~/notes/AI Tool Architecture.md
  - ~/agent-config/openclaw/AGENTS.md
  - ~/CLAUDE.md
  - ~/skills/claude-code/SKILL.md
  - ~/skills/morning/SKILL.md
---

# Multi-Tool AI Architecture: Scout / Command Centre Pattern

## Problem

With 5 AI coding tools (Claude Code, OpenCode, Codex, Cursor Agent, OpenClaw), it's unclear how they relate. Without explicit roles, tools get used interchangeably when they have different strengths, and handoffs between tools are ad-hoc.

## Architecture

Each tool has a clear role:

- **Claude Code (Command Centre):** Deep context, vault access, orchestration, judgment. Expensive. Runs when user is at terminal.
- **OpenCode (Workhorse):** Free, unlimited. Bulk coding — file ops, refactoring, tests. No judgment, no vault.
- **Codex (Specialist):** Paid escalation for hard problems. Claude Code escalates here after OpenCode fails 2-3 times.
- **Cursor Agent (Workshop):** IDE-integrated, MCP support. Alternative to Codex for complex tasks.
- **OpenClaw (Scout):** Always-on, mobile-first. Runs cron jobs, handles notifications, quick lookups. Cheap models.

## Key Insight: Scout → Command Centre Handoff

OpenClaw (scout) produces intelligence via cron jobs but can't maintain a conversation. Claude Code (command centre) has deep reasoning but only exists when the user starts a session.

**The gap:** No interrupt path from scout to command centre. Scout flags things via Telegram; user bridges manually.

**Solution — escalation skill:** `/claude-code` skill with model routing lets OpenClaw fire one-shot tasks to Claude Code:
```
/claude-code haiku <quick task>     — file lookups, status checks
/claude-code sonnet <analysis>      — code review, research
/claude-code opus <deep task>       — architecture, complex debugging
```

**Solution — automated morning handoff:** Cron job at 6:50 (after 6:45 weather) delivers triage to Telegram: calendar, signals.log, TODOs. `/morning` skill in Claude Code also reads signals.log for deeper sessions.

## Lesson: Cron > Detection for Recurring Automation

Initial approach: detect "first message before 10am" and auto-run morning briefing. This requires time-checking logic baked into behavioural instructions.

Better approach: schedule a cron job. It's simpler, more reliable, and doesn't pollute the system prompt with detection rules. The cron runs regardless of when the user opens a session.

**Principle:** If something should happen at a predictable time, use a scheduler. Reserve behavioural instructions for things that depend on conversational context.

## Token Economics

Push work downward to the cheapest capable tool:
- OpenCode (free) for grunt work
- OpenClaw (cheap) for always-on scouting
- Sonnet/haiku subagents within Claude Code for lighter subtasks
- Claude Code opus for orchestration and judgment only
- Codex (paid) only when cheaper tools fail

## Prevention

- When adding a new AI tool, explicitly define its role relative to existing tools
- Document escalation paths (who delegates to whom, and when)
- Keep the architecture doc (`~/notes/AI Tool Architecture.md`) updated
- Review cron jobs monthly — dead crons waste scout cycles

## Related

- `~/notes/AI Tool Architecture.md` — full framing with diagrams
- delegation-reference skill — routing tables for Claude Code's delegates
- `~/.openclaw/cron/jobs.json` — OpenClaw cron configuration
