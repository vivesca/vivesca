---
name: mcp-sync
description: Sync MCP servers across Claude Code, Codex, and OpenCode from a standalone canonical config. Use when adding or updating MCP servers.
user_invocable: true
---

# MCP Sync

Syncs MCP server configurations across all three AI coding tools from a single source of truth.

## Architecture

```
~/agent-config/mcp-servers.json   ← Canonical source (clean, version-controlled)
        ↓ mcp-sync --apply
claude mcp add ...                ← Commands printed (run manually)
~/.codex/config.toml              ← Auto-updated (TOML)
~/.opencode/mcp.json              ← Auto-updated (JSON)
```

## Usage

```bash
mcp-sync           # Dry run - show what would change
mcp-sync --apply   # Update Codex/OpenCode, print Claude commands
```

## Files

- `SKILL.md` — This documentation
- `mcp-sync.py` — Sync script (symlinked to `~/scripts/mcp-sync.py`)

## Workflow

1. **Add/edit server in canonical:** `~/agent-config/mcp-servers.json`
2. **Run sync:** `mcp-sync --apply`
3. **For Claude Code:** Run the printed `claude mcp add` commands (if not already configured)

## Canonical Config Format

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package-name"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  },
  "_codexExtras": {
    "context7": { "url": "https://..." }
  }
}
```

## Notes

- Env vars use `${VAR}` syntax — actual values read from environment at runtime
- `_codexExtras` contains Codex-only servers (context7, serena)
- Claude Code commands are printed but not auto-executed (requires manual run)
- OpenCode strips env var values (reads from env at runtime)
