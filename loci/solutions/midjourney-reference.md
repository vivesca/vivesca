# Midjourney Reference

Created: 2026-02-27
Updated: 2026-02-28

## Key People

- **Tatiana Tsiguleva** ([@ciguleva](https://x.com/ciguleva)) — Midjourney educator, Perplexity creative ambassador. [Substack](https://ciguleva.substack.com), [SREF collection on Gumroad](https://aig.gumroad.com/l/styles) (640+ codes).
- **Lucas Crespo** ([@lucas__crespo](https://x.com/lucas__crespo)) — Every's creative lead. Midjourney daily driver. Also uses Claude for art direction. [Shared workflow with 300+ people](https://x.com/lucas__crespo/status/2021998980813795518).
- **Dan Shipper** — [Podcast with Lucas (~33:41)](https://x.com/danshipper/status/1909976169082179935) discussing cover image process.

## Perplexity Creative Ambassador Codes

### 2026 Codes (latest aesthetic — use these first)

In 2026 ambassadors switched from `--p` moodboards to `--sref` params.

| Who | Date | Code | Link |
|-----|------|------|------|
| Tatiana #1 | Jan 2026 | `--chaos 10 --exp 30 --sref 3737544406 --profile xc42mvx --v 7` | [Tweet](https://x.com/ciguleva/status/2009025727698538804) |
| Tatiana #2 | Feb 2026 | `--chaos 20 --sref 5877700996 4815442863 2174344444 1699284549 3888100065 352184820 481439432 4866446247::2 --profile 75t3ipc --stylize 50` | [Tweet](https://x.com/ciguleva/status/2020550524224053600) |
| Phi Hoang | Jan 2026 | `--sref 6726456675 1575582868` | [Tweet](https://x.com/apostraphi/status/2016214945512264114) |
| Gizem Akdag | Jan 2026 | `--sref 6726456675 1575582868 7906576498` | [Tweet](https://x.com/gizakdag/status/2015499433270518175) |

### Tatiana Moodboard Series (2025 — still work)

| # | Date | Code | Link |
|---|------|------|------|
| 1 | Jan 9, 2025 | `--p m7276087242781622288` | [Tweet](https://x.com/ciguleva/status/1877369933958455597) |
| 2 | Jan 28, 2025 | `--p m7282799307516805136` | [Tweet](https://x.com/ciguleva/status/1884237844358521079) |
| 3 | Feb 26, 2025 | `--p m7293744149541421086` | [Tweet](https://x.com/ciguleva/status/1894878098086076691) |
| 4 | Mar 29, 2025 | `--p m7304915009769832477` | [Tweet](https://x.com/ciguleva/status/1906041470165103082) |
| 5 | May 6, 2025 | `--p m7318781846345482242` | [Tweet](https://x.com/ciguleva/status/1919968423628685541) |
| 6 | Jun 16, 2025 | `--p m7333589242683064325` | [Tweet](https://x.com/ciguleva/status/1934711669017723327) |
| 7 | Jul 24, 2025 | `--p kuwwd66 --sref 257047628 --profile l3h4vio --sw 500 --stylize 500` | [Tweet](https://x.com/ciguleva/status/1948212177149837732) |
| 8 | Sep 15, 2025 | `--p ray6vm9 --c 10 --exp 30 --sref 2005786696 1542689275 3118717105` | [Tweet](https://x.com/ciguleva/status/1967640945421324791) |

### Gizem Akdag (@gizakdag) — Individual Blend Drops

More artistic/experimental than Tatiana's editorial style. Sells SREF bundles (300+ codes) on [Contra](https://x.com/gizakdag/status/2027391858716848365).

| Date | Code | Notes | Link |
|------|------|-------|------|
| Jan 25, 2026 | `--sref 6726456675 1575582868 7906576498` | "First Perplexity blend of the year" | [Tweet](https://x.com/gizakdag/status/2015499433270518175) |
| Aug 21, 2025 | `--c 20 --ar 2:3 --exp 100 --sref 526771482 3119424919 1648758673 --p` | "Secret blend" (war) | [Tweet](https://x.com/gizakdag/status/1958597825375477815) |
| Aug 14, 2025 | `--c 20 --ar 2:3 --exp 15 --sref 4051164299 --p` | Futurism | [Tweet](https://x.com/gizakdag/status/1956088496420168042) |
| Mar 24, 2025 | `--sref 2295094873` | "New favourite" | [Tweet](https://x.com/gizakdag/status/1904179732003840362) |

### Mac Baconai (@Macbaconai) — AI Artist

Perplexity + Leonardo AI ambassador. More artistic one-offs than structured series.

| Date | Code | Notes | Link |
|------|------|-------|------|
| Jun 2024 | `--sref 2575959499 --style raw --chaos 33 --ar 85:128 --stylize 250 --p` | "Your Imagination" | [Tweet](https://x.com/Macbaconai/status/1806405359432520027) |
| Aug 2024 | `--sref 270847807` | MJ v6.1 | [Tweet](https://x.com/Macbaconai/status/1819497291348431306) |
| Jun 2024 | `--c 30 --ar 2:3 --sref 159188116 --p --s 800` | Collab w/ Gizem | [Tweet](https://x.com/Macbaconai/status/1805690210941866252) |

### Phi Hoang (@apostraphi) — Perplexity Designer (Internal)

Co-creates moodboards with Tatiana. Shares own blends.

| Date | Code | Notes | Link |
|------|------|-------|------|
| Jan 2026 | `--sref 6726456675 1575582868` | "New year, new aesthetics" | [Tweet](https://x.com/apostraphi/status/2016214945512264114) |
| Sep 2025 | `--p ray6vm9 --c 10 --exp 30 --sref 2005786696` | Moodboard #8 (co-release) | [Tweet](https://x.com/apostraphi/status/1967664043965239411) |

## Prompt Framework

### Basic Structure
```
Camera Angle + Style + Subject + Descriptive Details
```

Place important elements first. Keep concise.

### Example
```
close-up editorial photo of [subject], neutral tones,
textured natural fabrics, daylight --ar 3:4
```

### Personalisation Layers
1. `--profile [code]` — requires rating 200+ images in Midjourney
2. `--sref [codes]` — blend 4-5+ style references for unique aesthetic
3. Tune with: `--sw 50` (style weight), `--stylize 50`, `--chaos 20`, `--exp 30`, `--raw`

### Brand Replication Method (Quartr Example)
Same 28 `--sref` codes + 4 `--profile` codes + identical params across every image. Only change the subject:

```
[simple subject] --chaos 100 --ar 1258:1523 --exp 100
--sref [28 codes] --profile [4 codes]
```

### Key Parameters
- `--sref [url/code]` — style reference (the core consistency tool)
- `--sw 400` — balanced; 800+ for strict brand adherence
- `--chaos 0-20` — low for repeatable results
- `--seed [number]` — near-identical variations
- `--no text` — suppress garbled AI text, add in Canva instead
- `--raw` — more realistic/photographic output
- `--iw 0.5-2` — image prompt weight (default 1)

### Sref Blending Rules
- **1 sref** = strong, clean style
- **2-3 sref** = interesting blend
- **4-5 sref** = max before things get muddy
- **7+ sref** = works if anchored with `--profile` + `--stylize 50` + `::2` weighting on dominant code

### Caveats
- **`--sref` codes require v7.** Adding `--v 6.1` silently breaks `--sref` — generation never starts. Drop the version flag to use MJ's default (v7).
- `--sref` codes may be time-limited. Generate your own via Style Creator for long-term reliability.
- **Grok X search can return incomplete sref codes.** Always verify against the original tweet via `bird read`. The Feb 2026 Tatiana code was missing `4866446247::2 --profile 75t3ipc --stylize 50` — the anchoring params that make 7+ srefs work.

## Midjourney Tools

### Moodboards
- Upload images, pick from gallery, or paste URLs to define your aesthetic
- Use in prompts: `--p [moodboard-code]`
- Wider aesthetic range than `--sref` — captures mood/feel, not just a specific style
- Living document — add/remove images over time, codes regenerate
- Mixable with `--sref`: `--sref 142710498 --profile drgmjoi 2jrqbw6`
- Works with v6 and v7. Cannot combine with `--sv` or `--sw`.
- **Workflow:** See image on X → copy image URL → paste into moodboard → use `--p` in prompts
- Terry's moodboards:
  - [7276087242781622288](https://www.midjourney.com/moodboards/7276087242781622288)
  - [7282799307516805136](https://www.midjourney.com/moodboards/7282799307516805136)
  - [7347088266165747749](https://www.midjourney.com/moodboards/7347088266165747749)

### Style Explorer
Browse SREF codes at midjourney.com/explore (Styles tab). Like to save.

### Style Creator
Generate custom SREF codes at midjourney.com/style-creator. Pick from image grids — 5-10 rounds to stabilise. Most direct path to a personal brand style.

### Personalize
Rate images at midjourney.com/personalize. 200+ ratings to unlock `--profile` codes.

## SREF Style Browsers — Ranked

Visually reviewed 2026-02-28.

### Tier 1 — Best External Browsers

**[Lummi.ai/sref-codes](https://www.lummi.ai/sref-codes)** — Best for quick editorial picks. ~20 curated styles, [Editorial](https://www.lummi.ai/sref-codes/editorial) filter, free.

**[SrefHunt](https://srefhunt.com)** — Cleanest third-party UI. Good category tags, free, community-driven.

### Tier 2 — Deep Exploration

**[Midlibrary.io](https://midlibrary.io)** — 4,000+ codes. Dense UI, skews artistic. Patreon ($5/mo).

**[Promptsref.com](https://promptsref.com)** — 1,500+ codes, colour palette extraction. Busy UI. Freemium.

### Tier 3 — Niche

**[Tatiana's Gumroad](https://aig.gumroad.com/l/styles)** — 640+ curated codes, paid. High editorial taste.
**[Srefs.co](https://srefs.co)** — 74K+ codes, Branding category (unverified — Cloudflare-blocked).

### Skip
- **Sref-midjourney.com** — almost entirely anime/illustration
- **Srefcodes.com** — closed to new users
- **Midlearning.com** — fully paywalled

## Generate via CLI (limen)

```bash
# With 2026 Perplexity-style sref codes (v7 default — do NOT add --v 6.1)
limen "AI governance in banking, abstract visualization --sref 6726456675 1575582868 7906576498 --ar 1:1" --out ./linkedin-images

# With your moodboard
limen "your subject --p 7347088266165747749 --ar 1:1" --out ./linkedin-images
```

Requires: `kleis` (cookie extraction) + `larvo` (stealth browser).
