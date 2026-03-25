---
title: URL Content Archival with Local Images
date: 2026-02-05
problem_type: feature_implementation
category: skills
tags: [web-scraping, obsidian, archival, images, jina-reader]
severity: low
source: "@yhslgg X thread"
---

# URL Content Archival with Local Images

## Problem

When archiving web articles to Obsidian, external image URLs eventually break (link rot). Need a way to download images locally and rewrite markdown paths.

## Solution

Created `/archive-article` skill that:

1. Fetches content via Jina Reader (`https://r.jina.ai/{url}`)
2. Extracts image URLs from markdown (standard `![](url)` and HTML `<img>`)
3. Downloads images with platform-specific headers
4. Rewrites paths to local `./images/img_01.jpg` format
5. Saves to `~/notes/Archive/{date}_{slug}/` structure

### Key Code Pattern

```python
def get_headers_for_url(url: str) -> dict:
    """Get appropriate headers based on image URL domain."""
    headers = {"User-Agent": USER_AGENT}

    if "xhscdn.com" in url or "xiaohongshu.com" in url:
        headers["Referer"] = "https://www.xiaohongshu.com/"
    elif "mmbiz.qpic.cn" in url or "weixin.qq.com" in url:
        headers["Referer"] = "https://mp.weixin.qq.com/"

    return headers
```

### Title Extraction Gotcha

Jina Reader returns `Title: xxx` format, not `# H1` markdown. Need to check both:

```python
# Try Jina format first: "Title: xxx"
match = re.search(r'^Title:\s*(.+)$', content, re.MULTILINE)
if match:
    return match.group(1).strip()

# Fallback to H1 markdown: "# Title"
match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
```

## Usage

```bash
# Archive directly from URL (auto-fetches via Jina)
python ~/skills/archive-article/archive.py --url "https://example.com/article"

# With pre-fetched content
python ~/skills/archive-article/archive.py --url "..." --content "$content"

# With explicit title
python ~/skills/archive-article/archive.py --url "..." --title "My Title"
```

## Output Structure

```
~/notes/Archive/
└── 2026-02-05_article-title-slug/
    ├── content.md      # Article with local image paths
    └── images/
        ├── img_01.jpg
        ├── img_02.png
        └── ...
```

## Platform Limitations

| Platform | Jina Reader | Notes |
|----------|-------------|-------|
| General web | ✅ Works | Default fallback |
| WeChat | ❌ Fails | Use `wechat-article` skill instead |
| Xiaohongshu | ⚠️ Needs testing | Images need Referer header |
| Login-required | ❌ Fails | Use browser automation |

## Related

- `content-fetch` skill — Fallback hierarchy documentation
- `wechat-article` skill — WeChat-specific extraction
- `summarize` skill — Content summarization (no archival)

## Source

Pattern adapted from [@yhslgg's URL reader skill thread](https://x.com/yhslgg/status/2018951488488513621) which uses Firecrawl → Jina → Playwright cascade.
