# Breaking AI News Alert — Brainstorm

**Date:** 2026-02-14
**Status:** Ready for planning

## What We're Building

A push-based Telegram alert for major AI industry events — model drops, strategic shifts, regulatory shocks. Extends the existing ai-news cron infrastructure. Fires rarely (1-3/month), only for genuine earthquakes.

This fills the gap between the daily 6:30 PM news scan and real-time awareness. The value proposition: Terry hears about GPT-5 dropping within 2 hours, not 8 — arriving at Capco conversations already informed.

## Why This Approach

### Tier A only — no toolchain alerts

Toolchain changes (Claude Code updates, API pricing) are a different problem better solved by release watchers (GitHub releases API). News scanning is the wrong tool for structured changelogs. If that pain emerges, build it separately.

### Keyword heuristics, no LLM

Earthquakes have loud titles. "Introducing Claude 5" and "OpenAI releases GPT-5" are not subtle — keyword patterns catch them cleanly. LLM classification adds cost, latency, and a black-box failure mode for edge cases that barely exist at this tier.

If false positives become annoying (>2 junk pings/month), bolt on an LLM second pass then. Classic "wait for the pain."

### RSS-only, no web scraping

Breaking monitor should be fast and reliable. RSS feeds are structured, dated, and parseable without fragile HTML selectors. Web-scrape sources can stay in the daily scan.

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Alert scope | Industry earthquakes only | Avoid noise. 1-3/month target. |
| Classification | Keyword heuristics | Debuggable, zero tokens, sufficient for loud events |
| Polling frequency | Every 2 hours, 8am-10pm HKT | 7 checks/day. Know within ~2 hours of any drop. |
| Sources | Lab blogs + top aggregators (~8 RSS feeds) | Where earthquakes surface first |
| LLM gate | Not now — add later if noise >2 junk pings/month | YAGNI |
| Toolchain alerts | Out of scope — separate system if needed | Different problem, different solution |

## Source Shortlist

Breaking monitor watches only these (all have RSS):

1. **Anthropic Blog** — no RSS, but can scrape `/news` page (already in daily cron)
2. **OpenAI Developer Blog** — `developers.openai.com/blog`
3. **Import AI** — `importai.substack.com/feed`
4. **Interconnects** — `robotic.substack.com/feed`
5. **Smol AI News** — `news.smol.ai/rss.xml`
6. **Simon Willison** — `simonwillison.net/atom/everything/`
7. **机器之心** — `wechat2rss.xlab.app/feed/...`
8. **量子位** — `wechat2rss.xlab.app/feed/...`
9. **Google DeepMind Blog** — `blog.google/technology/ai/` (scrape, no RSS)

Note: Anthropic Blog has no RSS. Options: scrape the page (like daily cron does), or add their blog RSS if one appears. For now, web scrape fallback is acceptable since it's one source.

## Keyword Pattern Design

**Entity triggers** (must appear in title):
- Company names: Anthropic, OpenAI, Google DeepMind, Meta AI, Mistral, xAI
- Regulatory: HKMA, MAS, SEC, EU AI Act, PBoC
- Model families: GPT, Claude, Gemini, Llama, Grok

**Action triggers** (must co-occur with entity):
- launches, releases, introduces, announces, unveils, open-sources
- acquires, merges, shuts down, bans, mandates

**Pattern logic:** `entity_match AND action_match` — both must fire. This prevents "OpenAI hires new VP" (entity but no action) and "Company launches new CRM" (action but no entity) from triggering.

**Negative patterns** (suppress even if both match):
- "partnership", "collaboration", "investment round" (unless >$1B)
- "beta", "preview", "limited access" (unless from top-3 labs)

## Architecture

```
~/scripts/crons/ai-news-breaking.py
  │
  ├─ Cron: 0 8,10,12,14,16,18,20,22 * * *  (every 2h, 8am-10pm HKT)
  ├─ Log:  ~/logs/cron-ainews-breaking.log
  │
  ├─ Fetch: RSS feeds from shortlist (~8 sources)
  │   └─ Filter: articles from last 3 hours only
  │
  ├─ Dedup: against ~/.cache/ai-news-breaking-state.json
  │   └─ Seen article IDs (bounded, last 200)
  │
  ├─ Classify: keyword pattern match on titles
  │   └─ entity_match AND action_match AND NOT negative_match
  │
  ├─ Throttle: max 3 alerts/day, 1-hour cooldown
  │
  ├─ Notify: tg-notify.sh
  │   └─ Format: 🚨 *Breaking:* [Title](url)\nSource: Name • HH:MM HKT
  │
  └─ Cross-post: append to ~/code/vivesca-terry/chromatin/AI News Log.md
      └─ Prevents daily scan from re-surfacing same article
```

## State File

```json
{
  "last_check": "2026-02-14T14:00:00+08:00",
  "seen_ids": ["hash1", "hash2"],
  "alerts_today": 1,
  "today_date": "2026-02-14",
  "last_alert_time": "2026-02-14T10:15:00+08:00"
}
```

## Reuse from Existing Code

From `ai-news-daily.py`:
- `fetch_rss()` — RSS parsing with date filtering
- `_title_prefix()` / `is_junk()` — dedup utilities
- `load_state()` / `save_state()` — state management pattern
- `format_markdown()` — log formatting (adapted for single articles)

From `tg-notify.sh`:
- Telegram delivery (no changes needed)

## Resolved Questions

1. **Dry-run mode:** Yes — `--dry-run` flag, prints what would alert without sending Telegram.
2. **Anthropic Blog without RSS:** Scrape `/news` page. It's one lightweight page every 2 hours — acceptable.
3. **Google DeepMind blog:** Added to breaking shortlist. They announce Gemini releases there.

## Out of Scope

- Toolchain/changelog watching (separate system if needed)
- LLM classification (add later if false positive rate >2/month)
- X/Twitter monitoring (rate limits, authentication complexity)
- WeChat article monitoring (latency too high for "breaking")
- Mobile push notifications beyond Telegram
