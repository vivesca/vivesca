# Analog Clock / Watchface UI Design Research

## Key Principles (Cross-Referenced)

### Hand Proportions
- Minute hand: 80% of dial radius — nearly touches the minute track
- Hour hand: ~50–55% of dial radius (visibly shorter, creates immediate distinction)
- Second hand: 90–100% of radius with a short counterbalance tail past center
- Hour hand ~1/3 wider than minute hand (width compensates for its shorter reach)
- No fixed industry standard — readability of the hour/minute distinction matters more than the specific ratio
- Source: facer.io community, W3Schools canvas clock, WatchUSeek

### Tick Marks
- 3-tier hierarchy: cardinal marks (12/3/6/9) > hour marks > minute marks
- Cardinal marks: widest, longest — the 12 o'clock mark should be visually distinct from all others
- Hour marks: roughly 3–4x the length of minute marks
- Minute marks: minimal — 1–2px wide, short enough to not crowd
- Every 5th mark (hour position) should be visually distinguished from the 4 between
- Zepp OS: minimum font/stroke width of 2px for any dial element

### Legibility (from Marco's Infograph critique)
- Hour hand tip should nearly touch the hour indices — large gaps introduce reading error
- Center complications (overlaid data at center) REDUCE contrast between dial and hands — place data in corners or outside hand sweep
- A prominent, distinct 12 o'clock marker is required for orientation
- Hierarchy: hour markers must be substantially larger than minute markers
- 30-second markings (instead of minute markings) reduce readability — use standard 60-division minute track

### Negative Space
- Keep the center ~20–25% of the dial radius free of data overlays — hands converge here and need contrast
- Data complications should live at: outer corners, bezel arcs, or inside a clearly bounded zone (not floating over hand paths)
- Apple Infograph failure case: center complications obscure hands, making it impossible to locate them against busy backgrounds

## Typography on Clock Faces

### Apple Watch (SF Compact)
- SF Compact Text: 19pt and below
- SF Compact Display: 20pt and above
- SF Compact Rounded used specifically for complications
- Weights: Regular, Medium, Semibold, Bold — avoid Thin/Light/Ultralight
- Threshold split (19pt/20pt) maps to the glanceable vs readable distinction

### Center Readout Rules
- A center digital readout works well when: (a) clock hands are thin enough not to obscure it, (b) the readout sits at a fixed baseline ~33% from top of the dial
- When in doubt, omit center text — the clock hands ARE the readout
- If showing data (temp, BPM, etc.), prefer a dedicated zone (below center, or a sub-dial) over floating text at pivot point

### General Typography
- Sans-serif only on dark faces (serifs at small sizes create noise)
- Tabular figures (monospaced numerals) for any changing readout — prevents layout shift
- Letter-spacing: slightly open (5–10% extra) helps at small sizes on dark backgrounds

## Color on Dark Clock Faces

### Background
- Preferred: #121212 or #1E1E1E (not pure black) — reduces halation effect around bright elements
- Exception: AOD (always-on display) requires #000000 to control power draw
- Zepp OS AOD spec: black background, white hands, illuminated pixels <10% of screen

### Hands and Markers
- Primary elements: #F0F0F0 or #E0E0E0 (off-white) — not pure white, less harsh
- For AOD/minimal: pointer must be white per Zepp spec
- High contrast (white markers on near-black) is the single most legible combination for analog time reading

### Accent Colors
- Use 1 accent color maximum (2 if tracking separate data streams, e.g., activity + BPM)
- Muted, medium-luminance colors work better than saturated hues on dark backgrounds
- Tested well: warm amber (#E8A838), teal/cyan (#4DD9AC), desaturated orange — avoid high-chroma red/green
- Contrast ratio target: 4.5:1 minimum for text; 7:1–10:1 is the sweet spot for glanceable legibility
- Avoid maximum contrast (21:1) for non-critical data — eye strain in dark environments

## Apple Watch Complication Design

### Complication Families (Series 4+)
- Graphic Corner: arc/gauge in corner, curves along display edge, can show gradient-colored progress arc + text
- Graphic Circular: small circular area, combines gauge ring + center text/icon
- Graphic Bezel: text curving along bezel circumference (up to ~180 degrees of text)
- Graphic Rectangular: wider zone, can show chart/graph data

### Data Layout Principles
- Corner complications don't compete with hands — spatial separation is the key design move
- Bezel text arcs use the outer ring that hands never reach — maximum info density, zero occlusion
- Center complications should be avoided on analog faces — Apple's own Infograph is evidence of this failure
- Color-coordinate complications with each other to create system coherence (audit default colors — activity green vs battery green should be the same green)

### Arc/Gauge Design
- Arcs are progress/range indicators; use fill fraction + optional gradient
- Gauge stroke weight should be consistent with tick mark weight — thin enough not to compete with hands
- Keep arc radius inside the minute track — arcs that reach beyond the tick marks look broken

## SVG Implementation Notes
- 450x450 units is the Wear OS standard canvas; works well for SVG viewBox
- Hand pivot at exact center (225, 225 for 450x450)
- Minute hand: length ~180 units (80% of 225 radius)
- Hour hand: length ~115–125 units (50–55% of radius)
- Second hand: ~200 units with ~40 unit counterweight past center
- Stroke width for minute ticks: 1–2px; hour ticks: 3–4px; cardinal ticks: 5–6px
- Always use stroke-linecap: round or square (not butt) for hands — butt ends look cheap at small sizes
