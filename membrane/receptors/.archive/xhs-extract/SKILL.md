---
name: xhs-extract
description: Extract text and images from Xiaohongshu (小红书/XHS) post URLs. Use when user shares an XHS link or says "xhs", "xiaohongshu", "小红书".
user_invocable: true
---

# XHS Post Extractor

Extract text content (title, body, tags, stats) and images from Xiaohongshu posts.

## Trigger

Use when:
- User shares an XHS / Xiaohongshu / 小红书 URL
- User says "extract xhs", "parse xhs", "xhs post"
- URL matches `xiaohongshu.com` or `xhslink.com`

## URL Formats

| Format | Example | Notes |
|--------|---------|-------|
| **Explore** | `xiaohongshu.com/explore/{24-char-hex}` | Standard web URL |
| **Discovery** | `xiaohongshu.com/discovery/item/{id}` | Older format |
| **User profile** | `xiaohongshu.com/user/profile/{author}/{id}` | Author-scoped |
| **Short link** | `xhslink.com/{code}` or `xhslink.com/a/{code}` | Share links from app |

Short links: resolve manually with `curl -sI <url> | grep -i location` or let the script handle it.

## Workflow

**XHS requires a real browser** — plain HTTP requests always hit "view in app" walls.
Playwright MCP (with Chrome extension mode) is the primary extraction method.

### Step 1: Playwright MCP (primary)

```
1. browser_navigate → the XHS URL (include xsec_token if present)
2. browser_evaluate → run extraction JS below
3. Parse the returned JSON
4. Download images with curl (Referer header required)
```

**Extraction JS for browser_evaluate:**

```javascript
() => {
  const result = {};
  if (window.__INITIAL_STATE__) {
    const state = window.__INITIAL_STATE__;
    const noteMap = state?.note?.noteDetailMap;
    if (noteMap) {
      const first = Object.values(noteMap)[0]?.note;
      if (first) {
        result.title = first.title || '';
        result.description = first.desc || '';
        result.author = first.user?.nickname || '';
        result.tags = (first.tagList || []).map(t => '#' + t.name);
        result.images = (first.imageList || []).map(i =>
          (i.urlDefault || i.url || '').replace(/^\/\//, 'https://')
        );
        result.likes = first.interactInfo?.likedCount || '';
        result.collects = first.interactInfo?.collectedCount || '';
        result.comments = first.interactInfo?.commentCount || '';
        result.type = first.type || '';
        return JSON.stringify(result, null, 2);
      }
    }
  }
  // Fallback: DOM scraping
  const title = document.querySelector('#detail-title')?.innerText
    || document.querySelector('[class*="title"]')?.innerText || '';
  const desc = document.querySelector('#detail-desc')?.innerText
    || document.querySelector('[class*="note-content"]')?.innerText || '';
  const imgs = [...document.querySelectorAll('[class*="note"] img, [class*="slide"] img')]
    .map(i => i.src || i.dataset?.src).filter(Boolean);
  const tags = [...document.querySelectorAll('a[class*="tag"]')]
    .map(a => a.innerText.trim()).filter(t => t.startsWith('#'));
  result.title = title;
  result.description = desc;
  result.images = imgs;
  result.tags = tags;
  return JSON.stringify(result, null, 2);
}
```

### Step 2: Download images

XHS CDN requires `Referer` header or returns 403.

```bash
curl -o "image_1.jpg" \
  -H "Referer: https://www.xiaohongshu.com/" \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15" \
  "<image_url>"
```

Or use the script's download helper:

```bash
uv run ~/scripts/xhs_extract.py "<url>" --output-dir ~/Downloads
```

### Step 3: Fallbacks

**If Playwright fails** (login modal blocks content):
- Close the login modal: `browser_click` on the close button (usually an X icon)
- Or use `/agent-browser` for visual navigation
- Or take a `browser_take_screenshot` and read the image directly

### Python Script (optional fast path)

Rarely works due to XHS anti-scraping, but worth a quick try:

```bash
uv run ~/scripts/xhs_extract.py "<url>" --no-images --json 2>&1
```

- Resolves short links, tries `__INITIAL_STATE__` then meta tags
- Detects "view in app" walls and exits with code 1
- If it succeeds (exit 0), it's faster than Playwright
- Options: `--output-dir <dir>`, `--no-images`, `--json`

## Output

**From Playwright:** JSON string with title, description, author, tags, images, likes, collects, comments.

**From script (markdown):** Title, author, stats, body text, tags, image links.

**From script (--json):** Structured dict with all fields.

**Images:** Save to `~/Downloads/xhs_{note_id}/` or specified dir.

## Error Handling

| Symptom | Cause | Action |
|---------|-------|--------|
| "登录继续查看该笔记" | Login wall | Close modal, content is behind it |
| Script exits 1 | Anti-scraping wall | Use Playwright (expected) |
| Image 403 | Missing Referer | Add `-H "Referer: https://www.xiaohongshu.com/"` |
| Short URL timeout | Expired share link | Ask user for full explore URL |
| Empty `__INITIAL_STATE__` | No cookies/session | Normal for requests; Playwright has session |

## Key Insight

XHS is a fully JS-rendered SPA. `requests`/`curl` get a skeleton HTML with "view in app" message. The actual content only loads via JavaScript in a browser context. **Always prefer Playwright for XHS.**

## Related

- `content-fetch` — General URL extraction (has XHS Referer note)
- `wechat-article` — Similar pattern for WeChat articles
- `archive-article` — Save to Obsidian with local images
