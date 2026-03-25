# Terminal Theme: Catppuccin Mocha Setup

Switched from Flexoki Dark to Catppuccin Mocha (Feb 2026). Covers Ghostty, tmux, Blink Shell.

## Why Catppuccin over Flexoki

- **Ecosystem breadth:** 300+ official ports (tmux, Neovim, Obsidian, Ghostty, Blink, VS Code, etc.). Flexoki is a one-person project with limited ports.
- **Blink Shell support:** First-party Catppuccin Blink port exists. Flexoki has no Blink port — would need manual porting.
- **Community momentum:** Most-cited theme in Claude Code + tmux setup guides (2025-2026).
- **Palette:** Warm pastels, mid-contrast. Comfortable for long coding sessions without being low-contrast.

## Ghostty

Config: `~/.config/ghostty/config`

```
theme = Catppuccin Mocha
```

## tmux

Config: `~/.tmux.conf`

Hand-mapped to `colour` numbers (NOT hex — hex breaks tmux tab mouse clicks in Ghostty).

| Role | colour# | Catppuccin name | Hex |
|------|---------|-----------------|-----|
| Status fg / session name | colour103 | Overlay 1 | #7f849c → #8787af |
| Idle/silence indicator | colour216 | Peach | #fab387 → #ffaf87 |
| Active tab fg (dim) | colour242 | Overlay 0 | #6c7086 → #6c6c6c |
| Tab bg | colour236 | Surface 0 | #313244 → #303030 |
| Current tab bg | colour239 | Surface 1 | #45475a → #4e4e4e |
| Current tab fg (active) | colour147 | Lavender | #b4befe → #afafff |
| Zoom indicator | colour147 | Lavender | #b4befe → #afafff |
| Pane border | colour236 | Surface 0 | #313244 → #303030 |
| Active pane border | colour111 | Blue | #89b4fa → #8787ff |

Design preserved from Flexoki setup:
- Idle = warm accent (peach replaces amber) → "needs you"
- Active = dim overlay → "busy, leave it alone"
- Current tab = brighter pill with lavender

**Not using catppuccin/tmux plugin** — it uses hex colours which break mouse clicks in Ghostty (tmux 3.6a). Hand-mapped colour numbers are the safe approach.

## Blink Shell (iOS)

Install from first-party repo: [github.com/catppuccin/blink](https://github.com/catppuccin/blink)

1. Open Blink → Settings → Appearance → New Theme
2. Paste raw URL: `https://raw.githubusercontent.com/catppuccin/blink/main/themes/catppuccin-mocha.js`
3. Apply as default theme

All four flavours available: mocha, macchiato, frappe, latte.

## Catppuccin Mocha Palette Reference

| Colour | Hex | Use |
|--------|-----|-----|
| Rosewater | #f5e0dc | |
| Flamingo | #f2cdcd | |
| Pink | #f5c2e7 | |
| Mauve | #cba6f7 | |
| Red | #f38ba8 | Errors |
| Maroon | #eba0ac | |
| Peach | #fab387 | Warnings, idle indicator |
| Yellow | #f9e2af | |
| Green | #a6e3a1 | Success |
| Teal | #94e2d5 | |
| Sky | #89dceb | |
| Sapphire | #74c7ec | |
| Blue | #89b4fa | Links, active borders |
| Lavender | #b4befe | Current/focused elements |
| Text | #cdd6f4 | Primary text |
| Subtext 1 | #bac2de | |
| Subtext 0 | #a6adc8 | Secondary text |
| Overlay 2 | #9399b2 | |
| Overlay 1 | #7f849c | Tertiary text |
| Overlay 0 | #6c7086 | Dimmed text |
| Surface 2 | #585b70 | |
| Surface 1 | #45475a | Elevated surfaces |
| Surface 0 | #313244 | Default surface |
| Base | #1e1e2e | Background |
| Mantle | #181825 | Deeper background |
| Crust | #11111b | Deepest background |

## Other themes considered

- **Gruvbox:** Closest to Flexoki's warmth, but ecosystem aging. Community energy shifted to Catppuccin.
- **Nord:** Beautiful cool-toned arctic palette. Long blue sessions can strain eyes.
- **Dracula:** High contrast, vivid. Fatiguing over hours.
- **Rose Pine:** Lovely warm muted tones but lower contrast makes Claude Code dense output harder to scan.
- **Tokyo Night:** Popular (DHH's Omakub default) but similar low-contrast concern.
- **Kanagawa:** Aesthetic but no Blink port.
- **Everforest:** Great eye comfort, no Blink port.

## Gotchas

- Ghostty theme names are case-sensitive: `Catppuccin Mocha` not `catppuccin-mocha`
- Hex colours in tmux status bar break click-to-switch tabs in Ghostty (tmux 3.6a) — always use `colour` numbers
- `#{p...}` padding breaks when nested with `#{?...}` conditionals — tabs silently vanish. Workaround: pad in `automatic-rename-format` with literal trailing spaces.
- `pane-focus-in 'refresh-client'` causes visual vibration in Ghostty — hook fires on every focus event. Use `client-attached` + `client-resized` instead.
- `monitor-activity on` causes near-constant status bar repaints with Claude Code running — each output burst triggers a repaint, manifests as random screen vibration. Disable for Ghostty.
- Blink Shell themes are JS files installed via raw GitHub URL
- `ghostty +list-themes | grep -i catppuccin` to verify available names
