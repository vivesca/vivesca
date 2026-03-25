# Blink Shell Setup

## One-tap Mac SSH + tmux

**Settings → Keyboard → Custom Presses**

- Text: `ssh mac -t "tmux new-session -A -s main"` + a real newline (press Return in the field)
- Assign to any key combo

This connects to the mac host and attaches (or creates) the main tmux session in one keystroke.

## Gotchas

- Aliases don't work in Blink's local shell — use Custom Presses instead.
- `\n` in the text field is sent literally. Must press Return to insert a real newline.
- Use the full command (`tmux new-session -A -s main`) not a shell alias — aliases aren't available in non-interactive SSH sessions.
- For Blink config questions, always search online — its shell is non-standard.

## Optimal Settings for Claude Code + tmux (iPhone 17 Pro Max)

Researched Mar 2026. Starting points, not gospel — verify with `tput cols`.

### Font

| Mode | Size | Font |
|---|---|---|
| Portrait | 13 pt | JetBrains Mono |
| Landscape | 12 pt | JetBrains Mono |

Target: **100+ cols in landscape** so Claude Code diff/tool-use output doesn't truncate. Run `tput cols` after setting font — if under 120 cols at 12pt landscape, drop to 11pt.

**How 13pt was determined:** one GitHub issue data point (blinksh/blink #282) + community anecdote. Not a measured optimum. Adjust to taste.

### Keyboard (critical)

- **Settings > Keyboard > Option key: As modifier → ESC** — without this, Meta/readline navigation in Claude Code breaks
- **Caps Lock → Ctrl** (Settings > Keyboard > Modifiers) — reduces strain from constant `Ctrl-b` tmux prefix

### Blink Appearance

- **Cursor Blink: Off** — easier to track in Claude Code approval dialogs
- **Screen fit: Fill** (three-finger tap) — max column count in landscape
- **Bell: Off**

### tmux.conf essentials

```
set -g mouse on                          # touch scroll in panes
set -g history-limit 50000
set -g default-terminal "xterm-256color"
set-option -ga terminal-overrides ",xterm-256color:Tc"
set-option -g bell-action none           # suppress iOS haptic on Claude Code task-complete bell
bind -n PageUp copy-mode -eu
```

### tmux Pane Layout

Don't 50/50 split in landscape — leaves ~63 cols each and Claude Code truncates. Instead:
- Claude Code pane: 90 cols (`tmux resize-pane -x 90`)
- Monitoring pane: remaining ~35 cols

### Host Entry

- Startup command: `tmux new -A -s mobile` — auto-attaches persistent session
- **Use Mosh, not SSH** — reconnects on network change; requires `mosh-server` on host

### Theme

Catppuccin Mocha — consistent with Ghostty, good contrast for Claude Code's dim ANSI metadata lines. Avoid light themes.

### Alternative: Moshi

getmoshi.app — newer iPhone terminal built for AI agent workflows, adds push notifications when Claude Code needs approval. Less mature than Blink but worth watching.
