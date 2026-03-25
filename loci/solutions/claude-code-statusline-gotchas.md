# Claude Code statusLine Gotchas

## PATH isolation

statusLine commands run in a non-interactive shell — `~/.zshrc` and `~/.zshenv` PATH additions are not inherited. Tools in `~/.local/bin/`, `~/bin/`, etc. are invisible by name.

**Fix:** Always use absolute paths for custom binaries in statusLine commands.

```json
"command": "/Users/terry/.local/bin/respirometry --statusline 2>/dev/null"
```

## Exit code sensitivity

If the statusLine command exits non-zero, the entire status bar display breaks (shows nothing or errors). Any external tool call that can fail needs a safety net.

**Fix:** Append `|| true` to any fallible subcommand, or wrap the whole command in `; true`.

```bash
respirometry_out=$(/Users/terry/.local/bin/respirometry --statusline 2>/dev/null); [ -n "$respirometry_out" ] && printf ' · %s' "$respirometry_out" || true
```

## Token-dependent tools are fragile in statusLine

statusLine polls frequently. Tools that depend on short-lived credentials (e.g. `respirometry` OAuth token, ~1hr TTL) will start returning errors mid-session. The `2>/dev/null || true` pattern hides the error gracefully, but the data disappears silently.

**Decision pattern:** If a tool depends on expiring credentials, keep it CLI-only rather than wiring into statusLine. Poll manually when needed.

## Discovered

2026-03-08 — attempting to wire `respirometry --statusline` into Claude Code statusLine.
