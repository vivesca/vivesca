"""respiration_sensor — Claude Code Max plan token budget usage (formerly respirometry).

Endosymbiosis: standalone Python script (~/.local/bin/respirometry) → Python organelle.
The original script fetched live OAuth usage from Anthropic's API, fell back to cached
JSONL history, and computed status thresholds. This organelle exposes the same logic as
importable functions, removing the subprocess layer that callers previously required.

Respiration in biology measures metabolic rate — the rate at which fuel is consumed.
This organelle measures token budget consumption: how much of the weekly allocation
has been burned, and whether the organism is at risk of anaerobic (over-budget) operation.

Core functions: sense_usage, budget_status, append_history, serialize_status.
"""

import configparser
import json
import subprocess
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

HISTORY_FILE = Path.home() / ".local/share/respirometry/history.jsonl"
WATCH_LOG = Path.home() / "genome/respirometry-log.jsonl"

_CONF_PATH = Path(__file__).parent / "respiration_sensor.conf"
_conf = configparser.ConfigParser()
_conf.read(_CONF_PATH)

# Budget thresholds
_THRESHOLD_SAFE = _conf.getint("thresholds", "threshold_safe", fallback=50)
_THRESHOLD_CAUTION = _conf.getint("thresholds", "threshold_caution", fallback=70)
_THRESHOLD_WARNING = _conf.getint("thresholds", "threshold_warning", fallback=85)
# above WARNING is DANGER


def get_oauth_token() -> str:
    """Read OAuth token from macOS Keychain via security CLI.

    Returns:
        Access token string.

    Raises:
        RuntimeError: If keychain entry is missing or token is expired.
    """
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError("No Keychain entry for 'Claude Code-credentials'")

    data = json.loads(result.stdout.strip())
    oauth = data["claudeAiOauth"]

    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    if oauth["expiresAt"] < now_ms:
        raise RuntimeError("Token expired. Start a Claude Code session to refresh.")

    return oauth["accessToken"]


def internalize_usage(token: str, timeout: int = 10) -> dict:
    """Fetch live usage metrics from Anthropic OAuth API.

    Args:
        token: OAuth access token.
        timeout: HTTP timeout in seconds.

    Returns:
        Raw API response dict with keys like "seven_day", "seven_day_sonnet".
    """
    req = urllib.request.Request(
        "https://api.anthropic.com/api/oauth/usage",
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": "oauth-2025-04-20",
            "User-Agent": "respiration_sensor/1.0.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _read_fallback() -> tuple[dict | None, int | None]:
    """Read the most recent cached entry from history JSONL files.

    Returns:
        (entry_dict, age_seconds) or (None, None) if no cache.
    """
    for path in [HISTORY_FILE, WATCH_LOG]:
        if not path.exists():
            continue
        lines = path.read_text().strip().splitlines()
        if not lines:
            continue
        entry = json.loads(lines[-1])
        ts_str = entry.get("ts", "")
        try:
            ts = datetime.fromisoformat(ts_str)
            age = (datetime.now(UTC) - ts.astimezone(UTC)).total_seconds()
        except (ValueError, TypeError):
            age = -1
        return entry, int(age) if age >= 0 else None
    return None, None


def sense_usage() -> tuple[dict, int | None]:
    """Fetch usage metrics, falling back to cache on API failure.

    Returns:
        (usage_dict, stale_age_seconds)
        stale_age_seconds is None if data is live, an integer if from cache.
        usage_dict contains keys like "seven_day" and "seven_day_sonnet", each
        with "utilization" (float 0-100) and optionally "resets_at".

    Raises:
        RuntimeError: If both live API and cache fail.
    """
    try:
        token = get_oauth_token()
        usage = internalize_usage(token)
        return usage, None
    except Exception as live_err:
        entry, age = _read_fallback()
        if entry is None:
            raise RuntimeError(
                f"Live API failed ({live_err}) and no cached data available"
            ) from live_err
        # Normalise cached format
        if "metrics" in entry:
            metrics = entry["metrics"]
            usage = {}
            for key in ["seven_day", "seven_day_sonnet"]:
                if key in metrics:
                    usage[key] = {
                        "utilization": metrics[key]["utilization"],
                        "resets_at": metrics[key].get("resets_at", ""),
                    }
            return usage, age
        return {
            "seven_day": {"utilization": entry.get("weekly_pct", 0)},
            "seven_day_sonnet": {"utilization": entry.get("sonnet_pct", 0)},
        }, age


def budget_status(usage: dict) -> str:
    """Classify budget pressure from usage metrics.

    Args:
        usage: dict from sense_usage() with "seven_day" / "seven_day_sonnet" keys.

    Returns:
        One of: "SAFE", "CAUTION", "WARNING", "DANGER"
    """
    seven = usage.get("seven_day", {})
    sonnet = usage.get("seven_day_sonnet", {})
    max_util = max(
        float(seven.get("utilization", 0)),
        float(sonnet.get("utilization", 0)),
    )
    if max_util < _THRESHOLD_SAFE:
        return "SAFE"
    if max_util < _THRESHOLD_CAUTION:
        return "CAUTION"
    if max_util < _THRESHOLD_WARNING:
        return "WARNING"
    return "DANGER"


def record_breath(usage: dict) -> None:
    """Append a usage snapshot to the history JSONL file.

    Args:
        usage: dict from internalize_usage() or sense_usage().
    """
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(UTC).isoformat(),
        "metrics": {},
    }
    for key in ["seven_day", "seven_day_sonnet"]:
        if key in usage:
            row["metrics"][key] = usage[key]
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(row) + "\n")


def _format_age(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def serialize_status(usage: dict, stale_age: int | None = None) -> dict:
    """Format usage as a structured status summary.

    Args:
        usage: dict from sense_usage().
        stale_age: Seconds since last live fetch, or None if current.

    Returns:
        {
            "status": "SAFE"|"CAUTION"|"WARNING"|"DANGER",
            "weekly_pct": float,
            "sonnet_pct": float,
            "session_pct": float | None,
            "stale": bool,
            "stale_label": str | None,  # e.g. "5m ago"
            "resets_at": str,
        }
    """
    seven = usage.get("seven_day", {})
    sonnet = usage.get("seven_day_sonnet", {})
    five = usage.get("five_hour", {})

    status = budget_status(usage)
    stale_label = _format_age(stale_age) if stale_age is not None else None

    return {
        "status": status,
        "weekly_pct": float(seven.get("utilization", 0)),
        "sonnet_pct": float(sonnet.get("utilization", 0)),
        "session_pct": float(five.get("utilization", 0)) if five else None,
        "stale": stale_age is not None,
        "stale_label": stale_label,
        "resets_at": str(seven.get("resets_at", "")),
    }


def sense() -> dict:
    """Top-level sense call: fetch usage and return structured status.

    This is the primary entry point for invoke_organelle-style callers.
    Never raises; returns {"error": "..."} on failure.

    Returns:
        serialize_status() output or {"error": "message"}.
    """
    try:
        usage, stale_age = sense_usage()
        return serialize_status(usage, stale_age)
    except Exception as exc:
        return {"error": str(exc)}
