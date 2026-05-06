@genome.md

## Codex Tool Mapping

When running as Codex (OpenAI Codex CLI), map CC tool references to Codex equivalents. Read becomes shell reads (`cat`/`sed`) or `rg`. Write becomes shell redirection or `apply_patch`. Edit and MultiEdit become `apply_patch`. Bash becomes `shell_command`. Grep becomes `rg`, falling back to `grep`. Glob becomes `rg --files` or `find`. WebFetch and WebSearch become `curl` or Context7. AskUserQuestion becomes a numbered list in chat, with the agent waiting for a reply. Task and Subagent run sequentially in the main thread, with `multi_tool_use.parallel` available for tool calls. Skill means open the referenced `SKILL.md` and follow it.
