---
name: exauro
description: Exa search API CLI — neural/semantic web search, find-similar, content extraction, AI answers. Use when WebSearch is too shallow or noesis is overkill. exauro search "topic", exauro answer "question", exauro similar <url>.
---

# exauro

Rust CLI wrapper for the [Exa search API](https://exa.ai). Neural/semantic search that understands meaning, not just keywords.

## When to Use

| Signal | Use |
|--------|-----|
| Keyword search sufficient | WebSearch (free) |
| Need cited, quality sources | `noesis search` (~$0.006) |
| **Need semantic/neural search** | `exauro search --search-type neural` |
| **Find pages like this URL** | `exauro similar <url>` |
| **Quick AI answer with citations** | `exauro answer "question"` |
| **Extract full content of a page** | `exauro contents <url>` |

## Commands

```bash
# Search (default: neural)
exauro search "AI governance frameworks Hong Kong" --n 10
exauro search "rust async tokio" --search-type fast
exauro search "topic" --json  # raw API response

# WeChat 公众号 discovery — Exa indexes mp.weixin.qq.com directly
exauro search "AI 银行 大模型 site:mp.weixin.qq.com" --search-type auto
exauro search "DeepSeek 银行 site:mp.weixin.qq.com" --search-type neural

# Find similar pages
exauro similar https://example.com/article

# Extract full content of a URL (incl. WeChat articles — bypasses CAPTCHA)
exauro contents https://mp.weixin.qq.com/s/...

# AI answer with citations
exauro answer "What is the HKMA's stance on AI in banking?"
```

### WeChat article workflow

**Discovery:** `exauro search "query site:mp.weixin.qq.com" --search-type auto` returns real mp.weixin.qq.com URLs with Chinese summaries. Neural search finds semantically related articles, not just keyword matches. No Sogou, no CDP Chrome, no login required.

**Fetch full content:** `exauro contents <url>` bypasses WeChat CAPTCHA (~80% success). See `wechat-article` skill for full detail.

## Setup

API key: `EXA_API_KEY` — stored in 1Password vault `Agents`, item `Agent Environment`.
Injected automatically via `~/.zshenv.tpl` → no manual setup needed.

## Source

- Binary: `~/bin/exauro`
- Source: `~/code/exauro/`
- Search type default: `neural` (semantic embedding-based)

## Gotchas

- **Build:** `exauro` is in the `~/code` workspace — build with `cd ~/code && cargo build --release -p exauro`, then `cp ~/code/target/release/exauro ~/bin/exauro`. Don't build from `~/code/exauro/` directly (workspace conflict).
- **phron workspace conflict (fixed Mar 2026):** `~/code/phron/Cargo.toml` had a bare `[workspace]` that caused "multiple workspace roots" errors. Removed. Rebuild if you see that error.
- **Unicode truncation (fixed Mar 2026):** Old binary panicked on CJK summaries (`byte index N is not a char boundary`). Fixed by switching from `&summary[..197]` to `.chars().take(100)`. If you see this panic, `cp ~/code/target/release/exauro ~/bin/exauro`.
- `reqwest` uses blocking client — not async, but fine for CLI use
- `search_type` enum values: `auto`, `neural`, `fast`, `deep`
