# Web Scraper: Parent `<a>` Link Pattern

Modern blog card layouts (Anthropic, Google DeepMind, likely others) wrap the entire card in an `<a>` tag with headings nested inside — not the traditional `<a>` inside `<h2>`.

## The Problem

Standard CSS selectors like `h2 a` or `article h2 a` return nothing because the `<a>` is an *ancestor* of the heading, not a descendant.

## The Fix

After matching headings without links, walk up the parent chain to find a wrapping `<a>`:

```python
parent = tag.parent
for _ in range(4):
    if parent is None:
        break
    if parent.name == "a":
        link = parent.get("href", "")
        break
    parent = parent.parent
```

## Affected Scripts

- `~/scripts/crons/ai-news-breaking.py` — fixed Feb 14
- `~/skills/ai-news/ai-news-daily.py` — still has the blind spot (backport pending)
