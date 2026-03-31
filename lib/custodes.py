"""custodes — dependency version tracking for immunosurveillance.

Snapshots installed package versions to a local JSON cache and detects
added, removed, or changed packages between runs.
"""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "custodes"
CACHE_FILE = CACHE_DIR / "deps.json"


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _current_deps() -> dict[str, str]:
    deps: dict[str, str] = {}
    for dist in importlib.metadata.distributions():
        name = dist.metadata.get("Name")
        version = dist.metadata.get("Version")
        if name and version:
            deps[name] = version
    return dict(sorted(deps.items()))


def _read_cache() -> dict[str, str]:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _write_cache(deps: dict[str, str]):
    _ensure_cache_dir()
    CACHE_FILE.write_text(json.dumps(deps, indent=2))


def _diff(old: dict[str, str], new: dict[str, str]) -> dict[str, dict]:
    added = {k: v for k, v in new.items() if k not in old}
    removed = {k: v for k, v in old.items() if k not in new}
    upgraded: dict[str, tuple[str, str]] = {}
    downgraded: dict[str, tuple[str, str]] = {}
    for name in old:
        if name in new and old[name] != new[name]:
            upgraded[name] = (old[name], new[name])
    return {"added": added, "removed": removed, "changed": upgraded}


def _format_report(diff: dict[str, dict], total: int, cached_total: int) -> str:
    lines = [f"Tracked {total} packages (cached: {cached_total})"]

    changes = diff["added"] or diff["removed"] or diff["changed"]

    if not changes:
        lines.append("No changes detected.")
        return "\n".join(lines)

    if diff["added"]:
        lines.append(f"\n  Added ({len(diff['added'])}):")
        for name, ver in sorted(diff["added"].items()):
            lines.append(f"    + {name} {ver}")

    if diff["removed"]:
        lines.append(f"\n  Removed ({len(diff['removed'])}):")
        for name, ver in sorted(diff["removed"].items()):
            lines.append(f"    - {name} {ver}")

    if diff["changed"]:
        lines.append(f"\n  Changed ({len(diff['changed'])}):")
        for name, (old_v, new_v) in sorted(diff["changed"].items()):
            lines.append(f"    ~ {name} {old_v} -> {new_v}")

    return "\n".join(lines)


def check_all(*, update_cache: bool = True) -> dict:
    """Check all installed deps against cache. Optionally update cache."""
    try:
        current = _current_deps()
        cached = _read_cache()

        if not cached:
            if update_cache:
                _write_cache(current)
            return {
                "report": f"Seeded cache with {len(current)} packages. Run again to detect changes.",
                "error": None,
                "changes_found": False,
            }

        diff = _diff(cached, current)
        report = _format_report(diff, len(current), len(cached))
        changes_found = bool(diff["added"] or diff["removed"] or diff["changed"])

        if update_cache:
            _write_cache(current)

        return {
            "report": report,
            "error": None,
            "changes_found": changes_found,
        }

    except Exception as exc:
        return {
            "report": "Error during dependency check.",
            "error": str(exc),
            "changes_found": False,
        }


def get_status() -> dict:
    """Show current cached versions (no network)."""
    try:
        cached = _read_cache()

        if not cached:
            return {
                "report": "No cached snapshot found. Run 'immunosurveillance check' first.",
                "error": None,
            }

        lines = [f"Cached {len(cached)} packages:"]
        for name, ver in cached.items():
            lines.append(f"  {name} {ver}")

        return {
            "report": "\n".join(lines),
            "error": None,
        }

    except Exception as exc:
        return {
            "report": "Error reading cache.",
            "error": str(exc),
        }


def get_diff() -> dict:
    """Check all deps, return diff only (don't update cache)."""
    return check_all(update_cache=False)
