---
name: assay-source
description: Evaluate which web scraping tool works best for a new content source. Runs Jina/Defuddle/Firecrawl comparison on signal/noise/links. Use when adding a new newsletter, blog, or regulatory source to the scraping pipeline.
user_invocable: true
---

# /assay-source — Web Source Extraction Evaluation

Compare scraping tools on a new source to find the best extractor before committing to a batch pipeline.

## Trigger

- "test scraping on [source]", "which tool for [source]", "add [source] to pipeline"
- Before building any new `*-brief` effector or adding a domain to pinocytosis DOMAIN_HINTS

## Input

User provides a URL to one representative article from the source.

## Procedure

### Step 1: Fetch with all free tools first

```bash
# Tier 1: Free, no dependencies beyond Python/Node
curl -s "https://r.jina.ai/URL" -H "Accept: text/markdown" -H "User-Agent: test/1.0" > /tmp/assay-jina.md
npx -y defuddle-cli parse URL --markdown > /tmp/assay-defuddle.md
python3 -c "import trafilatura; dl=trafilatura.fetch_url('URL'); print(trafilatura.extract(dl, output_format='txt', include_links=True) or '')" > /tmp/assay-trafilatura.md

# Tier 2: Free, needs Playwright
python3 -c "
import asyncio
from crawl4ai import AsyncWebCrawler
async def f():
    async with AsyncWebCrawler(verbose=False) as c:
        r = await c.arun(url='URL')
        print(r.markdown or '')
asyncio.run(f())
" > /tmp/assay-crawl4ai.md

# Tier 3: Free, but plain text (no links)
# Exa — only if you need to test search/extract quality, not for scraping comparison

# Tier 4: Paid — only if free tools all fail or score poorly
pinocytosis --method firecrawl --json URL > /tmp/assay-firecrawl.md
```

Run all free tools first. Only burn a Firecrawl credit if no free tool scores well (signal < 80% or the source is paywalled).

### Step 2: Define signal markers

Read the article content and identify 15-20 markers that MUST be present in a good extraction:
- Key entity names (people, companies, regulators)
- Key statistics/numbers
- Section headers or structural markers
- Specific quotes or phrases

Also define noise markers (~10): cookie, subscribe, sign up, newsletter, privacy policy, footer, navigation, Accept all, terms and conditions, copyright.

### Step 3: Score each tool

For each tool's output, count:
- **Signal**: how many of the 15-20 markers are found
- **Noise**: how many noise markers are found
- **Ratio**: signal / (noise + 1)
- **External links**: `](http` links NOT pointing to the source domain, with anchor text > 2 chars
- **Chars**: total length (for reference only — NOT a quality proxy)

### Step 4: Classify the link delta

If one tool has significantly more links than another:
- List every link the winner has that the runner-up doesn't
- Classify each as: NEWS (journalism source), BANK (bank/regulator doc), PDF, TECH/LINKEDIN, IMAGE (junk), PROMO (junk), JUNK
- Report: "X valuable, Y junk" — the delta might be footer noise, not article sources

### Step 5: Check metadata

For each tool, note:
- Date in body? (Y/N)
- Author in body? (Y/N)
- Title extracted? (Y/N)

These matter less for LLM consumption but note them.

### Step 6: Recommend

Present results as a table and state the winner with reasoning. Ignore:
- Char count differences (misleading — more chars often = more nav junk)
- Bold/italic formatting differences (irrelevant for LLM consumption)
- Image count differences

The winner is the tool with: highest signal coverage, lowest noise, source links preserved, and lowest cost.

### Step 7: Update routing

If the winner is clear:
1. Add domain to `DOMAIN_HINTS` in `~/germline/effectors/pinocytosis`
2. Note the result in `~/epigenome/marks/finding_web_extraction_benchmark_20260401.md`

## Key Lessons (from Evident benchmark)

- **Char count lies.** Jina's 47K on HKMA was 90% nav junk vs Defuddle's clean 5K with identical signal.
- **"More links" can be junk.** Firecrawl's 15 extra links on Evident were all staff LinkedIn profiles from the footer.
- **Jina auth gotcha.** Bearer token returns 403 from Python urllib. Use unauthenticated with User-Agent header for Reader.
- **Firecrawl penetrates paywalls** that others can't (FT: 9/9 signal vs next best 5/9). Reserve credits for this.
- **Defuddle and Jina tie on public pages** — same signal, same noise, Jina has no local dependency.

## Output

The recommendation plus a decision: "Use [tool] for [domain]. Added to DOMAIN_HINTS."

## Motifs
- [audit-first](../motifs/audit-first.md)
- [escalation-chain](../motifs/escalation-chain.md)
