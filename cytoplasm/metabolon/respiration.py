"""respiration — autonomic pacing and budget regulation.

The organism's respiratory system. Pure arithmetic, no LLM judgment.
Controls how fast the organism burns its budget: interactive pressure,
daily wave counting, skip-until scheduling, saturation weighting,
and the pacing gate that pulse consults before each wave.

Five-layer self-regulation:
1. Interactive awareness — blends live session util with learned hourly patterns
2. Measured wave cost — tracks per-wave deltas (including zeros) for accuracy
3. Skip-until — fast-exit scheduling when pacing blocks
4. Saturation penalty — wasted waves count at 1.5x cost
5. Pacing gate — combines all layers into a single go/no-go decision
"""

import datetime
import json
import subprocess
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
from metabolon.cytosol import VIVESCA_ROOT

LOG_DIR = Path.home() / "logs"
EVENT_LOG = LOG_DIR / "vivesca-events.jsonl"
_LEGACY_EVENT_LOG = LOG_DIR / "copia-events.jsonl"
CONF_PATH = VIVESCA_ROOT / "respiration.conf"
DAILY_STATE_FILE = Path.home() / "tmp" / "respiration-daily.json"
SKIP_UNTIL_FILE = Path.home() / "tmp" / ".respiration-skip-until"
INTERACTIVE_PATTERN_FILE = Path.home() / "tmp" / ".respiration-pattern.json"
PACING_ALERT_FILE = Path.home() / "tmp" / ".respiration-alerted.json"

# Legacy paths — checked on first read, then ignored
_LEGACY_DAILY_STATE = Path.home() / "tmp" / "lucerna-daily-waves.json"
_LEGACY_SKIP_UNTIL = Path.home() / "tmp" / ".lucerna-skip-until"
_LEGACY_PATTERN = Path.home() / "tmp" / ".lucerna-interactive-pattern.json"
_LEGACY_ALERT = Path.home() / "tmp" / ".lucerna-pacing-alerted.json"
_LEGACY_CONF = VIVESCA_ROOT / "lucerna.conf"

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
TACHYCARDIA_THRESHOLD = 60  # % — send TG alert when weekly crosses this
AEROBIC_CEILING = 80  # % — stop if weekly usage exceeds this
SONNET_CEILING = 90  # % — stop if sonnet usage exceeds this
SYMPATHETIC_RESERVE = 15  # % — reserve for interactive work
BASAL_RATE = 0.5  # pulse's share when Terry is idle
MIN_BASAL_RATE = 0.15  # pulse's share when Terry is very active
MAX_DAILY_WAVES = 10  # hard cap on waves per calendar day
DEFAULT_COST_PER_WAVE = 1.0  # fallback estimate; replaced by measured average
SATURATION_PENALTY = 1.5  # saturated waves count 1.5x cost


# ---------------------------------------------------------------------------
# Legacy migration helpers
# ---------------------------------------------------------------------------


def _migrate_path(new: Path, legacy: Path) -> None:
    """If legacy file exists but new doesn't, rename it."""
    if not new.exists() and legacy.exists():
        legacy.rename(new)


def _ensure_migrated():
    """One-time migration of legacy state files."""
    _migrate_path(DAILY_STATE_FILE, _LEGACY_DAILY_STATE)
    _migrate_path(SKIP_UNTIL_FILE, _LEGACY_SKIP_UNTIL)
    _migrate_path(INTERACTIVE_PATTERN_FILE, _LEGACY_PATTERN)
    _migrate_path(PACING_ALERT_FILE, _LEGACY_ALERT)
    _migrate_path(CONF_PATH, _LEGACY_CONF)
    _migrate_path(EVENT_LOG, _LEGACY_EVENT_LOG)


_migrated = False


def _maybe_migrate():
    global _migrated
    if not _migrated:
        _ensure_migrated()
        _migrated = True


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def log_event(event: str, **kwargs):
    """Append structured event to JSONL log for observability."""
    entry = {
        "ts": datetime.datetime.now().isoformat(),
        "event": event,
        **kwargs,
    }
    with open(EVENT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    detail = " ".join(f"{k}={v}" for k, v in kwargs.items() if k != "output_tail")
    print(f"[{entry['ts'][11:19]}] {event} {detail}", flush=True)


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


def send_distress_signal(msg: str):
    """Send a cellular distress signal via Telegram."""
    try:
        subprocess.run(["deltos", msg], capture_output=True, timeout=10)
    except Exception:
        log(f"TG alert failed: {msg}")


def _send_pacing_alert_once(reason: str):
    """Alert on pacing block, but only once per calendar day."""
    _maybe_migrate()
    today = datetime.date.today().isoformat()
    try:
        data = json.loads(PACING_ALERT_FILE.read_text())
        if data.get("date") == today:
            return
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    send_distress_signal(f"Pulse paused for today: {reason}")
    PACING_ALERT_FILE.write_text(json.dumps({"date": today}))


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

_telemetry_cache: dict | None = None
_telemetry_cache_time: float = 0
TELEMETRY_CACHE_TTL = 30  # seconds


def _fetch_telemetry() -> dict | None:
    global _telemetry_cache, _telemetry_cache_time
    if (
        _telemetry_cache is not None
        and (time.time() - _telemetry_cache_time) < TELEMETRY_CACHE_TTL
    ):
        return _telemetry_cache
    try:
        result = subprocess.run(
            ["respirometry", "--json"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0:
            log(f"respirometry failed: {result.stderr.strip()}")
            return None
        _telemetry_cache = json.loads(result.stdout)
        _telemetry_cache_time = time.time()
        return _telemetry_cache
    except Exception as e:
        log(f"respirometry error: {e}")
        return None


def measure_respiration() -> dict | None:
    """Measure current respiration rate — live token usage. Returns full dict or None."""
    return _fetch_telemetry()


def respiration_snapshot() -> dict | None:
    """Snapshot current respiratory rate as {weekly, sonnet}. Returns None on failure."""
    telemetry = _fetch_telemetry()
    if telemetry:
        return {
            "weekly": telemetry.get("seven_day", {}).get("utilization", 0),
            "sonnet": telemetry.get("seven_day_sonnet", {}).get("utilization", 0),
        }
    return None


def check_vital_capacity() -> tuple[bool, str]:
    """Check vital capacity — coarse budget gate. Returns (has_capacity, reason)."""
    usage = measure_respiration()
    if usage is None:
        return False, "budget_unknown"

    weekly = usage.get("seven_day", {}).get("utilization", 0)
    sonnet = usage.get("seven_day_sonnet", {}).get("utilization", 0)

    log(f"Budget: weekly={weekly}%, sonnet={sonnet}%")

    if weekly > AEROBIC_CEILING:
        return False, f"weekly_{weekly}%_exceeds_{AEROBIC_CEILING}%"
    if sonnet > SONNET_CEILING:
        return False, f"sonnet_{sonnet}%_exceeds_{SONNET_CEILING}%"

    weekly_remaining = 100 - weekly
    if weekly_remaining < SYMPATHETIC_RESERVE:
        return (
            False,
            f"weekly_remaining_{weekly_remaining}%_below_reserve_{SYMPATHETIC_RESERVE}%",
        )

    if weekly > TACHYCARDIA_THRESHOLD or sonnet > TACHYCARDIA_THRESHOLD:
        send_distress_signal(f"Respiration: budget climbing -- weekly={weekly}%, sonnet={sonnet}%")

    # Pacing gate — are we burning faster than the week can sustain?
    pacing_ok, pacing_reason = check_pacing()
    if not pacing_ok:
        _send_pacing_alert_once(pacing_reason)
        return False, pacing_reason

    return True, f"ok_weekly={weekly}%_sonnet={sonnet}%"


def get_respiratory_status() -> str:
    """Per-wave respiratory status. Returns: green, yellow, red, or unknown."""
    telemetry = _fetch_telemetry()
    if telemetry:
        subprocess.run(["respirometry", "log"], capture_output=True, timeout=10)
        weekly = telemetry.get("seven_day", {}).get("utilization", 0)
        sonnet = telemetry.get("seven_day_sonnet", {}).get("utilization", 0)
        max_util = max(weekly, sonnet)
        log_event("budget_raw", weekly=weekly, sonnet=sonnet)
        if max_util < 95:
            return "green"
        elif max_util < 98:
            return "yellow"
        else:
            return "red"

    # Fall back to cached
    try:
        result = subprocess.run(
            ["respirometry-cached", "--budget", "--overnight"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        status = result.stdout.strip().lower() or "unknown"
        if status != "unknown":
            log_event("budget_source", source="cached_stale")
        return status
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Daily wave counter (workaround for integer-rounded utilization)
# ---------------------------------------------------------------------------


def _today_str() -> str:
    return datetime.date.today().isoformat()


def _load_circadian_state() -> dict:
    """Load today's circadian cycle state. Resets on new day."""
    _maybe_migrate()
    try:
        circadian_state = json.loads(DAILY_STATE_FILE.read_text())
        if circadian_state.get("date") == _today_str():
            return circadian_state
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {
        "date": _today_str(),
        "count": 0,
        "saturated": 0,
        "day_start_weekly": None,
        "wave_deltas": [],
    }


def _save_circadian_state(state: dict):
    DAILY_STATE_FILE.write_text(json.dumps(state))


def get_daily_wave_count() -> int:
    return _load_circadian_state().get("count", 0)


def get_daily_saturated_count() -> int:
    return _load_circadian_state().get("saturated", 0)


def increment_daily_wave_count(saturated: bool = False, wave_delta: float = 0.0):
    """Record one more wave, its saturation status, and its measured delta."""
    circadian_state = _load_circadian_state()
    circadian_state["count"] = circadian_state.get("count", 0) + 1
    if saturated:
        circadian_state["saturated"] = circadian_state.get("saturated", 0) + 1
    deltas = circadian_state.get("wave_deltas", [])
    deltas.append(wave_delta)
    circadian_state["wave_deltas"] = deltas
    _save_circadian_state(circadian_state)
    return circadian_state["count"]


def set_circadian_baseline(weekly: float):
    """Record the circadian baseline — weekly % at the start of today's first wave."""
    circadian_state = _load_circadian_state()
    if circadian_state.get("day_start_weekly") is None:
        circadian_state["day_start_weekly"] = weekly
        _save_circadian_state(circadian_state)


# ---------------------------------------------------------------------------
# Sympathetic awareness (layer 1)
# ---------------------------------------------------------------------------


def _load_sympathetic_pattern() -> dict:
    """Load hourly sympathetic (fight-or-flight) usage pattern."""
    _maybe_migrate()
    try:
        return json.loads(INTERACTIVE_PATTERN_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _record_sympathetic_sample(hour: int, session_util: float):
    """Record a sympathetic nervous system sample for pattern learning.

    Maintains an exponential moving average per hour-of-day.
    """
    pattern = _load_sympathetic_pattern()
    key = str(hour)
    if key in pattern:
        # EMA with alpha=0.2 — adapts over ~5 samples
        pattern[key] = round(0.8 * pattern[key] + 0.2 * session_util, 1)
    else:
        pattern[key] = round(session_util, 1)
    INTERACTIVE_PATTERN_FILE.write_text(json.dumps(pattern))


def get_interactive_pressure() -> float:
    """How actively Terry is using Claude (0.0 = idle, 1.0 = heavy).

    Combines live session utilization with learned hourly patterns.
    Live signal gets 70% weight when available.
    """
    telemetry = _fetch_telemetry()
    hour = datetime.datetime.now().hour

    live_util = 0.0
    if telemetry:
        live_util = telemetry.get("five_hour", {}).get("utilization", 0)
        _record_sympathetic_sample(hour, live_util)

    pattern = _load_sympathetic_pattern()
    pattern_util = pattern.get(str(hour), 0)

    blended = 0.7 * live_util + 0.3 * pattern_util if telemetry else pattern_util
    pressure = max(0.0, min(1.0, (blended - 20) / 40))

    log_event(
        "interactive_pressure",
        live=round(live_util, 1),
        pattern=round(pattern_util, 1),
        blended=round(blended, 1),
        pressure=round(pressure, 2),
        hour=hour,
    )

    return pressure


def get_tidal_volume() -> float:
    """Tidal volume — pulse's share of the daily budget, adjusted for sympathetic pressure."""
    genome = read_respiratory_genome()
    base = genome.get("basal_rate", BASAL_RATE)
    floor = genome.get("min_basal_rate", MIN_BASAL_RATE)
    pressure = get_interactive_pressure()
    share = base - pressure * (base - floor)
    return share


# ---------------------------------------------------------------------------
# Measured wave cost (layer 2)
# ---------------------------------------------------------------------------


def get_measured_cost_per_wave() -> float:
    """Estimate actual cost per wave from isolated per-wave deltas.

    Including zeros is critical: integer-rounded deltas of [0,1,0,0,1,0,1]
    average to 0.43, far more accurate than filtering to non-zero (always 1.0).
    """
    circadian_state = _load_circadian_state()
    wave_deltas = circadian_state.get("wave_deltas", [])

    if len(wave_deltas) >= 3:
        avg = sum(wave_deltas) / len(wave_deltas)
        log_event(
            "cost_measured",
            method="today_isolated",
            cost=round(avg, 3),
            samples=len(wave_deltas),
        )
        return max(avg, 0.1)

    try:
        deltas = []
        for line in EVENT_LOG.read_text().strip().splitlines()[-500:]:
            e = json.loads(line)
            if e.get("event") == "wave_usage":
                d = e.get("weekly_delta", 0)
                deltas.append(d)
        if len(deltas) >= 10:
            avg = sum(deltas) / len(deltas)
            log_event(
                "cost_measured",
                method="historical_all",
                cost=round(avg, 3),
                samples=len(deltas),
            )
            return max(avg, 0.1)
    except Exception:
        pass

    return DEFAULT_COST_PER_WAVE


# ---------------------------------------------------------------------------
# Apnea scheduling (layer 3)
# ---------------------------------------------------------------------------


def is_apneic() -> tuple[bool, str]:
    """Check if the organism is in apnea (breathing pause from prior pacing block)."""
    _maybe_migrate()
    try:
        skip_until_str = SKIP_UNTIL_FILE.read_text().strip()
        skip_until = datetime.datetime.fromisoformat(skip_until_str)
        now = (
            datetime.datetime.now(skip_until.tzinfo)
            if skip_until.tzinfo
            else datetime.datetime.now()
        )
        if now < skip_until:
            remaining = (skip_until - now).total_seconds() / 60
            return True, f"skip_until {skip_until_str} ({remaining:.0f}m remaining)"
    except (FileNotFoundError, ValueError):
        pass
    return False, ""


def induce_apnea(
    daily_budget: float,
    cost_per_wave: float,
    waves_today: int,
    sustainable_daily: float,
):
    """Induce apnea — calculate when the next breath (wave) is permitted."""
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)

    if waves_today >= MAX_DAILY_WAVES:
        SKIP_UNTIL_FILE.write_text(midnight.isoformat())
        log_event("skip_set", until=midnight.isoformat(), reason="daily_cap")
        return

    skip_until = min(now + datetime.timedelta(hours=1), midnight)
    SKIP_UNTIL_FILE.write_text(skip_until.isoformat())
    log_event("skip_set", until=skip_until.isoformat(), reason="pacing_recheck")


def resume_breathing():
    """Resume breathing — clear apnea state after a successful wave."""
    SKIP_UNTIL_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Saturation-weighted burn (layer 4)
# ---------------------------------------------------------------------------


def get_effective_burn(waves_today: int, saturated_today: int, cost_per_wave: float) -> float:
    """Calculate effective budget burn, penalizing saturated waves."""
    genome = read_respiratory_genome()
    penalty = genome.get("saturation_penalty", SATURATION_PENALTY)
    productive = waves_today - saturated_today
    effective_waves = productive + (saturated_today * penalty)
    return effective_waves * cost_per_wave


# ---------------------------------------------------------------------------
# Pacing gate (layer 5 — combines all)
# ---------------------------------------------------------------------------


def check_pacing() -> tuple[bool, str]:
    """Check whether pulse is burning faster than the week can sustain."""
    telemetry = _fetch_telemetry()
    if telemetry is None:
        return False, "pacing_no_data"

    weekly = telemetry.get("seven_day", {}).get("utilization", 0)
    resets_at_str = telemetry.get("seven_day", {}).get("resets_at", "")
    if not resets_at_str:
        return True, "pacing_no_reset_info"

    try:
        resets_at = datetime.datetime.fromisoformat(resets_at_str)
        now = datetime.datetime.now(resets_at.tzinfo)
    except (ValueError, TypeError):
        return True, "pacing_bad_reset_format"

    set_circadian_baseline(weekly)

    days_remaining = max((resets_at - now).total_seconds() / 86400, 0.25)
    remaining_budget = 100 - weekly - SYMPATHETIC_RESERVE
    sustainable_daily = remaining_budget / days_remaining

    dynamic_share = get_tidal_volume()
    daily_budget = sustainable_daily * dynamic_share

    cost_per_wave = get_measured_cost_per_wave()

    waves_today = get_daily_wave_count()
    saturated_today = get_daily_saturated_count()
    estimated_burn = get_effective_burn(waves_today, saturated_today, cost_per_wave)

    log_event(
        "pacing_check",
        weekly=weekly,
        days_remaining=round(days_remaining, 1),
        remaining_budget=round(remaining_budget, 1),
        sustainable_daily=round(sustainable_daily, 1),
        dynamic_share=round(dynamic_share, 2),
        daily_budget=round(daily_budget, 1),
        cost_per_wave=round(cost_per_wave, 2),
        waves_today=waves_today,
        saturated_today=saturated_today,
        estimated_burn=round(estimated_burn, 1),
    )

    if estimated_burn >= daily_budget:
        induce_apnea(daily_budget, cost_per_wave, waves_today, sustainable_daily)
        return False, (
            f"pacing_exceeded: {waves_today} waves (eff ~{estimated_burn:.1f}%) "
            f">= daily allowance {daily_budget:.1f}% "
            f"(share={dynamic_share:.0%}, cost={cost_per_wave:.2f}/wave)"
        )

    if waves_today >= MAX_DAILY_WAVES:
        induce_apnea(daily_budget, cost_per_wave, waves_today, sustainable_daily)
        return False, f"daily_cap: {waves_today} >= {MAX_DAILY_WAVES}"

    return True, (
        f"pacing_ok: {waves_today} waves (eff ~{estimated_burn:.1f}%), "
        f"allowance {daily_budget:.1f}%/day"
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def read_respiratory_genome() -> dict:
    """Read the respiratory genome (respiration.conf). Fresh on every call."""
    _maybe_migrate()
    try:
        if CONF_PATH.exists():
            return json.loads(CONF_PATH.read_text())
    except Exception:
        pass
    return {}
