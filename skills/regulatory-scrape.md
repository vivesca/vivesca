# regulatory-scrape

Extract regulatory documents as frontmattered markdown to `~/epigenome/chromatin/euchromatin/regulatory/`.

## Frontmatter

```yaml
---
title: "..."
issuer: fca|pra|boe|ico|dsit|cma|hkma|sfc|mas|eba
date: YYYY-MM-DD
source: <URL>
type: supervisory-statement|discussion-paper|feedback-statement|guidance|white-paper|report|letter|minutes|survey|strategy|code-of-practice|consultation|call-for-input
status: final|consultation|live
---
```

## Filename convention

`{issuer}-{YYYY-MM}-{slug}.md` — e.g. `fca-2024-04-ai-update.md`

## Per-regulator knowhow

### Bank of England / PRA (bankofengland.co.uk)
- **Blocks bots.** WebFetch and Jina return 403/422. Use `curl` with browser User-Agent header.
- **PDFs preferred.** Substantive content often in PDF at `/-/media/boe/files/...`. Landing pages are stubs.
- **CID-encoded fonts.** Some PDFs defeat pypdf/pdfminer/pdftotext. Use PyMuPDF (`fitz`) as fallback.
- **HTML extraction:** If the page has a `<main>` element, parse that — skip nav/footer.
- Domain hints: add `"bankofengland.co.uk": "curl"` mentally — pinocytosis defuddle will fail.

### FCA (fca.org.uk)
- **Mixed HTML + PDF.** Some docs are HTML pages, others are PDFs linked from landing pages.
- **PDF paths:** usually `/publication/.../*.pdf` or `/publications/.../*.pdf`.
- **Landing pages:** check for "Download PDF" or "Read the full document" links before scraping page text.
- defuddle/Jina generally work for HTML pages.

### gov.uk (DSIT, CMA)
- **Clean and scrape-friendly.** defuddle and Jina both work well.
- **HTML version preferred** — many docs have both HTML and PDF; HTML extracts cleaner.
- **Long docs:** some (AI Playbook = 228K) are very large single pages. No special handling needed.

### ICO (ico.org.uk)
- **Multi-page guidance.** Major guidance docs (ExplAIn, AI & Data Protection) are split across 10-20 sub-pages.
- **Must consolidate.** Fetch the overview page, extract all section links, fetch each, combine into one file.
- **Blog posts** are single pages, straightforward.
- defuddle/Jina work for individual pages.

### HKMA (hkma.gov.hk)
- defuddle works well. Circulars are clean HTML.
- Some older docs are PDF-only.

### General rules
1. Always check if a landing page links to a PDF — the PDF has the real content.
2. Strip cookie banners, navigation chrome, footer links, sidebar content.
3. Preserve paragraph numbers (e.g. "2.14"), footnotes, and hyperlinks to referenced standards.
4. Convert chart/figure descriptions to text (ranked lists, tables) since images can't be rendered.
5. If a document has annexes/appendices, include them — they often contain the actionable detail.
6. Use `pinocytosis <url>` as first attempt. If it fails or returns thin content, apply per-regulator knowhow above.

## Batch workflow

For a new jurisdiction:
1. Research regulators and build a catalog (TSV or markdown table with URLs)
2. Dispatch CC agents in parallel (7 at a time), each with 1-3 URLs + this skill's knowhow
3. Agents use pinocytosis + per-regulator fallbacks
4. Check results: `ls -lh ~/epigenome/chromatin/euchromatin/regulatory/{issuer}*`
5. Re-fetch any failures

## CLI effector

`regulatory-scrape` handles simple single-page grabs:
```
regulatory-scrape <url> --issuer fca --date 2024-04-22 --title "AI Update" --type guidance
regulatory-scrape --batch catalog.tsv
```

For multi-page docs, PDF extraction, or bot-blocked sites, use agent dispatch instead.
