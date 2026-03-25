---
module: Browser Automation
date: 2026-01-20
problem_type: runtime_error
component: browser_automation
symptoms:
  - "Click targets wrong element"
  - "Element not found after previous action"
  - "Unexpected page state after interaction"
root_cause: async_timing
resolution_type: process_change
severity: high
tags: [agent-browser, refs, snapshot, stale-refs]
---

# agent-browser refs shift after actions

## Problem

After any `agent-browser` action (click, fill, scroll), the element refs in the snapshot become stale. Using old refs targets wrong elements or fails entirely.

## Symptoms

- Clicking `button[3]` hits a different button than expected
- "Element not found" errors
- Actions succeed but on wrong elements
- Page state doesn't match expectations

## Root Cause

DOM mutations. Modern web apps constantly update the DOM—adding, removing, and reordering elements. Each action can trigger React re-renders, lazy loading, or dynamic updates that invalidate the ref index.

## Solution

**Always re-snapshot before each action:**

```bash
# Take snapshot
agent-browser snapshot

# Do action
agent-browser click --ref "button[2]"

# MUST re-snapshot before next action
agent-browser snapshot

# Now safe to use new refs
agent-browser fill --ref "input[0]" --text "hello"
```

## Anti-Pattern

```bash
# BAD - refs from first snapshot are stale
agent-browser snapshot
agent-browser click --ref "button[2]"
agent-browser click --ref "link[5]"  # WRONG - using stale refs
```

## Prevention

Treat every action as invalidating the current snapshot. Build the habit: action → snapshot → action → snapshot.
