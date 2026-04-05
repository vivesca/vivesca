---
name: hygroreception
description: HK Observatory one-line weather CLI. Use when user asks about weather, temperature, typhoon, or rain in HK. "weather", "hko", "天氣". NOT for weather in other cities.
user_invocable: true
---

# hygroreception

HK Observatory weather — fetches live data and prints a one-line summary.

## Trigger

Use when:
- User says "weather", "hko", "temperature", "typhoon", "天氣", "颱風"
- Morning check-ins

## Workflow

```bash
hygroreception
# ⛈️ 16–23°C, cloudy with occasional showers. A few thunderstorms later, muggy
```

Present the output to the user.

## Output Format

```
[⚠️ Warning1 • Warning2]
{emoji} {lo}–{hi}°C, {forecast_desc}[, {rain}mm rain][, UV N][, muggy]
```

Emoji priority: 🌀 typhoon → 🌧️ rain warning/heavy rain → ⛈️ thunder → 🌦️ shower → ☁️ cloudy → ☀️ sunny/fine → 🌤️ default

## Warning Types

🌀 Typhoon (T1-T10) · ⛈️ Rainstorm (Amber/Red/Black) · 🥵 Very Hot · 🥶 Cold · ❄️ Frost · 💨 Strong Monsoon · ⚡ Thunderstorm · 🔥 Fire Danger · ⛰️ Landslip · 🌊 Tsunami

## Error Handling

- **If API unreachable**: Report error, suggest checking HKO website directly
- **If Shau Kei Wan not available**: Falls back to "Hong Kong Observatory" reading

## Internals

Fetches three HKO opendata endpoints fresh every run (no `/tmp` caching):
- `rhrread` — current temperature, humidity, rainfall, UV
- `find` — 9-day forecast (matched to today by `forecastDate`, not blindly `[0]`)
- `warnsum` — active warning signals

Temperature station: Shau Kei Wan → Hong Kong Observatory fallback.
Muggy: humidity ≥ 90%. UV suffix: only if index ≥ 6.

## Gotchas

- Old `weather.py` used `/tmp/hko_*.json` pre-cached files — stale data caused wrong temps. `hygroreception` always fetches fresh.
- `forecastDate` is an integer in the JSON (e.g., `20260303`) — matched as string.

## Repo

`~/code/hygroreception/` · crates.io: `hygroreception`
