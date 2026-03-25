# agent-browser CDP Gotchas

## v0.5.0 → v0.9.3 Upgrade Fixes EAGAIN

- v0.5.0 produced `Resource temporarily unavailable (os error 35)` on 8GB Macs under memory pressure
- v0.9.3 handles CDP connections more reliably — same machine, same conditions, no EAGAIN
- Installed via pnpm: `pnpm add -g agent-browser`

## Shell Quoting for `eval`

Smart quotes (`'` / `'`) cause `SyntaxError: Invalid or unexpected token` in JS eval.

**Fix:** Use heredoc for complex JS:
```bash
cat > /tmp/script.js << 'EOF'
var x = document.querySelectorAll('input');
// ... your JS here
EOF
agent-browser --cdp 9222 eval "$(cat /tmp/script.js)"
```

## Pre-flight: Check Chrome CDP Is Running

Always verify before any CDP operation:
```bash
pgrep -f "Chrome CDP" >/dev/null && echo "running" || open "/Applications/Chrome CDP.app"
```
Without this, agent-browser commands silently timeout with unhelpful errors (e.g. `Timeout 10000ms exceeded. waiting for locator(':root')`).

## `snapshot <url>` Doesn't Reliably Navigate

`agent-browser --cdp 9222 snapshot "https://example.com"` is supposed to navigate then snapshot, but it often snapshots the **existing active tab** instead. Navigate first, then snapshot:
```bash
agent-browser --cdp 9222 eval "window.location.href = 'https://example.com'"
sleep 8
agent-browser --cdp 9222 snapshot
```

## Playwright CDP Fallback for Text Extraction

When agent-browser `eval`/`snapshot` both timeout or hang, connect via Playwright directly:
```python
from playwright.async_api import async_playwright
async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    text = await page.evaluate("document.body.innerText")
```
More reliable than agent-browser for bulk text extraction. Use `curl localhost:9222/json/list` first to identify which tab index to use.

## CDP Tab Management

- `agent-browser --cdp 9222` connects to active tab — if no tabs open, fails with "No page found"
- Create tab: `curl -s -X PUT "http://localhost:9222/json/new?about:blank"`
- List tabs: `curl -s http://localhost:9222/json/list`
- Close tab: `curl -s "http://localhost:9222/json/close/<TAB_ID>"`
- Multiple open tabs eat RAM — close unused tabs before heavy pages

## Page Load Timeouts

Workday and other SPAs often timeout on `open` (waits for `load` event that never fires).

**Workaround:** Navigate via JS eval instead:
```bash
agent-browser --cdp 9222 eval "window.location.href = 'https://example.com'"
sleep 5  # Wait for SPA to render
agent-browser --cdp 9222 get url  # Verify navigation
```

## Snapshot Timeout on Heavy Pages

Workday SPA can cause `snapshot` to timeout. Wait 5-10 seconds after navigation, or use `eval` to extract form fields directly:
```bash
agent-browser --cdp 9222 eval "var els=document.querySelectorAll('input,select,textarea'); ..."
```

## React/Angular Forms: JS Fill vs Playwright Fill

- `eval` with `nativeInputValueSetter` updates DOM but NOT React/Angular internal state
- `fill @ref "text"` fires proper Playwright events that DO update framework state
- For simple `<input>` fields, Playwright `fill` usually works
- For complex Workday widgets (combobox, custom selects), both may fail
- **Best approach for step 1:** Use Playwright `fill` for text inputs, JS `eval` for verification
