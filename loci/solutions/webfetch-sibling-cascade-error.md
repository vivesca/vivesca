# WebFetch: Sibling Tool Call Cascade Failure

## The Problem

When multiple `WebFetch` calls are made in the same tool-call block and one returns a non-2xx status (e.g. 404), **all sibling calls in the same block fail** with `"Sibling tool call errored"` — even if those URLs are valid.

## Example

```
# All in one block:
WebFetch url1  → 404
WebFetch url2  → "Sibling tool call errored" (url2 was fine)
WebFetch url3  → "Sibling tool call errored" (url3 was fine)
```

## The Fix

Put speculative/uncertain URLs in a **separate block** from critical fetches. If you're not confident all URLs will resolve, split across multiple messages:

```
# Block 1: URLs you're confident about
WebFetch known-good-url1
WebFetch known-good-url2

# Block 2: Speculative URLs (may 404)
WebFetch guessed-url
WebFetch search-constructed-url
```

## When This Hits

- Constructing article URLs from search results (slug may be wrong)
- Fetching from paywalled sites (may 403)
- RSS feeds that have moved (301 → different host, but WebFetch follows then errors)

## Discovered

2026-02-18 during `/ai-news` deep scan — Latent Space URL 404'd, killing 4 parallel fetches.
