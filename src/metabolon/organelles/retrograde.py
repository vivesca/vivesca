from __future__ import annotations

"""retrograde — symbiont influence tracking.

Retrograde signaling: mitochondria (symbiont) send signals BACK to the
nucleus (organism) that change gene expression. Measures the balance of
influence between organism and symbiont.

  Anterograde (organism → symbiont): organism directing the LLM
    - channel calls, agent dispatches, pulse systoles

  Retrograde (symbiont → organism): LLM changing the organism
    - git commits authored by Claude/agents
    - memory (histone) writes
    - methylation proposals accepted
    - mismatch repair corrections

  signal_balance(days) → ratio + assessment:
    > 3:1 anterograde = "sovereign"
    1:1 - 3:1 = "balanced"
    < 1:1 = "dependent"
"""


import datetime
import json
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SIGNALS_LOG = Path.home() / ".cache" / "retrograde" / "signals.jsonl"
EVENT_LOG = Path.home() / "logs" / "vivesca-events.jsonl"
METHYLATION_CANDIDATES = Path.home() / ".cache" / "inflammasome" / "methylation-candidates.jsonl"
INFECTIONS_LOG = Path.home() / ".local" / "share" / "vivesca" / "infections.jsonl"
METHYLATION_JSONL = Path.home() / "germline" / "methylation.jsonl"

TRACKED_REPOS = [
    Path.home() / "germline",
    Path.home() / "epigenome",
]


# ---------------------------------------------------------------------------
# Core signal logging
# ---------------------------------------------------------------------------


def log_signal(direction: str, signal_type: str, detail: str = "") -> None:
    """Append one signal to ~/.cache/retrograde/signals.jsonl."""
    SIGNALS_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.datetime.now(datetime.UTC).isoformat(),
        "direction": direction,
        "type": signal_type,
        "detail": detail,
    }
    with SIGNALS_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Measurement helpers
# ---------------------------------------------------------------------------


def _cutoff_iso(days: int) -> str:
    dt = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    return dt.isoformat()


def _count_anterograde(days: int) -> int:
    """Count organism→symbiont signals: pulse systoles + channel calls logged in event log."""
    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    count = 0
    for path in [EVENT_LOG]:
        if not path.exists():
            continue
        try:
            for line in path.read_text().splitlines():
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError, ValueError:
                    continue
                ts_str = entry.get("ts", "")
                # parse ts — may or may not have timezone
                try:
                    ts = datetime.datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=datetime.UTC)
                except ValueError:
                    continue
                if ts < cutoff:
                    continue
                event = entry.get("event", "")
                cmd = entry.get("cmd", "")
                # systole starts + explicit channel dispatches
                if event in ("systole_start", "run_start", "adapt_start") or cmd == "channel":
                    count += 1
        except Exception:
            pass
    # Also include manually logged signals
    count += _count_logged(days, "anterograde")
    return count


def _count_retrograde(days: int) -> int:
    """Count symbiont→organism signals: agent git commits + memory writes + methylations."""
    count = 0
    cutoff_iso = _cutoff_iso(days)

    # 1. Git commits by Claude/agents
    for repo in TRACKED_REPOS:
        if not (repo / ".git").exists():
            continue
        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "log",
                    f"--since={cutoff_iso}",
                    "--author=Claude",
                    "--oneline",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            count += len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
        except Exception:
            pass

    # 2. Methylation proposals (candidates accepted + committed methylation.jsonl entries)
    cutoff_dt = datetime.datetime.fromisoformat(cutoff_iso)
    for path in [METHYLATION_CANDIDATES, METHYLATION_JSONL]:
        if not path.exists():
            continue
        try:
            for line in path.read_text().splitlines():
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError, ValueError:
                    continue
                ts_str = entry.get("ts", "")
                try:
                    ts = datetime.datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=datetime.UTC)
                    if cutoff_dt.tzinfo is None:
                        _cutoff = cutoff_dt.replace(tzinfo=datetime.UTC)
                    else:
                        _cutoff = cutoff_dt
                    if ts >= _cutoff:
                        count += 1
                except ValueError:
                    pass
        except Exception:
            pass

    # 3. Mismatch repair corrections (real tool infections healed by the organism).
    # Exclude inflammasome test fixtures (fail_tool, failing_tool, unknown_tool, "tool")
    # which are synthetic probe artefacts, not real corrections.
    _TEST_FIXTURES = {"fail_tool", "failing_tool", "unknown_tool", "tool"}
    if INFECTIONS_LOG.exists():
        try:
            for line in INFECTIONS_LOG.read_text().splitlines():
                entry = json.loads(line)
                if entry.get("tool", "") in _TEST_FIXTURES:
                    continue
                ts_str = entry.get("ts", "")
                try:
                    ts = datetime.datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=datetime.UTC)
                    if cutoff_dt.tzinfo is None:
                        _cutoff = cutoff_dt.replace(tzinfo=datetime.UTC)
                    else:
                        _cutoff = cutoff_dt
                    if ts >= _cutoff and entry.get("healed"):
                        count += 1
                except ValueError:
                    pass
        except Exception:
            pass

    # 4. Manually logged retrograde signals
    count += _count_logged(days, "retrograde")
    return count


def _count_logged(days: int, direction: str) -> int:
    """Count entries in signals.jsonl matching direction within window."""
    if not SIGNALS_LOG.exists():
        return 0
    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    count = 0
    try:
        for line in SIGNALS_LOG.read_text().splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError, ValueError:
                continue
            if entry.get("direction") != direction:
                continue
            try:
                ts = datetime.datetime.fromisoformat(entry["ts"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=datetime.UTC)
                if ts >= cutoff:
                    count += 1
            except ValueError, KeyError:
                pass
    except Exception:
        pass
    return count


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def signal_balance(days: int = 7) -> dict:
    """Compute anterograde/retrograde ratio over last N days.

    Returns:
        anterograde_count, retrograde_count, ratio, assessment
        assessment: "sovereign" | "balanced" | "dependent"
    """
    ante = _count_anterograde(days)
    retro = _count_retrograde(days)

    ratio = (float(ante) if ante > 0 else 1.0) if retro == 0 else ante / retro

    if ratio >= 3.0:
        assessment = "sovereign"
    elif ratio >= 1.0:
        assessment = "balanced"
    else:
        assessment = "dependent"

    return {
        "anterograde_count": ante,
        "retrograde_count": retro,
        "ratio": round(ratio, 2),
        "assessment": assessment,
        "window_days": days,
    }
