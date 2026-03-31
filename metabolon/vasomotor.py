from __future__ import annotations

"""vasomotor — autonomic pacing and budget regulation.

The organism's respiratory system. Pure arithmetic, no LLM judgment.
Controls how fast the organism burns its budget: interactive pressure,
daily systole counting, skip-until scheduling, saturation weighting,
and the pacing gate that pulse consults before each systole.

Five-layer self-regulation:
1. Interactive awareness — blends live session util with learned hourly patterns
2. Measured systole cost — tracks per-systole deltas (including zeros) for accuracy
3. Skip-until — fast-exit scheduling when pacing blocks
4. Saturation penalty — wasted systoles count at 1.5x cost
5. Pacing gate — combines all layers into a single go/no-go decision
"""

import contextlib
import datetime
import json
import subprocess
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
from metabolon.cytosol import VIVESCA_ROOT
from metabolon.locus import pulse_reports

LOG_DIR = Path.home() / "logs"
EVENT_LOG = LOG_DIR / "vivesca-events.jsonl"
_LEGACY_EVENT_LOG = LOG_DIR / "polarization-events.jsonl"
CONF_PATH = VIVESCA_ROOT / "respiration.conf"
METHYLATION_FILE = VIVESCA_ROOT / "methylation.jsonl"
DAILY_STATE_FILE = Path.home() / "tmp" / "respiration-daily.json"
SKIP_UNTIL_FILE = Path.home() / "tmp" / ".respiration-skip-until"
INTERACTIVE_PATTERN_FILE = Path.home() / "tmp" / ".respiration-pattern.json"
PACING_ALERT_FILE = Path.home() / "tmp" / ".respiration-alerted.json"

# Legacy paths — checked on first read, then ignored
_LEGACY_DAILY_STATE = Path.home() / "tmp" / "lucerna-daily-waves.json"
_LEGACY_SKIP_UNTIL = Path.home() / "tmp" / ".lucerna-skip-until"
_LEGACY_PATTERN = Path.home() / "tmp" / ".lucerna-interactive-pattern.json"
_LEGACY_ALERT = Path.home() / "tmp" / ".lucerna-pacing-alerted.json"
_LEGACY_CONF = VIVESCA_ROOT / "vasomotor.conf"  # previous name before respiration.conf
_LEGACY_CONF_LUCERNA = VIVESCA_ROOT / "lucerna.conf"

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
TACHYCARDIA_THRESHOLD = 60  # % — send TG alert when weekly crosses this
AEROBIC_CEILING = 80  # % — stop if weekly usage exceeds this
SONNET_CEILING = 90  # % — stop if sonnet usage exceeds this
SYMPATHETIC_RESERVE = 15  # % — reserve for interactive work
BASAL_RATE = 0.5  # pulse's share when Terry is idle
MIN_BASAL_RATE = 0.15  # pulse's share when Terry is very active
MAX_DAILY_SYSTOLES = 10  # hard cap on systoles per calendar day
DEFAULT_COST_PER_SYSTOLE = 1.0  # fallback estimate; replaced by measured average
SATURATION_PENALTY = 1.5  # saturated systoles count 1.5x cost


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
    # Conf rename chain: lucerna.conf → vasomotor.conf → respiration.conf
    _migrate_path(_LEGACY_CONF, _LEGACY_CONF_LUCERNA)  # lucerna → vasomotor
    _migrate_path(CONF_PATH, _LEGACY_CONF)  # vasomotor → respiration
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


def record_event(event: str, **kwargs):
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


def emit_distress_signal(msg: str):
    """Send a cellular distress signal via Telegram."""
    try:
        from metabolon.organelles.secretory_vesicle import secrete_text

        secrete_text(msg, html=False, label="Distress")
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
    emit_distress_signal(f"Pulse paused for today: {reason}")
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


def measure_vasomotor_tone() -> dict | None:
    """Measure current respiration rate — live token usage. Returns full dict or None."""
    return _fetch_telemetry()


def vasomotor_snapshot() -> dict | None:
    """Snapshot current respiratory rate as {weekly, sonnet}. Returns None on failure."""
    telemetry = _fetch_telemetry()
    if telemetry:
        return {
            "weekly": telemetry.get("seven_day", {}).get("utilization", 0),
            "sonnet": telemetry.get("seven_day_sonnet", {}).get("utilization", 0),
        }
    return None


_RESETS_AT_FILE = Path.home() / "tmp" / ".respiration-resets-at"


def _hours_to_reset(telemetry: dict | None) -> float | None:
    """Hours until the weekly budget resets. None if unknown.

    Persists resets_at to disk so stale telemetry doesn't erase the value.
    """
    resets_at_str = ""
    if telemetry:
        resets_at_str = telemetry.get("seven_day", {}).get("resets_at", "")
        if resets_at_str:
            # Persist for fallback when telemetry is stale/unavailable
            _RESETS_AT_FILE.write_text(resets_at_str)
    if not resets_at_str:
        # Fallback: read last known reset time from disk
        try:
            resets_at_str = _RESETS_AT_FILE.read_text().strip()
        except FileNotFoundError:
            return None
    if not resets_at_str:
        return None
    try:
        resets_at = datetime.datetime.fromisoformat(resets_at_str)
        now = datetime.datetime.now(resets_at.tzinfo)
        return max((resets_at - now).total_seconds() / 3600, 0.5)
    except (ValueError, TypeError):
        return None


def oxygen_debt(hours_to_reset: float) -> float:
    """Use-it-or-lose-it pressure: 0.0 (no urgency) to 1.0 (budget expiring).

    Ramps linearly from 36h (0.0) to 6h (1.0). Below 6h, full debt.
    """
    return max(0.0, min(1.0, (48 - hours_to_reset) / 42))


def assess_vital_capacity() -> tuple[bool, str]:
    """Check vital capacity — coarse budget gate. Returns (has_capacity, reason)."""
    usage = measure_vasomotor_tone()
    if usage is None:
        return False, "budget_unknown"

    weekly = usage.get("seven_day", {}).get("utilization", 0)
    sonnet = usage.get("seven_day_sonnet", {}).get("utilization", 0)

    log(f"Budget: weekly={weekly}%, sonnet={sonnet}%")

    genome = vasomotor_genome()
    aerobic_ceiling = genome.get("aerobic_ceiling", AEROBIC_CEILING)
    sonnet_ceiling = genome.get("sonnet_ceiling", SONNET_CEILING)
    sympathetic_reserve = genome.get("sympathetic_reserve", SYMPATHETIC_RESERVE)
    tachycardia_threshold = genome.get("tachycardia_threshold", TACHYCARDIA_THRESHOLD)

    # Oxygen debt: relax thresholds when budget expires soon
    # Falls through to persisted resets_at when live telemetry is stale
    hours = _hours_to_reset(usage)
    if hours is None:
        hours = _hours_to_reset(None)  # try persisted fallback
    debt = oxygen_debt(hours) if hours is not None else 0.0
    effective_ceiling = aerobic_ceiling + debt * 10  # 80% → 90% under full debt
    effective_reserve = sympathetic_reserve * (1 - 0.7 * debt)  # 15% → 4.5%

    if weekly > effective_ceiling:
        return False, f"weekly_{weekly}%_exceeds_ceiling_{effective_ceiling:.0f}%"
    if sonnet > sonnet_ceiling:
        return False, f"sonnet_{sonnet}%_exceeds_{sonnet_ceiling}%"

    weekly_remaining = 100 - weekly
    if weekly_remaining < effective_reserve:
        return (
            False,
            f"weekly_remaining_{weekly_remaining}%_below_reserve_{effective_reserve:.0f}%",
        )

    if weekly > tachycardia_threshold or sonnet > tachycardia_threshold:
        emit_distress_signal(f"Respiration: budget climbing -- weekly={weekly}%, sonnet={sonnet}%")

    # Pacing gate — are we burning faster than the week can sustain?
    pacing_ok, pacing_reason = assess_pacing()
    if not pacing_ok:
        _send_pacing_alert_once(pacing_reason)
        return False, pacing_reason

    return True, f"ok_weekly={weekly}%_sonnet={sonnet}%"


def vasomotor_status() -> str:
    """Per-systole respiratory status. Returns: green, yellow, red, or unknown."""
    telemetry = _fetch_telemetry()
    if telemetry:
        subprocess.run(["respirometry", "log"], capture_output=True, timeout=10)
        weekly = telemetry.get("seven_day", {}).get("utilization", 0)
        sonnet = telemetry.get("seven_day_sonnet", {}).get("utilization", 0)
        max_util = max(weekly, sonnet)
        record_event("budget_raw", weekly=weekly, sonnet=sonnet)
        if max_util < 95:
            return "green"
        elif max_util < 98:
            return "yellow"
        else:
            return "red"

    # Fall back to cached
    try:
        result = subprocess.run(
            ["respirometry", "--budget", "--overnight"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        status = result.stdout.strip().lower() or "unknown"
        if status != "unknown":
            record_event("budget_source", source="cached_stale")
        return status
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Daily systole counter (workaround for integer-rounded utilization)
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
        "systole_deltas": [],
    }


def _save_circadian_state(state: dict):
    DAILY_STATE_FILE.write_text(json.dumps(state))


def daily_systole_count() -> int:
    return _load_circadian_state().get("count", 0)


# Backward-compat alias
daily_wave_count = daily_systole_count


def daily_saturated_count() -> int:
    return _load_circadian_state().get("saturated", 0)


def breathe(saturated: bool = False, systole_delta: float = 0.0, wave_delta: float = 0.0):
    """Record one more systole, its saturation status, and its measured delta."""
    circadian_state = _load_circadian_state()
    circadian_state["count"] = circadian_state.get("count", 0) + 1
    if saturated:
        circadian_state["saturated"] = circadian_state.get("saturated", 0) + 1
    delta = systole_delta or wave_delta  # accept either name (wave_delta: legacy compat)
    deltas = circadian_state.get("systole_deltas", [])
    deltas.append(delta)
    circadian_state["systole_deltas"] = deltas
    _save_circadian_state(circadian_state)
    return circadian_state["count"]


def calibrate_circadian(weekly: float):
    """Record the circadian baseline — weekly % at the start of today's first systole."""
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


def interactive_pressure() -> float:
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

    record_event(
        "interactive_pressure",
        live=round(live_util, 1),
        pattern=round(pattern_util, 1),
        blended=round(blended, 1),
        pressure=round(pressure, 2),
        hour=hour,
    )

    return pressure


def tidal_volume() -> float:
    """Tidal volume — pulse's share of the daily budget, adjusted for sympathetic pressure."""
    genome = vasomotor_genome()
    base = genome.get("basal_rate", BASAL_RATE)
    floor = genome.get("min_basal_rate", MIN_BASAL_RATE)
    pressure = interactive_pressure()
    share = base - pressure * (base - floor)
    return share


# ---------------------------------------------------------------------------
# Measured systole cost (layer 2)
# ---------------------------------------------------------------------------


def measured_cost_per_systole() -> float:
    """Estimate actual cost per systole from isolated per-systole deltas.

    Including zeros is critical: integer-rounded deltas of [0,1,0,0,1,0,1]
    average to 0.43, far more accurate than filtering to non-zero (always 1.0).
    """
    circadian_state = _load_circadian_state()
    systole_deltas = circadian_state.get("systole_deltas", [])

    if len(systole_deltas) >= 3:
        avg = sum(systole_deltas) / len(systole_deltas)
        record_event(
            "cost_measured",
            method="today_isolated",
            cost=round(avg, 3),
            samples=len(systole_deltas),
        )
        return max(avg, 0.1)

    try:
        deltas = []
        for line in EVENT_LOG.read_text().strip().splitlines()[-500:]:
            e = json.loads(line)
            if e.get("event") == "systole_usage":
                d = e.get("weekly_delta", 0)
                deltas.append(d)
        if len(deltas) >= 10:
            avg = sum(deltas) / len(deltas)
            record_event(
                "cost_measured",
                method="historical_all",
                cost=round(avg, 3),
                samples=len(deltas),
            )
            return max(avg, 0.1)
    except Exception:
        pass

    genome = vasomotor_genome()
    return genome.get("default_cost_per_systole", DEFAULT_COST_PER_SYSTOLE)


# Backward-compat alias — remove after all callers updated
measured_cost_per_wave = measured_cost_per_systole


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
    cost_per_systole: float,
    systoles_today: int,
    sustainable_daily: float,
):
    """Induce apnea — calculate when the next breath (systole) is permitted."""
    genome = vasomotor_genome()
    max_daily_systoles = genome.get("max_daily_systoles", MAX_DAILY_SYSTOLES)
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)

    if systoles_today >= max_daily_systoles:
        SKIP_UNTIL_FILE.write_text(midnight.isoformat())
        record_event("skip_set", until=midnight.isoformat(), reason="daily_cap")
        return

    skip_until = min(now + datetime.timedelta(hours=1), midnight)
    SKIP_UNTIL_FILE.write_text(skip_until.isoformat())
    record_event("skip_set", until=skip_until.isoformat(), reason="pacing_recheck")


def resume_breathing():
    """Resume breathing — clear apnea state after a successful systole."""
    SKIP_UNTIL_FILE.unlink(missing_ok=True)


def set_recovery_interval():
    """Set next-beat delay based on oxygen debt. High debt = short recovery."""
    telemetry = _fetch_telemetry()
    hours = _hours_to_reset(telemetry)
    if hours is None:
        minutes = 120  # fallback: 2h
    else:
        debt = oxygen_debt(hours)
        # 120min at debt=0, 30min at debt=1
        minutes = max(30, round(120 - debt * 90))
    skip_until = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    SKIP_UNTIL_FILE.write_text(skip_until.isoformat())
    record_event("recovery_interval", minutes=minutes, until=skip_until.isoformat())


# ---------------------------------------------------------------------------
# Saturation-weighted burn (layer 4)
# ---------------------------------------------------------------------------


def effective_burn(systoles_today: int, saturated_today: int, cost_per_systole: float) -> float:
    """Calculate effective budget burn, penalizing saturated systoles."""
    genome = vasomotor_genome()
    penalty = genome.get("saturation_penalty", SATURATION_PENALTY)
    productive = systoles_today - saturated_today
    effective_systoles = productive + (saturated_today * penalty)
    return effective_systoles * cost_per_systole


# ---------------------------------------------------------------------------
# Pacing gate (layer 5 — combines all)
# ---------------------------------------------------------------------------


def assess_pacing() -> tuple[bool, str]:
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

    calibrate_circadian(weekly)

    days_remaining = max((resets_at - now).total_seconds() / 86400, 0.25)

    genome = vasomotor_genome()
    sympathetic_reserve = genome.get("sympathetic_reserve", SYMPATHETIC_RESERVE)
    max_daily_systoles = genome.get("max_daily_systoles", MAX_DAILY_SYSTOLES)

    # Oxygen debt: reduce reserve and boost share when budget expires soon
    hours = days_remaining * 24
    debt = oxygen_debt(hours)
    effective_reserve = sympathetic_reserve * (1 - 0.7 * debt)

    remaining_budget = 100 - weekly - effective_reserve
    sustainable_daily = remaining_budget / days_remaining

    dynamic_share = tidal_volume()
    if debt > 0:
        dynamic_share = min(0.8, dynamic_share + debt * 0.4)
    daily_budget = sustainable_daily * dynamic_share

    cost_per_systole = measured_cost_per_systole()

    systoles_today = daily_systole_count()
    saturated_today = daily_saturated_count()
    estimated_burn = effective_burn(systoles_today, saturated_today, cost_per_systole)

    record_event(
        "pacing_check",
        weekly=weekly,
        days_remaining=round(days_remaining, 1),
        oxygen_debt=round(debt, 2),
        remaining_budget=round(remaining_budget, 1),
        sustainable_daily=round(sustainable_daily, 1),
        dynamic_share=round(dynamic_share, 2),
        daily_budget=round(daily_budget, 1),
        cost_per_systole=round(cost_per_systole, 2),
        systoles_today=systoles_today,
        saturated_today=saturated_today,
        estimated_burn=round(estimated_burn, 1),
    )

    if estimated_burn >= daily_budget:
        induce_apnea(daily_budget, cost_per_systole, systoles_today, sustainable_daily)
        return False, (
            f"pacing_exceeded: {systoles_today} systoles (eff ~{estimated_burn:.1f}%) "
            f">= daily allowance {daily_budget:.1f}% "
            f"(share={dynamic_share:.0%}, cost={cost_per_systole:.2f}/systole)"
        )

    if systoles_today >= max_daily_systoles:
        induce_apnea(daily_budget, cost_per_systole, systoles_today, sustainable_daily)
        return False, f"daily_cap: {systoles_today} >= {max_daily_systoles}"

    return True, (
        f"pacing_ok: {systoles_today} systoles (eff ~{estimated_burn:.1f}%), "
        f"allowance {daily_budget:.1f}%/day"
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def vasomotor_genome() -> dict:
    """Read the respiratory genome (vasomotor.conf). Fresh on every call."""
    _maybe_migrate()
    try:
        if CONF_PATH.exists():
            return json.loads(CONF_PATH.read_text())
    except Exception:
        pass
    return {}


ROLLBACK_DIR = Path.home() / "tmp" / "conf-rollback"


def _snapshot_conf(path: Path):
    """Snapshot a conf file before modification — demethylation safety net."""
    ROLLBACK_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot = ROLLBACK_DIR / f"{path.name}.{ts}"
    with contextlib.suppress(Exception):
        snapshot.write_text(path.read_text())


def _write_genome(genome: dict):
    """Write updated genome back to conf, with rollback snapshot."""
    _snapshot_conf(CONF_PATH)
    CONF_PATH.write_text(json.dumps(genome, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Yield sensor
# ---------------------------------------------------------------------------

YIELD_DIRS = [
    pulse_reports,
    Path.home() / "tmp",  # pulse-manifest, briefs
]


def measure_yield(since_hours: float = 24) -> dict:
    """Measure metabolic yield — did recent pulse outputs persist?

    Counts files in pulse output dirs created since cutoff.
    Also checks git for pulse commits that survived (not reverted).
    Returns {files_created, git_commits, yield_summary}.
    """
    cutoff = datetime.datetime.now().timestamp() - since_hours * 3600
    files_created = 0

    for d in YIELD_DIRS:
        if not d.exists():
            continue
        for f in d.iterdir():
            if not f.is_file():
                continue
            try:
                if f.stat().st_ctime >= cutoff and "pulse" in f.name.lower():
                    files_created += 1
            except OSError:
                continue

    # Count git commits by pulse in tracked repos
    git_commits = 0
    since_iso = datetime.datetime.fromtimestamp(cutoff).isoformat()
    for repo in [Path.home() / "germline", Path.home() / "epigenome"]:
        if not (repo / ".git").exists():
            continue
        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "log",
                    f"--since={since_iso}",
                    "--author=Claude",
                    "--oneline",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            git_commits += len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
        except Exception:
            pass

    return {
        "files_created": files_created,
        "git_commits": git_commits,
        "yield_summary": f"{files_created} files, {git_commits} commits",
    }


# ---------------------------------------------------------------------------
# LLM adaptation — post-cycle parameter tuning
# ---------------------------------------------------------------------------

ADAPT_PROMPT = """You are the organism's respiratory tuner. Review the current state and adjust parameters.

## Current conf
{conf_json}

## Budget state
Weekly: {weekly}%, Sonnet: {sonnet}%, Hours to reset: {hours_to_reset:.0f}h

## Systole outcomes this cycle
Systoles run: {systoles_run}, Saturated: {saturated}, Failed: {failed}
Stop reason: {stop_reason}

## Yield (last 24h)
{yield_summary}

## Recent events (last 10)
{recent_events}

## Rules
- Output ONLY a JSON object with keys you want to change. Omit unchanged keys.
- Adjustable keys (haiku): stroma_pct, tropism, default_cost_per_systole, saturation_penalty
- Adjustable keys (sonnet adds): systole_model, saturation_patience, basal_rate, min_basal_rate, tachycardia_threshold
- Adjustable keys (opus adds): aerobic_ceiling, sonnet_ceiling, sympathetic_reserve, max_daily_systoles, bounds
- Bounds: stroma_pct [0,50], basal_rate [0.05,0.5], min_basal_rate [0.05,0.4], saturation_patience [1,5], systole_model [haiku,sonnet,opus], tachycardia_threshold [40,80], aerobic_ceiling [60,95], sonnet_ceiling [70,98], sympathetic_reserve [5,30], max_daily_systoles [5,30], default_cost_per_systole [0.1,5.0], saturation_penalty [1.0,3.0]
- tropism: null (balanced) or a specific north star name to prioritize
- Think about: Is budget being wasted? Is the organism producing useful output? Should it shift focus?
- If things look fine, output {{}}
- CRYSTALLIZATION: If you notice a pattern in the recent events (e.g. "budget always wastes >15% near reset", "stroma_pct gets lowered every cycle"), add a "crystallize" key with a one-line description of the formula that should replace this recurring judgment. Example: {{"stroma_pct": 15, "crystallize": "lower stroma_pct when yield >20 files/day"}}
"""


_REVIEW_STATE_FILE = Path.home() / "tmp" / ".respiration-review-state.json"

SONNET_SUFFIX = """

## Sonnet-tier review (daily)
You are the daily structural reviewer, independent of haiku's per-cycle adjustments.
Review from raw data — do NOT assume haiku's recent adjustments were correct.
In addition to parameter adjustments:
1. Review the crystallization log below for patterns worth codifying as formulas
2. Look for structural issues: wrong ramp curves, missing sensors, misaligned thresholds
3. Check the adaptation history — is haiku making good or bad adjustments?
4. Add "structural" key with observations (list of strings) if you see anything

## Adaptation history (haiku's recent adjustments)
{adapt_history}

## Crystallization log
{crystal_log}

## All organism conf files (review any that need adjustment)
{organism_confs}
"""

OPUS_SUFFIX = """

## Opus-tier review (weekly)
You are the weekly architectural reviewer. You see what haiku and sonnet cannot.
Review from raw data — do NOT assume lower tiers' adjustments were correct.
Your job is deeper:
1. Are the FORMULAS themselves right? (e.g., is oxygen_debt's 36h→6h ramp the right curve?)
2. Are there missing sensors? (what should the organism measure that it doesn't?)
3. Are the bounds in the conf appropriate?
4. Review the full crystallization log — which candidates should become deterministic rules?
5. **Naming audit**: scan effector names, conf names, module names for non-cell-biology violations. ALL names must be cell biology. Latin, English, or acronyms that aren't cell bio = violation. Flag in "structural".
6. **Stale reference audit**: check for broken symlinks, paths referencing old names, dead imports.
7. Add "architectural" key with recommendations (list of strings) for code changes
8. Add "crystallize" for any pattern you'd promote to a formula
9. Add "structural" for naming violations, stale references, and anything sonnet-level

## Adaptation history (all tiers)
{adapt_history}

## Crystallization log (full)
{crystal_log}

## Sonnet structural observations (if any)
{sonnet_observations}

## All organism conf files (review any, adjust any)
{organism_confs}

Output format: for vasomotor.conf adjustments, use the normal JSON format.
For OTHER conf files, add an "organism_confs" key with a dict of {{filename: {{key: value}}}} changes.
Example: {{"infra_pct": 20, "organism_confs": {{"endocytosis.conf": {{"weekly_transcytose_threshold": "5"}}, "synapse.conf": {{"mit_threshold": "4"}}}}}}
"""


def _load_review_state() -> dict:
    """Load review state — tracks when each tier last ran."""
    try:
        return json.loads(_REVIEW_STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_review_state(state: dict):
    _REVIEW_STATE_FILE.write_text(json.dumps(state))


def _detect_ligand() -> str | None:
    """Detect signal ligands that trigger higher-tier review regardless of schedule.

    Returns tier name if a ligand is detected, None for clock-only.
    """
    try:
        lines = EVENT_LOG.read_text().strip().splitlines()[-50:]
    except Exception:
        return None

    recent = list(lines)
    circuit_breakers = sum(1 for line in recent if '"circuit_breaker"' in line)
    saturations = sum(1 for line in recent if '"saturation_idle"' in line)
    rejections = sum(1 for line in recent if '"adapt_rejected"' in line)

    # Opus ligand: circuit breaker or repeated rejections (haiku trying to touch what it can't)
    if circuit_breakers >= 1 or rejections >= 3:
        return "opus"
    # Sonnet ligand: repeated saturation (something structural is wrong)
    if saturations >= 2:
        return "sonnet"
    return None


def _select_review_tier() -> str:
    """Select review tier: ligand-triggered (signal) OR clock-triggered (schedule).

    Ligand binding overrides the clock — specific signals escalate to higher tiers.
    Clock: haiku every cycle, sonnet daily, opus weekly.
    """
    # Ligand binding: specific signals trigger higher tiers
    ligand = _detect_ligand()
    if ligand:
        record_event("ligand_detected", tier=ligand)
        return ligand

    # Clock-triggered fallback
    state = _load_review_state()
    now = datetime.datetime.now()

    opus_last = state.get("opus_last", "")
    sonnet_last = state.get("sonnet_last", "")

    try:
        if (
            not opus_last
            or (now - datetime.datetime.fromisoformat(opus_last)).total_seconds() > 604800
        ):
            return "opus"
    except ValueError:
        return "opus"

    try:
        if (
            not sonnet_last
            or (now - datetime.datetime.fromisoformat(sonnet_last)).total_seconds() > 86400
        ):
            return "sonnet"
    except ValueError:
        return "sonnet"

    return "haiku"


def _mark_review(tier: str):
    state = _load_review_state()
    state[f"{tier}_last"] = datetime.datetime.now().isoformat()
    _save_review_state(state)


def _gather_adapt_context(
    systoles_run: int, saturated: int, failed: int, stop_reason: str
) -> dict:
    """Gather raw data for all review tiers — each tier sees the same ground truth."""
    genome = vasomotor_genome()
    telemetry = _fetch_telemetry()
    hours = _hours_to_reset(telemetry)

    recent_lines = ""
    try:
        lines = EVENT_LOG.read_text().strip().splitlines()[-10:]
        recent_lines = "\n".join(lines)
    except Exception:
        recent_lines = "(no events)"

    # Adaptation history: what have previous adapt calls done?
    adapt_history = ""
    try:
        all_lines = EVENT_LOG.read_text().strip().splitlines()
        adapt_events = [
            line for line in all_lines[-200:] if '"adapt_applied"' in line or '"adapt_noop"' in line
        ]
        adapt_history = "\n".join(adapt_events[-20:]) or "(no history)"
    except Exception:
        adapt_history = "(no history)"

    crystal_log = "(empty)"
    crystal_file = METHYLATION_FILE
    with contextlib.suppress(FileNotFoundError):
        crystal_log = crystal_file.read_text().strip() or "(empty)"

    # Sonnet structural observations
    sonnet_obs = ""
    try:
        all_lines = EVENT_LOG.read_text().strip().splitlines()
        structural = [line for line in all_lines[-500:] if '"structural_observation"' in line]
        sonnet_obs = "\n".join(structural[-10:]) or "(none)"
    except Exception:
        sonnet_obs = "(none)"

    # Organism-wide conf scan (for sonnet/opus tiers)
    org_confs = ""
    try:
        conf_files = sorted(VIVESCA_ROOT.rglob("*.conf"))
        sections = []
        for cf in conf_files:
            if ".venv" in str(cf) or "__pycache__" in str(cf):
                continue
            content = cf.read_text().strip()
            if content:
                rel = cf.relative_to(VIVESCA_ROOT)
                sections.append(f"### {rel}\n```\n{content[:500]}\n```")
        org_confs = "\n\n".join(sections) or "(no conf files)"
    except Exception:
        org_confs = "(scan failed)"

    return {
        "genome": genome,
        "telemetry": telemetry,
        "hours": hours,
        "weekly": telemetry.get("seven_day", {}).get("utilization", 0) if telemetry else 0,
        "sonnet_util": telemetry.get("seven_day_sonnet", {}).get("utilization", 0)
        if telemetry
        else 0,
        "yield_data": measure_yield(),
        "recent_events": recent_lines,
        "adapt_history": adapt_history,
        "crystal_log": crystal_log,
        "sonnet_observations": sonnet_obs,
        "organism_confs": org_confs,
        "systoles_run": systoles_run,
        "saturated": saturated,
        "failed": failed,
        "stop_reason": stop_reason,
    }


def adapt(systoles_run: int, saturated: int, failed: int, stop_reason: str):
    """Post-cycle LLM review — three independent tiers.

    haiku (every cycle): parameter tuning from raw state.
    sonnet (daily): structural review + crystallization + haiku audit.
    opus (weekly): architectural review + formula assessment + bounds check.

    Each tier reviews raw data independently — not the tier below's output.
    """
    ctx = _gather_adapt_context(systoles_run, saturated, failed, stop_reason)
    genome = ctx["genome"]

    # Base prompt — same raw data for all tiers
    prompt = ADAPT_PROMPT.format(
        conf_json=json.dumps(
            {k: v for k, v in genome.items() if not k.startswith("_") and k != "bounds"}, indent=2
        ),
        weekly=ctx["weekly"],
        sonnet=ctx["sonnet_util"],
        hours_to_reset=ctx["hours"] or 0,
        systoles_run=ctx["systoles_run"],
        saturated=saturated,
        failed=failed,
        stop_reason=stop_reason,
        yield_summary=ctx["yield_data"]["yield_summary"],
        recent_events=ctx["recent_events"],
    )

    # Select tier and add tier-specific context
    tier = _select_review_tier()
    if tier == "opus":
        prompt += OPUS_SUFFIX.format(
            adapt_history=ctx["adapt_history"],
            crystal_log=ctx["crystal_log"][-4000:],
            sonnet_observations=ctx["sonnet_observations"],
            organism_confs=ctx["organism_confs"],
        )
    elif tier == "sonnet":
        prompt += SONNET_SUFFIX.format(
            adapt_history=ctx["adapt_history"],
            crystal_log=ctx["crystal_log"][-2000:],
            organism_confs=ctx["organism_confs"],
        )

    # Route through conf-driven command — different models per tier
    review_tiers = genome.get("review_tiers", {})
    tier_conf = review_tiers.get(tier, {})
    cmd_template = tier_conf.get("cmd", ["channel", tier, "-p"])
    timeout = tier_conf.get("timeout", 60)

    record_event("adapt_start", tier=tier, cmd=cmd_template[0])

    try:
        import shutil

        # Resolve first element to full path
        binary = shutil.which(cmd_template[0])
        if not binary:
            log(f"adapt: {cmd_template[0]} not found")
            return
        cmd = [binary, *cmd_template[1:], prompt]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            log(f"adapt: {tier} ({cmd_template[0]}) failed: {result.stderr.strip()[:100]}")
            return

        # Parse JSON from response (may be wrapped in markdown)
        text = result.stdout.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        adjustments = json.loads(text)
        if not adjustments:
            record_event("adapt_noop")
            return

        # Crystallization: LLM spotted a recurring pattern worth codifying
        crystal = adjustments.pop("crystallize", None)
        structural = adjustments.pop("structural", None)
        crystal_file = METHYLATION_FILE

        if crystal:
            record_event("crystallize_candidate", rule=crystal)
            log(f"adapt: CRYSTALLIZE → {crystal}")
            entry = {
                "ts": datetime.datetime.now().isoformat(),
                "type": "crystallize",
                "candidate": crystal,
            }
            with open(crystal_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        if structural:
            record_event("structural_observation", observations=structural)
            log(f"adapt: STRUCTURAL → {structural}")
            entry = {
                "ts": datetime.datetime.now().isoformat(),
                "type": "structural",
                "observations": structural,
            }
            with open(crystal_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        # Architectural observations (opus-tier)
        architectural = adjustments.pop("architectural", None)
        if architectural:
            record_event("architectural_observation", observations=architectural)
            log(f"adapt: ARCHITECTURAL → {architectural}")
            entry = {
                "ts": datetime.datetime.now().isoformat(),
                "type": "architectural",
                "observations": architectural,
                "tier": tier,
            }
            with open(crystal_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        _mark_review(tier)

        # Apply bounded adjustments with authority check
        bounds = genome.get("bounds", {})
        authority = genome.get("tier_authority", {}).get(tier, [])
        applied = {}
        rejected = {}
        for key, new_val in adjustments.items():
            if key.startswith("_") or key == "bounds":
                continue
            if authority and key not in authority:
                rejected[key] = new_val
                continue
            if key in bounds:
                b = bounds[key]
                if isinstance(b, list) and isinstance(b[0], (int, float)):
                    new_val = max(b[0], min(b[1], new_val))
                elif isinstance(b, list) and isinstance(b[0], str) and new_val not in b:
                    continue
            old_val = genome.get(key)
            if old_val != new_val:
                genome[key] = new_val
                applied[key] = {"from": old_val, "to": new_val}

        if rejected:
            record_event("adapt_rejected", tier=tier, keys=rejected)
            log(f"adapt: {tier} rejected (no authority): {list(rejected.keys())}")

        if applied:
            _write_genome(genome)
            record_event("adapt_applied", tier=tier, adjustments=applied)
            log(f"adapt: {applied}")
        else:
            record_event("adapt_noop", proposed=adjustments)

        # Apply organism-wide conf adjustments (sonnet/opus only)
        org_adjustments = adjustments.get("organism_confs", {})
        if org_adjustments and isinstance(org_adjustments, dict):
            import configparser

            for conf_name, changes in org_adjustments.items():
                if not isinstance(changes, dict):
                    continue
                # Find the conf file in the organism
                matches = list(VIVESCA_ROOT.rglob(conf_name))
                matches = [m for m in matches if ".venv" not in str(m)]
                if not matches:
                    log(f"adapt: conf {conf_name} not found")
                    continue
                conf_path = matches[0]
                cp = configparser.ConfigParser()
                try:
                    cp.read(conf_path)
                except configparser.Error:
                    log(f"adapt: {conf_name} is not standard INI, skipping")
                    continue
                org_applied = {}
                for key, val in changes.items():
                    # Find which section contains this key
                    for section in cp.sections():
                        if key in cp[section]:
                            old = cp[section][key]
                            cp[section][key] = str(val)
                            org_applied[key] = {"from": old, "to": str(val)}
                            break
                if org_applied:
                    _snapshot_conf(conf_path)
                    tmp = conf_path.with_suffix(".conf.tmp")
                    with open(tmp, "w") as f:
                        cp.write(f)
                    tmp.replace(conf_path)
                    record_event("adapt_organism_conf", conf=conf_name, adjustments=org_applied)
                    log(f"adapt: {conf_name} → {org_applied}")

    except (json.JSONDecodeError, ValueError) as e:
        log(f"adapt: parse error: {e}")
        record_event("adapt_error", error=str(e))
    except Exception as e:
        log(f"adapt: {e}")
        record_event("adapt_error", error=str(e))
