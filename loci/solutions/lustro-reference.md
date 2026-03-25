# Lustro Reference

CLI for surveying the AI/tech landscape. Project: `~/code/lustro`.

## Source Health

- **Run `lustro check` monthly.** ~12% source rot rate per quarter (17/138 broken Feb 2026). Main cause: site migrations (Substack, Medium slug changes, domain moves), not content death.
- **`feedparser` silent failure:** `feedparser.parse()` on a 404 returns a valid object with `entries = []`. No exception. Must check `feed.bozo` + `feed.status` to detect dead feeds. Fixed in fetcher.py Feb 2026 (returns `None` for dead feeds, `[]` for healthy-but-empty).
- **RSS→web fallback:** If `fetch_rss` returns `None` and source has a `url` key, falls back to `fetch_web`. Added Feb 2026.
- **Consecutive-zero tracking:** State tracks `_zeros:<name>` counter. Warns at >=5 consecutive zero-article fetches.

## Full Content Fetch Modes

Some RSS feeds only provide stubs (45 chars). Two modes to get full content:

### `full_fetch: true`
Uses trafilatura to follow each entry's article URL. Works for public static HTML.
```yaml
- name: Some Blog
  rss: https://example.com/feed
  full_fetch: true
```
- Fast, no browser overhead
- Fails on JS-rendered or Cloudflare-protected pages

### `stealth_fetch: true`
Uses nodriver (stealth Chrome) to bypass Cloudflare + render JS. Takes priority over `full_fetch`.
```yaml
- name: AIGC Weekly (歸藏)
  rss: https://quaily.com/op7418/feed/atom
  stealth_fetch: true
```
- Slow (~5-8s per article, Chrome launch)
- Requires a one-time headed login to persist session in `~/.config/lustro/nodriver-profile/`
- Session expires after weeks/months — refresh by re-running headed login:
  ```bash
  cd /tmp && uv run --python 3.13 --with nodriver python3 -c "
  import asyncio, nodriver as uc
  from pathlib import Path
  async def main():
      b = await uc.start(headless=False, user_data_dir=str(Path.home()/'.config/lustro/nodriver-profile'))
      await b.get('https://quaily.com/dashboard/login')
      await asyncio.sleep(120)  # log in via Jump Desktop
      b.stop()
  asyncio.run(main())
  "
  ```
- Profile stored at `~/.config/lustro/nodriver-profile/` (not backed up — recreate on new machine)

## Vendor Newsletters (Email-Only)

Some vendors surface content via email that has no RSS/web equivalent:
- **OpenAI Dev News** — API doc updates, cookbook additions, engineering quotes. No web archive.
- Pattern: newsletters that curate across blog + docs + cookbook are a superset of any single RSS feed.
- Keep these in Gmail; Lustro covers the individual source blogs.

## Config Locations

- Active sources: `~/.config/lustro/sources.yaml`
- Defaults (for `lustro init`): `~/code/lustro/src/lustro/sources/default.yaml`
- State: `~/.config/lustro/state.json`
- Log: `~/.config/lustro/news.md`
- Article cache: `~/.config/lustro/cache/`

## Chinese Sources

- **InfoQ 中文 AI&大模型:** Via RSSHub (`rsshub.rssforever.com/infoq/topic/AI`). Topic ID 31, alias "AI". Public RSSHub instances are unreliable (504s) — accept intermittent failures or self-host.
- **机器之心:** RSS killed (redirects to Feishu form). No RSSHub route. Only viable path is WeChat feed via wechat2rss (`localhost:8001/feed/3073282833.xml`). Depends on OrbStack running.
- **少数派 (sspai):** Has RSS (`sspai.com/feed`) but too broad (gaming, lifestyle, productivity mixed in). No topic filtering. Skipped.
- **BestBlogs.dev:** Curated weekly newsletter (15-20 articles). No RSS. Good for email reading but don't add to lustro — double-processes content already covered by individual Chinese sources.
- **RSSHub public instances:** `rsshub.rssforever.com` and `rsshub.feeded.xyz` both intermittently 504. For reliable Chinese feeds, prefer wechat2rss or self-hosted RSSHub.

## Env Var Expansion

Config YAML supports `${VAR}` syntax (expanded via `os.path.expandvars` before YAML parse). Used for wechat2rss token (`${WECHAT2RSS_TOKEN}`). Set in `~/.zshenv`.

## Common Issues

- **Source shows 200 in `check` but fetches 0 articles:** RSS key present but feed is dead. `feedparser` doesn't throw on 404. Fixed with bozo check + fallback.
- **Medium custom domains return 403:** Bot-blocking on the custom domain (e.g. `eng.lyft.com`). Fix: use `medium.com/feed/<publication>` RSS instead — Medium doesn't bot-block its RSS endpoints. Works for all Medium-hosted blogs.
- **JS-heavy sites timeout:** McKinsey, some bank blogs. Check if they have a Medium mirror (`quantumblack.medium.com/feed` fixed McKinsey).
- **User-Agent matters:** The old `AI-News-Bot/1.0` UA was blocked by Goldman; a full browser UA was blocked by Meta AI and BCG. The standard crawler format (`Mozilla/5.0 (compatible; Lustro/0.2; +URL)`) passes all of them. Fixed Feb 2026.
- **SSL 526 errors:** Cloudflare origin cert issue on the site's end. Nothing to do but wait and check monthly.
- **Log entries appending to bottom instead of top:** Marker mismatch in `append_to_log()`. Code looks for `<!-- News entries below -->` but file has `<!-- News entries below, added by /lustro -->`. If the marker doesn't match, falls back to `content +=` (appends to end). Fixed Mar 2026 — marker in `log.py` updated to match file. Symptom: `lustro check` shows sources scanning fine but vault log has no new entries near top.
- **WeChat full-text via Wechat2RSS:** The `content[0].value` field in Wechat2RSS RSS entries contains the full article HTML — no re-fetch needed. Old code ignored it and re-fetched from `mp.weixin.qq.com`, hitting CAPTCHA (returned 65 chars of "环境异常" garbage). Fixed Mar 2026: `fetch_rss()` now extracts from `entry.content` if present; `archive_article()` skips trafilatura when pre-fetched text exists. This pattern applies to any RSS proxy that embeds full content in the feed.
- **IOSCO RSS dead (May 2023):** `iosco.org/rss/rss.xml` last updated May 2023 despite the site having current content. `bozo=True` but still returns 200. Switched to web scrape of `iosco.org/v2/media_room/?subsection=media_releases` with selector `ol li`. Titles include date text suffix (e.g. "IOSCO publishes X 19 Mar 2026") — acceptable for dedup since prefix is based on first 6 meaningful words. Links go to `/news/pdf/IOSCONEWS[N].pdf`. Fixed Mar 2026.
- **MAS website outage (Mar 2026):** `mas.gov.sg` entire website in maintenance mode. All pages return a maintenance placeholder page. Stealth_web fetch returns nav junk (titles like "Development", "Monetary Policy"). Source commented out in sources.yaml until MAS restores service. Symptom: `_zeros:MAS (Singapore)` incrementing despite stealth_web fetches completing.
- **Zero-article warnings for slow-cadence sources:** Monthly sources with `_zero_threshold=2` would warn after just 2 weeks of no articles — correct for genuinely broken feeds but noisy for sources that simply publish infrequently. Fixed Mar 2026: raised `monthly` threshold to 5 and `biweekly` to 3 in `cli.py`. HKMA inSight cadence changed `weekly→monthly` (publishes ~quarterly in practice).
- **Zero counter inflation from dedup:** Sources can show high `_zeros:X` counts when articles ARE found but deduplicated from the log (already logged in a prior run). This is correct behaviour — not a code bug. The zeros counter reflects "no new articles added to log", not "fetch failed". Use `lustro check` to distinguish dead feed (HTTP error) from dedup silence.
