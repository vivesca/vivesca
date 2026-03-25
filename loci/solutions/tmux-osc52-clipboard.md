# tmux OSC 52 Clipboard — Blink SSH

Copy tmux pane content to iOS clipboard from Blink Shell via SSH.

## What Works

Write OSC 52 directly to the pane's TTY device. tmux reads it as pane output and (with `allow-passthrough on`) forwards it to Blink, which updates iOS clipboard.

**Script: `~/scripts/tmux-osc52.sh`**
```bash
#!/bin/bash
PANE="$1"
TTY="$2"
DATA=$(tmux capture-pane -p -t "$PANE" | base64 | tr -d '\n')
printf '\033]52;c;%s\007' "$DATA" > "$TTY"
```

**tmux binding (`~/.tmux.conf`):**
```
bind-key y run-shell "bash ~/scripts/tmux-osc52.sh #{pane_id} #{pane_tty}"
```

**Required tmux settings (already in config):**
```
set -g set-clipboard on
set -g allow-passthrough on
set -as terminal-features ",*:clipboard"
```

## What Doesn't Work

- **`pbcopy` in run-shell** — copies to macOS clipboard, not iOS. pbcopy has no TTY in tmux run context and doesn't route via OSC 52.
- **`copy-mode \; send-keys -X select-all \; send-keys -X copy-pipe-and-cancel`** — copy-mode chaining is unreliable; copy-mode may not be fully initialized when send-keys -X fires, even with `run-shell -d 0.1` delay.

## Quoting Gotcha

`#{pane_id}` and `#{pane_tty}` must NOT be wrapped in single quotes in the run-shell string — tmux expands them before passing to sh, and single quotes become literal characters in the shell command.

```
# WRONG — single quotes become literal in shell
bind-key y run-shell "bash ~/scripts/tmux-osc52.sh '#{pane_id}' '#{pane_tty}'"

# RIGHT — bare expansion
bind-key y run-shell "bash ~/scripts/tmux-osc52.sh #{pane_id} #{pane_tty}"
```

## How OSC 52 Flows

```
Script writes to /dev/ttys00X (slave PTY)
  → tmux reads from master PTY (as pane output)
  → allow-passthrough on: tmux forwards OSC 52 to outer terminal
  → SSH connection carries it to Blink
  → Blink interprets OSC 52, updates iOS clipboard
```
