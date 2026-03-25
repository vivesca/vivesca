---
name: sessions
description: Check how many Claude Code sessions are running. Use when user says "sessions", "how many claudes", or wants to check for context fragmentation.
user_invocable: true
---

# Sessions Skill

Check active Claude Code sessions to monitor context fragmentation.

## Instructions

1. Run this command to find Claude Code CLI processes:
   ```bash
   pgrep -fl "claude" | grep -E "\.local/bin/claude" | grep -v grep
   ```

2. Count the number of main CLI processes (ignore support processes like `--claude-in-chrome-mcp`, `--chrome-native-host`)

3. Report:
   - **1 session**: "1 Claude session active. Context consolidated."
   - **2+ sessions**: List PIDs and remind: "Multiple sessions = context fragmentation. Is this a new plan, or execution you could delegate from one session?"

4. Optionally show tmux windows for context:
   ```bash
   tmux list-windows -a 2>/dev/null
   ```
