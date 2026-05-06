---
name: metabolize
description: Extract ideas, data, quotes, and cross-pollination from articles — Capco consulting lens. Handles single URLs and the daily endocytosis batch. "metabolize", "process articles", "what came in today", "extract from this article"
model: opus
triggers:
  - metabolize
  - process articles
  - what came in today
  - endocytosis
  - extract from this article
  - pull useful things out of
---

# Metabolize — endosomal processing of raw articles

**Biology:** Endosomal cargo processing + antigen presentation. Raw articles (antigens) are broken down and key fragments (epitopes) are presented for downstream consumption.

**What this does:** Extracts what matters from articles — ideas, data, quotes, cross-pollination — through the Capco lens. Two modes: single-article (URL or text handed in by user) and daily-batch (reads endocytosis cache).

## When this fires

- **Single-article mode:** Terry shares a URL/text and asks to "extract", "metabolize", "pull useful things out of", or just hands me an article in a context where extraction is the obvious move (e.g. an AI/banking blog post relevant to current consulting work).
- **Daily-batch mode:** "process today's articles", "metabolize", "what came in today" — runs after endocytosis fetch (daily 18:30), or before a client meeting when fresh signal is wanted.

## Procedure — single-article mode

### 1. Fetch the article

If Terry hands a URL: `pinocytosis "<url>" --json` (CLI, preferred) or `lysozyme "<url>"` for clean prose. If he hands raw text or a local file path, read it directly.

### 2. Extract — through the Capco lens

You are an AI Solution Lead at Capco Hong Kong advising large international banks on AI governance, risk tiering, and responsible AI deployment. Free-text extraction with these surfaces (skip what doesn't apply):

- **Headline thesis** — what the article claims, in one sentence
- **Ideas** — load-bearing concepts, framings, mental models worth borrowing
- **Data** — names/numbers/dates/benchmarks that quantify the claim
- **Quotes** — verbatim lines worth preserving (prefer over paraphrase)
- **Cross-pollination** — where this resonates with the organism, current consulting work, or a known stakeholder concern. Be specific — name the skill/paper/person.
- **What to DO** — brief a client? watch? build capability? draft a garden post? ignore?

### 3. Report inline

Default: report extraction inline in chat — Terry reads chromatin through CC, so the live response IS the deliverable for one-off articles. No card written unless Terry asks "save this" or the article is high-signal enough to warrant catalog (then route to `/phagocytosis`).

### 4. Offer downstream routing

If extraction surfaced something publishable, offer the next step (garden post via exocytosis, paper material, talking-point) — don't auto-execute.

---

## Procedure — daily-batch mode

### 1. Gather raw articles

Read today's articles from the endocytosis cache:

```
~/.cache/endocytosis/articles/YYYY-MM-DD_*.json
```

Each file has: title, source, summary, text (full article if tier 1), link, date.

If no articles from today, check yesterday. Report count to user.

### 2. Load consulting context

Read the most recent weekly brief for recurrence context:

```
~/epigenome/chromatin/chemosensory/weekly-ai-digest-*.md
```

Take the latest one. This gives you what was already briefed — so you can flag "this confirms/contradicts what we covered last week."

### 3. Extract — per article

For each article, extract what matters. No rigid schema. You are:

> An AI Solution Lead at Capco Hong Kong advising large international banks on AI governance, risk tiering, and responsible AI deployment.

For each article, write a free-text extraction:
- **What happened** — the fact, with names/numbers/dates
- **Why it matters for banks** — specific, not "AI is changing banking"
- **What to DO** — brief a client? Watch? Build capability? Ignore?
- **Anything else** — regulatory signal, competitive move, contrarian angle, quotable stat — whatever opus thinks matters for this specific article. Skip fields that don't apply.

If the article is noise (scrape failure, no substantive signal, dev tooling with no banking angle), mark as junk and move on.

### 4. Write cards

Write each extraction as a markdown file in:

```
~/epigenome/chromatin/chemosensory/cards/YYYY-MM-DD_<source-slug>_<hash>.md
```

Format:

```markdown
---
title: <article title>
source: <source name>
date: <YYYY-MM-DD>
link: <url>
---

<free text extraction>
```

### 5. Report

Tell the user:
- How many articles processed
- How many were junk (skipped)
- Top 3 most interesting (one line each)
- Any connections to the recent weekly brief

## Anti-patterns

| Don't | Do |
|-------|-----|
| Force every article into the same fields | Extract what matters per article |
| Invent banking relevance where there is none | Mark as junk and skip |
| Summarize — "this article discusses..." | Extract — "FCA announced X, banks need Y" |
| Ignore recurrence | Flag if this confirms/contradicts recent brief |
| Process 100 articles without checking budget | Process in batches of 10, report progress |

## Progressive testing

First time: process 3 articles, show output, get feedback.
After confirmation: process the rest of the day's batch.
Never run the full set untested.
