---
name: kinema
description: Render an HTML animation page to MP4 / GIF / PNG-frames, optionally with background music. Use when the user wants to turn a working HTML animation into a video file (e.g. for a garden post hero, a Twitter share, a launch reel, a deck embed, or a README demo). Greek κίνημα — motion. Triggers — "render to MP4", "export this animation", "turn this HTML into a video", "make a GIF", "60fps video", "add BGM to this video", "video for [post]". NOT for designing the animation itself (use frontend-design / animate) — only for capturing it.
version: 0.1.0
user-invocable: true
argument-hint: "[html-file] [--mp4|--gif|--with-bgm <mood>]"
---

# kinema — HTML animation → MP4 / GIF

Wraps two extracted scripts pinned at `~/germline/effectors/huashu-extracts/`. Skill is the *judgment layer*: when to render, what target format, what BGM mood, when to skip.

## Source

Scripts and audio assets cherry-picked from [`alchaincyf/huashu-design`](https://github.com/alchaincyf/huashu-design) at SHA `23f60d9b4304f20851469987c6e2c92242b94a45` (2026-04-25). The upstream skill itself was rejected — see `~/germline/effectors/huashu-extracts/PROVENANCE.md` for the rationale and the monthly upstream-watch routine.

## Hard preconditions

Before invoking the renderer:

1. **The HTML must be visually verified.** Open it. The animation should run end-to-end without errors. Don't render broken motion — the cost of a bad render is wasted minutes; the cost of a re-render after fixing is the full pipeline again.
2. **The HTML must signal animation-ready.** Either it uses the upstream `animations.jsx` Stage component (sets `window.__ready` automatically) or you've added: `document.fonts.ready.then(() => requestAnimationFrame(() => { window.__ready = true; }));` after first render. Without this, the recorder falls back to a 1.5s font-wait and may leave 1-2s of black at the start.
3. **Confirm duration.** Pass `--duration=N` matching the actual animation length. Default 30s — over-rendering is ~free, under-rendering cuts the climax.

## Format choice

| Target | Format | When |
|---|---|---|
| Twitter/X, Slack, README preview | GIF 960×540 15fps palette-optimized | < 30s, ≤ 4 MB |
| Garden post hero, blog embed | MP4 25fps 1920×1080 H.264 CRF 18 | most cases, 1-2 MB |
| Portfolio / Bilibili / "feels expensive" | MP4 60fps 1920×1080 (minterpolate) | only when the motion benefits — text reveals don't need 60fps |

Default to 25fps MP4 unless the user explicitly asks for higher.

## Commands

```bash
# 1. Bare MP4 (silent)
NODE_PATH=$(npm root -g) node ~/germline/effectors/huashu-extracts/scripts/render-video.js \
  <html-file> --duration=30

# 2. GIF (after step 1)
~/germline/effectors/huashu-extracts/scripts/convert-formats.sh <video.mp4> --gif

# 3. Add BGM (after step 1)
~/germline/effectors/huashu-extracts/scripts/add-music.sh <video.mp4> \
  --mood=<tech|tutorial|educational|ad>
```

BGM moods are scene-coded (see `~/germline/effectors/huashu-extracts/assets/bgm/`):
- `tech` — product launches, capability reveals
- `tutorial` — walk-throughs, explainers
- `educational` — slow exposition
- `ad` — short upbeat sells

For garden posts specifically (Terry's prose-only rule): export silent. Audio belongs on platforms where users opted in (Twitter autoplay, video-first sites). On terryli.hm, autoplay audio is hostile.

## When NOT to render

- Animation isn't visually verified yet → fix first.
- Static infographic → no, just take a PNG.
- The user asked for "a video" but the source is text-only → push back; suggest motion design first.
- Garden post for terryli.hm where the post is fundamentally prose → check whether a hero animation actually adds — most posts don't need one.

## Dependencies (one-time)

```bash
npm install -g playwright pptxgenjs sharp
playwright install chromium
# ffmpeg via brew/apt as standard
```

## Knowledge base

When designing the source animation (before rendering), consult:
- `~/germline/effectors/huashu-extracts/references/animation-best-practices.md` (506 lines)
- `~/germline/effectors/huashu-extracts/references/video-export.md` (209 lines)
- `~/germline/effectors/huashu-extracts/references/audio-design-rules.md` (260 lines, only when BGM is in scope)

## Limits

- The upstream `animations.jsx` React+Babel-standalone scaffold is *not* extracted. To use the Stage/Sprite component model, copy from `/tmp/huashu-design/assets/animations.jsx` (or re-clone — pinned SHA `23f60d9b`) into the project. Decide per-project whether that scaffold is worth its weight or whether bare CSS animations / Framer Motion are simpler.
- HTML → PPTX is a separate concern — bare scripts at `~/germline/effectors/huashu-extracts/scripts/{html2pptx.js,export_deck_pptx.mjs}`. Not routed through this skill yet (rare use case).
