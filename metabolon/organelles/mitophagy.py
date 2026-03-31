from __future__ import annotations

"""mitophagy — selective removal of underperforming LLM models.

Auto-blacklist threshold: <50% success over >=5 attempts in last 7 days.
Blacklist is advisory — always logged, never silently dropped.
"""


import json
import time
from pathlib import Path
from typing import Any

_CACHE_DIR = Path.home() / ".cache" / "mitophagy"
_OUTCOMES_PATH = _CACHE_DIR / "outcomes.jsonl"
_BLACKLIST_PATH = _CACHE_DIR / "blacklist.json"

TASK_TYPES = frozenset(
    {"probe", "repair", "research", "coding", "synthesis", "hybridization", "routing"}
)

_BLACKLIST_MIN_ATTEMPTS = 5
_BLACKLIST_MAX_RATE = 0.50
_FALLBACK_MODEL = "opus"


def _ensure_cache() -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _load_blacklist() -> dict[str, list[str]]:
    try:
        if _BLACKLIST_PATH.exists():
            return json.loads(_BLACKLIST_PATH.read_text())
    except Exception:
        pass
    return {}


def _save_blacklist(bl: dict[str, list[str]]) -> None:
    _ensure_cache()
    _BLACKLIST_PATH.write_text(json.dumps(bl, indent=2))


def _load_outcomes(since_ts: float = 0.0) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        if not _OUTCOMES_PATH.exists():
            return rows
        with _OUTCOMES_PATH.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    if row.get("ts", 0) >= since_ts:
                        rows.append(row)
                except Exception:
                    pass
    except Exception:
        pass
    return rows


def record_outcome(model: str, task_type: str, success: bool, duration_ms: int = 0) -> None:
    """Append one outcome. Auto-triggers blacklist check after write."""
    _ensure_cache()
    row = {
        "ts": time.time(),
        "model": model,
        "task_type": task_type,
        "success": success,
        "duration_ms": duration_ms,
    }
    with _OUTCOMES_PATH.open("a") as f:
        f.write(json.dumps(row) + "\n")
    # Auto-blacklist check
    since = time.time() - 7 * 86400
    relevant = [
        r
        for r in _load_outcomes(since_ts=since)
        if r.get("model") == model and r.get("task_type") == task_type
    ]
    if len(relevant) >= _BLACKLIST_MIN_ATTEMPTS:
        rate = sum(1 for r in relevant if r.get("success")) / len(relevant)
        if rate < _BLACKLIST_MAX_RATE and not is_blacklisted(model, task_type):
            blacklist(model, task_type)


def model_fitness(model: str = "", task_type: str = "", days: int = 7) -> list[dict]:
    """Success rate per model per task type over last N days.

    Returns [{model, task_type, attempts, successes, rate, blacklisted}].
    """
    since = time.time() - days * 86400
    counts: dict[tuple[str, str], list[bool]] = {}
    for row in _load_outcomes(since_ts=since):
        m, t = row.get("model", ""), row.get("task_type", "")
        if model and m != model:
            continue
        if task_type and t != task_type:
            continue
        counts.setdefault((m, t), []).append(bool(row.get("success")))
    bl = _load_blacklist()
    results = []
    for (m, t), sl in sorted(counts.items()):
        attempts = len(sl)
        successes = sum(sl)
        results.append(
            {
                "model": m,
                "task_type": t,
                "attempts": attempts,
                "successes": successes,
                "rate": round(successes / attempts, 3),
                "blacklisted": t in bl.get(m, []),
            }
        )
    return results


def blacklist(model: str, task_type: str) -> None:
    """Add model+task_type to blacklist. Logs the event — advisory only."""
    bl = _load_blacklist()
    tasks = bl.setdefault(model, [])
    if task_type not in tasks:
        tasks.append(task_type)
    _save_blacklist(bl)
    try:
        from metabolon.metabolism.infection import record_infection

        record_infection(
            tool=f"mitophagy:blacklist:{model}",
            error=f"auto-blacklisted for task_type={task_type} (<50% over >=5 attempts)",
            healed=False,
        )
    except Exception:
        pass


def is_blacklisted(model: str, task_type: str) -> bool:
    """True if model is on the blacklist for task_type."""
    return task_type in _load_blacklist().get(model, [])


def recommend_model(task_type: str) -> str:
    """Best non-blacklisted model for task_type. Fallback: 'opus'."""
    since = time.time() - 7 * 86400
    counts: dict[str, list[bool]] = {}
    for row in _load_outcomes(since_ts=since):
        if row.get("task_type") != task_type:
            continue
        m = row.get("model", "")
        if not m or is_blacklisted(m, task_type):
            continue
        counts.setdefault(m, []).append(bool(row.get("success")))
    if not counts:
        return _FALLBACK_MODEL
    best = max(
        counts.items(), key=lambda kv: (sum(kv[1]) / len(kv[1]) if kv[1] else 0, len(kv[1]))
    )
    return best[0]
