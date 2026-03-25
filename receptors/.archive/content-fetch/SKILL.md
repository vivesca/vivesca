---
name: content-fetch
description: Reference for URL fetching patterns and fallbacks. Consult when extracting content from web URLs.
user_invocable: false
---

# Content Fetch

Patterns for fetching and extracting content from URLs.

## Tool Selection

| URL Type | Primary Tool | Fallback |
|----------|--------------|----------|
| General web | `WebFetch` | Jina Reader |
| WeChat articles | `summarize --extract` CLI | Jina Reader, manual copy |
| YouTube | `summarize` | yt-dlp |
| PDFs | `pdf-extract` (LlamaParse) | Local OCR |
| Xiaohongshu (XHS) | `xhs-extract` script | Playwright MCP |
| Login-required | Browser automation | None |

## WebFetch Patterns

```
WebFetch(url, prompt="Extract the main content")
```

**Handles:**
- HTML → Markdown conversion
- Redirect following (returns redirect URL if different host)
- 15-minute cache

**Gotchas:**
- Fails on authenticated pages (Google Docs, Confluence, Jira)
- Use `ToolSearch` first to find specialized MCP tools

## Redirect Handling

When WebFetch returns a redirect message:
1. Extract the redirect URL from response
2. Make a new WebFetch request with that URL
3. Don't assume original URL worked

## WeChat URL Patterns

| Pattern | Type | Handling |
|---------|------|----------|
| `mp.weixin.qq.com/s/...` | Short URL | Fetch directly |
| `mp.weixin.qq.com/s?__biz=...` | Long URL | Fetch directly |
| `weixin.qq.com/r/...` | QR redirect | Follow redirect first |

## Error Handling

| Error | Meaning | Action |
|-------|---------|--------|
| `INVALID_URL` | Malformed URL | Check URL format |
| `POOR_CONTENT_QUALITY` | Extraction failed | Try Jina Reader or browser automation |
| 404 | Page not found | URL may have expired |
| 429 | Rate limited | Wait and retry |
| Login wall | Requires auth | Use browser automation |

## Fallback Hierarchy

```
1. WebFetch (fast, cached)
   ↓ fails
2. Jina Reader (free, simple)
   ↓ fails
3. Browser automation (for login-required or complex pages)
   ↓ fails
4. Ask user for copy/paste
```

### Jina Reader

Free, no API key. Prepend `https://r.jina.ai/` to any URL:

```bash
curl -s -H "Accept: text/markdown" "https://r.jina.ai/https://example.com/article"
```

**Handles:** Most general web pages, blogs, docs
**Fails on:** WeChat, login-required sites, some anti-scrape sites

## Login-Required Sites

These always need browser automation:
- LinkedIn (job pages, profiles)
- X/Twitter
- WhatsApp Web
- Most banking/corporate sites

## Chinese Platform Gotchas

### WeChat (mp.weixin.qq.com)

**Primary:** `summarize` CLI — bypasses WeChat CAPTCHA where WebFetch and Jina fail.

```bash
# Extract text only (no LLM summary)
summarize "https://mp.weixin.qq.com/s/ARTICLE_ID" --extract-only --model anthropic/claude-sonnet-4

# With summary
summarize "https://mp.weixin.qq.com/s/ARTICLE_ID" --model anthropic/claude-sonnet-4
```

**Why it works:** Uses a Chrome 123 User-Agent string (`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...`) with standard Node.js fetch. WebFetch and Jina use bot-like UAs that trigger WeChat's CAPTCHA. If the Chrome UA also gets blocked, `summarize` auto-falls back to Firecrawl (needs `FIRECRAWL_API_KEY`).

**Note:** `wechat-article` script (wechat.imagenie.us API) is dead (404 as of Feb 2026).

**Backup options:**
1. **Firecrawl** — AI-driven, paid (500 free/month). Configure: `export FIRECRAWL_API_KEY=...`
2. **Mirror search** — Articles often reposted to zhihu.com, 163.com, csdn.net

**URL tip:** Short URLs (`/s/ABC123`) more stable than long URLs (`?__biz=...`) which trigger CAPTCHAs.

### Xiaohongshu (小红书)

Images require Referer header or you get 403:

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)...',
    'Referer': 'https://www.xiaohongshu.com/'
}
requests.get(image_url, headers=headers)
```

### Douyin / Bilibili

Require browser automation for most content. Heavy anti-scrape.

## Content Extraction Prompts

**For articles:**
```
"Extract the main article content, including title, author, date, and body text"
```

**For job postings:**
```
"Extract job title, company, location, requirements, responsibilities, and salary if disclosed"
```

**For documentation:**
```
"Extract the technical documentation, including code examples"
```

## Related Skills

- `analyze` — Article evaluation workflow (replaced evaluate-article)
- `wechat-article` — WeChat-specific extraction
- `summarize` — Content summarization including YouTube transcripts
- `pdf-extract` — PDF text extraction
- `chrome-automation` — Browser fallback patterns
