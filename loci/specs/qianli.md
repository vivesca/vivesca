# qianli (千里) — Chinese Platform Search CLI

## Purpose

Unified CLI for searching Chinese content platforms from the terminal. Covers WeChat 公众号 (via Sogou), 36kr (36氪), Xiaohongshu (小红书), and Zhihu (知乎). Two backends: direct CDP websocket for fast sources, MediaCrawler subprocess for authenticated platforms.

Designed for research workflows: called via Bash when needed, zero token overhead when not (no MCP).

## Architecture (v0.2.0, Feb 2026)

```
PyPI: qianli (0.2.0) — pip install qianli
GitHub: github.com/terry-li-hm/qianli
Source: ~/code/qianli/src/qianli/
Entry point: qianli
```

Two backends:

### CDP Direct (wechat, 36kr)
- `cli.py`: subcommands via argparse
- Open tab via CDP websocket → wait for SPA render → evaluate JS extractor → parse JSON → close tab
- Fast: 4-18s per search

### MediaCrawler Subprocess (xhs, zhihu)
- `mc.py`: wraps `~/code/MediaCrawler` as subprocess
- Patches `CRAWLER_MAX_NOTES_COUNT` in config (restored in finally)
- Runs with MC's own venv python, reads JSON output from temp dir
- Normalizes MC output to qianli's result format
- Slower: 30-60s per search

### Why this hybrid approach

Direct CDP is fast but XHS anti-bot kills websocket for ALL tabs (not just its own). Zhihu blocks CDP `Runtime.evaluate` entirely. MediaCrawler (44k stars, active) handles both via Playwright+CDP with proper anti-detection. Using it as a subprocess keeps qianli's core simple while gaining robust XHS/Zhihu support.

## Sources

| Source | Backend | Auth | Status | Speed |
|--------|---------|------|--------|-------|
| **WeChat** (公众号) | CDP direct | No | Working | ~4-12s |
| **36kr** (36氪) | CDP direct | No | Working (CAPTCHA at high volume) | ~6-18s |
| **XHS** (小红书) | MediaCrawler | Yes (QR) | Working (1-2/day safe) | ~30-60s |
| **Zhihu** (知乎) | MediaCrawler | Yes (QR) | Available (may be unreliable) | ~30-60s |

### Evaluated and dropped
- **Huxiu (虎嗅)** — SPA, not URL-addressable. Indexed by Sogou.
- **Weibo** — entertainment-heavy, low signal.

## Usage

```bash
# Fast CDP sources
qianli wechat "AI 银行 香港"
qianli 36kr "大模型 金融"

# MediaCrawler sources (requires first-run QR auth)
qianli xhs "AI banking Hong Kong"
qianli zhihu "大模型 金融应用"

# Aggregate (wechat + 36kr only, skips slow sources)
qianli all "AI banking"

# Read page content
qianli read <url>

# JSON output
qianli xhs "AI" --limit 3 --json
```

## Search Options

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | 5 (3 for `all`) | Max results per source |
| `--json` | false | JSON output |

## Output Format

Default: compact text. `--json` for structured output.

```
[wechat] 香港金管局GenAI沙盒首批成果发布
         机器之心 · 2025-11-15
         https://mp.weixin.qq.com/s/xxx

[xhs] AI驱动的银行客服新时代
      @fintech_hk · 2025-12-01 · ❤ 1.2k
      https://www.xiaohongshu.com/explore/abc123
```

## Prerequisites

- CDP Chrome running (port 9222) — `open "/Applications/Chrome CDP.app"`
- MediaCrawler at `~/code/MediaCrawler` with `.venv` (for xhs/zhihu)
- XHS/Zhihu: first-run QR auth via MediaCrawler `--headless false`

## Dependencies

- `websockets` (Python, pip dep)
- CDP Chrome on port 9222
- `~/code/MediaCrawler` + venv (external, not a pip dep)
- Python 3.11+

## Snapshot DOM Structures (confirmed Feb 14, 2026)

### Sogou WeChat
Sample: `~/docs/specs/qianli-samples/sogou-wechat.txt`
Key fields: heading text (title), link URL (Sogou redirect), paragraph text (snippet), trailing text (account + date).

### 36kr
Sample: `~/docs/specs/qianli-samples/36kr.txt`
Key fields: first link text (title), `/p/ID` URL, last link text (snippet), trailing text (date).

## Known Risks

1. **DOM changes.** WeChat/36kr extractors rely on page structure.
2. **Sogou redirect expiry.** Temp redirect links expire.
3. **36kr SPA load time.** 12-18s wait. Intermittent failures.
4. **XHS anti-bot.** Conservative pacing required. MediaCrawler handles better than raw CDP.
5. **Zhihu anti-detection.** May still be unreliable.
6. **Config patching race.** mc.py patches MediaCrawler config temporarily. Don't run concurrent MC searches.
7. **Rate limiting.** All platforms throttle. Few searches/day is safe.

## Not in Scope

- Publishing/posting
- Image/video download
- Profile scraping
- Scheduled/batch operations
- MCP server mode

## Next Steps

- [x] WeChat + 36kr via direct CDP (v0.1.0)
- [x] Packaged on PyPI (v0.1.1, Feb 14)
- [x] XHS + Zhihu via MediaCrawler backend (v0.2.0, Feb 14)
- [ ] First-run QR auth for XHS + Zhihu (Terry, manual)
- [ ] Publish v0.2.0 to PyPI
