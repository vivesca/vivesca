"""chemoreceptor — Oura health sensing (formerly sopor). Endosymbiosis: Python CLI -> organelle.

Reads Oura Ring data via the Oura API v2. Credential resolution: OURA_TOKEN env var first,
then macOS Keychain entry 'oura-token'. Requires httpx (already a vivesca dependency).

Core functions: today(), week(), readiness(), sleep_score(), hrv().
"""

from __future__ import annotations

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
    """Read Oura personal access token from macOS Keychain entry 'oura-token'."""
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


def hrv(target_date: str | None = None) -> dict[str, Any]:
    """Return average HRV and heart rate from last night's sleep.

    Reads from the detailed sleep endpoint (not daily summary) to extract
    average_hrv and average_heart_rate from the longest sleep session.

    Args:
        target_date: ISO date string, defaults to today.

    Returns:
        Dict with keys: date, average_hrv (ms, float|None), average_heart_rate (bpm, float|None).
    """
    d = target_date or _today_date()
    records = _fetch("sleep", d, d)

    if not records:
        return {"date": d, "average_hrv": None, "average_heart_rate": None}

    # Pick the record with the longest total_sleep_duration
    def _duration(rec: dict) -> int:
        v = rec.get("total_sleep_duration", 0)
        try:
            return int(v) if v else 0
        except (TypeError, ValueError):
            return 0

    best = max(records, key=_duration)
    return {
        "date": d,
        "average_hrv": best.get("average_hrv"),
        "average_heart_rate": best.get("average_heart_rate"),
        "lowest_heart_rate": best.get("lowest_heart_rate"),
    }


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


def sense() -> dict[str, Any]:
    """Top-level sense call: today's health snapshot.

    Primary entry point for invoke_organelle-style callers.
    Never raises; returns {"error": "..."} on failure.

    Returns:
        today() output merged with hrv() output, or {"error": "message"}.
    """
    try:
        t = today()
        h = hrv(t.get("date"))
        return {**t, **{k: v for k, v in h.items() if k != "date"}}
    except Exception as exc:
        return {"error": str(exc)}
