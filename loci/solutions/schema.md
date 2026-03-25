# YAML Frontmatter Schema

Adapted from Every's compound-engineering schema for Terry's workflow.

## Required Fields

- **module** (string): Module/area name or "GLOBAL" for cross-cutting issues
- **date** (string): ISO 8601 date (YYYY-MM-DD)
- **problem_type** (enum): Category of issue
- **component** (enum): Technical component affected
- **symptoms** (array): 1-5 specific observable symptoms
- **root_cause** (enum): What caused the issue
- **resolution_type** (enum): How it was resolved
- **severity** (enum): One of [critical, high, medium, low]

## Optional Fields

- **tags** (array): Searchable keywords (lowercase, hyphen-separated)
- **related_files** (array): Paths to related config/scripts

## Enum Values

### problem_type

- `runtime_error` — Tool crashes, unexpected failures
- `config_error` — Wrong settings, missing config
- `integration_issue` — Tool interop problems
- `performance_issue` — Slow, resource-heavy
- `ui_bug` — Browser automation issues
- `logic_error` — Wrong assumptions, bad mental models
- `workflow_issue` — Process/sequence problems
- `best_practice` — Patterns worth documenting
- `security_issue` — Data exposure, permission issues

### component

- `claude_code` — Claude Code CLI, settings, hooks
- `browser_automation` — Playwright, agent-browser, Claude in Chrome
- `mcp_server` — MCP tools and servers
- `skill` — Skill definitions and routing
- `cli_tool` — wacli, gog, bird, gh, etc.
- `vault` — Obsidian vault, notes
- `delegation` — OpenCode, Codex delegation
- `search` — Grep, Glob, file discovery
- `api` — External API quirks

### root_cause

- `wrong_api` — Used tool incorrectly
- `config_error` — Missing or wrong configuration
- `async_timing` — Race condition, stale state
- `permission_issue` — Access denied, sandbox
- `tool_limitation` — Tool can't do what was expected
- `missing_context` — Didn't check existing info first
- `mental_model_error` — Wrong assumption about how something works

### resolution_type

- `workaround` — Work around the limitation
- `config_change` — Fix settings
- `tool_switch` — Use different tool
- `process_change` — Change workflow/sequence
- `hard_rule` — Add to CLAUDE.md hard rules

## Category Mapping

Based on `problem_type`, documentation is filed in:

- `runtime_error` → `docs/solutions/ai-tooling/`
- `config_error` → `docs/solutions/claude-config/`
- `integration_issue` → `docs/solutions/ai-tooling/`
- `performance_issue` → `docs/solutions/ai-tooling/`
- `ui_bug` → `docs/solutions/browser-automation/`
- `logic_error` → `docs/solutions/workflow-issues/`
- `workflow_issue` → `docs/solutions/workflow-issues/`
- `best_practice` → `docs/solutions/best-practices/`
- `security_issue` → `docs/solutions/ai-tooling/`
- `skill` issues → `docs/solutions/skills/`

## Example

```yaml
---
module: Browser Automation
date: 2026-01-15
problem_type: ui_bug
component: browser_automation
symptoms:
  - "React input shows text but button stays disabled"
  - "Form submission fails silently"
root_cause: wrong_api
resolution_type: workaround
severity: high
tags: [agent-browser, react, input-events]
---
```
