# remark-citation plugin

Build-time Markdown citation tooltip system for the terryli.hm Astro blog.

## What it does

Transforms standard Markdown links with a title attribute into citation links. Desktop gets Tippy.js hover tooltips; mobile gets numbered footnotes.

## Syntax

```md
[Link text](https://url.com "Institution § One-sentence summary of the paper.")
```

Use `§` to separate institution from summary. If no `§`, the whole title is used as summary.

## Files

- `~/code/blog/src/utils/remark-citation.ts` — remark plugin (build time)
- `~/code/blog/src/layouts/PostDetailsChiri.astro` — Tippy init + mobile footnote injection (runtime)

## Dependencies

```
tippy.js, unist-util-visit, unified, @types/mdast
```

## How it works

1. **Build time:** `remark-citation` visits all `Link` nodes with a title. Injects `class="citation-link"`, `data-institution`, `data-summary`, `data-footnote-index` via `hProperties`.
2. **Runtime desktop** (`hover: hover`): Tippy tooltip shows institution (blue, uppercase) + summary. Click goes to paper.
3. **Runtime mobile** (`hover: none`): Superscript `[N]` injected after each citation link. Numbered `<section id="citation-footnotes">` appended to article with institution, summary, and ↗ link.

## Config

Wired into `astro.config.ts`:
```ts
import remarkCitation from "./src/utils/remark-citation";
// ...
markdown: {
  remarkPlugins: [..., remarkCitation],
}
```

## Status

Built Mar 8 2026. Build passes. Browser test pending.
