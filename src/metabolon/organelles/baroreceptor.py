"""baroreceptor — HK Observatory environmental sensor (baroreceptor = pressure sensor)."""

import json
import sys
import urllib.request
from datetime import datetime

NOW_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en"
FIND_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=en"
WARN_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=warnsum&lang=en"

WARN_ICONS = {
    "WTCSGNL": "🌀",
    "WRAIN": "⛈️",
    "WHOT": "🥵",
    "WCOLD": "🥶",
    "WFROST": "❄️",
    "WMSGNL": "💨",
    "WTS": "⚡",
    "WFIRE": "🔥",
    "WL": "⛰️",
    "WTMW": "🌊",
}


def _fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        try:
            return json.loads(resp.read().decode())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from {url}: {e}") from e


def _to_int(value) -> int | None:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return None
    return None


def _get_place_value(data: list, place: str, key: str, cast=_to_int):
    for entry in data:
        if entry.get("place") == place:
            return cast(entry[key]) if key in entry else None
    return None


def _format_rain(mm: float) -> str:
    return str(int(mm)) if mm == int(mm) else str(mm)


def build_weather_line(now: dict, find: dict, warn: dict) -> str:
    # humidity — first entry
    humidity = None
    hum_raw = now.get("humidity", {})
    hum_data = hum_raw.get("data", []) if isinstance(hum_raw, dict) else []
    if hum_data:
        humidity = _to_int(hum_data[0].get("value"))

    # UV — first entry
    uv_val = 0
    uv_raw = now.get("uvindex", {})
    uv_data = uv_raw.get("data", []) if isinstance(uv_raw, dict) else []
    if uv_data:
        uv_val = _to_int(uv_data[0].get("value")) or 0

    # today's forecast
    today_str = datetime.now().strftime("%Y%m%d")
    forecasts = find.get("weatherForecast", [])
    if not forecasts:
        raise ValueError("missing weatherForecast data")

    today = next(
        (e for e in forecasts if str(e.get("forecastDate", "")) == today_str),
        forecasts[0],
    )

    lo = _to_int(today.get("forecastMintemp", {}).get("value"))
    hi = _to_int(today.get("forecastMaxtemp", {}).get("value"))
    if lo is None or hi is None:
        raise ValueError("missing forecastMintemp/forecastMaxtemp value")
    forecast_desc = today.get("forecastWeather", "")

    # rainfall — Eastern District with Chai Wan fallback
    rain_mm = 0.0
    rain_raw = now.get("rainfall", {})
    rain_data = rain_raw.get("data", []) if isinstance(rain_raw, dict) else []
    if rain_data:
        val = _get_place_value(rain_data, "Eastern District", "max", cast=float)
        if val is None:
            val = _get_place_value(rain_data, "Chai Wan", "max", cast=float)
        rain_mm = val or 0.0

    # warnings
    warnings = []
    for key, val in warn.items():
        if key == "WFIRE":
            continue  # fire danger suppressed
        name = val.get("name") if isinstance(val, dict) else None
        if name is None:
            continue
        icon = WARN_ICONS.get(key, "⚠️")
        if key == "WTCSGNL":
            code = str(val.get("code", ""))
            warnings.append(f"{icon} T{code}")
        else:
            clean = name.replace(" Warning Signal", "").replace(" Warning", "")
            warnings.append(f"{icon} {clean}")

    # weather emoji
    fc = forecast_desc.lower()
    if any("🌀" in w for w in warnings):
        emoji = "🌀"
    elif any("⛈️" in w for w in warnings) or rain_mm > 5.0:
        emoji = "🌧️"
    elif "thunder" in fc:
        emoji = "⛈️"
    elif "rain" in fc or "shower" in fc:
        emoji = "🌦️"
    elif "cloudy" in fc:
        emoji = "☁️"
    elif "sunny" in fc or "fine" in fc:
        emoji = "☀️"
    else:
        emoji = "🌤️"

    # description: strip trailing period, lowercase first char
    desc = forecast_desc.rstrip(".")
    if desc:
        desc = desc[0].lower() + desc[1:]

    parts = [f"{emoji} {lo}\u2013{hi}\u00b0C, {desc}"]
    if rain_mm > 0.0:
        parts.append(f"{_format_rain(rain_mm)}mm rain")
    if uv_val >= 6:
        parts.append(f"UV {uv_val}")
    if humidity is not None and humidity >= 90:
        parts.append("muggy")

    line = ", ".join(parts)
    if warnings:
        warn_str = " \u2022 ".join(warnings)
        line = f"\u26a0\ufe0f {warn_str}\n{line}"

    return line


def sense() -> str:
    """Fetch current HK weather and return a one-line summary."""

    now = _fetch_json(NOW_URL)
    find = _fetch_json(FIND_URL)
    warn = _fetch_json(WARN_URL)
    return build_weather_line(now, find, warn)


def _cli() -> None:
    if len(sys.argv) == 1:
        print(
            json.dumps(
                {
                    "ok": True,
                    "command": "hygroreception",
                    "result": {
                        "description": "Fetch current Hong Kong weather from the Observatory",
                        "commands": {
                            "hygroreception": "Print one-line current HK weather summary"
                        },
                    },
                    "next_actions": [
                        {
                            "command": "hygroreception",
                            "description": "Get the current Hong Kong weather summary",
                        }
                    ],
                    "version": "0.1.0",
                }
            )
        )
        sys.exit(0)

    try:
        print(sense())
    except Exception as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
