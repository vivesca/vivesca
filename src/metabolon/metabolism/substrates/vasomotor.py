"""VasomotorSubstrate — metabolism of autonomous pacing/budgeting.

Senses the vivesca-events JSONL log to assess respiration pacing health:
daily burn vs budget, saturation rates, cost volatility, and process
liveness. Proposes tuning actions when pacing drifts.
"""

import contextlib
import json
import statistics
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from metabolon.cytosol import VIVESCA_ROOT


def _parse_ts(ts_str: str) -> datetime:
    """Parse an ISO timestamp, with or without timezone info."""
    # Try the standard format first (no tz), then with tz
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts_str, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    # Fallback: fromisoformat handles timezone-aware strings
    return datetime.fromisoformat(ts_str)


class VasomotorSubstrate:
    """Substrate for respiration pacing system health."""

    name: str = "respiration"

    def __init__(
        self,
        events_path: Path | None = None,
        state_path: Path | None = None,
        config_path: Path | None = None,
        pulse_dir: Path | None = None,
    ):
        self.events_path = events_path or (Path.home() / "logs" / "vivesca-events.jsonl")
        self.state_path = state_path or (Path.home() / "tmp" / "respiration-daily.json")
        self.config_path = config_path or (VIVESCA_ROOT / "vasomotor.conf")
        self.pulse_dir = pulse_dir or (Path.home() / "docs" / "pulse")

    def sense(self, days: int = 30) -> list[dict]:
        """Read vivesca-events.jsonl for the last N days, summarise daily pacing."""
        if not self.events_path.exists():
            return []

        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Accumulate events by date
        daily: dict[str, dict] = defaultdict(
            lambda: {
                "date": "",
                "events": [],
                "systole_count": 0,
                "saturated_count": 0,
                "pacing_checks": [],
                "cost_samples": [],
                "systole_costs": [],
                "systole_yields": [],
                "failed_systoles": 0,
                "successful_systoles": 0,
                "systole_durations": [],
                "budget_samples": [],
                "circuit_breakers": 0,
            }
        )

        try:
            text = self.events_path.read_text()
        except OSError:
            return []

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts_str = event.get("ts", "")
            if not ts_str:
                continue

            try:
                ts = _parse_ts(ts_str)
            except ValueError, TypeError:
                continue

            if ts < cutoff:
                continue

            date_key = ts.strftime("%Y-%m-%d")
            day = daily[date_key]
            day["date"] = date_key
            day["events"].append(event)

            evt_type = event.get("event", "")

            if evt_type == "systole_start":
                day["systole_count"] += 1

            elif evt_type == "saturation_detected":
                day["saturated_count"] += 1

            elif evt_type == "pacing_check":
                day["pacing_checks"].append(event)

            elif evt_type == "cost_measured":
                cost = event.get("cost")
                if cost is not None:
                    day["cost_samples"].append(float(cost))

            elif evt_type == "systole_usage":
                delta = event.get("weekly_delta")
                if delta is not None:
                    day["systole_costs"].append(float(delta))

            elif evt_type == "systole_yield":
                day["systole_yields"].append(event.get("secretion_count", 0))

            elif evt_type == "systole_end":
                if event.get("exit_code") == 0:
                    day["successful_systoles"] += 1
                else:
                    day["failed_systoles"] += 1
                elapsed = event.get("elapsed_s")
                if elapsed:
                    day["systole_durations"].append(float(elapsed))

            elif evt_type == "budget_raw":
                weekly = event.get("weekly")
                if weekly is not None:
                    day["budget_samples"].append({"ts": ts_str, "weekly": float(weekly)})

            elif evt_type == "circuit_breaker":
                day["circuit_breakers"] += 1

        # Build daily summaries
        result: list[dict] = []
        for date_key in sorted(daily.keys()):
            day = daily[date_key]
            events = day["events"]
            timestamps = []
            for e in events:
                ts_str = e.get("ts", "")
                if ts_str:
                    with contextlib.suppress(ValueError, TypeError):
                        timestamps.append(_parse_ts(ts_str))

            # Compute max gap between consecutive events
            apnea_window = 0.0
            if len(timestamps) >= 2:
                timestamps.sort()
                for i in range(1, len(timestamps)):
                    gap = (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600
                    if gap > apnea_window:
                        apnea_window = gap

            # Extract budget info from latest pacing_check
            daily_budget = None
            estimated_burn = None
            if day["pacing_checks"]:
                latest_pc = day["pacing_checks"][-1]
                daily_budget = latest_pc.get("daily_budget") or latest_pc.get(
                    "lucerna_daily_budget"
                )
                estimated_burn = latest_pc.get("estimated_burn")
                # Fall back: systoles_today as burn proxy
                if estimated_burn is None:
                    estimated_burn = latest_pc.get("systoles_today") or latest_pc.get(
                        "waves_today"
                    )

            # Compute avg systole duration
            avg_duration = (
                statistics.mean(day["systole_durations"]) if day["systole_durations"] else None
            )

            # Compute budget climb rate (% per hour)
            budget_climb_rate = None
            samples = day["budget_samples"]
            if len(samples) >= 2:
                first, last = samples[0], samples[-1]
                try:
                    t0 = _parse_ts(first["ts"])
                    t1 = _parse_ts(last["ts"])
                    hours = (t1 - t0).total_seconds() / 3600
                    if hours > 0:
                        budget_climb_rate = (last["weekly"] - first["weekly"]) / hours
                except ValueError, TypeError:
                    pass

            total_yield = sum(day["systole_yields"])
            total_cost = sum(day["systole_costs"])
            rq = round(total_yield / total_cost, 2) if total_cost > 0 else None

            result.append(
                {
                    "date": date_key,
                    "systole_count": day["systole_count"],
                    "saturated_count": day["saturated_count"],
                    "daily_budget": daily_budget,
                    "estimated_burn": estimated_burn,
                    "cost_samples": day["cost_samples"],
                    "systole_costs": day["systole_costs"],
                    "systole_yields": day["systole_yields"],
                    "rq": rq,
                    "apnea_window": apnea_window,
                    "event_count": len(events),
                    "failed_systoles": day["failed_systoles"],
                    "successful_systoles": day["successful_systoles"],
                    "avg_systole_duration": avg_duration,
                    "budget_climb_rate": budget_climb_rate,
                    "circuit_breakers": day["circuit_breakers"],
                }
            )

        return result

    def candidates(self, sensed: list[dict]) -> list[dict]:
        """Identify pacing issues from sensed daily summaries."""
        if not sensed:
            return []

        dysregulations: list[dict] = []

        # Per-day checks
        overburn_days = []
        saturated_days = []
        starved_days = []
        silent_days = []

        for day in sensed:
            budget = day.get("daily_budget")
            burn = day.get("estimated_burn")

            # Overburn: daily burn > daily budget
            if budget is not None and burn is not None:
                if budget > 0 and burn > budget:
                    overburn_days.append(day)

                # Starvation: <50% of budget used
                if budget > 0 and burn < budget * 0.5:
                    starved_days.append(day)

            # Saturation: >30% systoles saturated
            systole_count = day.get("systole_count", 0)
            sat_count = day.get("saturated_count", 0)
            if systole_count > 0 and sat_count / systole_count > 0.3:
                saturated_days.append(day)

            # Silence: >4h gap between events
            if day.get("apnea_window", 0) > 4:
                silent_days.append(day)

        # Aggregate: only flag if pattern is consistent (>= 2 days or significant)
        if overburn_days:
            dysregulations.append(
                {
                    "issue": "overburn",
                    "severity": "high" if len(overburn_days) >= 3 else "medium",
                    "evidence": [
                        f"{d['date']}: burn={d['estimated_burn']}, budget={d['daily_budget']}"
                        for d in overburn_days
                    ],
                    "count": len(overburn_days),
                }
            )

        if saturated_days:
            dysregulations.append(
                {
                    "issue": "saturation",
                    "severity": "high" if len(saturated_days) >= 3 else "medium",
                    "evidence": [
                        f"{d['date']}: {d['saturated_count']}/{d['systole_count']} systoles saturated"
                        for d in saturated_days
                    ],
                    "count": len(saturated_days),
                }
            )

        if starved_days:
            dysregulations.append(
                {
                    "issue": "starvation",
                    "severity": "medium" if len(starved_days) >= 3 else "low",
                    "evidence": [
                        f"{d['date']}: burn={d['estimated_burn']}, budget={d['daily_budget']}"
                        for d in starved_days
                    ],
                    "count": len(starved_days),
                }
            )

        # Volatility: cost_per_systole stddev > mean across all days
        all_costs: list[float] = []
        for day in sensed:
            all_costs.extend(day.get("systole_costs", []))

        if len(all_costs) >= 3:
            mean_cost = statistics.mean(all_costs)
            stdev_cost = statistics.stdev(all_costs)
            if mean_cost > 0 and stdev_cost > mean_cost:
                dysregulations.append(
                    {
                        "issue": "volatility",
                        "severity": "medium",
                        "evidence": [
                            f"cost stddev={stdev_cost:.2f} > mean={mean_cost:.2f} "
                            f"across {len(all_costs)} systoles"
                        ],
                        "count": 1,
                    }
                )

        if silent_days:
            dysregulations.append(
                {
                    "issue": "silence",
                    "severity": "high" if len(silent_days) >= 3 else "low",
                    "evidence": [
                        f"{d['date']}: {d['apnea_window']:.1f}h gap" for d in silent_days
                    ],
                    "count": len(silent_days),
                }
            )

        # --- Checks absorbed from monitor ---

        # Failure ratio: more failures than successes in recent days
        recent = sensed[-7:]
        total_fails = sum(d.get("failed_systoles", 0) for d in recent)
        total_ok = sum(d.get("successful_systoles", 0) for d in recent)
        if total_fails >= 3 and total_fails > total_ok:
            dysregulations.append(
                {
                    "issue": "failure_ratio",
                    "severity": "high",
                    "evidence": [f"{total_fails} failed vs {total_ok} successful in last 7 days"],
                    "count": total_fails,
                }
            )

        # Circuit breaker: any fires in the window
        breaker_days = [d for d in sensed if d.get("circuit_breakers", 0) > 0]
        if breaker_days:
            total_breakers = sum(d["circuit_breakers"] for d in breaker_days)
            dysregulations.append(
                {
                    "issue": "circuit_breaker",
                    "severity": "high",
                    "evidence": [f"{d['date']}: {d['circuit_breakers']}x" for d in breaker_days],
                    "count": total_breakers,
                }
            )

        # Budget climb rate: any day with >5%/hr burn rate
        fast_burn_days = [
            d
            for d in sensed
            if d.get("budget_climb_rate") is not None and d["budget_climb_rate"] > 5
        ]
        if fast_burn_days:
            dysregulations.append(
                {
                    "issue": "fast_burn",
                    "severity": "high" if len(fast_burn_days) >= 2 else "medium",
                    "evidence": [
                        f"{d['date']}: {d['budget_climb_rate']:.1f}%/hr" for d in fast_burn_days
                    ],
                    "count": len(fast_burn_days),
                }
            )

        # Systole duration anomaly: recent avg >2x the overall avg
        all_durations = [
            d["avg_systole_duration"] for d in sensed if d.get("avg_systole_duration") is not None
        ]
        if len(all_durations) >= 3 and recent:
            overall_avg = statistics.mean(all_durations)
            recent_durations = [
                d["avg_systole_duration"]
                for d in recent
                if d.get("avg_systole_duration") is not None
            ]
            if recent_durations and overall_avg > 0:
                recent_avg = statistics.mean(recent_durations)
                if recent_avg > overall_avg * 2:
                    dysregulations.append(
                        {
                            "issue": "slow_systoles",
                            "severity": "medium",
                            "evidence": [
                                f"recent avg {recent_avg:.0f}s vs overall {overall_avg:.0f}s"
                            ],
                            "count": 1,
                        }
                    )

        # Output absorption: is the organism producing faster than
        # the symbiont can digest? Count recent deliverables.
        if self.pulse_dir.exists():
            now_ts = datetime.now(UTC).timestamp()
            week_ago = now_ts - 7 * 86400
            daily_output: dict[str, int] = defaultdict(int)
            for f in self.pulse_dir.iterdir():
                if f.is_file():
                    mtime = f.stat().st_mtime
                    if mtime > week_ago:
                        day_key = datetime.fromtimestamp(mtime, UTC).strftime("%Y-%m-%d")
                        daily_output[day_key] += 1

            overproduction_days = [
                (day, count) for day, count in daily_output.items() if count > 20
            ]
            if len(overproduction_days) >= 2:
                dysregulations.append(
                    {
                        "issue": "overproduction",
                        "severity": "high" if len(overproduction_days) >= 3 else "medium",
                        "evidence": [
                            f"{day}: {count} files" for day, count in sorted(overproduction_days)
                        ],
                        "count": len(overproduction_days),
                    }
                )

        # --- Reafference: did prior actions produce the intended effect? ---
        conf = {}
        try:
            if self.config_path.exists():
                conf = json.loads(self.config_path.read_text())
        except json.JSONDecodeError, OSError:
            pass

        yield_history = conf.get("_efference_copy", [])
        if yield_history and sensed:
            current_issue_set = {c.get("issue") for c in dysregulations}
            for prior in yield_history:
                prior_issue = prior.get("issue")
                prior_ts = prior.get("ts", "")
                if prior_issue and prior_issue not in current_issue_set:
                    dysregulations.append(
                        {
                            "issue": "reafference_confirmed",
                            "severity": "info",
                            "evidence": [f"{prior_issue} resolved since {prior_ts[:10]}"],
                            "count": 1,
                        }
                    )
                elif prior_issue and prior_issue in current_issue_set:
                    dysregulations.append(
                        {
                            "issue": "reafference_mismatch",
                            "severity": "low",
                            "evidence": [
                                f"{prior_issue} persists despite action on {prior_ts[:10]}"
                            ],
                            "count": 1,
                        }
                    )

        return dysregulations

    def act(self, candidate: dict) -> str:
        """Apply autonomic tuning for a pacing issue.

        High-severity issues with deterministic fixes are applied directly
        to vasomotor.conf. Medium/low issues are reported but not applied.
        All adjustments are bounded to prevent runaway feedback.
        """
        issue = candidate.get("issue", "unknown")
        severity = candidate.get("severity", "unknown")
        count = candidate.get("count", 0)

        # Load current conf
        conf = {}
        try:
            if self.config_path.exists():
                conf = json.loads(self.config_path.read_text())
        except json.JSONDecodeError, OSError:
            pass

        applied = False

        if issue == "overburn" and severity == "high":
            # Reduce daily share by 10%, floor at 0.10
            current = conf.get("basal_rate", 0.5)
            new_val = round(max(0.10, current * 0.9), 2)
            conf["basal_rate"] = new_val
            applied = True
            action = f"APPLIED: basal_rate {current} → {new_val} ({count} day(s) over budget)"

        elif issue == "saturation" and severity == "high":
            # Increase saturation penalty, cap at 3.0
            current = conf.get("saturation_penalty", 1.5)
            new_val = round(min(3.0, current + 0.5), 1)
            conf["saturation_penalty"] = new_val
            applied = True
            action = f"APPLIED: saturation_penalty {current} → {new_val} ({count} day(s) >30% saturated)"

        elif issue == "starvation" and severity in ("medium", "high"):
            # Increase daily share by 10%, cap at 0.6
            current = conf.get("basal_rate", 0.5)
            new_val = round(min(0.6, current * 1.1), 2)
            conf["basal_rate"] = new_val
            applied = True
            action = f"APPLIED: basal_rate {current} → {new_val} ({count} day(s) under 50%)"

        elif issue == "overburn":
            action = f"reduce dynamic_share by 10% ({count} day(s) over budget)"
        elif issue == "saturation":
            action = f"increase saturation penalty ({count} day(s) with >30% saturated)"
        elif issue == "starvation":
            action = f"increase dynamic_share by 10% ({count} day(s) under 50% utilisation)"
        elif issue == "volatility":
            action = "systole cost variance exceeds mean — monitoring"
        elif issue == "silence":
            action = f"check launchctl status ({count} day(s) with >4h gap)"
        elif issue == "overproduction" and severity == "high":
            # Producing faster than symbiont can absorb — throttle
            current = conf.get("basal_rate", 0.5)
            new_val = round(max(0.10, current * 0.85), 2)
            conf["basal_rate"] = new_val
            applied = True
            action = f"APPLIED: basal_rate {current} → {new_val} (hyperventilating — {count} day(s) >20 files)"

        elif issue == "overproduction":
            action = f"producing >20 files/day on {count} day(s) — symbiont can't absorb"

        elif issue == "failure_ratio":
            action = f"{count} failed systoles — check logs"
        elif issue == "circuit_breaker":
            action = f"circuit breaker fired {count}x — check ~/logs/vivesca-events.jsonl"
        elif issue == "fast_burn":
            action = f"budget climbing >5%/hr on {count} day(s)"
        elif issue == "slow_systoles":
            action = "systole duration >2x baseline — possible stall pattern"
        elif issue == "reafference_confirmed":
            action = f"prior action worked — {candidate.get('evidence', [''])[0]}"
        elif issue == "reafference_mismatch":
            action = f"prior action ineffective — {candidate.get('evidence', [''])[0]}"
        else:
            action = f"review: {issue}"

        if applied:
            # Record what we did and when, so yield can be measured next cycle
            history = conf.get("_efference_copy", [])
            history.append(
                {
                    "ts": datetime.now(UTC).isoformat(),
                    "issue": issue,
                    "action": action,
                }
            )
            # Keep last 10 actions only
            conf["_efference_copy"] = history[-10:]
            try:
                self.config_path.write_text(json.dumps(conf, indent=2))
            except OSError:
                action = action.replace("APPLIED", "FAILED")

        return f"[{severity}] {action}"

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        """Format a human-readable pacing report."""
        lines: list[str] = []
        lines.append(f"Respiration substrate: {len(sensed)} day(s) sensed")
        lines.append("")

        if sensed:
            total_systoles = sum(d.get("systole_count", 0) for d in sensed)
            total_saturated = sum(d.get("saturated_count", 0) for d in sensed)
            budgeted_days = [d for d in sensed if d.get("daily_budget") is not None]

            all_yields = sum(sum(d.get("systole_yields", [])) for d in sensed)
            all_costs = sum(sum(d.get("systole_costs", [])) for d in sensed)
            overall_rq = round(all_yields / all_costs, 2) if all_costs > 0 else None

            lines.append("-- Overview --")
            lines.append(f"  Total systoles: {total_systoles}")
            lines.append(f"  Total saturated: {total_saturated}")
            if overall_rq is not None:
                lines.append(f"  RQ (files/%-point): {overall_rq}")
            if budgeted_days:
                avg_budget = statistics.mean(d["daily_budget"] for d in budgeted_days)
                avg_burn = statistics.mean(d.get("estimated_burn", 0) or 0 for d in budgeted_days)
                lines.append(f"  Avg daily budget: {avg_budget:.1f}")
                lines.append(f"  Avg daily burn: {avg_burn:.1f}")

            # Per-day detail (last 7 days only to keep report readable)
            recent = sensed[-7:]
            lines.append("")
            lines.append("-- Recent days --")
            for d in recent:
                budget_str = (
                    f"{d['daily_budget']:.1f}" if d.get("daily_budget") is not None else "N/A"
                )
                burn_str = (
                    f"{d['estimated_burn']}" if d.get("estimated_burn") is not None else "N/A"
                )
                rq_str = f"{d['rq']}" if d.get("rq") is not None else "N/A"
                lines.append(
                    f"  {d['date']}: systoles={d['systole_count']} "
                    f"saturated={d['saturated_count']} "
                    f"budget={budget_str} burn={burn_str} "
                    f"rq={rq_str} "
                    f"gap={d['apnea_window']:.1f}h"
                )

        if acted:
            lines.append("")
            lines.append("-- Issues --")
            for action in acted:
                lines.append(f"  {action}")

        if not acted and sensed:
            lines.append("")
            lines.append("No pacing issues detected.")

        lines.append("")
        lines.append(f"Summary: {len(acted)} issue(s) found.")

        return "\n".join(lines)
