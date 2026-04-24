"""Photoreception gather — morning brief context.

Sensing light: first input of the day.
Collects: sleep (Oura), calendar, todo, tonus, budget, weather (optional).
"""

import concurrent.futures

from metabolon.pinocytosis import (
    intake_context,
    run_cmd,
    secrete_json,
    secrete_text,
    transduce,
)

# ---------------------------------------------------------------------------
# Morning-specific gatherers
# ---------------------------------------------------------------------------


def intake_sleep() -> dict:
    """Gather sleep/readiness data from Oura via chemoreceptor."""
    try:
        from metabolon.organelles.chemoreceptor import sense

        data = sense()
        if "error" in data:
            return {
                "label": "Sleep / Readiness",
                "ok": False,
                "content": f"sopor error: {data['error']}",
            }
        parts = []
        for key, label in [
            ("sleep_score", "Sleep"),
            ("readiness_score", "Readiness"),
        ]:
            if data.get(key) is not None:
                parts.append(f"{label}: {data[key]}")
        if data.get("resilience", {}).get("level"):
            parts.append(f"Resilience: {data['resilience']['level']}")
        if data.get("total_sleep_duration") is not None:
            parts.append(f"Total sleep: {data['total_sleep_duration'] / 3600:.1f}h")
        if data.get("efficiency") is not None:
            parts.append(f"Efficiency: {data['efficiency']}%")
        if data.get("average_hrv") is not None:
            parts.append(f"Avg HRV: {data['average_hrv']} ms")
        if data.get("lowest_heart_rate") is not None:
            parts.append(f"Lowest HR: {data['lowest_heart_rate']} bpm")
        content = " | ".join(parts) if parts else "No Oura data"
        return {"label": "Sleep / Readiness", "ok": True, "content": content}
    except Exception as exc:
        return {"label": "Sleep / Readiness", "ok": False, "content": f"sopor unavailable: {exc}"}


def intake_weather() -> dict:
    """Gather HK weather from hygroreception CLI."""
    ok, out = run_cmd(["hygroreception", "now"], timeout=10)
    return {"label": "Weather (HKO)", "ok": bool(ok), "content": ok or out or "(unavailable)"}


# ---------------------------------------------------------------------------
# Section ordering and dispatch
# ---------------------------------------------------------------------------

SECTION_ORDER = [
    "datetime",
    "sleep",
    "weather",
    "calendar",
    "todo",
    "now",
    "budget",
]

_MORNING_GATHERERS = {
    "sleep": intake_sleep,
    "weather": intake_weather,
}


def intake(as_json: bool = True, send_weather: bool = False) -> str:
    """Run full photoreception gather. Returns formatted string."""
    ctx = intake_context(
        include=["date", "now", "budget", "todo", "calendar"],
        calendar_date="today",
        calendar_days=1,
        todo_filter="today",
    )

    results = transduce(ctx)

    # Morning-specific gatherers in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(_MORNING_GATHERERS)) as pool:
        futures = {pool.submit(fn): key for key, fn in _MORNING_GATHERERS.items()}
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as exc:
                results[key] = {"label": key, "ok": False, "content": f"[gatherer error: {exc}]"}

    ordered = {key: results[key] for key in SECTION_ORDER if key in results}

    if as_json:
        return secrete_json(ordered)
    return secrete_text("PHOTORECEPTION MORNING BRIEF", ordered, SECTION_ORDER)


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Gather context for morning brief.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--send", action="store_true", help="Send weather to Tara.")
    args = parser.parse_args()
    print(intake(as_json=args.json, send_weather=args.send))


if __name__ == "__main__":
    main()
