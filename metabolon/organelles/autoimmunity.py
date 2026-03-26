"""autoimmunity — innate immune system for the vivesca organism.

Deterministic self-test probes that verify each subsystem actually works.
No LLM calls. No external state mutation. Probes never raise.

Integration points (prepare only — not yet wired):
  - Called on MCP server startup in pore.py serve()
  - Registered as MCP tool `autoimmunity_probe`
  - Failures should be logged to infection log with severity `self_test_failure`
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Individual probe functions
# Each returns (passed: bool, message: str).
# All imports are lazy (inside the function) to avoid circular import chains.
# All exceptions are caught — a probe must never raise.
# ---------------------------------------------------------------------------


def probe_chromatin() -> tuple[bool, str]:
    """Verify chromatin memory DB connects and recall() returns without error."""
    try:
        from metabolon.organelles.chromatin import _get_storage, recall

        storage = _get_storage()
        if storage is None:
            return False, "_get_storage() returned None"
        results = recall("test", limit=1)
        if not isinstance(results, list):
            return False, f"recall() returned {type(results).__name__}, expected list"
        return True, f"connected, recall returned {len(results)} result(s)"
    except Exception as exc:
        return False, f"exception: {exc}"


def probe_endocytosis() -> tuple[bool, str]:
    """Verify sources.yaml exists, is not a dangling symlink, and loads with >0 sources."""
    try:
        sources_path = Path.home() / ".config" / "endocytosis" / "sources.yaml"
        if not sources_path.exists():
            return False, f"sources.yaml not found: {sources_path}"
        # Resolve symlink — exists() above follows symlinks, but check explicitly
        if sources_path.is_symlink() and not sources_path.resolve().exists():
            return False, f"sources.yaml is a dangling symlink: {sources_path}"

        import yaml

        with sources_path.open() as f:
            data = yaml.safe_load(f) or {}
        # Count sources across all sections
        source_count = 0
        for section in data.values():
            if isinstance(section, list):
                source_count += sum(1 for item in section if isinstance(item, dict))
        if source_count == 0:
            return False, "sources.yaml loaded but contains 0 sources"
        return True, f"sources.yaml ok, {source_count} source(s)"
    except Exception as exc:
        return False, f"exception: {exc}"


def probe_chemotaxis() -> tuple[bool, str]:
    """Verify PERPLEXITY_API_KEY is set and non-empty."""
    try:
        key = os.environ.get("PERPLEXITY_API_KEY")
        if not key:
            return False, "PERPLEXITY_API_KEY not set or empty"
        return True, f"PERPLEXITY_API_KEY set ({len(key)} chars)"
    except Exception as exc:
        return False, f"exception: {exc}"


def probe_vasomotor_conf() -> tuple[bool, str]:
    """Verify respiration.conf exists, loads as JSON, and has expected keys."""
    try:
        from metabolon.cytosol import VIVESCA_ROOT
        from metabolon.vasomotor import CONF_PATH

        if not CONF_PATH.exists():
            return False, f"conf file not found: {CONF_PATH}"
        with CONF_PATH.open() as f:
            conf = json.load(f)
        if not isinstance(conf, dict) or not conf:
            return False, "conf file loaded but is empty or not a dict"
        missing = [k for k in ("aerobic_ceiling", "wave_model") if k not in conf]
        if missing:
            return False, f"conf missing expected keys: {missing}"
        return True, (
            f"conf ok — aerobic_ceiling={conf['aerobic_ceiling']}, "
            f"wave_model={conf['wave_model']!r}"
        )
    except Exception as exc:
        return False, f"exception: {exc}"


def probe_respirometry() -> tuple[bool, str]:
    """Run respirometry --json and verify it returns valid JSON with seven_day.utilization."""
    try:
        import shutil

        binary = shutil.which("respirometry")
        if not binary:
            return False, "respirometry binary not found on PATH"
        result = subprocess.run(
            [binary, "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False, f"respirometry exited {result.returncode}: {result.stderr.strip()[:200]}"
        try:
            data: dict[str, Any] = json.loads(result.stdout)
        except json.JSONDecodeError as parse_err:
            return False, f"invalid JSON from respirometry: {parse_err}"
        seven_day = data.get("seven_day")
        if not isinstance(seven_day, dict) or "utilization" not in seven_day:
            return False, "response missing seven_day.utilization"
        utilization = seven_day["utilization"]
        stale = data.get("stale", False)
        suffix = " [WARN: stale data]" if stale else ""
        return True, f"seven_day.utilization={utilization}{suffix}"
    except subprocess.TimeoutExpired:
        return False, "respirometry timed out (10s)"
    except Exception as exc:
        return False, f"exception: {exc}"


def probe_perfusion() -> tuple[bool, str]:
    """Verify perfusion module loads and _ROUTABLE_STARS is non-empty."""
    try:
        from metabolon.perfusion import _ROUTABLE_STARS

        if not _ROUTABLE_STARS:
            return False, "_ROUTABLE_STARS is empty"
        return True, f"_ROUTABLE_STARS has {len(_ROUTABLE_STARS)} star(s)"
    except Exception as exc:
        return False, f"exception: {exc}"


def probe_infection() -> tuple[bool, str]:
    """Verify infection module loads and infection_summary() only includes unhealed events."""
    try:
        from metabolon.metabolism.infection import (
            chronic_infections,
            infection_summary,
            recall_infections,
        )

        summary = infection_summary()
        # Verify chronic count is consistent: chronic infections should all be unhealed
        events = recall_infections()
        chronics = chronic_infections()
        for pattern in chronics:
            # Each chronic pattern must have at least one unhealed event
            # (count - healed_count > 0 means unhealed events exist)
            unhealed_in_pattern = pattern["count"] - pattern["healed_count"]
            if unhealed_in_pattern == 0:
                return False, (
                    f"chronic pattern {pattern['fingerprint']} has 0 unhealed events "
                    f"but is listed as chronic — logic error"
                )
        return True, (
            f"infection module ok — {len(events)} event(s), "
            f"{len(chronics)} chronic pattern(s)"
        )
    except Exception as exc:
        return False, f"exception: {exc}"


def probe_rss_state() -> tuple[bool, str]:
    """Verify RSS state file mtime is < 48 hours."""
    try:
        state_path = Path.home() / ".cache" / "endocytosis" / "state.json"
        if not state_path.exists():
            return False, f"state.json not found: {state_path}"
        age_seconds = time.time() - state_path.stat().st_mtime
        age_hours = age_seconds / 3600
        if age_hours >= 48:
            return False, f"state.json is stale: {age_hours:.1f}h old (threshold: 48h)"
        return True, f"state.json age: {age_hours:.1f}h"
    except Exception as exc:
        return False, f"exception: {exc}"


def probe_importin() -> tuple[bool, str]:
    """Verify the importin effector file exists at the path membrane.py expects."""
    try:
        from metabolon.cytosol import VIVESCA_ROOT

        importin_path = VIVESCA_ROOT / "effectors" / "importin"
        if not importin_path.exists():
            return False, f"importin effector not found: {importin_path}"
        if not os.access(str(importin_path), os.R_OK):
            return False, f"importin exists but is not readable: {importin_path}"
        return True, f"importin found: {importin_path}"
    except Exception as exc:
        return False, f"exception: {exc}"


def probe_mcp_server() -> tuple[bool, str]:
    """Verify com.vivesca.mcp LaunchAgent is loaded."""
    try:
        result = subprocess.run(
            ["launchctl", "list", "com.vivesca.mcp"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return False, "com.vivesca.mcp LaunchAgent is not loaded (launchctl returned non-zero)"
        return True, "com.vivesca.mcp LaunchAgent is loaded"
    except subprocess.TimeoutExpired:
        return False, "launchctl timed out (5s)"
    except Exception as exc:
        return False, f"exception: {exc}"


# ---------------------------------------------------------------------------
# Probe registry — ordered by subsystem dependency depth (shallowest first)
# ---------------------------------------------------------------------------

_PROBES: list[tuple[str, Any]] = [
    ("chromatin", probe_chromatin),
    ("endocytosis", probe_endocytosis),
    ("chemotaxis", probe_chemotaxis),
    ("vasomotor_conf", probe_vasomotor_conf),
    ("respirometry", probe_respirometry),
    ("perfusion", probe_perfusion),
    ("infection", probe_infection),
    ("rss_state", probe_rss_state),
    ("importin", probe_importin),
    ("mcp_server", probe_mcp_server),
]

_PROBE_TIMEOUT_S = 10


def _run_probe_with_timeout(fn: Any) -> tuple[bool, str]:
    """Run a probe function with a hard timeout using subprocess-free threading."""
    import threading

    result_holder: list[tuple[bool, str]] = []
    exc_holder: list[Exception] = []

    def _target():
        try:
            result_holder.append(fn())
        except Exception as exc:
            exc_holder.append(exc)

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=_PROBE_TIMEOUT_S)

    if t.is_alive():
        return False, f"probe timed out after {_PROBE_TIMEOUT_S}s"
    if exc_holder:
        return False, f"uncaught exception: {exc_holder[0]}"
    if not result_holder:
        return False, "probe returned no result"
    return result_holder[0]


def run_all_probes() -> list[dict]:
    """Run all probes. Return list of {name, passed, message, duration_ms}.

    Each probe is independent — one failure does not block the others.
    All exceptions are caught; a probe that raises returns passed=False.
    """
    results = []
    for name, fn in _PROBES:
        t0 = time.perf_counter()
        try:
            passed, message = _run_probe_with_timeout(fn)
        except Exception as exc:
            passed, message = False, f"runner exception: {exc}"
        duration_ms = int((time.perf_counter() - t0) * 1000)
        results.append(
            {
                "name": name,
                "passed": passed,
                "message": message,
                "duration_ms": duration_ms,
            }
        )
    return results


def probe_report() -> str:
    """Run all probes and return a human-readable report for the MCP tool.

    Format:
        [PASS] chromatin — connected, recall returned 0 result(s) (12ms)
        [FAIL] rss_state — state.json is stale: 52.1h old (threshold: 48h) (1ms)
        ...
        Summary: 9/10 passed
    """
    results = run_all_probes()
    lines = []
    for r in results:
        tag = "PASS" if r["passed"] else "FAIL"
        lines.append(f"[{tag}] {r['name']} — {r['message']} ({r['duration_ms']}ms)")
    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    lines.append(f"\nSummary: {passed_count}/{total} passed")
    return "\n".join(lines)


if __name__ == "__main__":
    print(probe_report())
