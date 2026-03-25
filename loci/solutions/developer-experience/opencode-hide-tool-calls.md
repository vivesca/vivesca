---
title: Hiding Tool Call Details in OpenCode CLI
status: resolved
category: developer-experience
tags: [opencode, cli, ui, configuration]
date: 2026-01-27
---

# Hiding Tool Call Details in OpenCode CLI

## Problem Statement
The OpenCode CLI (powered by gemini-3-flash or other models) displays `tool_call` lines by default (e.g., `tool_call: read '...'`). Users may find this output distracting or cluttered and wish to hide it for a cleaner interface.

## Symptoms
- Visible lines starting with `tool_call:` in the terminal output.
- Inability to find a static configuration key in `opencode.json` to disable this globally.

## Root Cause Analysis
OpenCode (v1.1.36) manages UI state primarily through its interactive TUI and runtime slash commands. While `opencode.json` supports tool permissions and model settings, UI display preferences like tool detail visibility are not currently supported as static configuration keys. Attempting to add keys like `toolDetails` or `tool_details_visibility` to the JSON config results in a startup error: `Unrecognized keys: "toolDetails"`.

## Working Solution
UI visibility must be toggled interactively during the session.

### Option 1: Slash Command
Use the built-in slash command to toggle tool details:
```bash
/details
```
This will hide the `tool_call` and `thinking` blocks from the output.

### Option 2: Keyboard Shortcut
In the OpenCode TUI, use the following shortcut to toggle visibility:
- **`Ctrl+X H`** (Toggles code/tool detail blocks)

## Prevention & Best Practices
- **Check Command Help**: Use `opencode --help` or `/help` to see available runtime controls.
- **Config Validation**: If `opencode` fails to start after editing `opencode.json`, revert the change. The CLI is strict about its schema.
- **TUI Controls**: Monitor the bottom status bar in the OpenCode TUI for interactive toggles.

## Related Documentation
- [[OpenCode Config Guide]] (External)
- [[CLI Aesthetics and Productivity]]

## Work Log
### 2026-01-27 - Problem Solved
- Investigated binary strings for configuration keys.
- Found `/details` command and `tool_details_visibility` internal keys.
- Verified that static JSON config does not accept these keys.
- Confirmed `/details` as the primary solution.
