---
module: Claude Configuration
date: 2026-02-04
problem_type: best_practice
component: skill
symptoms:
  - "Confusion about when to use skills vs agents"
  - "Agent type not found errors"
  - "Understanding how commands route to implementations"
root_cause: missing_context
resolution_type: workflow_improvement
severity: low
tags: [compound-engineering, plugin-architecture, skills, agents, commands]
---

# Compound Engineering Plugin Architecture

## Overview

The compound-engineering plugin has three component types that serve different purposes:

| Component | Location | Invoked By | Purpose |
|-----------|----------|------------|---------|
| **Commands** | `commands/*.md` | User (`/command`) | Entry points, orchestration |
| **Agents** | `agents/category/*.md` | Task tool | Parallel work, specialized personas |
| **Skills** | `skills/name/SKILL.md` | Skill tool | Context loading, reference material |

## How They Interact

```
User invokes /workflows:plan
    ↓
Command (commands/workflows/plan.md) loaded
    ↓
Command instructs Claude to spawn agents:
    Task learnings-researcher("search for relevant patterns")
    Task repo-research-analyst("analyze codebase")
    ↓
Agents run in parallel, return results
    ↓
Command may load skills for reference:
    Skill brainstorming (for techniques)
    ↓
Command orchestrates final output
```

## Component Details

### Commands (`/command-name`)

- **Location**: `commands/*.md` or `commands/category/*.md`
- **Purpose**: User-facing entry points that orchestrate workflows
- **Pattern**: Describe what Claude should do, may spawn agents
- **Example**: `/workflows:plan`, `/workflows:compound`, `/lfg`

Commands often contain `Task agent-name(args)` syntax telling Claude to spawn agents.

### Agents (Task tool)

- **Location**: `agents/category/agent-name.md`
- **Purpose**: Specialized personas for parallel work
- **Pattern**: YAML frontmatter (name, description, model) + persona instructions
- **Naming**: `compound-engineering:category:agent-name`
- **Example**: `learnings-researcher`, `code-simplicity-reviewer`

Agents are spawned via Task tool:
```
Task: subagent_type="compound-engineering:research:learnings-researcher"
      prompt="Search for browser automation patterns"
```

### Skills (Skill tool)

- **Location**: `skills/skill-name/SKILL.md`
- **Purpose**: Reference material loaded into context
- **Pattern**: YAML frontmatter + detailed instructions/templates
- **Example**: `compound-docs`, `brainstorming`, `git-worktree`

Skills are loaded via Skill tool — they don't run as separate agents.

## Common Gotcha

**Bug pattern**: Command describes spawning agent, but only skill exists.

Example: `/workflows:compound` says "Routes To: `compound-docs` skill" but also describes "parallel subagents". Claude constructs `compound-engineering:workflow:compound-docs` expecting an agent file at `agents/workflow/compound-docs.md`, but only `skills/compound-docs/` exists.

**Fix**: Every agent mentioned in commands needs a corresponding `agents/category/name.md` file.

## Verification Pattern

Before contributing or debugging:

1. Check if component exists:
   - Agent: `ls agents/category/`
   - Skill: `ls skills/`
   - Command: `ls commands/`

2. Verify upstream has same structure:
   ```bash
   gh api repos/EveryInc/compound-engineering-plugin/contents/plugins/compound-engineering/agents/category --jq '.[].name'
   ```

3. Check existing issues:
   ```bash
   gh issue list --repo EveryInc/compound-engineering-plugin --search "agent not found"
   ```

## Related

- PR #149: Added missing compound-docs agent
- Issue #138: Original bug report for compound-docs
- `workflows-compound-missing-agents.md`: Specific bug documentation
