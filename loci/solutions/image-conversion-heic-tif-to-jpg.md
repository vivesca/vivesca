# HEIC/TIF to JPG Conversion

## Best tool: ImageMagick (`magick`)

```bash
magick input.heic -quality 92 -sampling-factor 4:4:4 output.jpg
```

## Quality sweet spot: q92

Tested on 3840x5760 headshot (TIF source):

| Quality | Size | Notes |
|---------|------|-------|
| q85 | 2.5 MB | noticeable on close inspection |
| q90 | 3.4 MB | good for web |
| q92 | 3.8 MB | sweet spot — visually lossless |
| q95 | 5.3 MB | diminishing returns start here |
| q97 | 7.5 MB | waste |
| q100 | 12.2 MB | bloated, no perceptible gain over q95 |

## Claude Code preview pattern

The Read tool can display images but has a 256KB size limit. HEIC photos from iPhone/Ray-Ban Meta are typically 1-4MB, so they need converting first.

```bash
sips -s format jpeg -s formatOptions 50 input.HEIC --out /tmp/preview.jpg
```

- **`sips`** over `magick` here — it's built into macOS, no install needed, and fast for previews.
- **Quality 50** is fine for visual inspection — keeps files well under 256KB. Not for archival.
- **`/tmp/` is fine** for ephemeral previews (won't survive reboot, but doesn't need to).
- **Batch preview:** `for f in *.HEIC; do sips -s format jpeg -s formatOptions 50 "$f" --out "/tmp/${f%.HEIC}.jpg"; done`

## Gotchas

- **sips default quality is NOT max.** `sips -s format jpeg` with no quality flag produces ~60-70% of max quality size. For archival, always set explicit quality.
- **4:4:4 chroma subsampling** preserves full colour detail. Default (4:2:0) subsamples chroma — fine for web, not for headshots/print.
- **cjpegli (Google's Jpegli)** is 35% better than traditional JPEG encoding at same quality, but not available as standalone binary in Homebrew's `jpeg-xl` package. Would need to build from libjxl source.

## Headshot vault location

`~/code/vivesca-terry/chromatin/assets/headshots/`
