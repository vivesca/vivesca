---
module: Claude Configuration
date: 2026-02-04
problem_type: runtime_error
component: skill
symptoms:
  - "Agent type 'haiku' not found when running /workflows:compound"
  - "Task tool fails with list of available agents"
  - "Parallel subagent strategy in skill doesn't execute"
root_cause: missing_tooling
resolution_type: workaround
severity: low
tags: [compound-engineering, workflows-compound, missing-agents, plugin-bug]
---

# /workflows:compound Missing Parallel Agent Types

## Problem

Running `/workflows:compound` fails when Claude tries to spawn parallel subagents. The skill describes launching specialized agents (Context Analyzer, Solution Extractor, etc.) but these agent types don't exist in the plugin.

## Error

```
Agent type 'haiku' not found. Available agents: Bash, general-purpose,
compound-engineering:research:learnings-researcher, ...
```

## Root Cause

The `/workflows:compound` command (line 26-71) describes an "Execution Strategy: Parallel Subagents" with:
- Context Analyzer
- Solution Extractor
- Related Docs Finder
- Prevention Strategist
- Category Classifier
- Documentation Writer

However, these are **conceptual descriptions** of what Claude should do, not actual agent persona files. When Claude interprets this literally and tries to spawn Task agents, it fails because:

1. No agent persona files exist for these "subagents"
2. "haiku" is a model parameter, not an agent type
3. The `compound-docs` skill (which it routes to) is designed for direct execution, not orchestration

## Workaround

Execute the documentation logic directly instead of spawning subagents:

1. Read conversation context
2. Extract problem/solution details
3. Generate YAML frontmatter
4. Write to `docs/solutions/[category]/[filename].md`
5. Commit

The skill works fine when Claude doesn't try to parallelize.

## Fix Options

**For plugin maintainers:**
1. Remove the "Parallel Subagents" section from the command
2. Or create actual agent persona files in `agents/workflow/` for each subagent
3. Or clarify that "subagents" means "mental steps" not "Task tool invocations"

**For users:**
Use the workaround above, or manually invoke the `compound-docs` skill logic.

## Related

- compound-engineering plugin v2.28.0
- `/workflows:compound` command at `commands/workflows/compound.md`
- `compound-docs` skill at `skills/compound-docs/SKILL.md`
