---
name: Thalamus Competitive Landscape Research (Mar 2026)
description: What already exists in the space of automated AI news briefings with banking-specific framing, structured extraction, regulatory tagging, quality gates, and gap analysis — compared against thalamus's actual pipeline.
type: reference
---

# Thalamus Competitive Landscape Research (Mar 2026)

## Thalamus's actual pipeline (ground truth from CONTEXT.md)
Gather → Extract (Sonnet, parallel) → Citation Check → Gap Analysis → Research (parallel) → Re-gap → Synthesise (Sonnet quality gate) → Write
- Reads from lustro JSON files (~/.cache/lustro-articles/)
- Extracts structured fields including regulatory_exposure (citation-checked, [INFERRED] tagged)
- Daily cadence: extracts today's articles, no gap analysis; weekly rolls up daily snapshots
- LLM calls via `claude --print` using Max20 subscription
- 15 modules, 74 tests, fully operational as of 2026-03-14

## Competitive Map

### Tier 1: Enterprise Market Intelligence Platforms (closest to spirit, farthest in cost)
**AlphaSense**
- Closest commercial analog in terms of "structured financial intelligence from unstructured sources"
- Does extract structured fields from earnings calls, filings, expert transcripts, news
- Has regulatory tone monitoring across peer banks
- Pricing: $10K+/year at low end, up to millions for enterprise
- Limitation: content is pre-curated from a proprietary corpus, not custom pipeline over your own sources
- No banking-specific gap analysis vs your own coverage areas
- Source: alpha-sense.com

**Feedly Teams + Leo AI**
- RSS-first aggregation with AI newsletter automation
- Can define custom prompts for domain-specific framing (role-based: "act as a FS market analyst")
- CitizensBank case study: uses Feedly automated newsletters for senior leadership briefings
- Gap vs thalamus: no structured JSON extraction, no citation check, no gap analysis, no quality gate
- More of a "smart RSS reader + email digest" than a pipeline
- Source: docs.feedly.com/article/753-guide-to-using-ai-in-automated-newsletters

**Contify**
- NLP-driven competitive intelligence platform
- Monitors 1M+ sources including regulatory docs, news, press releases
- Dashboard-based (competitors, customers, market segments)
- No banking-specific gap analysis; no structured field extraction at the article level
- B2B SaaS, pricing not public

### Tier 2: Workflow Automation (n8n/Make templates)
**n8n workflows (community templates)**
- Multiple templates: RSS → AI filter → Google Sheets, daily digest → Slack/email
- Best template: "Daily news digest & weekly trends with AI filtering, Slack & Google Sheets"
  - Extracts: Title, Author, Summary, URL
  - Generates weekly trend report Monday
  - Architecture: Ingestion → Aggregation → AI Analysis → Curation → Delivery
- Gap vs thalamus: general-purpose extraction only, no banking framing, no regulatory tagging, no citation check, no gap analysis, no quality gate
- Source: n8n.io/workflows/10977-*

**upGrowth AI executive digest**
- n8n-style pipeline: aggregate by focus areas, keywords → cluster into Market Trends / Competitor Updates / Regulatory Alerts → email
- Closer to thalamus's framing than most n8n templates
- Gap: no structured JSON, no citation validation, no gap analysis pass

### Tier 3: Open Source Projects
**Taranis AI (github.com/taranis-ai/taranis-ai)**
- OSINT tool for CSIRT/NIS authorities (cybersecurity intel, not FS AI landscape)
- Pipeline: collect from web/RSS/Twitter/email → AI enhance → analyst refines → PDF output
- Has multi-source collection, NLP enrichment, structured report output
- Gap vs thalamus: purpose-built for cybersecurity threat intel, not AI landscape; no banking framing, no regulatory field extraction, no automated gap analysis
- Closest open-source structural analog, but wrong domain

**bboyett/ai-briefing (github.com)**
- Daily AI headline digest, GitHub Actions, static site
- Keyword-filtered RSS scraping, HTML output
- No structured extraction, no quality gates, no domain framing — general AI news

**AI4Finance-Foundation/FinRobot**
- Financial analysis agent platform
- Perception module captures news, market data, economic indicators
- Structured instructions via Financial Chain-of-Thought
- Gap vs thalamus: stock/equity analysis focus, not AI landscape monitoring; no weekly cadence automation, no gap analysis

**AI-Alliance/deep-research-agent-for-finance**
- Investment research report generator
- Stock info, business overview, risk/opportunity assessment
- Gap vs thalamus: generates reports on specific companies, not AI landscape monitoring; no regulatory tagging, no gap analysis

**GPT Researcher (gpt-researcher)**
- Deep research agent, 2000+ word reports with citations
- Domain-customisable in principle
- Gap vs thalamus: on-demand research tool, not scheduled pipeline; no structured field extraction, no gap analysis, no quality gate architecture

### Tier 4: Consumer/Prosumer News Aggregators
- **Mailbrew**: personal digest builder (RSS, newsletters, social) — no structured extraction
- **Perplexity Tasks**: recurring research queries with email delivery — no structured fields, no gap analysis
- **NewsDigest.ai**: multilingual real-time financial news summaries — no structured extraction
- **LLRX AI in Finance column**: semi-monthly human-curated briefing for banking/finance — not automated

## Key Finding

**No product does what thalamus does.** The gap is specific and real:

| Feature | AlphaSense | Feedly Teams | n8n templates | Taranis AI | thalamus |
|---|---|---|---|---|---|
| RSS/custom source ingestion | Partial | Yes | Yes | Yes | Yes (via lustro) |
| Banking-specific framing | Partial | Prompt-only | No | No | Yes (built-in) |
| Structured field extraction | Partial | No | Minimal | No | Yes (Sonnet, parallel) |
| Regulatory exposure tagging | Yes (coarse) | No | No | No | Yes (citation-checked) |
| Citation/[INFERRED] check | No | No | No | No | Yes |
| Gap analysis pass | No | No | No | No | Yes |
| Quality gate (LLM judge) | No | No | No | No | Yes |
| Open source / self-hostable | No | No | Yes (template) | Yes | Yes |
| Cost | $10K+/yr | $$$+ | Near-zero | Free | Free (Max20) |

## What exists in adjacent spaces (partial overlap)
- AlphaSense: closest spirit match but $10K+, proprietary corpus, no gap analysis
- Feedly Leo: best-known "smart RSS for teams" but stops at prompt-guided summaries
- n8n templates: democratize the gather→summarize arc; no structured extraction or quality layers
- Taranis AI: best structural analog (OSINT pipeline with structured output) but wrong domain
- GPT Researcher: on-demand deep research but no scheduled pipeline or gap architecture

## Misinformation patterns to watch
- "automated briefing" in vendor marketing usually means "scheduled email digest" — not structured extraction + gap analysis
- "structured extraction" in n8n templates = Title/Author/URL — not field schema with validation
- AlphaSense "regulatory tone monitoring" = sentiment from earnings calls, not article-level regulatory exposure tagging

## Best sources for this domain
- n8n.io/workflows (community templates)
- docs.feedly.com (Feedly Leo capabilities)
- github.com/taranis-ai/taranis-ai (OSINT pipeline reference)
- alpha-sense.com (enterprise benchmark)
- re-cinq.com/blog/n8n-news-feed (practitioner n8n write-up)
