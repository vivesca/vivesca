#!/bin/bash
# Toggle Claude-in-Chrome MCP on/off in Claude Code settings.
# Usage: toggle-chrome-mcp.sh [on|off|status]
#
# When off, saves ~6-8K tokens/session from tool definitions + safety rules.

SETTINGS="$HOME/agent-config/claude/settings.json"

current=$(python3 -c "
import json
with open('$SETTINGS') as f:
    d = json.load(f)
print(d.get('claudeInChromeDefaultEnabled', True))
")

case "${1:-status}" in
  on)
    python3 -c "
import json
with open('$SETTINGS') as f:
    d = json.load(f)
d['claudeInChromeDefaultEnabled'] = True
with open('$SETTINGS', 'w') as f:
    json.dump(d, f, indent=2)
"
    echo "Chrome MCP: ON (restart claude to take effect)"
    ;;
  off)
    python3 -c "
import json
with open('$SETTINGS') as f:
    d = json.load(f)
d['claudeInChromeDefaultEnabled'] = False
with open('$SETTINGS', 'w') as f:
    json.dump(d, f, indent=2)
"
    echo "Chrome MCP: OFF (restart claude to take effect)"
    ;;
  status)
    echo "Chrome MCP: $([ "$current" = "True" ] && echo ON || echo OFF)"
    ;;
  *)
    echo "Usage: toggle-chrome-mcp.sh [on|off|status]"
    exit 1
    ;;
esac
