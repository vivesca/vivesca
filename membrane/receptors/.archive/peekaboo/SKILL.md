---
name: peekaboo
description: macOS UI capture and automation via Peekaboo CLI — screenshots, clicks, inspection.
user_invocable: false
github_url: https://github.com/steipete/peekaboo
github_hash: 69376fa
---

# Peekaboo

macOS UI automation CLI: capture/inspect screens, target UI elements, drive input, and manage apps/windows/menus.

## Prerequisites

- macOS only
- `peekaboo` CLI installed: `brew install steipete/tap/peekaboo`
- Screen Recording + Accessibility permissions granted to terminal app (Ghostty/Terminal)

## Core Commands

### Screenshots

```bash
# Capture full screen
peekaboo image --mode screen --path /tmp/screen.png

# Capture frontmost window
peekaboo image --mode frontmost --path /tmp/window.png

# Capture specific app window
peekaboo image --app Safari --path /tmp/safari.png

# Capture specific window by title
peekaboo image --window-title "Login" --path /tmp/login.png
```

### Vision (UI Element Analysis)

```bash
# Analyze UI elements in frontmost window (returns element IDs for clicking)
peekaboo see --json

# Analyze specific app with annotated screenshot
peekaboo see --app Safari --annotate --path /tmp/annotated.png

# Analyze with AI description
peekaboo see --analyze "Describe what's on screen"
```

### List Apps/Windows

```bash
peekaboo list apps
peekaboo list windows --app Safari
peekaboo list screens
peekaboo list menubar
peekaboo permissions
```

### Interaction

```bash
# Click by element ID (from `see` command)
peekaboo click --on B1
peekaboo click --id T2

# Click by query text
peekaboo click "Submit Button"

# Click by coordinates
peekaboo click --coords 100,200

# Double/right click
peekaboo click --on B1 --double
peekaboo click --coords 100,200 --right

# Keyboard typing
peekaboo type "Hello world"
peekaboo type "user@example.com" --return    # Type and press enter
peekaboo type "password" --clear             # Clear field first

# Hotkeys
peekaboo hotkey "cmd,c"           # Copy
peekaboo hotkey "cmd,shift,t"     # Reopen tab
peekaboo hotkey "cmd space"       # Spotlight

# Individual keys
peekaboo press enter
peekaboo press escape
peekaboo press tab

# Mouse
peekaboo move --coords 100,200
peekaboo scroll down
peekaboo drag --from 100,100 --to 200,200
```

### App Control

```bash
peekaboo app launch Safari
peekaboo app quit Safari
peekaboo app hide Safari
peekaboo app unhide Safari
```

### Clipboard

```bash
peekaboo clipboard read
peekaboo clipboard write "text to copy"
peekaboo paste "text"    # Sets clipboard, pastes, restores
```

## JSON Output

Add `--json` or `-j` for machine-readable output.

## Workflow: Click by Vision

1. `peekaboo see --json` → get element IDs (B1, T2, etc.)
2. `peekaboo click --on B1` → click the element

## Integration

Complements browser automation tools. Use peekaboo for native macOS apps, Claude in Chrome for web pages.
