---
name: limen
description: Generate Midjourney images from the terminal. Use when user wants to create images with Midjourney.
---

# Limen — Midjourney CLI

Generate Midjourney images from the terminal. `limen "prompt"` → submit → poll → download 4 images.

## When to Use

- User wants to generate an image with Midjourney
- LinkedIn post needs a branded thumbnail
- Any "make me an image" request where MJ quality is wanted

## Quick Reference

```bash
# Basic generation
limen "a glass cathedral, architectural photography --ar 16:9"

# With style reference codes (Perplexity aesthetic)
limen "AI governance in banking, abstract visualization --sref 6726456675 1575582868 7906576498 --ar 1:1"

# With moodboard
limen "your subject --p 7347088266165747749 --ar 1:1"

# Custom output directory
limen "prompt" --out ./my-images

# Extract/refresh cookies only
limen login
```

## Key MJ Parameters

Pass inline with the prompt text — limen submits them verbatim to MJ:

- `--ar 16:9` — aspect ratio (1:1 for LinkedIn square, 16:9 for landscape)
- `--v 6.1` — version (omit to use default v7)
- `--sref [codes]` — style reference codes for consistent aesthetic
- `--p [moodboard-code]` — moodboard for brand consistency
- `--style raw` — more photographic output
- `--c [0-100]` — chaos (low = repeatable)
- `--sw [0-1000]` — style weight

## Gotchas

- **`--sref` codes require v7.** Adding `--v 6.1` silently breaks `--sref` — generation never starts, no error. Omit `--v` to use default.
- **`--sref` accepts external image URLs.** Not just MJ codes — any public image URL works (tested with CloudFront CDN). Pass inline: `--sref https://example.com/img1.png https://example.com/img2.png`.
- **Cookies expire.** JWT-based, auto-refreshed from Chrome via kleis. If auth fails, run `limen login` or log in at midjourney.com in Chrome first.
- **Keychain must be unlocked.** `security unlock-keychain ~/Library/Keychains/login.keychain-db` if kleis fails.
- **headless: false.** Limen opens a visible browser window. This is required — Cloudflare blocks headless.
- **Poll timeout is 5 min.** Most generations complete in 15-30s. If it times out, the prompt was likely silently rejected.
- **Previous images on page.** Polling counts new images above baseline. If 0 new detected, no stale images are returned.

## Architecture

```
limen "prompt"
  ├─ kleis midjourney.com          → decrypt Chrome cookies (Rust CLI)
  ├─ larvo createStealthContext()  → stealth Playwright browser (npm)
  ├─ navigate to midjourney.com/imagine
  ├─ submit prompt text
  ├─ poll for 4 new cdn.midjourney images
  └─ download full-res ONGs
```

## LinkedIn Brand Images

See `~/docs/solutions/linkedin-thumbnail-brand-style.md` for:
- Perplexity creative ambassador style codes
- Terry's moodboard codes
- Prompt framework and dimension specs
- SREF browser rankings

## Dependencies

- **kleis** (`cargo install kleis`) — Chrome cookie extraction
- **larvo** (`pnpm add larvo`) — stealth browser contexts
- **Chrome** — must be logged in at midjourney.com
- **Midjourney subscription** — active plan required

## Source

`~/code/limen/` — TypeScript, private GitHub repo
