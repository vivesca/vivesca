---
name: AINews / Cora / Source Analytics Research (Mar 2026)
description: Research on smol.ai AINews pipeline architecture, Cora by Every.to, and source-quality-scoring tools for RSS/news digests
type: reference
---

## smol.ai AINews

**What it is:** Daily newsletter for AI engineers. 99% LLM-generated, 1% human editorial (swyx as editor-in-chief picking best of 4 pipeline runs).

**Data sources:** 12 subreddits, 544 Twitter/X accounts, 24 Discord servers (~206 channels, ~7–12K messages per cycle). Saves ~500–1000+ minutes of reading time per issue.

**Pipeline architecture (confirmed):**
- Stage 1: Collect Discord/Reddit/X messages
- Stage 2: When links are dropped in Discord, pipeline clicks through and fetches summaries of linked content (multi-hop)
- Stage 3: Source-specific recaps by platform (Twitter, Reddit, Discord)
- Stage 4: Thematic clustering ("Model Wars", "Agent Engineering", "Security" etc.)
- Stage 5: "Summaries of Summaries" — final synthesis using Gemini 3.0 Pro Preview
- Stage 6: swyx runs 4 parallel pipeline variants, picks the best as editor

**Open source status:** PARTIALLY open. `ainews-web-2025` (Astro frontend + Resend email) is public on GitHub. The actual LLM aggregation pipeline is NOT public — it's proprietary/private.

**Structured extraction / gap analysis / quality gates:** NOT publicly documented. The pipeline "flags signal loss when ecosystem fragmentation obscures important developments" and "highlights adoption friction points alongside benchmark claims" — but this is editorial characterization in the newsletter output, not a formal structured schema or gap analysis system.

**"Synx" name:** No connection to smol.ai found. The user's reference to "synx" is not confirmed — may be a confusion with another product. The only SYNX found is Silynxcom (tactical headsets).

**Key sources:** news.smol.ai, github.com/smol-ai, latent.space

---

## Cora by Every.to

**What it is:** AI email management tool — NOT a news digest or RSS aggregator. Focused on email inbox triage and newsletter summarization within email.

**Product page:** cora.computer / every.to/p/introducing-cora-manage-your-inbox-with-ai

**Core functions:**
1. Inbox filtering: routes urgent human emails to inbox, archives non-urgent
2. Reply drafting: trains on user's writing style from email history
3. Twice-daily "Brief": beautiful digest of all non-urgent emails (newsletters, notifications, payments, calendar)

**Newsletter digest features:**
- Extracts "interesting stories" from newsletters with source attribution
- Summarizes bottom-line-first, bolds key insights
- Preserves technical language in specialized newsletters
- Matches summaries to what's "likely to matter to you" (personalization)

**Source analytics / quality scoring:** NONE documented. No per-source insight density tracking, no feed quality scoring, no analytics on which newsletters produce most value.

**Architecture / models:** Uses models from Google, Anthropic, and OpenAI. Newsletter summarization initially used GPT-4o, switched to GPT-4o-mini (10x cost reduction). Flexible pipeline with rigorous evals.

**Status:** Out of beta as of June 2025. $15/month. 2,500+ beta users. Gmail only (no Outlook).

**Not relevant to:** RSS pipelines, structured card extraction, gap analysis, source quality scoring. It's email-native, not a general news intelligence tool.

---

## Source Analytics / Insight Density Scoring Tools

**Key finding: No dedicated product exists** that tracks per-RSS-source insight quality, actionability density, or "which feeds produce the most valuable intelligence over time." This is a genuine gap.

**Closest approaches:**

1. **Feedly AI / Leo AI (enterprise):** Monitors 140M+ sources, uses AI Feeds with NLP to surface relevant items. Produces Insights Cards and thematic dashboards. Does NOT expose per-source quality scores or engagement metrics to users. Qualitative filtering, not quantitative source analytics.

2. **Inoreader (advanced):** Powerful filtering and tagging but no per-feed quality scoring. Read-count stats only.

3. **RSSbrew (open source, self-hosted):** GitHub yinan-c/RSSbrew. Aggregates, filters, AI-summarizes RSS. No documented source quality analytics.

4. **Hacker News:** Research confirms HN has the strongest correlation between score and quality among social aggregators (vs Reddit which has weak correlation). hnrss.org filter by 100+ points = effective signal filter.

5. **Mailbrew (acquired by Readwise 2023, discontinued):** Had per-source max-item controls but no quality scoring.

**What does exist in custom build territory:**
- GitHub: "AI Daily Digest" (TypeScript/Bun, 90 tech blogs, AI scores/filters articles, generates Markdown with trend analysis)
- GitHub: "AI News Aggregator" (Python, RSS → Notion daily digest)
- These are personal projects, not products with source analytics dashboards.

**Methodology note:** "Source quality" as a persistent tracked metric across sessions (insight density per feed, actionability rate, discovery rate) does not appear to exist as a commercial feature in any RSS/news tool as of March 2026. It's genuinely novel territory.

---

## Custom Pipeline Comparison vs AINews

User's proposed pipeline: gather RSS → extract structured cards (domain-specific schema) → gap analysis → research gaps → synthesize weekly briefing with quality gate.

**Where AINews is stronger:**
- Scale: monitors social (Discord/Twitter/Reddit) not just RSS — captures ambient discussion and emerging memes, not just published articles
- Multi-hop: clicks through links in Discord to read source articles (not just headlines)
- Multi-source deduplication at scale
- Established audience and editorial layer

**Where custom pipeline is stronger:**
- Structured cards with domain-specific schema: AINews produces prose, not structured data
- Gap analysis: AINews identifies themes but doesn't have a formal "what's missing from coverage" step
- Quality gate: AINews quality is editorial (swyx picks from 4 runs), not programmatic
- Source analytics: custom pipeline could track per-source insight density — AINews doesn't
- Domain specificity: AINews is broad AI engineering; custom pipeline can be scoped to specific domains (FS AI, regulatory, APAC)
- RSS-native: if sources are mostly blogs/publications rather than social discussion, RSS is more appropriate

**Key gap in AINews:** The pipeline is closed-source and social-first. It's not a general framework. It's a specific product for a specific audience. There's no way to fork it for a different domain.
