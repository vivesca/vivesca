#!/usr/bin/env -S uv run --script
from __future__ import annotations

# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""cibus — Hong Kong restaurant finder via OpenRice API."""


import argparse
import json
import sys
from datetime import datetime
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

HKT = ZoneInfo("Asia/Hong_Kong")
API = "https://www.openrice.com/api/v2/search"
PRICE_LABELS = {1: "<$50", 2: "$51-100", 3: "$101-200", 4: "$201-400", 5: "$401-800"}

# Cuisine name → OpenRice cuisineId (from API probing 2026-03-19)
CUISINES: dict[str, int] = {
    "chiu chow": 1001,
    "chiuchow": 1001,
    "潮州": 1001,
    "cantonese": 1002,
    "guangdong": 1002,
    "粵菜": 1002,
    "廣東": 1002,
    "yunnan": 1003,
    "滇菜": 1003,
    "雲南": 1003,
    "hong kong": 1004,
    "hk style": 1004,
    "港式": 1004,
    "hakka": 1005,
    "客家": 1005,
    "shanghainese": 1007,
    "jiangzhe": 1007,
    "江浙": 1007,
    "sichuan": 1008,
    "szechuan": 1008,
    "川菜": 1008,
    "四川": 1008,
    "taiwanese": 1009,
    "taiwan": 1009,
    "台灣": 1009,
    "korean": 2001,
    "韓國": 2001,
    "vietnamese": 2002,
    "viet": 2002,
    "越南": 2002,
    "filipino": 2003,
    "菲律賓": 2003,
    "thai": 2004,
    "泰國": 2004,
    "singaporean": 2005,
    "singapore": 2005,
    "新加坡": 2005,
    "japanese": 2009,
    "日本": 2009,
    "日式": 2009,
    "italian": 3006,
    "意大利": 3006,
    "western": 4000,
    "西式": 4000,
    "american": 4001,
    "美國": 4001,
    "international": 6000,
    "多國": 6000,
}

# District name → OpenRice districtId (from API probing 2026-03-19)
DISTRICTS: dict[str, int] = {
    "sheung wan": 1001,
    "上環": 1001,
    "central": 1003,
    "中環": 1003,
    "wan chai": 1006,
    "灣仔": 1006,
    "causeway bay": 1019,
    "銅鑼灣": 1019,
    "north point": 1013,
    "北角": 1013,
    "tai koo": 1015,
    "太古": 1015,
    "tsim sha tsui": 2008,
    "tst": 2008,
    "尖沙咀": 2008,
    "mong kok": 2010,
    "旺角": 2010,
    "san po kong": 2022,
    "新蒲崗": 2022,
    "kwun tong": 2026,
    "觀塘": 2026,
    "yuen long": 3003,
    "元朗": 3003,
    "tsuen wan": 3018,
    "荃灣": 3018,
    "sha tin": 3009,
    "沙田": 3009,
    "tuen mun": 3013,
    "屯門": 3013,
    "tai po": 3008,
    "大埔": 3008,
}


def resolve_id(name: str, table: dict[str, int], label: str) -> int | None:
    """Fuzzy-match a user string to a known ID."""
    if not name:
        return None
    key = name.lower().strip()
    if key in table:
        return table[key]
    # Substring match
    matches = [(k, v) for k, v in table.items() if key in k or k in key]
    if len(matches) == 1:
        return matches[0][1]
    if len(matches) > 1:
        opts = ", ".join(m[0] for m in matches)
        print(f"Ambiguous {label} '{name}'. Matches: {opts}", file=sys.stderr)
        return matches[0][1]
    print(
        f"Unknown {label} '{name}'. Known: {', '.join(sorted(set(str(v) + ':' + k for k, v in table.items())))}",
        file=sys.stderr,
    )
    return None


def fetch(
    rows: int, cuisine_id: int | None, district_id: int | None, budget: int | None
) -> list[dict]:
    """Call the OpenRice search API with structured filters."""
    params = [f"rows={rows}", "sortBy=ORScoreDesc", "regionId=0"]
    if cuisine_id:
        params.append(f"cuisineId={cuisine_id}")
    if district_id:
        params.append(f"districtId={district_id}")
    if budget:
        params.append(f"priceRangeId={budget}")

    url = f"{API}?{'&'.join(params)}"
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "cibus/1.0"})
    with urlopen(req, timeout=15) as resp:
        body = resp.read()

    if body[:1] == b"<":
        print(
            "Error: API returned HTML (likely rate-limited or captcha). Try again later.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print("Error: API returned invalid JSON.", file=sys.stderr)
        sys.exit(1)
    return data.get("paginationResult", {}).get("results", [])


def current_hours(poi: dict) -> str:
    """Get today's hours from poiHours."""
    now = datetime.now(HKT)
    today_dow = now.weekday() + 1  # OR: 1=Mon..7=Sun; Python: 0=Mon..6=Sun
    for h in poi.get("poiHours", []):
        if h.get("dayOfWeek") == today_dow:
            if h.get("isClose"):
                return "Closed"
            if h.get("is24hr"):
                return "24h"
            start = h.get("period1Start", "")[:5]
            end = h.get("period1End", "")[:5]
            return f"{start}-{end}" if start and end else "—"
    return "—"


def format_table(results: list[dict]) -> str:
    """Format results as a compact table."""
    if not results:
        return "No results found."

    headers = ["#", "Name", "Cuisine", "District", "Score", "Reviews", "Price", "Open", "Hours"]
    rows: list[list[str]] = []

    for i, r in enumerate(results, 1):
        name = r.get("name", "?")
        cuisines = ", ".join(
            c["name"] for c in r.get("categories", []) if c.get("categoryTypeId") == 1
        )
        district = r.get("district", {}).get("name", "?")
        score = r.get("scoreOverall")
        score_str = f"{score:.1f}" if score else "—"
        smile = r.get("scoreSmile", 0)
        cry = r.get("scoreCry", 0)
        reviews = f"{r.get('reviewCount', 0)} ({smile}↑{cry}↓)"
        price = PRICE_LABELS.get(r.get("priceRangeId", 0), "?")
        phones = r.get("phones", [])
        phone = phones[0] if phones else "—"
        open_now = "Yes" if r.get("openNow") else "No"
        hours = current_hours(r)

        rows.append(
            [str(i), name, cuisines or "—", district, score_str, reviews, price, open_now, hours]
        )

    # Calculate column widths
    widths = [max(len(h), *(len(row[j]) for row in rows)) for j, h in enumerate(headers)]

    def fmt(cells: list[str]) -> str:
        return " | ".join(c.ljust(widths[j]) for j, c in enumerate(cells))

    lines = [fmt(headers), " | ".join("-" * w for w in widths)]
    lines.extend(fmt(row) for row in rows)

    # Links + address + phone below table
    lines.append("")
    for i, r in enumerate(results, 1):
        url = r.get("shortenUrl", "")
        addr = r.get("addressOtherLang") or r.get("address", "")
        phone = r.get("phones", [""])[0]
        lines.append(f"  [{i}] {url}  {addr}  tel:{phone}")

    return "\n".join(lines)


def list_options() -> None:
    """Print known cuisines and districts."""
    print("Cuisines:")
    seen: set[int] = set()
    for name, cid in sorted(CUISINES.items(), key=lambda x: x[1]):
        if cid not in seen and not any(ord(c) > 127 for c in name):
            print(f"  {name}")
            seen.add(cid)
    print("\nDistricts:")
    seen.clear()
    for name, did in sorted(DISTRICTS.items(), key=lambda x: x[1]):
        if did not in seen and not any(ord(c) > 127 for c in name):
            print(f"  {name}")
            seen.add(did)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hong Kong restaurant finder (OpenRice)",
        epilog="Examples:\n  cibus -c italian -a central\n  cibus -c japanese -a tst -b 4\n  cibus -c thai --rows 10\n  cibus --list",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "query", nargs="*", help="Shorthand: 'cuisine area' (e.g., 'italian central')"
    )
    parser.add_argument(
        "--area",
        "--district",
        "-a",
        "-d",
        dest="area",
        help="District (e.g., 'central', 'tst', 'mong kok')",
    )
    parser.add_argument("--cuisine", "-c", help="Cuisine (e.g., 'italian', 'japanese', 'thai')")
    parser.add_argument(
        "--budget",
        "-b",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Price: 1=<$50, 2=$51-100, 3=$101-200, 4=$201-400, 5=$401-800",
    )
    parser.add_argument("--rows", "-n", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--json", "-j", action="store_true", help="Output raw JSON")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List known cuisines and districts"
    )
    args = parser.parse_args()

    if args.list:
        list_options()
        return

    # Parse positional "cuisine area" shorthand
    cuisine = args.cuisine
    area = args.area
    if args.query and not cuisine and not area:
        words = " ".join(args.query).lower()
        # Try to match cuisine first, then area from remainder
        for name in sorted(CUISINES, key=len, reverse=True):
            if name in words:
                cuisine = name
                words = words.replace(name, "").strip()
                break
        if words:
            area = words

    if not cuisine and not area and not args.budget:
        parser.error("Provide --cuisine, --area, --budget, or positional 'cuisine area'")

    cuisine_id = resolve_id(cuisine, CUISINES, "cuisine") if cuisine else None
    district_id = resolve_id(area, DISTRICTS, "district") if area else None

    if cuisine and not cuisine_id:
        sys.exit(1)

    try:
        results = fetch(args.rows, cuisine_id, district_id, args.budget)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Client-side post-filter (safety net if API params are imprecise)
    if cuisine_id:
        results = [
            r
            for r in results
            if any(
                c.get("categoryId") == cuisine_id
                for c in r.get("categories", [])
                if c.get("categoryTypeId") == 1
            )
            or not r.get("categories")  # keep if no category data
        ]
    if district_id:
        results = [
            r
            for r in results
            if r.get("district", {}).get("districtId") == district_id
            or not r.get("district", {}).get("districtId")
        ]

    if args.json:
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print(format_table(results))


if __name__ == "__main__":
    main()
