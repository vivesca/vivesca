---
name: gog-keyring-headless
description: gog CLI needs GOG_KEYRING_PASSWORD env var for headless (no TTY) operation
type: solution
---

## Problem

`gog gmail send` (and other write commands) fail with:
```
no TTY available for keyring file backend password prompt; set GOG_KEYRING_PASSWORD
```

## Fix

Set `GOG_KEYRING_PASSWORD` in the environment:
- Shell: `~/.zshenv.local`
- MCP server: `com.vivesca.mcp.plist` EnvironmentVariables dict

Value is the keyring file encryption password (not an API key).
