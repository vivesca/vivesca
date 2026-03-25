#!/usr/bin/env python3
"""Shared nudge logger — generalized Hebbian learning for all advisory hooks.

Any hook that gives advice (not guards/denials) should call log_nudge() so
accuracy is measurable at /weekly. The loop:

  hook fires prediction → log → did user act on it? → log outcome → /weekly reviews

Accuracy = acted_on / total fires. Low accuracy = the hook is wrong or noisy.

Bio: Hebbian learning = "neurons that fire together wire together."
Hooks that fire but don't predict user behavior should weaken (suppress/fix).

Accuracy reviewed at /ecdysis. Usage from other hooks:
    from hebbian_nudge import log_nudge
    log_nudge("mitogen", "delegate", prompt_snippet="build a cli tool")
"""

import json
import time
from pathlib import Path

NUDGE_LOG = Path.home() / ".claude" / "nudge-log.jsonl"


def log_nudge(
    hook: str, prediction: str, prompt_snippet: str = "", metadata: dict | None = None
) -> None:
    """Log an advisory hook's prediction for accuracy tracking.

    Args:
        hook: Hook name (e.g., "mitogen", "priming", "allostasis")
        prediction: What the hook predicted/suggested (e.g., "delegate", "use-skill:phagocytosis")
        prompt_snippet: First ~200 chars of the prompt that triggered it
        metadata: Optional extra context
    """
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hook": hook,
        "prediction": prediction,
        "prompt": prompt_snippet[:200],
    }
    if metadata:
        entry["meta"] = metadata

    try:
        with NUDGE_LOG.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def summarize(days: int = 7) -> dict:
    """Summarize nudge accuracy for /weekly review.

    Returns: {hook_name: {total: N, predictions: {pred: count}}}
    """
    from datetime import datetime, timedelta

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    stats: dict = {}
    if not NUDGE_LOG.exists():
        return stats

    for line in NUDGE_LOG.read_text().strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            if entry.get("ts", "") < cutoff:
                continue
            hook = entry.get("hook", "unknown")
            pred = entry.get("prediction", "unknown")
            if hook not in stats:
                stats[hook] = {"total": 0, "predictions": {}}
            stats[hook]["total"] += 1
            stats[hook]["predictions"][pred] = stats[hook]["predictions"].get(pred, 0) + 1
        except (json.JSONDecodeError, ValueError):
            continue

    return stats


if __name__ == "__main__":
    # CLI mode: print weekly summary
    import sys

    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    stats = summarize(days)
    if not stats:
        print("No nudge data in the last", days, "days.")
    else:
        print(f"Nudge accuracy report (last {days} days):")
        for hook, data in sorted(stats.items()):
            preds = ", ".join(f"{k}={v}" for k, v in data["predictions"].items())
            print(f"  {hook}: {data['total']} fires ({preds})")
