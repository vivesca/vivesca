# Glasses Shopping Research — Know-How (OWNDAYS, JINS, Zoff)

**Created:** 2026-02-14
**Context:** Researching glasses for Capco consulting role

## Key Learnings

### Website Structure

- OWNDAYS HK catalog is JS-rendered SPA. Category listing pages don't expose product data in raw HTML — WebFetch gets navigation/menus only.
- **Individual product pages DO work** with WebFetch — specs, colours, prices, and image URLs are all in the HTML.
- Product URLs follow pattern: `owndays.com/hk/zh_hk/products/{MODEL_NUMBER}`
- **Colour variants require `?sku=` parameter:** Default page shows first colourway only. Append `?sku=XXXX` to get variant images/specs (e.g., SENICHI35: 7607=Black, 7608=Brown Demi, 7609=Dark Smoke). SKU numbers are in the page HTML even when variant images aren't.
- SENICHI line uses sequential numbering (SENICHI7 through SENICHI40 as of Feb 2026). Can enumerate exhaustively.

### Image Verification

- Each product page has a hero gallery (images 1-4) followed by brand marketing images, then related product thumbnails at the bottom.
- **First `storage/products/*.webp` URL on the page IS the hero image.** Safe to grab with `grep -o 'storage/products/[a-f0-9-]*\.webp' | head -1`.
- Download with curl, view with Read tool (WebP format works with Read).
- Cross-sell images appear AFTER the hero gallery — they won't pollute a `head -1` grab.

### Catalog Search Strategy

1. **Shape filters for initial sweep:** `?shape=boston&gender=male`, `?shape=wellington&gender=male`, `?shape=square&gender=male`. These pages are JS-rendered so use the agent (100 tool calls needed for full crawl).
2. **Sequential enumeration for specific lines:** For premium lines like SENICHI, enumerate model numbers sequentially. Check for 404 to find the end of the line.
3. **Visual review is essential:** Specs alone mislead. JD1009Y-8A sounded like "dark titanium boston" but was actually black rims with gold hardware — completely different aesthetic. Always download and view product images before finalising recommendations.
4. **"Out of stock" online ≠ unavailable:** OWNDAYS runs separate online/in-store inventory. Most models are in-store only. Don't filter by availability.

### Spec Gotchas

- "Boston/polygon" dual-categorisation exists (e.g., SENICHI37). Worth looking at visually — some read more boston, some more polygon.
- Lens width alone doesn't determine how wide a frame sits. Total frame width matters but isn't listed on the site. The 48-50mm range is a proxy.
- Bridge width affects nose fit more than comfort — wider bridge (22mm+) can sit differently on Asian nose bridges despite "Asian fit" nose pads.
- Weight varies 8g-28g across similar-looking frames. Celluloid (SENICHI) runs 16-25g; resin (AIR) runs 8-13g.

### Shopping Strategy

- OWNDAYS stores: Hysan Place (CWB), Langham Place (MK), MOKO, APM.
- Bring model numbers to the store. Staff can pull from back stock.
- In-store try-on checklist matters more than online research — fit is everything.

## JINS HK Website

- Angular SPA. Category listings work but **no frame dimensions on HK site** — lens width, bridge, temple length are absent.
- Cross-reference dimensions from JINS US (`us.jins.com`) or JINS Japan (`jins.com/jp`) — universal model numbering.
- Colour codes are numeric (00=black, 86=dark tort, 82=tort, 94=black, 09=matte black). NEW CLASSIC line uses its own codes (18, 29).
- Premium lines: Made in Japan ($1,899), UKIYO ($1,899), Combination Made in Japan ($1,899), NEW CLASSIC ($1,399).
- **JINS SABAE** (top-tier) not listed on HK site — ask in-store.
- 11 stores in HK. No online ordering — catalog only.
- Product images at `jins.com.hk:8000/files/{uuid}.jpg` — note the port 8000.

## Zoff HK Website

- Shopify-based (`hk.zoff.com`). **Full specs listed on every product page** — best of the three brands for online research.
- Images on Shopify CDN: `cdn.shopify.com/s/files/1/0783/0129/9002/files/{model}-{colour}_01.jpg`
- **All prices include standard lenses** — major cost advantage vs OWNDAYS (frame only) and JINS (varies).
- Made in Japan line all priced at HKD 1,698. Standard tiers: $598 (sale) → $798-1,098 (classic) → $1,198 (trend) → $1,698 (premium/MIJ).
- Zoff skews large — most men's frames are 52-56mm. Smaller frames (47-51mm) often tagged "Women" or "Unisex" but are fine for anyone.
- 15 stores in HK. Glasses ready in ~30 minutes.

## Cross-Brand Comparison Notes

- **Always compare total cost.** Zoff includes lenses; OWNDAYS and JINS may not. A $1,698 Zoff frame = ~$2,200+ at OWNDAYS after lens add-on.
- **Weight matters more than expected.** Range is 7g (Zoff titanium) to 39.5g (JINS UKIYO). Heavy frames cause nose-pad marks and headaches.
- **"Gold hardware" is a hidden trap.** Multiple "black" models across JINS and OWNDAYS use gold temples/bridge. Always check the actual image, not just the colour name.
- **Dark tortoiseshell vs solid brown:** These are different. "Brown Demi" / "Habana" = tortoiseshell pattern. "Brown" / "Brown Sasa" = solid. Tortoiseshell reads more sophisticated for professional contexts.
- **Langham Place (MK) has both Zoff and OWNDAYS** — efficient for comparison shopping.

## Red-Team / Due Diligence Learnings

### Material Science: Celluloid vs Acetate

- **Celluloid (cellulose nitrate)** — used by OWNDAYS SENICHI line and some premium Japanese brands. Rich lustre from camphor content, but camphor sublimates over time → frame becomes brittle. Expected lifespan 2-5 years. Sensitive to alcohol (hand sanitiser, wipes), UV, and humidity. HK's subtropical climate likely accelerates degradation. Flammable (banned in EU toys since 2006).
- **Acetate (cellulose acetate)** — modern standard. More stable, 3-5+ year lifespan. "Vintage acetate" (Zoff's term for no-additive acetate) sits between celluloid and standard acetate — trades plasticiser stability for material purity.
- **Bottom line:** Celluloid frames are consumables, not investments. Price per year, not per frame.
- Sources: Feel Seeds (JP repair), OptiBoard, note.com comparisons.

### Pricing Traps

- **Zoff "included lens" is 1.55 spherical** — worst spec among the three brands. Upgrading to 1.6 aspherical costs ~$498 extra. Always calculate all-in cost including lens upgrade.
- **OWNDAYS includes thin aspherical free** with all frames. Better included lens than Zoff or JINS.
- **"Included lenses" comparison:** OWNDAYS (thin aspherical, free) > JINS (varies by line) > Zoff (1.55 spherical, worst).

### Warranty Gotchas

- OWNDAYS has the strongest HK warranty: 1yr frame + 1yr lens + 1-month exchange + 50% accident coverage.
- Zoff is weakest: 1yr frame + 6-month lens + no exchange + no accident coverage.
- JINS sits in between.
- **OWNDAYS exclusion to watch:** "accidental damage" vs "defect" line drawn aggressively. If model is discontinued, replacement options are limited.
- **Zoff prescription accuracy:** Reports of misaligned optical centres at Telford branch. Verify prescription on pickup.

### Weight: Listed vs Actual

- OWNDAYS lists frame-only weight. Mobile01 reviewer measured 千一作 at ~45g with lenses — nearly 3x the listed frame weight. This is normal (lenses add 15-25g depending on prescription) but worth knowing.
- **Wellington shapes weigh more** than boston in the same line (more material). A reviewer specifically warned against wellington for first-time 千一作 buyers.
- Always try on with demo lenses in-store — frame-only weight is misleading.

### Review Availability

- OWNDAYS SENICHI has some reviews (Mobile01, Japanese blogs). Enough to identify issues.
- Zoff Made in Japan (newer models like ZX241004) has zero user reviews. Buying blind.
- JINS premium lines have moderate Japanese review coverage but sparse HK-specific feedback.
- **Search strategy for red-teaming:** "[model] problems", "[brand] 缺點", "[brand] 評價", Mobile01, LIHKG, HardwareZone SG, min-hyou (JP), Trustpilot.

### Store-Specific Warnings

- **OWNDAYS Hysan Place (CWB):** Staff flagged as "terrible" and "unprofessional" on Trustpilot (Feb 2025). Try Langham Place instead.
- **Zoff Telford (德福):** Prescription accuracy complaint. Verify on pickup.
- **OWNDAYS HK pricing:** 10-20% higher than same frames in Japan.
