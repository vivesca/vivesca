---
name: wechat-article
description: Fetch and read WeChat public article content (mp.weixin.qq.com URLs). Use when needing to extract text from a WeChat article link.
user_invocable: false
---

# WeChat Article Fetching

## TL;DR

```bash
exauro contents "https://mp.weixin.qq.com/s/..."
```

That's the best tool. Everything else fails.

## Tool Comparison

| Tool | Result |
|------|--------|
| `exauro contents <url>` | **Works** for most articles (~80% success) |
| `defuddle parse <url>` | Blocked — returns empty/stub content |
| `peruro <url>` | Blocked — WeChat CAPTCHA |
| `WebFetch` | Blocked — WeChat CAPTCHA ("环境异常") |
| `qianli read <url>` | Fails — "failed to extract page content" |
| `qianli wechat "keywords"` | Returns Sogou search snippets only — no full text |

## When exauro fails

Some articles still return no content (Exa hasn't indexed them). Options:

1. **Search by title** — `qianli wechat "article title keywords"` for snippets
2. **Find mirrors** — `exauro search "article title"` — sometimes picked up by aggregators
3. **Accept the gap** — note as "not fetched" and move on

## Batch processing

For multiple WeChat URLs, run in parallel:

```bash
exauro contents "https://mp.weixin.qq.com/s/url1" &
exauro contents "https://mp.weixin.qq.com/s/url2" &
wait
```

## Validated

Confirmed working: 2026-03-07. 4/7 WeChat articles fetched successfully via `exauro contents` in AI x Finance digest session.
