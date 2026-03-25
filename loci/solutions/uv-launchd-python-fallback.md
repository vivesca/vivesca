---
title: "uv run --script falls back to system Python in LaunchAgents"
category: runtime-errors
tags: [uv, launchd, python, cron, macos]
date: 2026-02-24
symptoms:
  - ModuleNotFoundError for inline PEP 723 dependencies
  - urllib3 warning referencing Python 3.9 site-packages
  - Script works interactively but fails from launchd
---

# uv run --script falls back to system Python in LaunchAgents

## Problem

A Python script using `uv run --script` with PEP 723 inline metadata (`# /// script` block) works perfectly from an interactive shell but fails with `ModuleNotFoundError` when run via macOS LaunchAgent.

### Symptoms

```
/Users/terry/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: ...
Traceback (most recent call last):
  File "script.py", line XX, in <module>
    import trafilatura
ModuleNotFoundError: No module named 'trafilatura'
```

Key tell: the `urllib3` warning references **system Python 3.9** site-packages (`Library/Python/3.9/`), not a uv-managed venv.

### Misleading signal

Some imports (feedparser, requests) may succeed because they happen to be pip-installed in system Python's user site-packages. This makes the failure intermittent — only deps NOT in system Python fail. Looks like a dep-specific issue but it's actually an environment issue.

## Root Cause

launchd provides a minimal environment (no `.zshenv`, no PATH augmentation). When `uv run --script` runs in this context, uv's Python discovery falls back to `/usr/bin/python3` (system Python 3.9 on macOS) instead of using a managed Python.

The script's `requires-python = ">=3.10"` SHOULD force uv to use a newer Python, but in the minimal launchd environment, uv's discovery mechanism doesn't work correctly.

Interactive shell works because `~/.zshenv` sets up PATH with Homebrew's Python, mise, etc. — uv finds Python 3.13+ easily.

## Fix

Add `--python 3.13` to the ProgramArguments in the plist:

```xml
<key>ProgramArguments</key>
<array>
    <string>/Users/terry/.local/bin/uv</string>
    <string>run</string>
    <string>--python</string>
    <string>3.13</string>
    <string>--script</string>
    <string>/path/to/script.py</string>
</array>
```

This forces uv to use a managed Python 3.13 (downloading it if needed on first run), bypassing system Python entirely.

### Verification

```bash
# Kick the LaunchAgent manually
launchctl kickstart gui/$(id -u)/com.terry.lustro-daily

# Check log — should see NO urllib3/Python 3.9 warnings
tail -20 ~/logs/cron-ainews.log
```

## Prevention

- **LaunchAgent Python scripts → `uv run --script` by default.** Single-file with deps = always inline script. Venv only if multi-file package with internal imports.
- **All `uv run --script` plists must include `--python 3.13`** (or whatever the current managed version is).
- **Never point a plist at `.venv/bin/python`** — symlinks break silently when uv upgrades Python. The oura-sync outage (Feb 27) lasted 5+ days before detection.
- Audit: `grep -r "\.venv" ~/agent-config/launchd/*.plist` — should return nothing.

## Variant: ~/bin scripts called from .zshrc

Same root cause, different trigger. `eval "$(keychain-env)"` in `.zshrc` runs before `mise activate` adds managed Python to PATH. The shebang `#!/usr/bin/env python3` resolves to `/usr/bin/python3` (3.9).

**Symptom:** `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` — the `str | None` union syntax requires 3.10+.

**Fix:** `from __future__ import annotations` at the top of the script. Makes all type hints lazy-evaluated strings, so `str | None` and `dict[str, str]` work on 3.9+. Cheaper than pinning the shebang to a specific Python path.

**Rule:** Any script in `~/bin/` that might be called early in shell init (from `.zshrc`/`.zshenv` before mise/Homebrew PATH) must either:
1. Use `from __future__ import annotations` if it has modern type hints, or
2. Use `#!/path/to/specific/python3.13` instead of `#!/usr/bin/env python3`

## Broader pattern: LaunchAgent PATH starvation

LaunchAgents run with a minimal PATH (`/usr/bin:/bin:/usr/sbin:/sbin`). ANY tool installed via Homebrew (`/opt/homebrew/bin`) is invisible. This caused bird CLI to silently fail in lustro's X/Twitter fetch for a week (Feb 21–27).

**Rule:** If a LaunchAgent calls a script that shells out to ANY Homebrew tool (bird, opencode, gh, etc.), add:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/Users/terry/.local/bin:/usr/local/bin:/usr/bin:/bin</string>
</dict>
```

**Also:** `uv venv` symlinks break when uv upgrades Python (3.12→3.13). Fix: `uv venv --python 3.13 --clear` + reinstall deps. Happened to oura-sync (Feb 27).

## Affected files

- `~/agent-config/launchd/com.terry.lustro-daily.plist` — PATH added (Feb 27)
- `~/agent-config/launchd/com.terry.lustro-breaking.plist` — PATH added (Feb 27)
- `~/agent-config/launchd/com.terry.capco-brief.plist` — created with PATH (Feb 27)
- `~/oura-data/.venv` — rebuilt for Python 3.13 (Feb 27)
- `~/agent-config/bin/keychain-env` (from __future__ fix applied Feb 2026)
