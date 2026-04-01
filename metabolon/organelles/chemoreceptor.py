from __future__ import annotations

"""chemoreceptor — Oura health sensing (formerly sopor). Endosymbiosis: Python CLI -> organelle.

Reads Oura Ring data via the Oura API v2. Credential resolution: OURA_TOKEN env var first,
then macOS Keychain entry 'oura-token'. Requires httpx (already a vivesca dependency).

Core functions: today(), week(), readiness(), sleep_score(), sleep_detail(), heartrate(), sense().
"""


import os
import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx

API_BASE = "https://api.ouraring.com/v2/usercollection"

# Sopor DuckDB path — used for subprocess fallback if needed by callers
_SOPOR_DB = Path.home() / ".local" / "share" / "sopor" / "sopor.duckdb"


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------


def _keychain_token() -> str | None:
    """Read Oura personal access token from macOS Keychain or 1Password."""
    import platform
    import shutil

    # macOS Keychain
    if platform.system() == "Darwin" and shutil.which("security"):
        try:
            r = subprocess.run(
                ["security", "find-generic-password", "-s", "oura-token", "-w"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode == 0:
                return r.stdout.strip() or None
        except Exception:
            pass

    # 1Password fallback
    op_bin = shutil.which("op") or os.path.expanduser("~/bin/op")
    try:
        r = subprocess.run(
            [op_bin, "read", "op://Agents/Agent Environment/oura_token"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0:
            return r.stdout.strip() or None
    except Exception:
        pass
    return None


def _get_token() -> str:
    """Resolve Oura token: OURA_TOKEN env var, then macOS Keychain.

    Raises:
        RuntimeError: If no token is found.
    """
    token = os.environ.get("OURA_TOKEN") or _keychain_token()
    if not token:
        raise RuntimeError(
            "OURA_TOKEN not set and no Keychain entry 'oura-token'. "
            "Get your token at https://cloud.ouraring.com/personal-access-tokens"
        )
    return token


# ---------------------------------------------------------------------------
# Low-level API client
# ---------------------------------------------------------------------------


def _fetch(endpoint: str, start: str, end: str, token: str | None = None) -> list[dict[str, Any]]:
    """Fetch a date range from Oura API v2.

    Oura's end_date is exclusive for some endpoints — bumped by +1 day to be safe.

    Args:
        endpoint: Oura collection name, e.g. 'daily_sleep', 'daily_readiness'.
        start: ISO date string, e.g. '2026-03-18'.
        end: ISO date string (inclusive), e.g. '2026-03-25'.
        token: Override token; resolved automatically if None.

    Returns:
        List of data records from the API response.

    Raises:
        RuntimeError: If token resolution fails.
        httpx.HTTPError: On network or HTTP errors.
    """
    if token is None:
        token = _get_token()
    end_plus = str(date.fromisoformat(end) + timedelta(days=1))
    with httpx.Client(
        base_url=API_BASE,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    ) as client:
        resp = client.get(
            f"/{endpoint}",
            params={"start_date": start, "end_date": end_plus},
        )
        resp.raise_for_status()
        return resp.json().get("data", [])


def _fetch_datetime(
    endpoint: str, start_dt: str, end_dt: str, token: str | None = None
) -> list[dict[str, Any]]:
    """Fetch a datetime range from Oura API v2 (for heartrate endpoint).

    Args:
        endpoint: Oura collection name, e.g. 'heartrate'.
        start_dt: ISO datetime string, e.g. '2026-03-27T00:00:00+08:00'.
        end_dt: ISO datetime string.
        token: Override token; resolved automatically if None.

    Returns:
        List of data records from the API response.
    """
    if token is None:
        token = _get_token()
    with httpx.Client(
        base_url=API_BASE,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    ) as client:
        resp = client.get(
            f"/{endpoint}",
            params={"start_datetime": start_dt, "end_datetime": end_dt},
        )
        resp.raise_for_status()
        return resp.json().get("data", [])


def heartrate(start_dt: str | None = None, end_dt: str | None = None) -> list[dict[str, Any]]:
    """Return heart rate time-series for a datetime range.

    Defaults to last night (bedtime_start to bedtime_end from sleep_detail).
    Each record: {bpm, source, timestamp}.

    Args:
        start_dt: ISO datetime, defaults to last night's bedtime_start.
        end_dt: ISO datetime, defaults to last night's bedtime_end.

    Returns:
        List of {bpm, source, timestamp} dicts.
    """
    if not start_dt or not end_dt:
        sd = sleep_detail()
        start_dt = start_dt or sd.get("bedtime_start")
        end_dt = end_dt or sd.get("bedtime_end")
    if not start_dt or not end_dt:
        return []
    return _fetch_datetime("heartrate", start_dt, end_dt)


def _today_date() -> str:
    """Return today's ISO date string."""
    return str(date.today())


def _week_start_date(days: int = 7) -> str:
    """Return ISO date string for N days ago."""
    return str(date.today() - timedelta(days=days))


# ---------------------------------------------------------------------------
# Public API: single-day accessors
# ---------------------------------------------------------------------------


def today(target_date: str | None = None) -> dict[str, Any]:
    """Return last night's combined health snapshot.

    Fetches daily_sleep and daily_readiness for the target date and merges
    them into a single dict with keys: date, sleep_score, readiness_score,
    contributors (readiness), sleep_contributors.

    Args:
        target_date: ISO date string, defaults to today.

    Returns:
        Dict with sleep_score, readiness_score, contributors, sleep_contributors.
        Returns empty dict if no data found.
    """
    d = target_date or _today_date()
    token = _get_token()

    sleep_records = _fetch("daily_sleep", d, d, token)
    readiness_records = _fetch("daily_readiness", d, d, token)

    result: dict[str, Any] = {"date": d}

    if sleep_records:
        s = sleep_records[0]
        result["sleep_score"] = s.get("score")
        result["sleep_contributors"] = s.get("contributors", {})

    if readiness_records:
        r = readiness_records[0]
        result["readiness_score"] = r.get("score")
        result["contributors"] = r.get("contributors", {})
        result["temperature_deviation"] = r.get("temperature_deviation")
        result["temperature_trend_deviation"] = r.get("temperature_trend_deviation")

    return result


def readiness(target_date: str | None = None) -> dict[str, Any]:
    """Return readiness score and contributors for a date.

    Args:
        target_date: ISO date string, defaults to today.

    Returns:
        Dict with keys: date, score, contributors (dict), temperature_deviation.
        Returns empty dict if no data found.
    """
    d = target_date or _today_date()
    records = _fetch("daily_readiness", d, d)

    if not records:
        return {"date": d, "score": None, "contributors": {}, "temperature_deviation": None}

    r = records[0]
    return {
        "date": d,
        "score": r.get("score"),
        "contributors": r.get("contributors", {}),
        "temperature_deviation": r.get("temperature_deviation"),
        "temperature_trend_deviation": r.get("temperature_trend_deviation"),
    }


def sleep_score(target_date: str | None = None) -> dict[str, Any]:
    """Return sleep score and contributors for a date.

    Args:
        target_date: ISO date string, defaults to today.

    Returns:
        Dict with keys: date, score, contributors (dict).
        Returns empty dict if no data found.
    """
    d = target_date or _today_date()
    records = _fetch("daily_sleep", d, d)

    if not records:
        return {"date": d, "score": None, "contributors": {}}

    s = records[0]
    return {
        "date": d,
        "score": s.get("score"),
        "contributors": s.get("contributors", {}),
    }


def sleep_detail(target_date: str | None = None) -> dict[str, Any]:
    """Return full detailed sleep record from last night.

    Reads from the detailed sleep endpoint and returns all fields from the
    longest sleep session, plus any additional sleep periods as 'extra_periods'.

    Args:
        target_date: ISO date string, defaults to today.

    Returns:
        Dict with all Oura sleep fields from the primary session.
        Time-series fields (heart_rate, hrv) included as-is.
    """
    d = target_date or _today_date()
    records = _fetch("sleep", d, d)

    if not records:
        return {"date": d}

    def _duration(rec: dict) -> int:
        v = rec.get("total_sleep_duration", 0)
        try:
            return int(v) if v else 0
        except (TypeError, ValueError):
            return 0

    best = max(records, key=_duration)
    others = [r for r in records if r is not best]

    result = {"date": d, **best}
    # Remove Oura internal ID, keep everything else
    result.pop("id", None)
    if others:
        result["extra_periods"] = [{k: v for k, v in r.items() if k != "id"} for r in others]
    return result


# Backward compat alias
hrv = sleep_detail


# ---------------------------------------------------------------------------
# Public API: weekly trends
# ---------------------------------------------------------------------------


def week(days: int = 7) -> list[dict[str, Any]]:
    """Return daily health data for the past N days.

    Fetches daily_sleep and daily_readiness for the range and merges them
    by date. Dates without data are omitted.

    Args:
        days: Number of days to look back, default 7.

    Returns:
        List of dicts (one per date with data), each with:
        date, sleep_score, readiness_score, temperature_deviation.
        Sorted oldest-first.
    """
    end = _today_date()
    start = _week_start_date(days)
    token = _get_token()

    sleep_records = _fetch("daily_sleep", start, end, token)
    readiness_records = _fetch("daily_readiness", start, end, token)

    sleep_by_date: dict[str, dict] = {r["day"]: r for r in sleep_records if "day" in r}
    readiness_by_date: dict[str, dict] = {r["day"]: r for r in readiness_records if "day" in r}

    all_dates = sorted(set(sleep_by_date) | set(readiness_by_date))
    result = []
    for d in all_dates:
        s = sleep_by_date.get(d, {})
        r = readiness_by_date.get(d, {})
        result.append(
            {
                "date": d,
                "sleep_score": s.get("score"),
                "readiness_score": r.get("score"),
                "temperature_deviation": r.get("temperature_deviation"),
                "sleep_contributors": s.get("contributors", {}),
                "readiness_contributors": r.get("contributors", {}),
            }
        )

    return result


# ---------------------------------------------------------------------------
# Top-level sense entry point (invoke_organelle compatible)
# ---------------------------------------------------------------------------


def _fetch_daily(endpoint: str, d: str, token: str) -> dict[str, Any]:
    """Fetch a single daily record, returning {} on failure."""
    try:
        records = _fetch(endpoint, d, d, token)
        return records[0] if records else {}
    except Exception:
        return {}


def sense() -> dict[str, Any]:
    """Top-level sense call: today's full health snapshot.

    Primary entry point for invoke_organelle-style callers.
    Fetches all available Oura daily endpoints.
    Never raises; returns {"error": "..."} on failure.

    Returns:
        Merged dict with sleep scores, readiness, detailed sleep, activity,
        stress, spo2, resilience, and sleep_time data.
    """
    try:
        d = _today_date()
        token = _get_token()

        # Core: daily scores + detailed sleep
        t = today(d)
        sd = sleep_detail(d)

        # Additional daily endpoints — each namespaced to avoid key collisions
        activity = _fetch_daily("daily_activity", d, token)
        stress = _fetch_daily("daily_stress", d, token)
        spo2 = _fetch_daily("daily_spo2", d, token)
        resilience = _fetch_daily("daily_resilience", d, token)
        sleep_time = _fetch_daily("sleep_time", d, token)
        cardio_age = _fetch_daily("daily_cardiovascular_age", d, token)
        vo2 = _fetch_daily("vO2_max", d, token)
        workouts = _fetch("workout", d, d, token)

        result = {**t, **{k: v for k, v in sd.items() if k != "date"}}

        if activity:
            result["activity"] = {
                "score": activity.get("score"),
                "steps": activity.get("steps"),
                "active_calories": activity.get("active_calories"),
                "total_calories": activity.get("total_calories"),
                "high_activity_time": activity.get("high_activity_time"),
                "medium_activity_time": activity.get("medium_activity_time"),
                "low_activity_time": activity.get("low_activity_time"),
                "sedentary_time": activity.get("sedentary_time"),
                "resting_time": activity.get("resting_time"),
                "equivalent_walking_distance": activity.get("equivalent_walking_distance"),
                "contributors": activity.get("contributors", {}),
            }

        if stress:
            result["stress"] = {
                "day_summary": stress.get("day_summary"),
                "stress_high": stress.get("stress_high"),
                "recovery_high": stress.get("recovery_high"),
            }

        if spo2:
            result["spo2"] = {
                "average": (spo2.get("spo2_percentage") or {}).get("average"),
                "breathing_disturbance_index": spo2.get("breathing_disturbance_index"),
            }

        if resilience:
            result["resilience"] = {
                "level": resilience.get("level"),
                "contributors": resilience.get("contributors", {}),
            }

        if sleep_time:
            result["sleep_time"] = {
                "recommendation": sleep_time.get("recommendation"),
                "status": sleep_time.get("status"),
                "optimal_bedtime": sleep_time.get("optimal_bedtime"),
            }

        if cardio_age:
            result["vascular_age"] = cardio_age.get("vascular_age")

        if vo2:
            result["vo2_max"] = vo2.get("vo2_max")

        if workouts:
            result["workouts"] = [
                {
                    "activity": w.get("activity"),
                    "calories": w.get("calories"),
                    "distance": w.get("distance"),
                    "intensity": w.get("intensity"),
                    "source": w.get("source"),
                    "start": w.get("start_datetime"),
                    "end": w.get("end_datetime"),
                    "label": w.get("label"),
                }
                for w in workouts
            ]

        return result
    except Exception as exc:
        return {"error": str(exc)}
