# Harness Configuration

How vivesca serves all 5 AI coding CLI tools from one repo.

## Architecture

Three layers, one source of truth each:

| Layer | Source | Path |
|-------|--------|------|
| Instructions | `genome.md` | `~/germline/genome.md` |
| Skills | `receptors/` | `~/germline/membrane/receptors/` |
| MCP | vivesca | `http://127.0.0.1:8741/mcp` |

## Per-tool config

### Claude Code
- Instructions: `~/.claude/CLAUDE.md` -> `~/germline/genome.md` (symlink)
- Skills: `~/.claude/skills` -> `~/germline/membrane/receptors` (symlink)
- MCP: Cloud-configured via Anthropic account (`user:mcp_servers` scope)
- Hooks: `synapse.py` (UserPromptSubmit), `axon.py` (PreToolUse), `dendrite.py` (PostToolUse)

### Codex (OpenAI)
- Instructions: `~/.codex/AGENTS.md` -> `~/germline/genome.md` (symlink)
- Skills: `~/.codex/skills` -> `~/germline/membrane/receptors` (symlink)
- MCP: `~/.codex/config.toml`
  ```toml
  [mcp_servers.vivesca]
  url = "http://127.0.0.1:8741/mcp"
  ```

### Gemini CLI
- Instructions: `~/.gemini/GEMINI.md` -> `~/germline/genome.md` (symlink)
- Skills: `~/.gemini/skills` -> `~/germline/membrane/receptors` (symlink)
- MCP: `~/.gemini/settings.json`
  ```json
  {"mcpServers": {"vivesca": {"url": "http://127.0.0.1:8741/mcp"}}}
  ```

### Goose
- Instructions: `~/.agents/AGENTS.md` -> `~/germline/genome.md` (symlink)
- Skills: `~/.agents/skills` -> `~/germline/membrane/receptors` (symlink)
- MCP: `~/.config/goose/config.yaml`
  ```yaml
  extensions:
    vivesca:
      type: sse
      uri: http://127.0.0.1:8741/mcp
  ```

### Droid (Factory)
- Instructions: `~/.factory/AGENTS.md` -> `~/germline/genome.md` (symlink)
- Skills: `~/.factory/skills` -> `~/germline/membrane/receptors` (symlink)
- MCP: `~/.factory/settings.json`
  ```json
  {"mcpServers": {"vivesca": {"url": "http://127.0.0.1:8741/mcp"}}}
  ```

## Setup on a new machine

```bash
# 1. Clone vivesca
git clone <vivesca-repo> ~/germline

# 2. Symlink instructions
ln -sf ~/germline/genome.md ~/.claude/CLAUDE.md
ln -sf ~/germline/genome.md ~/.codex/AGENTS.md
ln -sf ~/germline/genome.md ~/.gemini/GEMINI.md
mkdir -p ~/.agents && ln -sf ~/germline/genome.md ~/.agents/AGENTS.md
mkdir -p ~/.factory && ln -sf ~/germline/genome.md ~/.factory/AGENTS.md

# 3. Symlink skills
ln -sf ~/germline/membrane/receptors ~/.claude/skills
ln -sf ~/germline/membrane/receptors ~/.codex/skills
ln -sf ~/germline/membrane/receptors ~/.gemini/skills
ln -sf ~/germline/membrane/receptors ~/.agents/skills
ln -sf ~/germline/membrane/receptors ~/.factory/skills

# 4. Start vivesca MCP server
vivesca serve --http

# 5. MCP config (copy from sections above, per tool)
```

## What each tool gets uniquely

- **CC only:** Hooks (budget enforcement, skill routing, safety guardrails). CC is the architect.
- **All tools:** Same genome rules, same skills, same MCP tools.
- **Goose/Droid:** Also get coaching file prepended at dispatch time via sortase.

## Adding a new skill

Create `~/germline/membrane/receptors/<name>/SKILL.md`. All 5 tools see it immediately.

## Adding a new tool

1. Symlink instructions and skills (two `ln -sf` commands)
2. Add MCP config in the tool's native format
3. Add a section to this file
