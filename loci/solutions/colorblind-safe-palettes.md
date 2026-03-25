# Colorblind-Safe Color Palettes for Data Visualization

## The Problem

Blue + purple is one of the most commonly confused pairings under protanopia/deuteranopia. Both shift toward similar perceived territory for red-green colorblind users. This affects ~8% of males.

## Gold Standard: Blue + Amber/Orange

The canonical colorblind-safe two-color pairing (Datawrapper, Okabe-Ito, Bang Wong). Blue is the safest hue (least affected by CVD). Amber/orange is perceived as distinct yellow-orange even by red-green colorblind users. They sit at opposite ends of the dichromat perceptual axis.

### Recommended Hex Codes

**On dark backgrounds (#0f172a):**
- Blue: `#7dd3fc` (sky-300) — 10.71:1 AAA
- Amber: `#fbbf24` (amber-400) — 10.69:1 AAA

**On light backgrounds (#f8fafc):**
- Blue: `#1e40af` (blue-800) — 8.34:1 AAA
- Orange: `#c2410c` (orange-700) — 4.95:1 AA

## Structural Constraint

No single saturated hue passes WCAG 4.5:1 on both dark navy and near-white backgrounds simultaneously. You MUST use per-mode shade variants (CSS custom properties or Tailwind dark: modifier).

## Alternatives

| Pair | Colorblind Safety | Aesthetic |
|------|-------------------|-----------|
| Blue + Amber | Excellent (gold standard) | Clean, warm/cool contrast |
| Teal + Coral | Acceptable (verify with simulator) | Transit-app vibes |
| Okabe-Ito Blue + Orange | Best-in-class (scientific) | Slightly muted |
| Blue + Purple | Poor (common confusion) | Popular but problematic |

## iOS App Icon Gotcha

**Don't bake glass/specular/shadow effects into app icons.** Since iOS 26, Liquid Glass is rendered dynamically by the GPU at runtime (gyroscope-tracking highlights, frosted translucency). Baked faux glass fights the OS overlay and looks wrong. Per Apple HIG: submit clean, bold, high-contrast artwork. Let the OS add depth. Apple's own Clock icon achieves polish through contrast and bold strokes, not glass layers.

## Sources

- Okabe-Ito palette (Nature Methods standard)
- Bang Wong "Points of view: Color blindness" (2011)
- Datawrapper colorblind visualization guide
- colourcontrast.cc for verified ratios
