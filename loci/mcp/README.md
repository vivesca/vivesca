# MCP Server Configuration

Model Context Protocol (MCP) servers used across Claude Code and OpenCode.

## Servers

| Server | Type | Description |
|--------|------|-------------|
| **gmail** | stdio | Gmail integration |
| **brave-search** | stdio | Web search via Brave |
| **tavily** | stdio | Web search/scrape |
| **oura** | stdio | Oura Ring data |
| **browser-tabs** | stdio | Chrome tab management |
| **perplexity** | stdio | AI search |
| **exa** | stdio | Code search |
| **serper** | stdio | Search/scrape |
| **context7** | remote | Framework documentation |

## Installation

### OpenCode
Already configured in `../opencode/opencode.json`.

### Claude Code
Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "/Users/terry/mcp-gmail/.venv/bin/python",
      "args": ["-m", "mcp_gmail.server"],
      "env": {
        "MCP_GMAIL_CREDENTIALS_PATH": "/Users/terry/code/epigenome/chromatin/scripts/credentials.json",
        "MCP_GMAIL_TOKEN_PATH": "/Users/terry/code/epigenome/chromatin/scripts/token.json"
      }
    }
  }
}
```
