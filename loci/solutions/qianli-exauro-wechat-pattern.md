# LRN-20260307-001: Exa indexes WeChat (and 36kr)

**Date:** 2026-03-07
**Context:** Refactoring qianli to remove CDP Chrome dependency

## Finding

Exa neural search API indexes `mp.weixin.qq.com` (WeChat 公众号) and `36kr.com` directly.
Use `site:` operator in the query string:

```bash
exauro search "AI 银行 site:mp.weixin.qq.com" --search-type auto
exauro search "大模型 site:36kr.com" --search-type auto
```

Returns real mp.weixin.qq.com URLs with Chinese-language summaries. No Sogou, no browser, no auth.

## What failed first

- Sogou via CDP Chrome: works but requires permanent Chrome daemon (fragile)
- Playwright/agent-browser on Sogou: anti-spider blocks headless browsers
- agent-browser on 36kr: anti-bot returns empty DOM even with 25s wait
- porta inject for Sogou cookies: no Sogou cookies in regular Chrome (only in CDP Chrome profile)

## Pattern

When browser automation hits anti-bot: check if a search API (Exa, Perplexity) already indexes the target. `site:` filtering works. Neural ranking often better than keyword search for research use cases.

## Also fixed

- exauro CJK panic: `&summary[..197]` → `summary.chars().take(100).collect::<String>()`
- phron workspace conflict: bare `[workspace]` in phron/Cargo.toml conflicted with ~/code/Cargo.toml
