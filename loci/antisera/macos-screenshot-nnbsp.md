---
name: macos-screenshot-nnbsp
description: macOS screenshot filenames contain Unicode narrow no-break space (U+202F) before AM/PM
type: solution
tags: [screenshot, macos, unicode, filename, gog, attach]
titer-hits: 108
titer-last-seen: 2026-04-24
---

## Problem

macOS screenshot filenames like `Screenshot 2026-03-26 at 8.23.33 PM.png` contain a Unicode narrow no-break space (`e2 80 af`, U+202F) before "AM"/"PM". This is invisible but breaks:
- Shell string literals
- `gog --attach` path arguments
- Any tool that constructs the path from visible characters

## Fix

Use glob to match the file, then pass the resolved path:
```bash
SCREENSHOT=$(ls ~/path/Screenshot\ 2026-03-26*)
```

Or copy to a clean-named temp file before passing to tools.
