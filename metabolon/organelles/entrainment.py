"""entrainment — circadian zeitgeber sensing and schedule advisory."""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any

HKT = datetime.timezone(datetime.timedelta(hours=8))
_SKIP_FILE = Path.home() / "tmp" / ".entrainment-suppress"
_LOG = Path.home() / "logs" / "vivesca-events.jsonl"
logger = logging.getLogger(__name__)


def zeitgebers() -> dict[str, Any]:
    """Read external synchronisation signals. Never raises."""
    now = datetime.datetime.now(tz=HKT)
    hour = now.hour
    is_night = hour >= 23 or hour < 6

    readiness: int | None = None
    try:
        from metabolon.organelles.chemoreceptor import sense as _s

        d = _s()
        if "error" not in d:
            readiness = d.get("readiness_score")
    except Exception as e:
        logger.debug("Oura unavailable: %s", e)

    budget = "unknown"
    try:
        from metabolon.vasomotor import vasomotor_status

        budget = vasomotor_status()
    except Exception as e:
        logger.debug("Budget unavailable: %s", e)

    rss_stale: bool | None = None
    try:
        from metabolon.organelles.endocytosis_rss.config import restore_config
        from metabolon.organelles.endocytosis_rss.state import restore_state

        cfg = restore_config()
        state = restore_state(cfg.state_path) or {}
        utc = datetime.UTC
        dts = []
        for v in state.values():
            if isinstance(v, str):
                try:
                    dt = datetime.datetime.fromisoformat(v)
                    dts.append(dt if dt.tzinfo else dt.replace(tzinfo=utc))
                except ValueError:
                    pass
        if dts:
            rss_stale = (datetime.datetime.now(tz=utc) - max(dts)).total_seconds() / 3600 > 4
    except Exception as e:
        logger.debug("RSS state unavailable: %s", e)

    return {
        "hkt_hour": hour,
        "weekday": now.strftime("%A"),
        "is_night": is_night,
        "asleep": is_night,
        "readiness": readiness,
        "budget_status": budget,
        "rss_stale": rss_stale,
    }


def optimal_schedule(signals: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return advisory {agent: {action, reason}} for each LaunchAgent."""
    if signals is None:
        signals = zeitgebers()
    night = signals.get("is_night", False)
    budget = signals.get("budget_status", "unknown")
    stale = signals.get("rss_stale")
    hour = signals.get("hkt_hour", 12)
    weekend = signals.get("weekday", "Mon") in ("Saturday", "Sunday")

    recs: dict[str, dict[str, str]] = {}
    notes: list[str] = []

    if budget == "red":
        recs["pulse"] = {"action": "suppress", "reason": "budget_red"}
        notes.append("pulse: budget exhausted")
    elif night:
        recs["pulse"] = {"action": "suppress", "reason": "night_hours"}
        notes.append("pulse: night suppressed")
    elif budget == "green" and 9 <= hour < 19 and not weekend:
        recs["pulse"] = {"action": "accelerate", "reason": "green_daytime"}
        notes.append("pulse: accelerate green+daytime")
    else:
        recs["pulse"] = {"action": "normal", "reason": "nominal"}

    if stale is True:
        recs["endocytosis"] = {"action": "trigger", "reason": "rss_stale_gt_4h"}
        notes.append("endocytosis: RSS stale, trigger now")
    elif night:
        recs["endocytosis"] = {"action": "suppress", "reason": "night_hours"}
        notes.append("endocytosis: night suppressed")
    else:
        recs["endocytosis"] = {"action": "normal", "reason": "nominal"}

    recs["transduction"] = {
        "action": "suppress" if night else "normal",
        "reason": "night_hours" if night else "nominal",
    }
    notes.append("transduction: night suppressed") if night else None
    return {"recommendations": recs, "summary": "; ".join(notes) or "all agents nominal"}


def entrain(dry_run: bool = True) -> dict[str, Any]:
    """Write circadian suppress markers and log entrainment decisions.

    When dry_run=False and pulse is suppressed, writes to the vasomotor
    SKIP_UNTIL_FILE so is_apneic() actually gates the next pulse invocation.
    """
    signals = zeitgebers()
    sched = optimal_schedule(signals)
    recs = sched["recommendations"]
    suppress = [lbl for lbl, r in recs.items() if r["action"] == "suppress"]
    trigger = [lbl for lbl, r in recs.items() if r["action"] == "trigger"]
    taken, deferred = [], []

    if suppress:
        payload = {
            "ts": datetime.datetime.now(tz=HKT).isoformat(),
            "suppress": suppress,
            "reasons": {lbl: recs[lbl]["reason"] for lbl in suppress},
        }
        if dry_run:
            deferred.append(f"WOULD suppress {suppress}")
        else:
            # Write advisory marker (entrainment-specific)
            _SKIP_FILE.parent.mkdir(parents=True, exist_ok=True)
            _SKIP_FILE.write_text(json.dumps(payload))
            taken.append(f"suppress marker written: {suppress}")
            # Wire pulse suppression into the vasomotor skip-until mechanism
            if "pulse" in suppress:
                try:
                    from metabolon.vasomotor import SKIP_UNTIL_FILE

                    pulse_reason = recs["pulse"].get("reason", "")
                    now = datetime.datetime.now(tz=HKT)
                    if pulse_reason == "night_hours":
                        wake = now.replace(hour=6, minute=0, second=0, microsecond=0)
                        if wake <= now:
                            wake += datetime.timedelta(days=1)
                    else:
                        wake = now + datetime.timedelta(hours=1)
                    SKIP_UNTIL_FILE.parent.mkdir(parents=True, exist_ok=True)
                    SKIP_UNTIL_FILE.write_text(wake.isoformat())
                    taken.append(f"vasomotor skip-until set: {wake.isoformat()}")
                except Exception as e:
                    logger.warning("Could not write vasomotor skip-until: %s", e)
    if trigger:
        (deferred if dry_run else taken).append(
            f"{'WOULD trigger' if dry_run else 'trigger'}: {trigger}"
        )

    try:
        with open(_LOG, "a") as fh:
            fh.write(
                json.dumps(
                    {
                        "ts": datetime.datetime.now(tz=HKT).isoformat(),
                        "event": "entrainment",
                        "dry_run": dry_run,
                        "summary": sched["summary"],
                        "suppress": suppress,
                        "trigger": trigger,
                    }
                )
                + "\n"
            )
    except Exception:
        pass

    return {
        "dry_run": dry_run,
        "signals": signals,
        "schedule": sched,
        "actions_taken": taken,
        "actions_deferred": deferred,
    }
