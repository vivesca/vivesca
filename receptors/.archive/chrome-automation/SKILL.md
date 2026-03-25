---
name: chrome-automation
description: Reference skill for Claude in Chrome browser automation best practices. Not user-invocable — use as internal guidance when automating Chrome.
user_invocable: false
platform: claude-code
platform_note: DORMANT — Chrome extension disabled (saves ~15-18K tokens/turn). Re-enable in chrome://extensions if needed. Prefer agent-browser CLI.
---

# Chrome Automation Best Practices

Reference for Claude in Chrome MCP tools. **Currently disabled** — using agent-browser CLI instead. Re-enable Chrome extension if you need interactive browser control on Terry's visible tabs.

## When to Re-enable

- Complex interactive tasks where Terry wants to watch and intervene
- Tasks that need real-time tab awareness (multiple tabs, switching)
- Debugging visual issues that need screenshot + click loops

## Session Startup

1. **Always create a new tab** at session start using `tabs_create_mcp`
2. Only use tabs you created in this session — never reuse tab IDs from previous sessions
3. If a tool returns "tab doesn't exist", call `tabs_context_mcp` to get fresh tab IDs

## Reading Page Content

- **`read_page` captures the full accessibility tree** including content below the viewport
- No scrolling needed to get below-fold content
- Workflow: navigate → wait 2 seconds → `read_page` once
- Use `max_chars` parameter if page is large (default 50000)

## Window Sizing

- **Resize window before `read_page`** to reduce tokens
- 800x600 for chat apps (WhatsApp, messaging)
- 1024x768 for general browsing

## Common Gotchas

| Issue | Solution |
|-------|----------|
| Tab ID invalid | Call `tabs_context_mcp` to refresh |
| LinkedIn "Saved" toggles | Clicking "Saved" unsaves — use three-dot menu |
| WhatsApp message direction | Left/white = incoming, right/green = outgoing |
| Gmail contenteditable | `form_input` unreliable on Gmail compose |

## Session Cleanup

Navigate to idle page after browser tasks:
```
https://terry-li-hm.github.io/claude-home/
```
