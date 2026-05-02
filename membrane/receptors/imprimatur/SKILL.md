---
name: imprimatur
description: Produce a banner for an HSBC committee paper Word template — Midjourney atmospheric background + official HSBC hexagon overlay (Open or Iconic variant). Single-call CLI. Triggers — "hsbc banner", "paper banner", "committee paper banner", "imprimatur".
user_invocable: true
triggers:
  - imprimatur
  - hsbc banner
  - committee paper banner
  - paper banner
  - generate banner
context: fork
epistemics: [create]
model: sonnet
---

# imprimatur — committee-paper banner producer

Produce a polished banner for an HSBC committee paper banner slot using:
- Midjourney for the atmospheric photo background (via limen on Mac, with cookie-bridge auto-refresh)
- Official HSBC hexagon overlay (Open or Iconic variant from bundled SVG)
- Sized variants matching the Word template slot (709×222) at 16:5 clean ratio

Latin "let it be printed" — the imprimatur is the institutional mark of authorisation that goes onto the published artefact.

## When to use

- Producing a banner for an HSBC committee paper (Board paper, AIRCo paper, CAIO brief, etc.) where the Word "Key Information" template has a banner slot
- Need on-brand HSBC visual language without manually re-deriving the cookie bridge / JWT refresh / composite pipeline
- Want a one-call workflow: prompt → 4 MJ variants → picked composite → sized ONGs

NOT for:
- Garden post hero images (different register; use limen directly)
- LinkedIn thumbnails (different brand context; use limen directly)
- Internal chromatin notes that don't externalise

## Quick reference

```bash
# Generate 4 candidates for review (no --pick)
python3 ~/.claude/skills/imprimatur/scripts/imprimatur.py \
    "wide horizontal photograph 16:5 ultra wide, vast atmospheric architectural cavern, light streaming through structural depth, dark moody warm tones, no text no people no logos" \
    --moodboard m7426636666346930219 \
    --variant open \
    --name banner-eunomia \
    --output-dir ~/epigenome/chromatin/immunity/assets/eunomia/

# Then pick the best of 4 and produce sized variants
python3 ~/.claude/skills/imprimatur/scripts/imprimatur.py \
    "...same prompt..." \
    --moodboard m7426636666346930219 \
    --variant open \
    --name banner-eunomia-final \
    --output-dir ~/epigenome/chromatin/immunity/assets/eunomia/ \
    --pick 1
```

## Variants

- **`--variant open`** (default for atmospheric/dark backgrounds) — 4 dark-red HSBC triangles (#B00010), inner centre transparent so photo shows through. Mirrors HSBC creative_hexes_poster.jpg brand language.
- **`--variant iconic`** — full official HSBC mark (4 red triangles + white centre rectangle), standard #db0011 red. Use over light/clean backgrounds where the mark should not be transparent.

## Outputs

For `--name banner-x` and `--pick N`:
- `banner-x.png` — source (typically 1952×608 or similar from MJ at 16:5)
- `banner-x-16x5-retina-1424x445.png` — recommended for Word paste
- `banner-x-16x5-1x-712x222.png` — direct slot size if file size matters

## Mandatory visual verification before declaring done

**Always Read the source PNG before reporting "banner done" to Terry.** The 2 May 2026 session shipped 4 consecutive banner versions (v00.01-v00.04) with a missing right-pointing hex triangle because `render_hex_overlay` had a hardcoded crop that chopped one of the four polygons. The bug was discovered visually by Terry, not by the script — there was no error to surface. Composite pipelines have many silent failure modes (cropped overlay, wrong red shade, hex sized wrong, off-centre composition, MJ photo with text/people/logos that snuck through prompt) and ALL of them require a human-eye check.

Procedure (mandatory, not advisory):
1. After `imprimatur.py` returns, immediately `Read` the source `banner-x.png` (which Claude Code renders as image).
2. Verify visually: (a) all 4 hex triangles present and pointing inward to a centre, (b) red shade matches variant (#B00010 dark for Open, #db0011 standard for Iconic), (c) hex centred and prominent without dominating, (d) no text/people/logos in the MJ background, (e) atmospheric register matches the paper's tone.
3. If any check fails, regenerate before reporting. Do NOT report "banner done" then await Terry's visual review — that flips the verification cost onto Terry and recreates the right-triangle-missing failure mode.

## Pipeline

1. **JWT freshness check** — if cached JWT in `/Users/terry/.limen/cookies.json` has <5 min remaining, drives Chrome on Mac to midjourney.com via osascript to refresh
2. **Cookie bridge** — fetches Mac Chrome cookies via porta cookie bridge (`http://127.0.0.1:7743`) and writes to limen cache (bypasses kleis/keychain block over ssh)
3. **Limen generation** — runs MJ via `ssh mac limen imagine ...` with `--ar 16:5 --style raw --stylize 200` plus user prompt + optional moodboard
4. **Pull images** — scp 4 generated ONGs to soma `/tmp/imprimatur/`
5. **Composite hexagon** — render bundled SVG via cairosvg; alpha_composite at center of background using PIL
6. **Sized variants** — write source + retina + 1x variants

## Gotchas (each one bit me at least once during 2 May session)

1. **chromatin/.gitignore line 38 ignores `assets/`** — output ONGs need `git add -f` to commit. Skill writes to user-specified `--output-dir`; user is responsible for committing.

2. **Limen keychain block over ssh** — kleis can't access Chrome Safe Storage from non-GUI session. Skill bypasses entirely via porta cookie bridge.

3. **JWT staleness in Chrome itself** — bridge faithfully fetches whatever Chrome has. If Chrome hasn't visited MJ in ~60min, JWT is stale even after bridge. Skill handles by driving Chrome to MJ via osascript before bridging.

4. **Don't include "hexagon" or "logo" in MJ prompt** — sref/prompt that mentions HSBC or hexagon causes MJ to reproduce approximations of the mark (brand-policy risk). Skill prompt should be pure background description; mark is composited in post.

5. **`__Host-` cookies require www subdomain query** — bridge endpoint `cookies?domain=midjourney.com` returns analytics only; `cookies?domain=www.midjourney.com` returns __Host- prefix cookies including the JWT. Skill queries both and merges.

6. **Open vs Iconic Hexagon variant choice** — Open over photo backgrounds (transparent center shows photo); Iconic over clean backgrounds (white center). Skill defaults to Open since most banners use atmospheric photos.

7. **Red shade matters** — standard #DA291C reads bright/marketing. HSBC's atmospheric brand assets use deeper red (~#B00010). Skill uses #B00010 for Open variant.

## Prerequisites

- Mac with Chrome logged in to midjourney.com (active subscription)
- Mac cookie bridge service running on port 7743 (porta)
- Limen installed on Mac at `~/code/limen` (TypeScript + pnpm)
- `cairosvg` and `pillow` on soma (`pip install cairosvg pillow`)
- ssh access from soma to mac

## Source

`~/.claude/skills/imprimatur/`
- `SKILL.md` — this file
- `scripts/imprimatur.py` — main CLI
- `assets/hsbc_open_hex_dark.svg` — Open Hexagon (4 dark-red triangles, transparent center)
- `assets/hsbc_iconic_hex.svg` — Iconic Hexagon (4 red triangles + white rect, standard mark)

## See also

- `limen` — Midjourney CLI (the underlying generation tool)
- `porta` — cookie bridge service (provides the auth substrate)
- `2026-05-02-hsbc-banner-workflow-learnings.md` (chromatin) — the workflow learning doc that this skill operationalises
