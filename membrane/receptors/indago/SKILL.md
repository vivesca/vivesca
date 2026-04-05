---
name: indago
description: Reference for searching information online — tool selection, search strategies, when to go deep vs quick, non-English search. Not user-invocable — use as internal guidance when performing searches.
user_invocable: false
triggers:
  - indago
  - web search
  - search tool
  - search online
  - research online
  - which search tool
---

# Web Search Tool Selection Guide

Reference for choosing the optimal search tool. Updated 2026-04-03.

## Primary Tools (2-tool surface)

All online search goes through **two** vivesca MCP tools:

| Tool | What | Depth param | Cost |
|------|------|-------------|------|
| **`rheotaxis_search`** | All search | `quick` (default) — multi-backend fanout | ~$0.01 |
| | | `thorough` — Perplexity sonar-pro | ~$0.02 |
| | | `deep` — Perplexity deep research | ~$0.40 |
| | | `parallel` — grok+exa+noesis+websearch + synthesis | ~$0.07 |
| **`pinocytosis`** | All URL fetch | defuddle→jina→firecrawl→agent-browser chain | Free |

**Default: `rheotaxis_search` with `depth=quick`.** Escalate depth only when needed.

## Also Available (secondary)

| Tool | Type | When to use instead |
|------|------|-----|
| **WebSearch** | CC built-in | Quick one-off when vivesca MCP is down |
| **mcp__jina__search_web** | Jina MCP | Batch parallel search (up to 5 queries) |
| **mcp__jina__search_arxiv** | Jina MCP | Academic paper search |
| **mcp__jina__read_url** | Jina MCP | Fallback URL fetch when pinocytosis chain fails |
| **WebFetch** | CC built-in | Last resort URL fetch |

## Internal Backends (not client-facing)

These are called internally by rheotaxis/pinocytosis. Don't invoke directly:
- `noesis` CLI — Perplexity API (used by rheotaxis deep + parallel)
- `exauro` CLI — Exa API (used by rheotaxis quick + parallel)
- `grok` CLI — xAI API (used by rheotaxis parallel)
- `defuddle` CLI — clean web extraction (used by pinocytosis)

## Free Synthesis Options (CC Max)

| Tool | Cost | Use |
|------|------|-----|
| **Sonnet subagent** (`Agent` tool, `model: "sonnet"`) | Free | Research + synthesis in one agent |
| **`claude --print --model sonnet`** | Free | Pipe search results through for synthesis |
| **Opus subagent** | Free but heavy | Only when Sonnet insufficient |

## Pre-Flight: Post-Cutoff Verification

**Before asserting any fact about models, frameworks, benchmarks, API features, or regulatory updates — web-search first if the information could have changed since May 2025.** Training data is stale for fast-moving domains. This is not optional.

Trigger categories (always verify):
- Model rankings and versions → `pondus rank` (free, instant, always current)
- Model head-to-head → `pondus compare <a> <b>`
- Framework versions and features → `WebSearch`
- Benchmark rankings beyond pondus → `WebSearch`
- API pricing and availability → `WebSearch`
- Regulatory guidance updates → `WebSearch`

Cost: `pondus` is free and instant. `WebSearch` is free and 5 seconds. Cost of getting it wrong in a consulting context: credibility.

## Default: rheotaxis_search MCP

**Not sure which tool? Use `rheotaxis_search`.** Default `depth=quick` hits Perplexity+Exa+Tavily+Serper in parallel (free). Need synthesis? Use `depth=parallel` (~$0.07) — runs grok+exa+noesis+websearch and synthesises agreements/disagreements.

## Cost Tiers — Route by Depth

| Depth | Cost | When |
|-------|------|------|
| `quick` (default) | ~$0.01 | Most searches — Perplexity sonar + Exa + Tavily + Serper |
| `thorough` | ~$0.02 | Structured surveys — Perplexity sonar-pro |
| `deep` | ~$0.40 | Novel research needing breadth + citations |
| `parallel` | ~$0.07 | Cross-validated — grok+exa+noesis+websearch + synthesis |

**Default to `quick`.** All depths have nonzero cost (API calls). For truly free: use `WebSearch` (CC built-in). Escalate only when the answer is incomplete or accuracy is critical.

## Use Case Routing

| Need | Tool + depth | Why |
|------|-------------|-----|
| Quick answer / link verification | `rheotaxis_search` (quick) | Free, multi-backend |
| Casual factual lookup | `rheotaxis_search` (quick) | Synthesized across 4 backends |
| Structured survey ("list the platforms for X") | `rheotaxis_search` (thorough) | Perplexity sonar-pro, tabular output |
| Algorithm/framework comparison | `rheotaxis_search` (quick) | Multi-backend gives comparative data |
| Deep analysis of novel questions | `rheotaxis_search` (deep) | Perplexity deep research, ~$0.40 |
| Cross-validated consulting research | `rheotaxis_search` (parallel) | 4 independent tools + synthesis, ~$0.07 |
| Employer/company culture reviews | `rheotaxis_search` (quick) | Glassdoor/Indeed indexed by backends |
| Verify claims / get primary sources | `WebSearch` | Returns links for manual review |
| AI news / X/Twitter reactions | `rheotaxis_search` (parallel) | grok backend covers X/Twitter |
| Academic papers | `mcp__jina__search_arxiv` | Free, arXiv-specific |
| Batch web search (multiple queries) | `mcp__jina__parallel_search_web` | Free, up to 5 queries |
| Fetch a URL | `pinocytosis` | Full fallback chain |
| Scrape JS-rendered URL (no Cloudflare) | `pinocytosis` | Falls through to agent-browser |
| Quick URL to markdown | `mcp__jina__read_url` | Free Jina reader — good fallback when defuddle fails |
| Scrape JS-heavy or Cloudflare-protected URL | `peruro <url>` | Only tool that reliably handles both. 1 credit/page. Don't reach for peruro if agent-browser suffices — save credits for Cloudflare. |
| Need facts from a protected page (not raw content) | `noesis search` | Synthesises from indexed sources — no direct fetch. ~$0.006 |
| Web search + scrape results | `peruro search <query>` | Returns scraped markdown per result, not just links |
| peruro failed + site needs Chrome auth | `stealth-browser` skill | Last resort — Chrome cookie injection + playwright-extra |
| Code & documentation | Context7 plugin | Best for library docs |
| Job/company research | `WebSearch` → `noesis ask` | Free first, paid for depth |
| **Rare/proprietary proper noun (insider term, project codename)** | **`WebSearch` first** | **Fast free sanity check. If nothing found, term isn't publicly indexed — no tool can help. Don't burn paid tools on unindexed terms (confirmed Mar 2026).** |
| **HK restaurant lookup** | **`exauro search` → `peruro`** | **exauro finds the OpenRice URL; peruro fetches full page (corkage, hours, policies)** |

## Unknown Site Types — Log and Learn

**First encounter with a new site type → run the ladder top-to-bottom, log all outcomes.**

Don't skip straight to peruro on unfamiliar sites — run noesis → exauro → peruro in order and record what each returns. Append findings to `~/docs/solutions/cloudflare-bypass-tools.md` under "Confirmed working sites". This builds empirical data without burning peruro credits speculatively on known patterns.

Known site types (skip to winner directly):
- OpenRice → `peruro`
- Wix JS-rendered (no Cloudflare) → `peruro` (agent-browser fails on dynamic pricing tables/widgets even without Cloudflare; confirmed jeffphysio.com Mar 2026)
- Cloudflare Bot Management → `peruro`
- Static HTML → `defuddle`
- SAP SuccessFactors (`career10.successfactors.com`) → `agent-browser` works fine (no Cloudflare). Navigate via employer careers site → Apply Now (direct URL fails). See `~/docs/solutions/browser-automation/successfactors-career-portal.md`.

## noesis CLI

Rust CLI wrapping the Perplexity API. Source: `~/code/noesis`. Binary: `noesis`. Published on crates.io as `noesis`.

```bash
noesis search "query"            # sonar               ~$0.006
noesis ask "query"               # sonar-pro           ~$0.01
noesis reason "query"            # sonar-reasoning-pro ~$0.01
noesis research "query"          # sonar-deep-research ~$0.40 ← EXPENSIVE
noesis research --save "query"   # research + save to ~/docs/solutions/research/
noesis log                       # last 20 queries
noesis log --stats               # cost summary by mode
```

**Flags:** `--raw` (JSON output), `--no-log` (skip logging).
**Log:** `~/.local/share/noesis/log.jsonl` — use `noesis log --stats` to assess cost over time.
**Fallback:** `~/scripts/perplexity.sh` (bash wrapper, same API, no logging).

Reasoning responses (`noesis reason`) strip `<think>` tags by default. Use `--raw` to preserve.

## Search Retrospective — When You Finally Find It

When a search succeeds after multiple attempts, **immediately capture the finding** before moving on. Ask three questions:

**1. Where did it live?**
Update the routing table or add a vault location note here. Future searches start there.
- Vault article notes: `~/epigenome/chromatin/Articles/` — `ls ~/epigenome/chromatin/Articles/ | grep -i <keyword>` beats `anam search` for filename-level lookup (Mar 2026).

**2. What does the failure tell us about the CLI?**
A search miss is a signal about the tool, not just the query. Ask:
- Did `anam` fail because the content was in a file never ingested (directory listing, not chat)? → `anam` indexes *chat history*, not vault files — wrong tool for this.
- Did `exauro` or `noesis` surface irrelevant results? → Was it a keyword vs semantic mismatch? Try the other.
- Did a multi-word `anam` query fail where a single keyword would have worked? → `anam` matches phrases, not individual words across a prompt. Use the most distinctive single term.
- Recurrent failure pattern → file a feature note in `~/docs/solutions/` or the relevant tool's skill.

**3. Should these findings be interlinked?**
After finding a cluster of related notes (articles, blog posts, vault notes), add wikilinks between them before moving on:
- Article note → related garden post: `[[Writing/Blog/Published/slug|Title]]`
- Garden post → other garden posts: inline prose link `[title](/posts/slug)`
- Article note → related article notes: `[[Articles/Filename|Title]]`

The moment of finding is when context is freshest. Don't defer any of these three.

## Capture Rule

**`noesis research` → always use `--save`.** Output is saved to `~/docs/solutions/research/YYYY-MM-DD-slug.md` with frontmatter (query, date, model, cost, sources). This prevents re-running $0.40 queries and preserves citations. No exceptions.

## grok CLI

Python script (`~/bin/grok`) wrapping xAI Responses API. Uses `grok-4-1-fast-reasoning` for web search, `grok-3-mini-fast` for plain LLM.

```bash
grok "query"                  # general web search       ~$0.02
grok --x-only "query"        # X/Twitter only            ~$0.02
grok --domain reddit.com "query"  # restrict to domain   ~$0.02
grok --no-search "query"     # plain LLM (no search)     ~$0.0002
grok --raw "query"           # raw JSON response
```

**Key feature:** `--x-only` restricts to `x.com` via `allowed_domains` — only way to search X/Twitter programmatically.
**Auth:** `XAI_API_KEY` in `~/.zshenv`.

### X/Twitter Search: grok vs bird

| Tool | Use When | Output |
|------|----------|--------|
| `grok --x-only "query"` | Sentiment/opinion synthesis, "what do people think of X" | AI-summarised answer from X posts |
| `bird search "query" -n 10 --plain` | Raw tweets, specific users, exact quotes | Raw tweet text with links |

**Default to `grok --x-only` for X/Twitter research.** It synthesises across many posts and surfaces patterns. Use `bird` when you need raw tweets (exact wording, photos, specific accounts) or to fetch a known user's timeline (`bird user-tweets <handle>`).

**Japanese keeb Twitter is a goldmine.** English Reddit/YouTube may have zero coverage for niche switches — Japanese X often has real user impressions, sound tests, and rankings. Search in Japanese when English comes up empty.

## Non-English Search — Match the Community's Language

**When English results are thin, search in the language of the community that actually uses the product/service.**

| Domain | Language | Example |
|--------|----------|---------|
| HK local (doctors, govt, restaurants, consumer sentiment, local services) | Chinese/Cantonese (中文) | `noesis search "香港脊椎側彎骨科醫生推薦 私家 2026"` |
| **HK professional salary / compensation data** | **English** | **Salary benchmarks published on Indeed HK, Payscale, Morgan McKinley — all in English. Chinese search returns regulatory docs and job listings, not salary numbers. Empirically confirmed Mar 2026.** |
| Niche keeb switches/builds | Japanese (日本語) | `bird search "HMX K01 タクタイル" -n 10` |
| Taobao/Chinese products | Chinese (中文) | Reviews, Douyin/Bilibili content |
| K-beauty, Korean tech | Korean (한국어) | Naver blogs, Korean review sites |

**Pattern:** English first (free). If results are retailer copy or zero community discussion → re-search in the relevant language.

**HK local sources by type:**
- Consumer sentiment / opinions → **LIHKG** (forums, ground-level)
- Editorial reviews, listicles → **HK01, Sundaykiss**
- F&B → **OpenRice** ← de facto standard for HK restaurants. **Never use noesis/Perplexity for HK restaurant lookups** — index gaps cause confident false negatives even with correct spelling (Tajimaya at APM undetected in English, Mar 2026). Two-step workflow: (1) `exauro search "<name> <district> restaurant"` — reliably surfaces the OpenRice URL; (2) `peruro "<openrice-url>"` — fetches full page content including corkage fees, cake cutting policy, opening hours. WebFetch/defuddle/agent-browser all fail on OpenRice (Cloudflare Bot Management).
- Finance / banking / fintech → **Planto, InvestBrother, EconManBlog, MoneyHero**

Validated: Cantonese search for HK banking app UX (Mox, ZA Bank) returned richer, more current results than English equivalents (Mar 2026).

**HK product price search:** See `~/docs/solutions/hk-product-price-search.md`.

**LinkedIn people research:** See `linkedin-research` skill.

## Researcher Agent Delegation

When constructing prompts for researcher subagents, **explicitly specify the search tool** for the topic:

| Topic type | Specify in agent prompt |
|---|---|
| Academic / scientific / neuroscience | Use `noesis research` for primary sources |
| Market / product research | `noesis ask` or `noesis search` |
| Quick factual lookup | `WebSearch` (default) |
| AI news / real-time | `grok` |

Default: agents fall back to WebSearch. For academic research this misses cited primary sources — always specify `noesis research` explicitly in the agent prompt.

## noesis research vs Researcher Agent

These are complementary, not interchangeable:

| Tool | Best for |
|------|----------|
| `noesis research` | Recent platform-specific facts: algorithm rules, word count thresholds, timing windows, product specs. Fast, cheap-ish ($0.40), current. |
| Researcher agent | Foundational academic synthesis: established theory, citable papers, cross-study analysis. Slower, more thorough. |

**Pattern:** use researcher agent for the "why" (mechanism, theory), `noesis research` for the "what now" (current platform behaviour, recent data). Both on the same topic often yields more than either alone — agent surfaces the theory, noesis surfaces what's changed since.

## Perplexity Quality Notes

- **All Perplexity tools inherit search index bias.** If a vendor publishes 4+ SEO comparison articles, they'll dominate results. Cross-check with WebSearch.
- **Route by question type.** `ask` for "what exists?" questions. `research` for "what does this mean?" or anything requiring depth. Cost is acceptable — use `research` freely when it adds value.
- **Never cite Perplexity metrics without checking the underlying source.** Fabricated case studies with round numbers (75% decrease, 40% increase) are common.

## WeChat Articles (mp.weixin.qq.com)

See the dedicated `wechat-article` skill.

## Motifs
- [escalation-chain](../motifs/escalation-chain.md)
