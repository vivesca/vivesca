---
name: qianli
description: Search Chinese content platforms (WeChat, 36kr, Zhihu, XHS) from the terminal. Use when searching for Chinese-language content or community discussions.
user_invocable: true
trigger: "/qianli"
---

# qianli

Search Chinese content platforms from the terminal.

## Trigger

User says "qianli", "chinese search", "search xhs", "search wechat", "search zhihu", "search 36kr", or wants Chinese-language content research.

## User-invocable

Yes. `/qianli`

## Usage

```bash
# Exa-backed (fast, no browser needed)
qianli wechat "AI 银行"          # WeChat 公众号 via Exa neural search
qianli 36kr "大模型 金融"         # 36kr tech news via Exa

# MediaCrawler sources (subprocess, 30-60s)
qianli xhs "AI banking"          # Xiaohongshu (requires first-run QR auth)
qianli zhihu "人工智能"           # Zhihu Q&A (requires first-run QR auth)

# Aggregate (wechat + 36kr only, fast)
qianli all "AI"

# Read page content via agent-browser
qianli read <url>
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | 5 (3 for `all`) | Max results per source |
| `--json` | false | JSON output instead of text |

## Architecture

Three backends:
- **Exa** (wechat, 36kr): Calls `exauro search "query site:mp.weixin.qq.com"` or `site:36kr.com`. Fast, no browser, no CDP Chrome. Neural search finds semantically related content.
- **agent-browser** (read): Opens URL in Playwright browser, extracts page text.
- **MediaCrawler** (xhs, zhihu): Runs `~/code/MediaCrawler` as subprocess with its own venv. Patches `CRAWLER_MAX_NOTES_COUNT` for limit, reads JSON output from temp dir.

**No CDP Chrome required.** CDP Chrome dependency was removed Mar 2026.

## Prerequisites

- `exauro` binary in PATH (`~/bin/exauro`) with `EXA_API_KEY` set
- `agent-browser` for `qianli read` only
- MediaCrawler installed at `~/code/MediaCrawler` with `.venv`
- XHS/Zhihu: first-run QR auth (see below)

## First-run auth (XHS/Zhihu)

Run once with `--headless false` to scan QR code in browser window:

```bash
cd ~/code/MediaCrawler && .venv/bin/python main.py \
  --platform xhs --type search --keywords "test" --headless false
```

## Gotchas

- `all` runs wechat + 36kr only (xhs/zhihu too slow for aggregation)
- XHS anti-bot: conservative pacing, 1-2 searches/day
- Zhihu: may still be unreliable depending on anti-bot state
- MediaCrawler patches config file temporarily (restored in finally block)
- **Exa coverage:** Indexes WeChat 公众号 and 36kr well. Results are semantically ranked, not chronological — for latest news use `noesis search` in Chinese instead.
- **36kr anti-bot (Mar 2026):** 36kr blocks headless Playwright (empty page). Exa is the only reliable 36kr search backend. Do NOT attempt agent-browser for 36kr.
- **Sogou removed (Mar 2026):** WeChat search previously used Sogou via CDP Chrome. Replaced by Exa which is faster, requires no browser, and returns semantic results.

## Source

- CLI: `~/code/qianli/src/qianli/cli.py`
- MC backend: `~/code/qianli/src/qianli/mc.py`
- MediaCrawler: `~/code/MediaCrawler/`

## Triggers

- qianli
- search wechat
- chinese content
- 36kr
- zhihu
- xhs
