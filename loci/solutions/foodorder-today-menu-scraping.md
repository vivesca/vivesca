# foodorder.today Menu Scraping

How to extract menus from 世通線上自助點餐系統 (foodorder.today POS) via CDP.

## When to Use

User shares a `foodorder.today/PosWMemServ/WMemProcess?func=s&appid=...` URL and wants the menu extracted.

## Key Facts

- **Framework:** uni-app (Vue-based SPA). WebFetch won't work — needs JS rendering via CDP.
- **Page navigates on load** — `agent-browser open` gets "Execution context was destroyed". Must use `eval` to navigate then snapshot separately.
- **Overlay ad on landing page** — blocks the "開始點餐" button. Dismiss `.overlayBG` first.
- **Virtualized scroll** — menu items render on demand per category. Can't just scroll to bottom.
- **Category sidebar** — `uni-scroll-view[0]` has category `uni-text` elements. `uni-scroll-view[1]` has menu items.

## Extraction Steps

### 1. Navigate (handle redirect)
```bash
agent-browser --cdp 9222 eval "window.location.href = '<URL>'" 2>&1
sleep 12
agent-browser --cdp 9222 snapshot
```

### 2. Dismiss overlay
```bash
agent-browser --cdp 9222 eval "document.querySelector('.overlayBG')?.querySelector('*')?.click()"
```

### 3. Click "開始點餐"
```bash
agent-browser --cdp 9222 click ".startText"
```
If blocked by overlay, re-dismiss then retry.

### 4. Extract menu category-by-category

Write these two JS helpers to `/tmp/`:

**`/tmp/click-cat.js`** — clicks next category (tracks index via `window.__catIdx`):
```js
(() => {
  const catSv = document.querySelectorAll('uni-scroll-view')[0];
  const catTexts = catSv.querySelectorAll('uni-text');
  const idx = parseInt(window.__catIdx || '0');
  if (idx < catTexts.length) {
    catTexts[idx].click();
    window.__catIdx = idx + 1;
    return 'clicked: ' + catTexts[idx].textContent.trim();
  }
  return 'done';
})()
```

**`/tmp/read-items.js`** — reads items from current category view:
```js
(() => {
  const menuSv = document.querySelectorAll('uni-scroll-view')[1];
  const items = [];
  const seen = new Set();
  menuSv.querySelectorAll('uni-view').forEach(el => {
    const text = el.textContent?.trim();
    if (text && text.includes('$') && text.length < 120 && text.length > 8) {
      const clean = text.replace(/\+\s*加入/g, '').replace(/\s+/g, ' ').trim();
      const prices = clean.match(/\$\d+\.\d+/g);
      if (prices && prices.length === 1 && !seen.has(clean)) {
        seen.add(clean);
        items.push(clean);
      }
    }
  });
  return JSON.stringify(items);
})()
```

**Shell loop** — iterate categories with 1.5s delay:
```bash
#!/bin/bash
categories=(...) # from snapshot sidebar text
for i in "${!categories[@]}"; do
  agent-browser --cdp 9222 eval "$(cat /tmp/click-cat.js)" 2>/dev/null
  sleep 1.5
  items=$(agent-browser --cdp 9222 eval "$(cat /tmp/read-items.js)" 2>/dev/null)
  echo "\"${categories[$i]}\": $items,"
done
```

### 5. Save to vault

Save to `~/notes/<Restaurant Name> Menu.md` with categories, items, and prices.

## Gotchas

- **Don't use async eval** — long-running async functions cause agent-browser daemon timeouts (resource error 35). Use the shell loop approach instead.
- **Shell quoting** — write JS to `/tmp/*.js` files, then `$(cat /tmp/file.js)`. Inline JS in bash breaks on `$` signs and quotes.
- **Items repeat across categories** — the same platter may appear in both "Specials" and "Seafood". Deduplicate at the vault note level if desired.
- **Tea drinks may show $0.00** — these are included free with the meal (CouCou's signature).
- **Token URL is session-bound** — the `Token=` parameter in the URL is time-limited. Extract promptly after receiving.

## Related Skills
- `browser-automation` — CDP setup and agent-browser reference
