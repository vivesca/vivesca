# Kindle Cloud Reader Automation Reference

Project: `~/code/kindle-extract/kindle-extract`

## Key Gotchas
- **Uses touch events, not mouse clicks.** Ionic/mobile-first framework — `element.click()` is silently ignored. Use `touchstart` + `touchend` dispatch with proper Touch constructor.
- **Left chevron (Previous Page) is read-only** for pages not yet visited in current session. Cannot navigate backward with clicks or keys.
- **TOC navigation to "Title Page"** = reliable way to reach page 1. Then touch events work from there.
- **`backdrop-no-scroll` on body** = normal state, not a bug. Doesn't prevent touch events.
