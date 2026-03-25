# LinkedIn Visual Brand

Created: 2026-02-27
Updated: 2026-02-28
See also: `midjourney-reference.md` (codes, tools, prompt framework)

## Why Bother

LinkedIn algorithm favours posts with images. A recognisable visual style = people stop scrolling before reading the byline. Every does this well — one creative lead (Lucas Crespo), AI-generated, one prompt at a time.

## Image Dimensions

- Post (square): **1200 x 1200** (1:1)
- Post (landscape): **1200 x 628** (1.91:1)
- Newsletter header: **1280 x 720** (16:9)
- Vertical (best engagement): **4:5** or **9:16** — takes more feed space

## Workflow

1. Generate 1-3 "master" images capturing your brand look
2. Use `/describe` on any image you like to reverse-engineer the prompt
3. Save those as `--sref` references
4. Build prompt template with fixed params
5. Add text/logo overlay in Canva

### Prompt Structure (Always Same Order)
```
[subject] → [composition] → [style/brand keywords] → [fixed params]
```

### Reusable "Style Snippet"
A block of keywords pasted at the end of every prompt:
```
cool blues, volumetric lighting, minimalist editorial,
sans-serif typography space --ar 16:9 --sref [your-ref-url] --sw 600
```

## Quickstart Checklist

1. Pick 3 adjectives for your brand (e.g. "precise, warm, technical")
2. Build a **Midjourney Moodboard** with images matching your aesthetic
3. Test with: `limen "[subject] --p [your-moodboard-code] --ar 1:1"`
4. Optionally layer a `--sref` code or Perplexity ambassador codes on top (see `midjourney-reference.md`)
5. Rate 200+ images to unlock `--profile` (optional but recommended)
6. Lock your params (aspect ratio, chaos, stylize)
7. Text overlay in Canva
8. Use consistently for 10+ posts

## Every Cover Art — Reverse-Engineered Style

Scraped 47 cover images from every.to (CloudFront CDN, `robots.txt` allows AI crawlers). Curated 10 strongest exemplars of their signature aesthetic.

### Aesthetic DNA

- **Engraving/woodcut/etching** illustration (fine crosshatch line work)
- **Neoclassical/Greco-Roman figures** (statues, classical dress, columns)
- **Bold flat color backgrounds** (teal, ochre/orange, yellow, deep blue, hot pink)
- **Anachronistic juxtaposition** — classical figures + modern tech objects
- **Editorial magazine composition** — single focal figure, clean negative space

### Curated 10 (source: `~/notes/assets/every-covers/`)

| # | File | Subject | Background |
|---|------|---------|------------|
| 1 | 3889 | Claude in trenchcoat | ochre |
| 2 | 3895 | Dandelion figures | yellow |
| 3 | 3939 | Roman pizza busts | teal |
| 4 | 3907 | Orchestra conductor | teal |
| 5 | 3932 | Roman figure with wine | yellow |
| 6 | 3938 | Finance woman at desk | orange |
| 7 | 3888 | Neoclassical rotunda | orange/blue |
| 8 | 3896 | Horseback riders | orange |
| 9 | 3890 | VR headset figure | teal |
| 10 | 3904 | Construction workers | sunset gradient |

### CloudFront URLs (public, live as of 2026-02-28)

```
https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3889/full_page_cover_Claude_on_trenchcoat_1.png
https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3895/full_page_cover_Find_the_social_dandelions.png
https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3939/full_page_cover_greco_roman_pizzas.png
https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3907/full_page_cover_What_the_Team_Behind_Cursor_Knows_About_the_Future_of_Code.png
https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3932/full_page_cover_What_Is_Taste_Really.png
https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3938/full_page_cover_Claude_Code_Finance_Fixed.png
https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3888/full_page_cover_skycrapper_2.png
https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3896/full_page_cover_horses_final.png
https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3890/full_page_cover_5_archetypes_1%282%29.png
https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3904/full_page_cover_Compound_Engineering__How_Every_Codes_With_Agents%282%29.png
```

### Working --sref Template (tested 2026-02-28)

MJ v7 accepts external CDN URLs in `--sref`. Tested with 3 URLs — strong style transfer (engraving + flat colour backgrounds). Use top 3 for speed, all 5 for stronger lock:

```bash
# Top 3 (fast, good style transfer)
EVERY_SREF_3="--sref https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3889/full_page_cover_Claude_on_trenchcoat_1.png https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3939/full_page_cover_greco_roman_pizzas.png https://d24ovhgu8s7341.cloudfront.net/uploads/post/cover/3938/full_page_cover_Claude_Code_Finance_Fixed.png"

# Usage
limen imagine "[subject], editorial illustration ${EVERY_SREF_3} --ar 16:9"
```

### Create a Proper Moodboard (2 min, manual)

Cloudflare blocks headless automation on midjourney.com. Do this in Chrome:

1. Go to [midjourney.com/moodboards](https://www.midjourney.com/moodboards) (must be logged in)
2. Click **Create New Moodboard**
3. Paste these CloudFront URLs one at a time (or drag-drop the files from `~/notes/assets/every-covers/`)
4. Name it "Every Editorial" or similar
5. Copy the moodboard code → update this doc + `midjourney-reference.md`

Once you have the code:
```bash
limen imagine "[subject], editorial illustration --p [MOODBOARD_CODE] --ar 16:9"
```

### Terry's Every-Style Moodboard Code

`--p [TODO: paste code after manual creation]`

### Next Steps

- [ ] Create Midjourney moodboard from curated 10 (2 min in Chrome)
- [ ] Optionally run Style Creator for a dedicated SREF code
- [ ] Test with different subjects to verify consistency

## Style Selection Workflow

1. **Midjourney Moodboard** — curate images that match your brand feel (simplest, most flexible)
2. **Midjourney Style Creator** — generate a custom SREF code as supplement (5-15 rounds)
3. **Lummi.ai Editorial** — scan ~20 curated styles in 10 min for inspiration
4. **Perplexity ambassador codes** — try latest 2026 codes as starting point
5. Mix and match: `[subject] --p [moodboard-code] --sref [optional code]`
