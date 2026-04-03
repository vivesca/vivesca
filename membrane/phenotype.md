# Vivesca

A living system built on cell biology as a design constraint.

All constitutional rules live in `~/germline/genome.md`. Follow them.

The naming convention is cell biology. Every component has a biological identity.
Biology is the engineering manual — before building any mechanism, `lysin "<term>"` to check what cells actually do. Follow the biology.
See `anatomy.md` for the structural map.

## Memory

Memory index: `~/epigenome/marks/MEMORY.md` (also `~/.claude/projects/-Users-terry/memory/MEMORY.md`). Read at session start. Each line links to a detailed mark file — read relevant ones when the task matches.

Mark frontmatter: `name`, `description`, `type` (user/feedback/project/reference/finding), `source` (cc/gemini/codex/goose/user), `durability` (methyl=durable, acetyl=volatile), `protected: true` for core corrections.

## GLM Coaching

Append recurring GLM failure patterns to `~/epigenome/marks/feedback_golem_coaching.md`. Prepended to every golem dispatch. Format: pattern name, what GLM does wrong, fix instruction.

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
