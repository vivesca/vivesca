---
name: manus
description: Reference for macOS UI automation via Peekaboo CLI. Not user-invocable — consult when automating app interactions, clicking UI elements, or taking screenshots programmatically.
user_invocable: true
disable-model-invocation: true
---

# Peekaboo CLI Reference

`peekaboo` — macOS UI automation. Binary at `/opt/homebrew/bin/peekaboo`.

## Permissions

Both must be granted or nothing works:
```bash
peekaboo permissions   # check status
```
- **Screen Recording** — required for `see`, `image`, `capture`
- **Accessibility** — required for `click`, `type`, `hotkey`, `list`

Grant in: System Settings → Privacy & Security → Screen Recording / Accessibility → add Terminal (or Claude Code process).

## Core Workflow

```
see → identify element IDs → click/type/hotkey
```

**Always `see` first.** Don't guess element IDs or coordinates.

```bash
peekaboo see --app Safari                        # screenshot + accessibility tree
peekaboo see --app Safari --json                 # machine-readable element list
peekaboo click "Submit" --app Safari             # click by text label
peekaboo click --on B3 --app Safari             # click by element ID from see output
peekaboo type "hello" --app Safari              # type into focused field
peekaboo hotkey "cmd,return" --app Safari       # keyboard shortcut
```

## Tools

| Tool | Purpose |
|------|---------|
| `see` | Screenshot + accessibility tree. Start here. |
| `click` | Click element by text, ID, or coordinates |
| `type` | Type text into focused element |
| `hotkey` | Press key combo (e.g. `"cmd,return"`, `"cmd,s"`) |
| `press` | Press single key (e.g. `return`, `escape`, `tab`) |
| `list` | List apps or windows (`list apps`, `list windows --app X`) |
| `image` | Screenshot to file (`--path /tmp/shot.png`) |
| `dialog` | Interact with standard macOS dialogs |
| `menu` | Click menu bar items |
| `window` | Resize/reposition windows |
| `app` | Launch/quit apps |
| `scroll` | Scroll in a direction |
| `hotkey` | Keyboard shortcuts |
| `space` | Switch/manage Spaces |

## Click Options

```bash
peekaboo click "Save" --app Due                         # by text (accessibility)
peekaboo click --on B3 --app Safari                    # by element ID from see
peekaboo click --coords "x,y" --app Safari             # by screen coordinates (logical px)
peekaboo click "OK" --app Finder --space-switch        # switch Space if window is on another Space
peekaboo click "OK" --app Finder --bring-to-current-space  # pull window to current Space
peekaboo click "OK" --app Finder --wait-for 8000       # wait up to 8s for element
```

## Hotkey Syntax

```bash
peekaboo hotkey "cmd,s"           # Cmd+S
peekaboo hotkey "cmd,return"      # Cmd+Return
peekaboo hotkey "cmd,shift,t"     # Cmd+Shift+T
peekaboo press return             # single key
peekaboo press escape
peekaboo press tab
```

## List Windows

```bash
peekaboo list windows --app Due
```

Output includes window title, ID, position, size. Use `--window-id <id>` or `--window-title <title>` to target specific windows in other commands.

**⚠️ Coordinate gotcha:** `list windows` position/size are in **physical (retina) pixels**. `click --coords` uses **logical pixels**. Do NOT use list windows coordinates directly for click — use `see` output element IDs instead.

## Screenshot

```bash
peekaboo image --app Safari --path /tmp/shot.png
peekaboo image --path /tmp/screen.png              # full screen
```

Then `Read /tmp/shot.png` to view it.

## Gotchas

- **App must be frontmost for `click "text"` to work reliably.** `osascript -e 'tell application "X" to activate'` first, then click.
- **`see` fails on protected/secure windows** (e.g. Due's Reminder Editor). Fall back to AppleScript or coordinate click.
- **AppleScript as fallback for dialog buttons** — when `peekaboo click "Save"` fails (custom controls), use:
  ```bash
  osascript -e 'tell application "System Events" to tell process "Due" to click button "Save" of window "Reminder Editor"'
  ```
  AppleScript ONLY works when the app is **visible on screen** (not in background, not on different Space). This is distinct from peekaboo's `--space-switch`.
- **`see` needs screen recording permission AND a capturable window.** Some windows (protected content, certain menu bar apps) will fail even with permission granted.
- **Permissions check:** `peekaboo permissions` — if either is `Denied`, nothing works. Grant in System Settings.
- **Don't use `peekaboo run` scripts** — requires Swift enum-coded JSON format (non-obvious schema, error-prone).

## Pattern: Click Button in Dialog

1. Activate app so it's visible on screen
2. Try `peekaboo click "ButtonName" --app AppName`
3. If not found → try `osascript` AppleScript fallback
4. If AppleScript fails → check `peekaboo list windows` to confirm window exists and is on current Space

```bash
osascript -e 'tell application "AppName" to activate' && sleep 0.3
peekaboo click "Save" --app AppName
# fallback:
osascript -e 'tell application "System Events" to tell process "AppName" to click button "Save" of window "Dialog Title"'
```

## Pattern: Read Screen State

```bash
peekaboo see --app Safari --json | python3 -c "
import sys, json
data = json.load(sys.stdin)
for el in data.get('elements', []):
    print(el)
"
```

## Pattern: Screenshot + Read

```bash
peekaboo image --app AppName --path /tmp/shot.png
# Then: Read /tmp/shot.png in Claude Code to visually inspect
```
