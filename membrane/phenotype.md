# Vivesca

A living system built on cell biology as a design constraint.

All constitutional rules live in `~/germline/genome.md`. Follow them.

The naming convention is cell biology. Every component has a biological identity.
Biology is the engineering manual — before building any mechanism, `lysin "<term>"` to check what cells actually do. Follow the biology.
See `anatomy.md` for the structural map.

## Memory

At the start of each session, read the memory index for project context and behavioral guidance:

```
~/epigenome/marks/MEMORY.md
```

(Also accessible at `~/.claude/projects/-Users-terry/memory/MEMORY.md` — same files via symlink.)

This is the memory index — an always-loaded context of gotchas, user facts, and behavioral corrections. It contains:
- Recurring error patterns to avoid (date/time, post-cutoff facts, product specs)
- Directory layout and path conventions
- Shell and tool gotchas
- User facts (schedule, health, preferences)
- Behavioral corrections (hard-earned — follow them)

Each line in MEMORY.md links to a detailed memory file. Read relevant ones when the task matches their description.

### Mark frontmatter (enhanced histone code)

When saving memory files, use this frontmatter:

```yaml
---
name: {{name}}
description: {{one-line description}}
type: {{user, feedback, project, reference, finding}}
source: {{cc, gemini, codex, goose, user}}  # imprinting: who wrote this mark
durability: {{methyl, acetyl}}               # methyl=durable (default), acetyl=volatile (checkpoints, resolved)
protected: {{true}}                          # CpG island — omit if not protected
---
```

`source` and `durability` are optional — defaults are `unknown` and `methyl`. Set `protected: true` only for core behavioral corrections that must never be erased.

## GLM Coaching

When reviewing Goose/GLM-5.1 output (diffs, sortase results, code), watch for recurring failure patterns and append them to the coaching note:

```
~/epigenome/marks/feedback_golem_coaching.md
```

This file is deterministically prepended to every `sortase exec -b goose` dispatch. Your additions directly improve future Goose output. Format each entry as: pattern name → what GLM does wrong → the fix instruction. Set `source: gemini` in the frontmatter when you update it.

<!-- BEGIN COMPOUND CODEX TOOL MAP -->
## Compound Codex Tool Mapping (Claude Compatibility)

This section maps Claude Code plugin tool references to Codex behavior.
Only this block is managed automatically.

Tool mapping:
- Read: use shell reads (cat/sed) or rg
- Write: create files via shell redirection or apply_patch
- Edit/MultiEdit: use apply_patch
- Bash: use shell_command
- Grep: use rg (fallback: grep)
- Glob: use rg --files or find
- LS: use ls via shell_command
- WebFetch/WebSearch: use curl or Context7 for library docs
- AskUserQuestion/Question: present choices as a numbered list in chat and wait for a reply number. For multi-select (multiSelect: true), accept comma-separated numbers. Never skip or auto-configure — always wait for the user's response before proceeding.
- Task/Subagent/Parallel: run sequentially in main thread; use multi_tool_use.parallel for tool calls
- TodoWrite/TodoRead: use file-based todos in todos/ with todo-create skill
- Skill: open the referenced SKILL.md and follow it
- ExitPlanMode: ignore
<!-- END COMPOUND CODEX TOOL MAP -->
