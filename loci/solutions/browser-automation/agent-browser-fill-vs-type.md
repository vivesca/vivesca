---
module: Browser Automation
date: 2026-01-15
problem_type: ui_bug
component: browser_automation
symptoms:
  - "Text appears in input field but submit button stays disabled"
  - "Form submission fails silently"
  - "React state doesn't update after typing"
root_cause: wrong_api
resolution_type: workaround
severity: high
tags: [agent-browser, react, input-events, fill, type]
---

# agent-browser fill vs type for React Inputs

## Problem

When using `agent-browser type` on React input fields, the text appears visually but React's internal state doesn't update. Submit buttons remain disabled because React doesn't detect the change.

## Symptoms

- Text shows in input field
- Send/submit button stays grayed out or disabled
- Form validation doesn't trigger
- No errors in console—just silent failure

## Root Cause

React uses synthetic events. The `type` command simulates individual keystrokes but doesn't trigger React's `onChange` handlers properly. React's controlled components need the full input event sequence.

## Solution

Use `fill` instead of `type`:

```bash
# BAD - React won't detect this
agent-browser type --text "my message" --ref "input[0]"

# GOOD - triggers proper React events
agent-browser fill --text "my message" --ref "input[0]"
```

## When This Applies

- Any React-based web app (most modern SPAs)
- Input fields in chat interfaces (WhatsApp Web, Slack, etc.)
- Form fields with real-time validation
- Any input where a button enables/disables based on content

## Prevention

Default to `fill` for all text input. Only use `type` when you specifically need character-by-character simulation (e.g., autocomplete testing).
