---
name: peekaboo
description: Peekaboo — Mac Screen Access. See and control both Macs remotely via Peekaboo + SSH. Use when needing to see screen state, screenshot, or click/type on Mac.
---

# Peekaboo — Mac Screen Access

See and control both Macs remotely via Peekaboo + SSH.

## Triggers

- "see my screen", "screenshot", "what's on my mac"
- "click on", "type on", "open app on mac"
- Any task requiring visual confirmation of Mac state

## Targets

| Host | Machine | Tailscale IP |
|------|---------|-------------|
| `m3` | MacBook Air M3 | 100.111.84.117 |
| `mac` | MacBook M1 | 100.94.27.93 |

Both have Peekaboo 3.0 daemon running as LaunchAgent (`com.steipete.peekaboo`), Screen Recording + Accessibility granted.

If user doesn't specify which Mac, ask.

## Commands

Replace `HOST` with `m3` or `mac`:

### Screenshot
```bash
ssh HOST "export PATH=/opt/homebrew/bin:\$PATH && peekaboo image --mode screen --path /tmp/cc_screen.png"
scp HOST:/tmp/cc_screen.png /tmp/cc_screen.png
# Then Read /tmp/cc_screen.png to view
```

### Screenshot specific app
```bash
ssh HOST "export PATH=/opt/homebrew/bin:\$PATH && peekaboo image --app 'Safari' --path /tmp/cc_screen.png"
```

### Click
```bash
ssh HOST "export PATH=/opt/homebrew/bin:\$PATH && peekaboo click --x 100 --y 200"
```

### Type
```bash
ssh HOST "export PATH=/opt/homebrew/bin:\$PATH && peekaboo type --text 'hello'"
```

### List windows
```bash
ssh HOST "export PATH=/opt/homebrew/bin:\$PATH && peekaboo list --windows --json"
```

### Daemon status
```bash
ssh HOST "export PATH=/opt/homebrew/bin:\$PATH && peekaboo daemon status --json"
```

## Notes

- Daemon must be running for capture to work (LaunchAgent handles this)
- If permissions show `false`, restart daemon: `peekaboo daemon stop && peekaboo daemon start`
- Images captured at 1x logical resolution by default; add `--retina` for 2x
- Add `--json` to any command for structured output
- `peekaboo see` does OCR + element detection — useful for finding click targets
