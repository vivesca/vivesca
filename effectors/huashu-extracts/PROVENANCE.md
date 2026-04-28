# huashu-design extracts

Cherry-picked infrastructure from a third-party design skill. Wholesale install rejected (Chinese SKILL.md, broad triggers collide with `frontend-design`/`animate`/`critique`/`transcription`, single-maintainer 9-day-old repo). Extracts are pinned — not tracked to mainline.

## Source
- Repo: https://github.com/alchaincyf/huashu-design
- Pinned SHA: `23f60d9b4304f20851469987c6e2c92242b94a45` (2026-04-25)
- Extracted: 2026-04-28
- Maintainer health at extract: 1 contributor, 30 commits across 4 days, 8.8k stars in 9 days (viral velocity, not validated adoption)

## What was taken
- `scripts/render-video.js` — HTML animation → MP4 via Playwright `recordVideo` + ffmpeg with font-ready signaling. Fills genuine gap (no HTML→video path before).
- `scripts/html2pptx.js` (978 LOC) + `export_deck_pptx.mjs` + `export_deck_pdf.mjs` — HTML slide → editable PPTX/PDF via pptxgenjs.
- `scripts/add-music.sh` + `convert-formats.sh` — BGM mixdown + format conversion glue.
- `assets/sfx/` — 9 SFX category folders (ui, keyboard, terminal, transition, impact, magic, progress, container, feedback).
- `assets/bgm/` — 6 scene BGMs (ad, educational, educational-alt, tech, tutorial, tutorial-alt).
- `references/{video-export,editable-pptx,audio-design-rules,sfx-library,animation-best-practices}.md` — knowledge base.

## What was rejected
- The `SKILL.md` itself (801 lines Chinese, broad triggers, philosophy-heavy, overlaps existing stack).
- Brand-asset protocol (overlaps existing `frontend-design`).
- 20 design philosophies / Junior Designer workflow / 5-dim review (overlaps `frontend-design`, `transcription`, `critique`).
- React-Babel slide stack (`deck_stage.js`, `deck_index.html`, `animations.jsx`, `design_canvas.jsx`) — extracted only on demand, not by default.
- Demo HTML files — useful as visual reference, not adopted as runnable.

## Update policy
Pinned. Do NOT auto-pull. Monthly upstream check via scheduled agent; manual diff + maintainer-health re-gate before any cherry-pick of new commits. Re-assay maintainer health at 3 months — if still 1 maintainer, treat fork as terminal.

## Dependencies (when first used)
- `npm install -g playwright pptxgenjs sharp`
- `ffmpeg` on PATH

## Local audio license
The audio assets were redistributed by the upstream author as part of the skill. Personal-use only — do not redistribute outside this organism without re-verifying licensing.
