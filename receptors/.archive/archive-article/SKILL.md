---
name: archive-article
description: Archive web articles to Obsidian with local images. Use when user wants to save an article permanently with images downloaded locally.
user_invocable: true
---

# Archive Article

Save web articles to Obsidian vault with images downloaded locally to prevent link rot.

## When to Use

- User wants to permanently save an article
- Content has images that might disappear
- Building a knowledge base / reference library

## Usage

### From Claude Code

```bash
# Archive with content already fetched
python ~/skills/archive-article/archive.py --url "https://example.com/article" --content "$(cat article.md)"

# Archive from URL (fetches content first)
python ~/skills/archive-article/archive.py --url "https://example.com/article"

# With custom title
python ~/skills/archive-article/archive.py --url "https://example.com/article" --title "My Article Title"
```

### Typical Workflow

1. Fetch content using WebFetch, Jina, or specialized tool
2. Pass to archive.py with source URL
3. Script downloads images, rewrites paths, saves to vault

```bash
# Example: Archive a blog post
content=$(curl -s "https://r.jina.ai/https://blog.example.com/post" -H "Accept: text/markdown")
python ~/skills/archive-article/archive.py --url "https://blog.example.com/post" --content "$content"
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

## Frontmatter

Saved articles include:

```yaml
---
title: Article Title
source: https://original.url/path
archived: 2026-02-05T13:30:00+08:00
---
```

## Platform-Specific Headers

The script automatically sets correct headers for:
- **Xiaohongshu**: `Referer: https://www.xiaohongshu.com/`
- **WeChat**: `Referer: https://mp.weixin.qq.com/`
- **General**: Standard User-Agent

## Dependencies

```bash
uv pip install httpx python-slugify
```
