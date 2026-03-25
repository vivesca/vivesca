# Telegram Web Automation via Chrome CDP

## What Works

**Session transfer:** Copy Chrome's profile after a clean quit (not kill) so LevelDB WAL flushes to disk. Then launch Chrome with `--remote-debugging-port=9222 --user-data-dir=/tmp/chrome-tg`. Playwright can connect via `connect_over_cdp("http://localhost:9222")` and Telegram Web will be logged in.

```bash
osascript -e 'quit app "Google Chrome"'
sleep 4
cp -r ~/Library/Application\ Support/Google/Chrome/Default /tmp/chrome-tg/Default
nohup /tmp/launch_chrome_debug.sh > /dev/null 2>&1 &
# launch_chrome_debug.sh: chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-tg
```

**Navigating to a chat:** `page.goto("https://web.telegram.org/k/#@BotFather")` triggers search — does NOT open the chat directly. Press `Escape` to dismiss search overlay. The chat composer becomes visible if the target was previously opened.

**Sending messages:** `.input-message-input[contenteditable]` is the composer selector.

**BotFather bot creation:** `/newbot` → bot name → username (must end in `bot`). Token in response matches `\d{8,12}:[A-Za-z0-9_-]{35,}`. If username taken, retry with alternatives.

## What Doesn't Work

- **URL hash navigation as chat opener:** `#@username` just searches, doesn't open the chat directly in the SPA.
- **Inline keyboard buttons:** BotFather's `/mybots` inline keyboard buttons are NOT standard `<button>` elements. They don't appear in `.reply-markup-button` queries. Not yet solved.
- **Copying IndexedDB while Chrome is running:** LevelDB WAL not flushed → session not transferred. Must quit Chrome cleanly first.
- **Bot username change:** `/setusername` is not a BotFather command. Username can't be changed via CLI automation (inline keyboard required).

## New Bot Activation

New bots require the user to send at least one message (`/start`) before the bot can message them. "chat not found" (400) = bot not yet started by user.

## Naming Convention

Terry prefers CamelCase bot usernames: `PhemeBot`, `ComesBot`, etc. Telegram requires username ends in `bot` (case-insensitive). Check availability first — common names taken.
