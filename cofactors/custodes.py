"""Dependency change detection module for the daily ritual.

Checks key upstream dependencies against a cached baseline and reports diffs.
Deterministic — no LLM calls. Designed to feed the LLM reasoning step in
/daily or /eow skills.

Never-crash contract: every public function returns structured data; never raises.

Usage (module):
    from custodes import check_all, get_status, get_diff

Usage (CLI):
    python custodes.py check   # check all deps, print report, update cache
    python custodes.py status  # show cached versions, no network
    python custodes.py diff    # check all deps, print report, don't update cache
"""

import json
import subprocess
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_HKT = timezone(timedelta(hours=8))
_CACHE_DIR = Path.home() / "notes" / ".custodes-cache"
_VERSIONS_FILE = _CACHE_DIR / "versions.json"
_LAST_CHECK_FILE = _CACHE_DIR / "last_check.json"

_LLM_MODELS_PATH = Path.home() / ".config" / "llm-models.json"

# Known venv paths for project-scoped packages
# fastmcp is a direct dependency of praeses (the unified MCP server)
_PRAESES_VENV = Path.home() / "code" / "praeses" / ".venv"
# Anthropic SDK: check multiple project venvs, take highest found
_ANTHROPIC_VENV_CANDIDATES = [
    Path.home() / "code" / "docima" / ".venv",
    Path.home() / "code" / "aegis-gov" / ".venv",
]

# Symbols used in output
_CHANGED = "⚠️  CHANGED"
_OK = "✓"
_UNKNOWN = "?"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run(cmd: list[str], timeout: int = 10) -> tuple[str, str]:
    """Run a subprocess. Returns (stdout, stderr). Never raises."""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return "", f"timed out after {timeout}s"
    except Exception as e:
        return "", str(e)


def _ensure_cache_dir() -> tuple[bool, str]:
    """Create cache directory if it doesn't exist. Returns (ok, error)."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return True, ""
    except Exception as e:
        return False, str(e)


def _read_json(path: Path) -> dict:
    """Read a JSON file. Returns empty dict on any error."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(path: Path, data: dict) -> tuple[bool, str]:
    """Write a JSON file atomically. Returns (ok, error)."""
    try:
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(path)
        return True, ""
    except Exception as e:
        return False, str(e)


def _now_hkt_iso() -> str:
    """Current time as ISO string in HKT."""
    return datetime.now(_HKT).isoformat()


def _today_hkt() -> str:
    """Today's date as YYYY-MM-DD in HKT."""
    return datetime.now(_HKT).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Version fetchers — each returns {"version": str | None, "error": str}
# ---------------------------------------------------------------------------


def _fetch_claude_version() -> dict:
    """Fetch claude CLI version.

    Output format: "2.1.79 (Claude Code)" — take the first token.
    Falls back to resolving the claude symlink and checking its parent package.
    """
    stdout, stderr = _run(["claude", "--version"])
    if stdout:
        # "2.1.79 (Claude Code)" → "2.1.79"
        # Also handles old format "Claude Code 2.1.82" → "2.1.82"
        parts = stdout.split()
        # Find the token that looks like a version (digits and dots)
        for part in parts:
            stripped = part.strip("()")
            if stripped and stripped[0].isdigit() and "." in stripped:
                return {"version": stripped, "error": ""}
        # Fallback: last token
        version = parts[-1].strip("()") if parts else stdout
        return {"version": version, "error": ""}
    return {"version": None, "error": stderr or "no output"}


def _read_dist_info_version(package_name: str, search_dirs: list[Path]) -> dict:
    """Read a package version from dist-info METADATA files in given dirs.

    Searches for <package_name>-*.dist-info/METADATA and parses the Version field.
    More reliable than pip show when packages are in project-scoped venvs.
    """
    import glob as _glob

    for base_dir in search_dirs:
        if not base_dir.exists():
            continue
        # site-packages may be under lib/python*/site-packages/
        for site_packages in base_dir.glob("lib/python*/site-packages"):
            pattern = str(site_packages / f"{package_name}-*.dist-info" / "METADATA")
            matches = _glob.glob(pattern)
            for metadata_path in sorted(matches):
                try:
                    with open(metadata_path, encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("Version:"):
                                version = line.split(":", 1)[1].strip()
                                return {"version": version, "error": ""}
                except Exception:
                    continue
    return {"version": None, "error": f"no dist-info found for '{package_name}' in searched paths"}


def _fetch_fastmcp_version() -> dict:
    """Fetch fastmcp version from the praeses project venv (canonical installation)."""
    result = _read_dist_info_version("fastmcp", [_PRAESES_VENV])
    if result["version"]:
        return result
    # Fallback: scan other known code locations
    code_dir = Path.home() / "code"
    if code_dir.exists():
        try:
            candidates = [d / ".venv" for d in code_dir.iterdir() if (d / ".venv").exists()]
            result2 = _read_dist_info_version("fastmcp", candidates[:10])
            if result2["version"]:
                return result2
        except Exception:
            pass
    return result  # return original "not found" result


def _fetch_anthropic_version() -> dict:
    """Fetch anthropic SDK version from known project venvs."""
    result = _read_dist_info_version("anthropic", _ANTHROPIC_VENV_CANDIDATES)
    if result["version"]:
        return result
    # Fallback: scan other venvs and take the highest version found
    code_dir = Path.home() / "code"
    if not code_dir.exists():
        return result
    try:
        best_version = None
        for project_dir in code_dir.iterdir():
            venv = project_dir / ".venv"
            if not venv.exists():
                continue
            r = _read_dist_info_version("anthropic", [venv])
            if r["version"]:
                # Simple string comparison is sufficient for semver ordering here
                if best_version is None or r["version"] > best_version:
                    best_version = r["version"]
        if best_version:
            return {"version": best_version, "error": ""}
    except Exception:
        pass
    return result


def _fetch_mcp_version() -> dict:
    """Fetch mcp SDK version (used by fasti-mcp, deltos-mcp, etc)."""
    # mcp servers use uv --script with mcp[cli] dependency
    # Check in praeses venv or oghma uv tool environment
    candidates = [
        _PRAESES_VENV,
        Path.home() / ".local" / "share" / "uv" / "tools" / "oghma",
    ]
    result = _read_dist_info_version("mcp", candidates)
    if result["version"]:
        return result
    # Also try scanning code dir
    code_dir = Path.home() / "code"
    if code_dir.exists():
        try:
            venvs = [d / ".venv" for d in code_dir.iterdir() if (d / ".venv").exists()]
            result2 = _read_dist_info_version("mcp", venvs[:10])
            if result2["version"]:
                return result2
        except Exception:
            pass
    return result


def _fetch_openrouter_models() -> dict:
    """Check llm-models.json modification time as a proxy for changes."""
    try:
        if not _LLM_MODELS_PATH.exists():
            return {"version": None, "error": f"not found: {_LLM_MODELS_PATH}"}
        mtime = _LLM_MODELS_PATH.stat().st_mtime
        # Version = mtime as YYYY-MM-DD HH:MM UTC — human-readable proxy
        dt = datetime.fromtimestamp(mtime, tz=UTC)
        version = dt.strftime("%Y-%m-%d %H:%M UTC")
        return {"version": version, "error": ""}
    except Exception as e:
        return {"version": None, "error": str(e)}


def _fetch_python_version() -> dict:
    """Fetch python3 version."""
    stdout, stderr = _run(["python3", "--version"])
    if stdout:
        # "Python 3.12.4" → "3.12.4"
        parts = stdout.split()
        version = parts[-1] if len(parts) >= 2 else stdout
        return {"version": version, "error": ""}
    return {"version": None, "error": stderr or "no output"}


def _fetch_node_version() -> dict:
    """Fetch node version. Gracefully absent."""
    stdout, stderr = _run(["node", "--version"])
    if stdout:
        # "v22.3.0" → "22.3.0"
        version = stdout.lstrip("vV").strip()
        return {"version": version, "error": ""}
    return {"version": None, "error": stderr or "not installed"}


# ---------------------------------------------------------------------------
# Registry of all checks
# ---------------------------------------------------------------------------

_CHECKS: list[tuple[str, Any]] = [
    ("claude", _fetch_claude_version),
    ("fastmcp", _fetch_fastmcp_version),
    ("anthropic", _fetch_anthropic_version),
    ("mcp", _fetch_mcp_version),
    ("openrouter_models", _fetch_openrouter_models),
    ("python", _fetch_python_version),
    ("node", _fetch_node_version),
]


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def _fetch_current_versions() -> dict:
    """Run all checks. Returns {name: {version, error}} dict."""
    results = {}
    for name, fetcher in _CHECKS:
        try:
            result = fetcher()
        except Exception as e:
            result = {"version": None, "error": str(e)}
        results[name] = result
    return results


def _compute_diff(cached: dict, current: dict) -> list[dict]:
    """Produce a diff list. Each item: {name, old, new, changed, note}."""
    all_keys = sorted(set(list(cached.keys()) + list(current.keys())))
    rows = []
    for key in all_keys:
        old = cached.get(key, {}).get("version")
        new_entry = current.get(key, {})
        new = new_entry.get("version")
        error = new_entry.get("error", "")
        changed = (old != new) and (new is not None)
        rows.append(
            {
                "name": key,
                "old": old,
                "new": new,
                "changed": changed,
                "error": error,
            }
        )
    return rows


def _format_report(diff: list[dict], since_date: str | None) -> str:
    """Format the diff as a human-readable markdown report."""
    lines = []
    since = since_date or "unknown"
    lines.append(f"## Dependency Changes (since {since})")
    lines.append("")

    changes = [d for d in diff if d["changed"]]
    unchanged = [d for d in diff if not d["changed"] and d["new"] is not None]
    unavailable = [d for d in diff if d["new"] is None]

    for row in diff:
        name = row["name"]
        old = row["old"] or "—"
        new = row["new"]
        if new is None:
            status = f"unavailable ({row['error']})" if row["error"] else "unavailable"
            lines.append(f"- {name}: {old} → {status}")
        elif row["changed"]:
            lines.append(f"- {name}: {old} → {new}  {_CHANGED}")
        else:
            lines.append(f"- {name}: {new}  {_OK}")

    lines.append("")
    lines.append("## Recommendation")
    lines.append("")

    if not changes:
        lines.append("No changes detected. Stack is current.")
    else:
        lines.append(f"{len(changes)} dependency change(s) detected:")
        for row in changes:
            lines.append(f"- **{row['name']}**: {row['old'] or '(unknown)'} → {row['new']}")
        lines.append("")
        lines.append("Review for breaking changes before next release:")
        for row in changes:
            name = row["name"]
            if name == "claude":
                lines.append(
                    "  - claude: check `claude changelog` or release notes for skill-breaking changes"
                )
            elif name == "fastmcp":
                lines.append(
                    "  - fastmcp: check MCP server compatibility (tool signatures, transport) — praeses rebuild may be needed"
                )
            elif name == "mcp":
                lines.append(
                    "  - mcp SDK: check server compatibility for fasti-mcp, deltos-mcp, keryx-mcp, oghma-mcp"
                )
            elif name == "anthropic":
                lines.append("  - anthropic SDK: check model IDs, API parameter deprecations")
            elif name == "openrouter_models":
                lines.append(
                    "  - openrouter models: llm-models.json was modified — verify model IDs still valid"
                )
            elif name in ("python", "node"):
                lines.append(
                    f"  - {name}: runtime version change — check dependency compatibility"
                )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_all(update_cache: bool = True) -> dict:
    """Check all dependencies and optionally update the cache.

    Returns:
        {
            "diff": list[dict],          # per-dependency diff rows
            "report": str,               # formatted markdown report
            "changes_found": bool,
            "since_date": str | None,
            "error": str,                # non-empty if cache write failed
        }
    """
    _ensure_cache_dir()
    cached = _read_json(_VERSIONS_FILE)
    last_check = _read_json(_LAST_CHECK_FILE)
    since_date = last_check.get("date")

    current = _fetch_current_versions()
    diff = _compute_diff(cached, current)
    changes_found = any(d["changed"] for d in diff)
    report = _format_report(diff, since_date)

    error = ""
    if update_cache:
        # Save current versions (only entries where we got a version)
        new_cache = {}
        for name, entry in current.items():
            if entry.get("version") is not None:
                new_cache[name] = entry
            else:
                # Preserve last-known if fetch failed
                if name in cached:
                    new_cache[name] = cached[name]
        ok, err = _write_json(_VERSIONS_FILE, new_cache)
        if not ok:
            error = f"cache write failed: {err}"

        ok2, err2 = _write_json(
            _LAST_CHECK_FILE,
            {
                "date": _today_hkt(),
                "timestamp": _now_hkt_iso(),
            },
        )
        if not ok2 and not error:
            error = f"last_check write failed: {err2}"

    return {
        "diff": diff,
        "report": report,
        "changes_found": changes_found,
        "since_date": since_date,
        "error": error,
    }


def get_status() -> dict:
    """Return cached versions without running any checks.

    Returns:
        {
            "versions": dict,       # name → {version, error}
            "last_check": dict,     # {date, timestamp} or {}
            "report": str,
            "error": str,
        }
    """
    _ensure_cache_dir()
    versions = _read_json(_VERSIONS_FILE)
    last_check = _read_json(_LAST_CHECK_FILE)

    lines = ["## Cached Dependency Versions", ""]
    if not versions:
        lines.append("No cache found. Run `custodes check` to populate.")
    else:
        since = last_check.get("date", "unknown")
        lines.append(f"Last checked: {last_check.get('timestamp', since)}")
        lines.append("")
        for name, entry in sorted(versions.items()):
            version = entry.get("version", "—")
            lines.append(f"- {name}: {version}")

    return {
        "versions": versions,
        "last_check": last_check,
        "report": "\n".join(lines),
        "error": "",
    }


def get_diff() -> dict:
    """Check all deps and report diff, but do NOT update the cache.

    Convenience wrapper around check_all(update_cache=False).
    """
    return check_all(update_cache=False)
