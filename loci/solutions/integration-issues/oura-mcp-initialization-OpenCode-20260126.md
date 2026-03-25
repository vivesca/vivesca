---
module: OpenCode
date: 2026-01-26
problem_type: integration_issue
component: tooling
symptoms:
  - "Oura MCP client not initialized"
  - "Oura tools failing in OpenCode but working in Claude Code"
root_cause: config_error
resolution_type: environment_setup
severity: medium
tags: [mcp, oura, opencode, environment-variables]
---

# Oura MCP initialization failure in OpenCode

## Symptom
When attempting to use Oura tools in OpenCode, the following error is returned:
`"error": "Oura client not initialized. Please provide an access token."`

This occurred even though the Oura MCP was configured and working in Claude Code.

## Investigation
1. **Tool inspection**: The `oura-mcp-server` (run via `uvx`) requires `OURA_PERSONAL_ACCESS_TOKEN` to be set in the environment.
2. **Configuration comparison**: Checked `~/.claude/settings.json` (Claude Code) and `~/.config/opencode/opencode.json` (OpenCode).
3. **Root cause identified**: OpenCode's MCP configuration for `oura` had an empty `environment` block. Unlike some environments that might inherit shell variables, OpenCode's local MCP processes need explicit environment mapping if not globally exported in the session.

## Solution
Update the OpenCode configuration files to explicitly pass the required tokens to the MCP server process.

1. Locate the token in `~/oura-data/.env`.
2. Edit `/Users/terry/.config/opencode/opencode.json` and `/Users/terry/.config/opencode/opencode.json.local`.
3. Add the tokens to the `environment` block:

```json
"oura": {
  "type": "local",
  "command": [
    "uvx",
    "oura-mcp-server"
  ],
  "environment": {
    "OURA_PERSONAL_ACCESS_TOKEN": "YOUR_TOKEN_HERE",
    "OURA_TOKEN": "YOUR_TOKEN_HERE"
  },
  "enabled": true
}
```

## Prevention
- **Explicit configuration**: When adding new MCP servers to OpenCode, always check if they require specific environment variables and add them to the `environment` key in `opencode.json`.
- **Process reload**: Remember that MCP servers are long-running processes; **OpenCode must be restarted** to pick up configuration changes in `opencode.json`.

## Related Issues
- None found.
