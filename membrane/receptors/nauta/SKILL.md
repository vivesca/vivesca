---
name: nauta
description: Web browser automation — 3-tier escalation from headless to AppleScript. Covers agent-browser, cookie bridge, LinkedIn, stealth, auth. Single reference for all web access.
user_invocable: false
platform: claude-code
platform_note: Primary browser automation tool. Zero token overhead when idle.
---

# Web Browser Automation

Single reference for all web access. Three tiers, escalate until one works.

## Tier Decision

```
Is the page public?
  YES → Tier 1 (agent-browser headless)
  NO → Is agent-browser session still valid?
    YES → Tier 1 (agent-browser headless with persistent profile)
    NO → Does the site block Playwright login?
      NO → Tier 2 (cookie bridge or headed login)
      YES → Tier 3 (AppleScript via SSH to Mac Chrome)
```

**Known Tier 3 sites (Playwright login blocked):** LinkedIn, Schwab, most financial sites.
**Unautomatable (reCAPTCHA v3 + popups):** PPS (ppshk.com) — call 2311 9876 instead.
**Known Tier 2 sites:** Vercel (Google OAuth → porta), Substack, Taobao, Shopify checkout (3D Secure needs headed).
**Known Tier 1 sites (form auth, no bot detection):** RVD e-billing (gov.hk SSO), BuyAndShip (email OTP).
**Always Tier 1:** Public pages, sites with valid session cookies.

### Auth Escalation (when Google OAuth is blocked headless)

Google Sign-In SDK opens popups that headless Chrome blocks silently. Escalation:
1. **porta cookie injection** — `porta_inject domain=accounts.google.com` before navigating. Works for redirect-based OAuth, fails for popup-based.
2. **Email OTP fallback** — many sites offer email OTP as alternative to Google login. Enter email → click "Log in with OTP" → grab code from Gmail via `gog gmail search` → fill OTP fields. Fully headless, no user intervention.
3. **Headed mode** — `AGENT_BROWSER_HEADED=1 agent-browser open <url>`. User clicks Google login in visible window.
4. **`--auto-connect`** — `agent-browser --auto-connect open <url>`. Connects to user's real Chrome (requires Chrome launched with `--remote-debugging-port=9222`).

---

## Tier 1 — agent-browser (Headless Playwright)

Zero token overhead. Invoked via Bash.

### Setup

Persistent profile via env var (set in `~/.claude/settings.json`):
```
export AGENT_BROWSER_PROFILE="$HOME/.agent-browser-profile"
```

### Core Workflow

```bash
agent-browser open https://example.com    # navigate
agent-browser wait 2000                    # let it load
agent-browser snapshot                     # accessibility tree with @refs
agent-browser click @ref_3                 # interact by ref
agent-browser fill @ref_7 "search term"   # clear + type
agent-browser get text body               # extract page text
agent-browser screenshot out.png           # visual capture
agent-browser close                        # cleanup
```

### Iframe Support (0.24.1+)

agent-browser auto-inlines iframe content in snapshots via `Target.setAutoAttach`. Refs inside iframes work directly — no frame switching needed.

```bash
agent-browser snapshot -i | grep "Card number"
# → Iframe "Field container for: Card number" [ref=e344]
#     - textbox "Card number" [required, ref=e344]

agent-browser fill @e344 "4111111111111111"  # fills directly into iframe
```

**Confirmed working:** Shopify checkout card fields (card number, expiry, CVV, name — each in separate iframes). chemotaxis MCP cannot do this yet — use agent-browser CLI directly for iframe fills.

### Session Persistence

```bash
agent-browser --session-name buyandship open "https://site.com"  # auto-saves cookies/localStorage
# Next time:
agent-browser --session-name buyandship open "https://site.com"  # auto-restores state
```

### E-commerce Checkout (Shopify)

**Cart API** — when "Add to Cart" button doesn't render or is broken:
```bash
# Discover variant IDs
agent-browser eval 'fetch(window.location.pathname + ".js").then(r=>r.json()).then(p=>p.variants.map(v=>({id:v.id,title:v.title,available:v.available,price:v.price})))'

# Add to cart directly
agent-browser eval 'fetch("/cart/add.js",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({items:[{id:VARIANT_ID,quantity:1}]})}).then(r=>r.json())'
```

**Checkout flow:**
1. Add to cart via API → navigate to `/checkout`
2. Fill shipping fields with `fill` (standard inputs)
3. Fill card fields with `fill @ref` (iframes — agent-browser handles automatically)
4. Click "Review order" → verify totals → click "Pay now"
5. **3D Secure:** headless Chrome cannot handle 3DS popups. Switch to `AGENT_BROWSER_HEADED=1` for the payment step. User approves 3DS in visible browser or via bank app notification.

**Session expiry:** Shopify checkout sessions expire after ~10 min of inactivity. If you get "There was a problem with our checkout", clear cart (`/cart/clear`), re-add items, and start fresh.

### Navigation Gotcha

`open <url>` can load the **existing active tab** instead of navigating. Always navigate via `eval`:
```bash
agent-browser eval "window.location.href = 'https://target.com'"
sleep 8
agent-browser snapshot
```

### Command Sequencing

**Strictly sequential.** Never fire concurrent commands — causes "Resource temporarily unavailable (os error 35)".

### Refs Shift After Actions

After any action, refs become stale. **Always re-snapshot before each action.**

### SPA Component Clicking (Angular, React, Vue)

In SPAs, the visible text is often a `<span>` or `<p>` inside a framework wrapper component (`mat-list-item`, `[role=listbox] > div`, React `li`, etc.). Clicking the text node does nothing — you need the interactive ancestor.

**Pattern:** Find the text, then `.closest()` up to the clickable wrapper:
```js
document.querySelector('.programTitle').closest('mat-list-item').click()
```

**General discovery approach:**
```js
// Find what wraps a visible text string
var el = Array.from(document.querySelectorAll('*'))
  .find(e => e.textContent.includes('Target Text') && e.offsetHeight < 100);
// Walk up: el.tagName, el.className, el.parentElement...
```

**Signs you hit this:** `click @ref` returns success but page doesn't navigate. URL stays the same. `snapshot` shows the element but it's a `StaticText` or `span`, not a link or button.

### Two Modes

| Mode | Command | Use case |
|------|---------|----------|
| **Headless** | `agent-browser open <url>` | Default — public web, authenticated sites with valid session |
| **Headed** | `agent-browser --headed open <url>` | Debugging, initial login (needs display) |

**Headed on soma (headless Linux):** Requires Xvfb:
```bash
Xvfb :99 -screen 0 1280x720x24 &
agent-browser close  # must close first
DISPLAY=:99 agent-browser --headed open "https://example.com"
```
No VNC on soma — can't view the display remotely.

### Form Filling: fill vs type vs eval

- **`fill <selector> <text>`** — clears + sets value. Triggers React/Vue reactivity. **Use for most inputs.**
- **`type <selector> <text>`** — appends char-by-char. Use for autocomplete.
- **`keyboard type <text>`** — types without selector. Use for LinkedIn messages (avoids `!` → `/!` escaping).
- **`eval "input.value = 'x'"`** — **NEVER for SPA forms.** Bypasses framework state.

### Multi-Tab Flows

```bash
agent-browser tab list       # list open tabs
agent-browser tab N          # switch to tab N
agent-browser tab new <url>  # open URL in new tab
```
Don't use `window.open()` via eval — loses original context.

### TOTP Race Condition

Combine fetch + fill + submit in one bash command:
```bash
OTP=$(op item get "ServiceName" --vault Agents --otp 2>/dev/null)
agent-browser fill 'input[type="text"]' "$OTP" 2>&1
agent-browser eval "Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Verify').click()" 2>&1
```

### When Blocked on Public Sites

Don't fight the block — find an alternative source or the hidden API:
```bash
# Find API endpoints in JS files
curl -s "https://site.com/main.js" | grep -o '"[^"]*\.php[^"]*"\|api/[^"]*"'
```

### Heavy SPA Iframes (OCI, AWS)

Content in sandboxed iframes — `snapshot` returns empty for same-origin iframes:
```bash
agent-browser eval "(function() {
  var f = document.getElementById('sandbox-maui-preact-container');
  return f && f.contentDocument ? f.contentDocument.body.innerText.substring(0, 2000) : 'no access';
})()"
```

**Cross-origin nested iframes** (e.g. shop.oracle.com inside OCI): `snapshot` can NOT see into them. `click @ref` and `eval` won't reach. Options:
1. **Keyboard fill** — Tab through form fields blind (fragile, need exact Tab order)
2. **Playwright CDP** — `connect_over_cdp('ws://127.0.0.1:<port>')`, then `page.frames` to find nested frame by URL and use `frame.query_selector()` / `frame.fill()`
3. **Coordinate click** — `agent-browser mouse move X Y && mouse down && mouse up` (pierces iframes at browser level)

### Mobile-Only Sites

```bash
agent-browser close
agent-browser set device "iPhone 13"
agent-browser open "https://example.com/menu" --wait 8000
```

### Keyboard Fill for Opaque Iframes

When Playwright can't find inputs (shadow DOM, cross-origin):
```python
page.mouse.click(480, 230)  # estimate from screenshot
page.keyboard.type("First Name")
page.keyboard.press("Tab")
page.keyboard.type("Last Name")
```

### Form Submit vs Click

Buttons with `type="button"` don't submit forms when clicked. Use `form.submit()`:
```bash
agent-browser eval "document.getElementById('formId').submit()"
```
This is common on gov.hk and legacy sites. Always check button type if click doesn't navigate.

### Eval Output Quoting

`agent-browser eval` wraps output in JSON quotes. Strip before processing:
```bash
# BAD — base64 decode fails on quoted string
agent-browser eval "btoa(data)" > /tmp/raw.txt
base64 -d /tmp/raw.txt  # fails — contains "..."

# GOOD
agent-browser eval "btoa(data)" > /tmp/raw.txt
sed 's/^"//;s/"$//' /tmp/raw.txt | base64 -d > /tmp/file.pdf
```

### PDF Download via Fetch

Sites that serve PDFs behind auth — download inside the browser session:
```bash
agent-browser eval "
  fetch('/path/to/document.pdf')
    .then(r => r.arrayBuffer())
    .then(buf => {
      const bytes = new Uint8Array(buf);
      let binary = '';
      for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
      return btoa(binary);
    })
" > /tmp/b64.txt
sed 's/^"//;s/"$//' /tmp/b64.txt | base64 -d > /tmp/doc.pdf
```

### reCAPTCHA v3 — Hard Wall

reCAPTCHA v3 scores ~20 signals: `navigator.webdriver`, CDP detection, canvas/WebGL fingerprint, IP reputation, Google cookies. Playwright fails all of them.

**What doesn't work:**
- Google cookie injection via `document.cookie` (wrong domain context, not HttpOnly)
- Visual CAPTCHA solving (it's the invisible v3 score, not the visual challenge)
- Headed mode (still Playwright's Chromium fingerprint)
- playwright-stealth (JS-level patches, doesn't fix canvas/WebGL/audio)

**What might work (untested):**
- CloakBrowser (C++-patched Chromium, MIT, headless Linux)
- Real Chrome via `channel="chrome"` + persistent profile + `context.addCookies()`
- After one successful login: save `storage_state` and reuse — bypasses reCAPTCHA on subsequent runs

### Reliability Tier

| Always works | `get url`, `get title`, `eval`, `snapshot`, `upload` |
|---|---|
| Usually works | `fill`, `check`, `press Enter/Tab` |
| Unreliable | `select @ref` (use JS eval), `click @ref` on complex widgets |
| Never works | Headless on career sites, JS `.value` for React |

### Fallback Table

| Fails | Do instead |
|-------|-----------|
| `open "url"` timeout | `eval "window.location.href = 'url'"` + `sleep 5` |
| `click @ref` timeout | `eval "document.querySelector('sel').click()"` |
| `select @ref` hangs | JS: `.value = 'x'` + `dispatchEvent(new Event("change", {bubbles:true}))` |
| All Playwright actions | Escalate to Tier 2 or 3 |

### Backup: Rodney

Go-based browser automation CLI using Chrome CDP. `~/go/bin/rodney`. Use when Playwright binaries break.
```bash
rodney start [--show]    # launch Chrome
rodney open <url>        # navigate
rodney ax-tree           # accessibility tree
rodney js <expression>   # eval JS
rodney stop              # shutdown
```

---

## Tier 2 — Cookie Bridge & Headed Login

When agent-browser session has expired and the site allows Playwright login.

### Option A: Cookie Bridge (Mac LaunchAgent → soma)

Permanent HTTP service on Mac that decrypts Chrome cookies and serves them over Tailscale.

```
Mac (100.94.27.93:9742) ←── curl from soma
  ~/bin/cookie-bridge (LaunchAgent, KeepAlive)
  Direct AES decryption — no keychain access at runtime
  Chrome Safe Storage key cached in 1Password
```

```bash
# From soma — get cookies for any domain
curl -s "http://100.94.27.93:9742/cookies?domain=google.com"
# Returns: {"NID": "...", "SID": "...", ...}
```

**Key implementation details:**
- Derives AES key via `PBKDF2(chrome_key, b'saltysalt', 1003, 16)`
- Strips `v10` prefix from encrypted values, decrypts AES-128-CBC with iv=`b' '*16`
- Copies Chrome Cookies SQLite to temp file (avoids locking)
- Chrome Safe Storage key in 1Password: `3tphbmft5i7gu6wh7skojaqpla`

**Gotchas:**
- `pycookiecheat` hangs over SSH (keychain blocked) — bypass entirely with direct decryption
- `CHROME_COOKIE_PASSWORD` env var doesn't prevent pycookiecheat from hitting keychain
- macOS keychain is inaccessible from SSH sessions (error -25308)
- Extract Chrome Safe Storage key once from local Terminal: `security find-generic-password -s "Chrome Safe Storage" -w`
- First run requires clicking "Always Allow" on keychain popup on Mac display

### Option A-legacy: kleis Cookie Extraction (Mac Chrome → agent-browser)

Extract cookies from Mac's Chrome, inject into agent-browser profile.

**Prerequisites:** kleis installed (`cargo install kleis`), macOS Keychain unlocked.

```bash
# On Mac — unlock keychain (must be local session, NOT SSH)
security unlock-keychain ~/Library/Keychains/login.keychain-db

# Extract cookies
ssh mac "kleis linkedin.com www.linkedin.com"  # → JSON array

# Inject into agent-browser via Playwright
# (write cookies JSON to /tmp, run playwright script to add_cookies)
```

**Keychain gotcha:** Cannot unlock over SSH — "User interaction is not allowed." Must be unlocked from a local terminal (Jump Desktop or physical access).

### Option B: porta Cookie Bridge (Mac-only CLI)

Bridges Chrome/Firefox/Arc cookies into agent-browser profile. **Not installed on soma or Mac as of Apr 2026.**

```bash
porta inject --domain vercel.com              # Chrome Default
porta inject --browser firefox --domain x.com  # Firefox
porta watch --domain site.com --interval 300   # auto-refresh
```

Install: `cd ~/code/porta && cargo install --path .`

**porta fails on:** LinkedIn (IP-bound session), cora.computer (Devise auth), any fingerprint-bound site. If porta fails → escalate to Tier 3.

### Option C: Headed Login (tessera flow)

Open browser in headed mode, user logs in via Jump Desktop.

```bash
agent-browser close
agent-browser --headed open "<login-url>"
# User logs in via Jump Desktop
agent-browser close
# Verify headless works:
agent-browser open "<protected-url>"
agent-browser get url  # should NOT redirect to login
```

**On soma:** Requires Xvfb + VNC (VNC not installed). Headed login not practical on soma.

### Option D: nodriver (Cloudflare + localStorage auth)

When site uses Cloudflare AND stores auth in localStorage (not cookies):
```bash
cd /tmp && uv run --python 3.13 --with nodriver python3 -c "
import asyncio, nodriver as uc
from pathlib import Path
PROFILE = Path.home() / '.config/endocytosis/nodriver-profile'
PROFILE.mkdir(parents=True, exist_ok=True)
async def main():
    b = await uc.start(headless=False, user_data_dir=str(PROFILE))
    await b.get('https://site.com/login')
    print('Log in via Jump Desktop — waiting 120s...')
    await asyncio.sleep(120)
    b.stop()
asyncio.run(main())
"
```

### Stealth Playwright (Cloudflare bypass)

For Cloudflare-blocked sites where you have Chrome cookies:

```bash
# Extract cookies
COOKIES=$(ssh mac "kleis example.com")

# Use playwright-extra + stealth plugin
# headless=False + DISPLAY=:99 on soma
# --disable-blink-features=AutomationControlled
```

Libraries: **kleis** (cookie extraction), **larvo** (stealth context wrapper).

---

## Tier 2.5 — agent-browser via SSH to Mac

**For sites like LinkedIn** where Playwright login is blocked on soma but works on Mac. Run agent-browser commands via `ssh mac` instead of locally. Same persistent profile, same API — just a different machine.

### Why Mac Works When Soma Doesn't

- Same IP as Mac Chrome (LinkedIn trusts the network)
- `--headed` mode internally sets `headless=false` even though no window appears on Mac
- Login via `keyboard type` + `click` succeeds from Mac (blocked on soma)

### Login (one-time, when session expires)

```bash
ssh mac "agent-browser close; sleep 2; agent-browser --headed open 'https://www.linkedin.com/login'"
# Fill credentials:
ssh mac "agent-browser click @e19 && agent-browser keyboard type 'terry.li.hm@gmail.com'"
LI_PASS=$(op item get "tlahsscuctajs753gkddj6re4i" --vault Agents --fields password --reveal | tr -d '\n')
ssh mac "agent-browser press Tab && agent-browser keyboard type '${LI_PASS}' && agent-browser click @e12"
# Verify:
sleep 8 && ssh mac "agent-browser get url"  # should be /feed, not /login
```

### Daily Use

```bash
ssh mac "agent-browser open 'https://www.linkedin.com/messaging/' && sleep 5 && agent-browser snapshot"
ssh mac "agent-browser click @eXX"  # interact with refs
ssh mac "agent-browser keyboard type 'message text'"
ssh mac "agent-browser screenshot /tmp/li.png"  # verify before sending
```

All agent-browser commands, refs, snapshot, fill, click — everything works. Just prefix with `ssh mac`.

### LinkedIn Messaging

```bash
# List conversations
ssh mac "agent-browser open 'https://www.linkedin.com/messaging/' && sleep 5 && agent-browser get text body" | head -40

# Read a conversation (click by ref from snapshot)
ssh mac "agent-browser snapshot" | grep -i "person name"
ssh mac "agent-browser click @eXX && sleep 3 && agent-browser get text body"
```

### Sending Messages

**Use `keyboard type` not `type`** — `type` escapes `!` → `\!`.
**Always screenshot + user confirmation before sending.** LinkedIn messages cannot be unsent.

---

## Tier 3 — AppleScript via SSH to Mac Chrome

**Last resort.** Uses the real Chrome browser on Mac with real cookies — zero bot detection. For when even agent-browser on Mac fails or when Chrome is already on the right page.

### When to Use

- Agent-browser session expired on Mac AND login fails
- Need to read content from an already-open Chrome tab quickly
- Schwab, banking sites that block all Playwright (even headed on Mac)

### Core Pattern

```bash
# Navigate
ssh mac 'osascript -e "tell application \"Google Chrome/" to set URL of active tab of first window to /"https://www.linkedin.com/messaging//""'
sleep 5

# Read page content
ssh mac 'osascript -e "tell application \"Google Chrome\" to execute active tab of first window javascript /"document.body.innerText/""'

# Execute JS (click, extract, etc.)
ssh mac 'osascript -e "tell application \"Google Chrome\" to execute active tab of first window javascript /"document.querySelector('"'"'.some-class'"'"').click()/""'
```

### Click Elements by Content

```bash
ssh mac 'osascript -e "tell application \"Google Chrome\" to execute active tab of first window javascript \"
  var items = document.querySelectorAll('"'"'.msg-conversation-listitem__link'"'"');
  for (var i = 0; i < items.length; i++) {
    if (items[i].innerText.indexOf('"'"'Person Name'"'"') !== -1) {
      items[i].click(); break;
    }
  }
  '"'"'clicked'"'"';
\""'
```

### Shell Quoting

AppleScript + SSH + JS = quoting hell. Rules:
- Outer: single quotes for SSH
- osascript: escaped double quotes `/"`
- JS strings inside: `'"'"'` for single quotes (break out of single quote, add escaped single, resume)

### LinkedIn Messaging (confirmed Apr 2026)

```bash
# Navigate to messaging
ssh mac 'osascript -e "tell application \"Google Chrome\" to set URL of active tab of first window to \"https://www.linkedin.com/messaging/\""'
sleep 5

# List conversations
ssh mac 'osascript -e "tell application \"Google Chrome\" to execute active tab of first window javascript \"document.body.innerText\""' | head -40

# Click into a conversation
ssh mac 'osascript -e "tell application \"Google Chrome\" to execute active tab of first window javascript \"var items = document.querySelectorAll('"'"'.msg-conversation-listitem__link'"'"'); for (var i = 0; i < items.length; i++) { if (items[i].innerText.indexOf('"'"'Contact Name'"'"') !== -1) { items[i].click(); break; } } '"'"'clicked'"'"';/""'
sleep 3

# Read conversation
ssh mac 'osascript -e "tell application \"Google Chrome\" to execute active tab of first window javascript \"document.querySelector('"'"'.msg-s-message-list-content'"'"') ? document.querySelector('"'"'.msg-s-message-list-content'"'"').innerText : '"'"'no list'"'"';/""'
```

### LinkedIn Message Sending

**Use `keyboard type` not `type`** — `type` escapes `!` → `\!`.
**Always screenshot + user confirmation before sending.** LinkedIn messages cannot be unsent.

```bash
agent-browser click @eXX   # textbox "Write a message..."
agent-browser keyboard type "Your message here"
agent-browser screenshot   # verify
# Wait for user confirmation
agent-browser click @eYY   # Send button
```

### "X replied on LinkedIn" Reflex

1. Navigate to messaging via AppleScript
2. Extract conversation text
3. Present the reply
4. Offer to draft a response — don't ask user what was said

### Gotchas

- **osascript JS doesn't trigger React state.** Reading works fine. Writing (form fills, clicks) may not work on React SPAs. Fall back to System Events keystrokes.
- **CSP may block write operations** on security-conscious sites. Fall back to `System Events` (`keystroke`, `click at {x, y}`).
- **Chrome must be running** on Mac with the target site logged in.
- **Only one active tab** per `execute active tab of first window`. Use `set active tab index` to switch.

### Form Filling via AppleScript (non-React)

```bash
ssh mac 'osascript << '"'"'EOF'"'"'
tell application "Google Chrome"
  execute active tab of front window javascript "
    function setVal(el, val) {
      var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, '"'"'value'"'"');
      if (s) s.set.call(el, val);
      el.dispatchEvent(new Event('"'"'input'"'"', {bubbles: true}));
      el.dispatchEvent(new Event('"'"'change'"'"', {bubbles: true}));
    }
    setVal(document.getElementById('"'"'firstname'"'"'), '"'"'Terry'"'"');
    '"'"'done'"'"';
  "
end tell
EOF'
```

---

Site-specific login flows, gotchas, and credentials → see [sites.md](sites.md)

---

## Soma (Linux) Compatibility

- `caffeinate` is macOS-only — chemotaxis.py guards with `sys.platform == "darwin"` (fixed 2026-04-02)
- After editing chemotaxis.py or other enzymes, must restart vivesca MCP (kill PID or SIGHUP)
- `__pycache__` clearing alone doesn't help — the MCP process has bytecode in memory
- Headed mode requires Xvfb (`Xvfb :99 &`), no VNC available for visual interaction

## Profile & Maintenance

- Profile data: `~/.agent-browser-profile/`
- Backup: `~/officina/browser-profile/`
- After agent-browser updates: `npx playwright install chromium`
- Per-session profiles: `AGENT_BROWSER_SESSION=cc-$TMUX_WINDOW`
- `--profile` flag: use `agent-browser close` first to restart with new options

## Useful Commands

```bash
agent-browser get title          # page title
agent-browser get url            # current URL
agent-browser get text body      # full page text
agent-browser eval "JS"          # run JS
agent-browser scroll down 500    # scroll
agent-browser press Enter        # keyboard
agent-browser screenshot         # capture
agent-browser tab list           # list tabs
agent-browser upload "sel" "/path"  # file upload
```

## Motifs
- [escalation-chain](../motifs/escalation-chain.md)
- [state-branch](../motifs/state-branch.md)
