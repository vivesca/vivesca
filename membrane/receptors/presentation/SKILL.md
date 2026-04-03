---
name: presentation
description: Reference for visual communication patterns in presentations and data storytelling. Consult when creating slides, LinkedIn visuals, or any content that shows scale, proportion, or adoption data.
user_invocable: true
disable-model-invocation: true
triggers:
  - presentation
  - slides
  - visualization
  - dot grid
  - data storytelling
  - chart
  - infographic
---

# Presentation & Visual Communication Patterns

Reference skill. Consult when Terry is building slides, visualizations, or data-driven content.

## Population-Scale Dot Grid

**When to use:** Showing how small a group is relative to the whole. Adoption rates, market penetration, minority populations — anything where "X% of Y" undersells the visual impact.

**Pattern:**
- Fixed grid (e.g., 50×50 = 2,500 dots), each dot = total ÷ grid size
- Categories ordered large→small, colored distinctly
- Dark/muted for the majority, vivid for the minority
- The emptiness IS the message — don't fill it with labels

**Reference implementation:** Deployed at [Vercel](https://ai-adoption-viz.vercel.app) / [Netlify](https://ai-adoption-corrected.netlify.app)
- Single-file HTML + vanilla JS, no dependencies
- Dark background (#0c0c0c), monospace type
- Interactive legend (click to highlight category)
- Comparison table (original vs corrected) with directional markers

**Provenance research:** `~/notes/Research/AI Adoption Dot Visualization - Provenance.md`

**Key design choices:**
- Grid gap matters — too tight looks like a heatmap, too loose loses density
- 50×50 is a sweet spot for desktop; scales down to mobile with 1px gap
- Bottom-right placement of rare categories draws the eye naturally (reading direction)
- Hover/click interactions add depth without clutter

## General Principles

1. **Show scale, don't state it.** "0.04% use coding tools" is forgettable. 1 red dot in a sea of 2,500 grey dots is visceral.
2. **Fact-check before publishing.** Viral visualizations cherry-pick for drama. Verify against primary sources (vendor reports, not press summaries). The AI adoption chart understated paid users 3× and coding tools 5×.
3. **Comparison tables beat paragraphs.** When correcting or contrasting data, a side-by-side table with directional markers (▲ ~3×) communicates instantly.
4. **Source everything.** Collapsible source list at the bottom. No URL = `[unverified]`.
5. **Dark theme for data viz.** Colored dots pop against dark backgrounds. Light backgrounds wash out subtle color differences.
6. **Single HTML file for portability.** No build step, no dependencies, opens anywhere. React via CDN if needed, but vanilla JS preferred for simple visualizations.

## Deployment Quick Reference

- **Vercel (preferred for speed):** `vercel --prod --yes` from project dir
- **Netlify:** `netlify api createSite --data '{"body":{"name":"site-name"}}'` then `netlify deploy --prod --dir=. --site <id>`
- See `~/docs/solutions/tool-gotchas.md` → Netlify CLI section for non-TTY workarounds
