---
module: Browser Automation
date: 2026-02-06
problem_type: ui_bug
component: browser_automation
symptoms:
  - "XHS Python script returns empty __INITIAL_STATE__ with all fields blank"
  - "requests/curl returns '当前内容仅支持在小红书 APP 内查看' (view in app)"
  - "xsec_token in URL does not help — same wall with or without it"
  - "OG meta tags only contain generic 小红书 branding, not post content"
root_cause: mental_model_error
resolution_type: tool_switch
severity: medium
tags: [xhs, xiaohongshu, playwright, scraping, anti-bot, chinese-platforms, initial-state]
related_files:
  - ~/scripts/xhs_extract.py
  - ~/skills/xhs-extract/SKILL.md
---

# XHS (小红书) Requires Real Browser for Content Extraction

## Problem

Building an XHS post extractor, the Python script (`requests` + BeautifulSoup) found
`window.__INITIAL_STATE__` in the page HTML but all fields were empty. Even with the
`xsec_token` query parameter, the server returns skeleton HTML with a "view in app"
message instead of actual post content.

## Wrong Assumption

"XHS embeds post data in `__INITIAL_STATE__` JSON, so we can parse it with requests."

**Reality:** XHS is a fully JS-rendered SPA. The `__INITIAL_STATE__` structure exists
in the SSR shell, but the actual note data (noteDetailMap) is only populated after
client-side JavaScript executes. No amount of headers, cookies, or tokens makes
`requests` work — you need a real browser JS runtime.

## What Didn't Work

1. **requests + mobile User-Agent** → Returns "当前内容仅支持在小红书 APP 内查看"
2. **requests + xsec_token** → Same wall
3. **Parsing `__INITIAL_STATE__`** → Structure exists but noteDetailMap is empty
4. **Meta/OG tags** → Only generic "小红书" branding, no post-specific content

## What Works

**Playwright MCP** (`browser_evaluate` with Chrome extension mode):

```
1. browser_navigate → XHS URL (with xsec_token if available)
2. browser_evaluate → JS that reads window.__INITIAL_STATE__.note.noteDetailMap
3. Parse returned JSON for title, desc, author, tags, imageList, interactInfo
```

The `__INITIAL_STATE__` is fully populated in the browser context because JS has
executed. One navigate + one evaluate = complete extraction.

**Key JS path:** `window.__INITIAL_STATE__.note.noteDetailMap[firstKey].note`

Fields available: `title`, `desc`, `user.nickname`, `tagList[].name`,
`imageList[].urlDefault`, `interactInfo.{likedCount,collectedCount,commentCount}`,
`type` ("normal" for photos, "video" for video posts).

## Image Downloads

XHS CDN requires `Referer: https://www.xiaohongshu.com/` header or returns 403.
The image URLs from `imageList` are temporary signed URLs (contain timestamps in path).

```bash
curl -o image.jpg \
  -H "Referer: https://www.xiaohongshu.com/" \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X)..." \
  "<image_url>"
```

## Login Modal

XHS shows a "登录继续查看该笔记" (login to continue) modal overlay, but the actual
content renders behind it. The `browser_evaluate` JS can read the data without
dismissing the modal.

## Prevention / Pattern

**For any Chinese social platform (XHS, Douyin, Bilibili):** assume JS rendering
is required. Don't waste time on requests-based approaches. Go straight to Playwright.

The Python script still has value as a fast-path attempt — it exits with code 1 in
~2 seconds when blocked, which is faster than discovering the wall through Playwright.
But treat Playwright as the primary path, not the fallback.

## Generalisation

This pattern applies to all modern JS-heavy SPAs with anti-scraping:

| Platform | requests works? | Playwright needed? |
|----------|:--------------:|:-----------------:|
| XHS (小红书) | No | Yes |
| Douyin (抖音) | No | Yes |
| Bilibili | Partial | For protected content |
| WeChat articles | Yes (via API) | No |
| LinkedIn | No | Yes |
