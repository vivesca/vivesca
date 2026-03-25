---
category: integration-issues
module: MCP / Search Tools
symptoms:
  - "McpError: MCP error -32603: Invalid API key"
  - "Unauthorized: missing or invalid API key"
tags:
  - tavily
  - mcp
  - configuration
  - api-keys
---

# Tavily MCP Invalid API Key Resolution

## Problem Symptom
When calling `tavily_tavily_search`, the tool returned:
`McpError: MCP error -32603: Invalid API key`

Direct `curl` tests against the Tavily API with the key found in `opencode.json` returned:
`{"detail":{"error":"Unauthorized: missing or invalid API key."}}`

## Investigation Steps
1.  **Checked `.zshrc`**: Found `TAVILY_API_KEY=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`.
2.  **Checked `opencode.json`**: Found a different key `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`.
3.  **Verified via `curl`**: Confirmed the `tvly-dev-...` key from `.zshrc` was valid, while the `tvly-7Fb...` key was invalid.
4.  **Inspected MCP registration**: `claude mcp get tavily` showed the server was connected but might have been using the old key cached in the process or local config.

## Root Cause
The Tavily MCP server was configured with an outdated/invalid API key in `~/.claude.json` and `~/.config/opencode/opencode.json`, which overrode the valid key exported in the shell environment.

## Working Solution
1.  **Update Config Files**:
    *   Replaced the old key with the valid `tvly-dev-...` key in:
        *   `~/.config/opencode/opencode.json`
        *   `~/.claude/settings.json` (added explicit `mcpServers` block)
2.  **Re-register MCP Server**:
    Use the `claude` CLI to ensure the key is explicitly passed to the server environment:
    ```bash
    claude mcp remove tavily
    claude mcp add tavily --env TAVILY_API_KEY=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 -- npx -y tavily-mcp@latest
    ```
3.  **Restart Session**:
    After updating the JSON configs and re-adding the server, the session may need to be restarted (`/clear` or exit/re-enter) for the tool list to refresh correctly.

## Prevention Strategies
- **Single Source of Truth**: Prefer managing API keys in `.zshrc` or a central `.env` and use `claude mcp add --env KEY=$KEY` to "pin" them to the MCP configuration.
- **Verify First**: Before troubleshooting the MCP layer, always use `curl` to verify the API key directly:
  ```bash
  curl -X POST https://api.tavily.com/search -H "Content-Type: application/json" -d "{\"api_key\": \"$TAVILY_API_KEY\", \"query\": \"test\"}"
  ```

## Cross-references
- `~/skills/web-search/SKILL.md` - Guide for selecting search tools.
- `~/.claude.json` - Local project MCP configuration.
