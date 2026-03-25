# Browser Automation for LLM Agents — Comparison (Feb 2026)

## Benchmark Results (Hacker News, 1604 AX nodes)

| Operation | Direct CDP | Playwright Python | agent-browser CLI |
|---|---|---|---|
| connect | 0ms (persistent ws) | 307ms | ~200ms |
| navigate | 725ms | 243ms | 5,864ms |
| eval (title) | 8.4ms | 17.4ms | 275ms |
| accessibility snapshot | 38ms (1,604 nodes) | 1,174ms (883 ARIA lines) | 22,393ms (884 lines) |
| innerText | 4.1ms | 4.8ms | n/a |

## Token Cost (MCP always-on)

| MCP Server | Tools | Tokens/turn |
|---|---|---|
| Playwright MCP | 22 | ~3,700 |
| Claude-in-Chrome | 17 | ~5,600 |
| agent-browser CLI | 0 (shell out) | 0 |

## Tool Architecture

| Tool | Layer | LLM Interface | Best For |
|---|---|---|---|
| **Direct CDP** | Raw websocket to Chrome | None (DIY JS eval) | Scraping, extraction, speed-critical ops |
| **Playwright Python** | Library over CDP | ARIA snapshot | Programmatic automation, testing |
| **Playwright MCP** | MCP server over Playwright | 22 tools, ARIA snapshot | Claude Code native browser control |
| **agent-browser** | CLI over Playwright | Snapshot + ref-based actions | Interactive agent loops from shell |
| **browser-use** | Agent framework over Playwright | Built-in LLM routing | Autonomous "do X" delegation |
| **Stagehand** | Browserbase cloud | Vision + DOM | Production with CAPTCHA/2FA |

## Key Findings

### CDP Extension Cleanup (Feb 14, 2026)
- **Before:** 16 targets (12 service workers from 39 extensions), eval avg 1,220ms, max 3,127ms
- **After:** 2-3 targets (0 SWs, 5 extensions kept), eval avg 3.5ms, max 24ms
- **Improvement:** 349x on document.title, 19x on simple eval
- Extensions kept: 1Password, iCloud Passwords, AdGuard, Cookie Dismisser, Obsidian Clipper
- Launch script: `/Applications/Chrome CDP.app/Contents/MacOS/launch.sh`

### XHS Pages Poison CDP
Anti-bot JS on XHS (Xiaohongshu) blocks websocket `recv()` for ALL tabs globally, not just its own target. Same behavior confirmed for Zhihu. Always close anti-bot pages after use.

### agent-browser Overhead
The 22-second snapshot isn't Playwright's fault — it's Node.js cold start + Playwright connection setup on every CLI invocation. A persistent Playwright connection (MCP or library) eliminates this. After CDP cleanup, cold start improved from 22s to ~1.5s.

## Decision (Feb 2026)

- **Scraping (qianli):** Direct CDP websocket. Nothing else comes close.
- **Interactive browsing:** agent-browser CLI (0 token cost, acceptable latency after cleanup).
- **Playwright MCP:** Not worth always-on (~3,700 tokens/turn). Same conclusion as Claude-in-Chrome and QMD MCP.
- **browser-use:** Not installed. Would only make sense for fully autonomous web tasks.
- **Stagehand:** Overkill for local automation. Cloud dependency not needed.

## Practical Setup

```bash
# Direct CDP (fastest)
python3 -c "
import asyncio, websockets, json
async def run():
    async with websockets.connect('ws://127.0.0.1:9222/devtools/page/TARGET_ID') as ws:
        await ws.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':'document.title'}}))
        print(await ws.recv())
asyncio.run(run())
"

# agent-browser (structured, LLM-friendly)
agent-browser --cdp 9222 snapshot
agent-browser --cdp 9222 eval "document.title"
agent-browser --cdp 9222 click "@ref"

# Playwright MCP (only if needed for heavy session)
# Add to claude config temporarily, or use alias
```

## Anti-Bot Bypass (Feb 2026)

### How sites detect CDP
1. **`Runtime.enable` serialisation** — CDP instruments JS object serialisation. Sites trigger specific patterns that behave differently when Runtime domain is active
2. **`navigator.webdriver`** — set by automation frameworks (masked by `--disable-blink-features=AutomationControlled`)
3. **`--remote-debugging-port` leaks** — detectable via `chrome://gpu/` command-line flags
4. **Injected VM scripts** — `Page.evaluateOnNewDocument` creates detectable `VM215`-style scripts

### nodriver (stealth CDP)
`pip install nodriver` — patches Chrome internals to hide all CDP signals.

**Test results on Taobao:**

| | CDP Chrome | nodriver |
|---|---|---|
| Body text | 0 chars (empty) | 2,035 chars (full) |
| Images | 0 | 178 |
| navigator.webdriver | false (with blink flag) | false |
| Anti-bot bypass | No | Yes |

**Constraint:** nodriver launches its own Chrome — can't share `user-data-dir` with running CDP Chrome. Must stop CDP Chrome first.

**Persistent session pattern (Mar 2026):** For sites using localStorage auth (JWT) + Cloudflare — where `porta` finds no cookies and headed Playwright is bot-blocked — use nodriver with a fixed `user_data_dir`:
```python
browser = await uc.start(headless=False, user_data_dir="~/.config/lustro/nodriver-profile")
# Log in once via headed window (Jump Desktop if on SSH)
# Subsequent headless runs reuse the saved session
browser = await uc.start(headless=True, user_data_dir="~/.config/lustro/nodriver-profile")
```
Quaily.com confirmed working (Mar 2026). Session persists until Quaily expires it (~weeks/months). Re-run headed to refresh.

**porta vs nodriver decision:**
- `porta` → cookies exist in Chrome → bridge them (fast, no Chrome launch)
- `nodriver` → no Chrome cookies (localStorage JWT) OR Cloudflare blocks Playwright → nodriver with persistent profile

### nodriver + Playwright bridge
nodriver provides stealth; Playwright provides the scraping API. Connect Playwright to nodriver's CDP port:
```python
import nodriver as uc
from playwright.async_api import async_playwright

browser = await uc.start(user_data_dir='~/chrome-debug-profile')
cdp_url = f'http://{browser.config.host}:{browser.config.port}'

pw = await async_playwright().start()
pw_browser = await pw.chromium.connect_over_cdp(cdp_url)
# Use Playwright normally — existing scrapers work unchanged
```

### Tools for bypass

| Tool | Approach | Anti-bot effectiveness |
|---|---|---|
| `--disable-blink-features=AutomationControlled` | Mask webdriver flag | Low (Taobao still detects) |
| **nodriver** | Patch Chrome CDP internals | High (Taobao, XHS work) |
| rebrowser-patches | Patch Puppeteer/Playwright | High (untested locally) |
| undetected-chromedriver | Patch ChromeDriver | Medium |
| curl_cffi | TLS fingerprint spoofing | For HTTP only, no JS |
