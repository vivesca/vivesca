"""inflammasome — innate immune system for the vivesca organism.

Deterministic self-test probes that verify each subsystem actually works.
No LLM calls. No external state mutation. Probes never raise.

Integration points:
  - Called on MCP server startup in pore.py serve()
  - Registered as MCP tool `inflammasome_probe`
  - Failures logged to infection log with tool name prefixed `self_test_failure:`
  - After run_all_probes(), call adaptive_response(results) to attempt known repairs

Adaptive immune layer (adaptive_response):
  - Each probe result dict gains a `repair_attempted` field (str | None).
  - Known fixable patterns receive a deterministic repair attempt (no LLM).
  - Unknown failures are logged to the infection log for human review.
  - Repairs are idempotent and never retried within the same probe cycle.
"""

import contextlib
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
        from metabolon.organelles.chromatin import recall

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


def probe_rheotaxis() -> tuple[bool, str]:
    """Verify PERPLEXITY_API_KEY is set and non-empty."""
    try:
        key = os.environ.get("PERPLEXITY_API_KEY")
        if not key:
            return False, "PERPLEXITY_API_KEY not set or empty"
        return True, f"PERPLEXITY_API_KEY set ({len(key)} chars)"
    except Exception as exc:
        return False, f"exception: {exc}"


def probe_rheotaxis_self_test() -> tuple[bool, str]:
    """Fires a minimal test query through rheotaxis CLI and validates the response."""
    try:
        import shutil

        binary = shutil.which("rheotaxis")
        if not binary:
            return False, "rheotaxis binary not found on PATH"

        result = subprocess.run(
            [binary, "--json", "test"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return False, f"rheotaxis exited {result.returncode}: {result.stderr.strip()[:200]}"

        if not result.stdout.strip():
            return False, "rheotaxis returned empty output"

        return True, "rheotaxis ok"

    except subprocess.TimeoutExpired:
        return False, "rheotaxis timed out (15s)"
    except Exception as exc:
        return False, f"exception: {exc}"


def probe_vasomotor_conf() -> tuple[bool, str]:
    """Verify respiration.conf exists, loads as JSON, and has expected keys."""
    try:
        from metabolon.vasomotor import CONF_PATH

        if not CONF_PATH.exists():
            return False, f"conf file not found: {CONF_PATH}"
        with CONF_PATH.open() as f:
            conf = json.load(f)
        if not isinstance(conf, dict) or not conf:
            return False, "conf file loaded but is empty or not a dict"
        missing = [k for k in ("aerobic_ceiling", "systole_model") if k not in conf]
        if missing:
            return False, f"conf missing expected keys: {missing}"
        return True, (
            f"conf ok — aerobic_ceiling={conf['aerobic_ceiling']}, "
            f"systole_model={conf['systole_model']!r}"
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

        infection_summary()
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
            f"infection module ok — {len(events)} event(s), {len(chronics)} chronic pattern(s)"
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
    """Verify vivesca MCP server is running."""
    import platform

    try:
        if platform.system() == "Darwin":
            result = subprocess.run(
                ["launchctl", "list", "com.vivesca.mcp"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return False, "com.vivesca.mcp LaunchAgent is not loaded"
            return True, "com.vivesca.mcp LaunchAgent is loaded"
        else:
            # Linux: check if vivesca serve process is running
            result = subprocess.run(
                ["pgrep", "-f", "vivesca serve"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return False, "vivesca serve process not found"
            pids = result.stdout.strip().splitlines()
            return True, f"vivesca serve running (pid {pids[0]})"
    except subprocess.TimeoutExpired:
        return False, "process check timed out (5s)"
    except Exception as exc:
        return False, f"exception: {exc}"


# ---------------------------------------------------------------------------
# Probe registry — ordered by subsystem dependency depth (shallowest first)
# ---------------------------------------------------------------------------

_PROBES: list[tuple[str, Any]] = [
    ("chromatin", probe_chromatin),
    ("endocytosis", probe_endocytosis),
    ("rheotaxis", probe_rheotaxis),
    ("rheotaxis_self_test", probe_rheotaxis_self_test),
    ("vasomotor_conf", probe_vasomotor_conf),
    ("respirometry", probe_respirometry),
    ("perfusion", probe_perfusion),
    ("infection", probe_infection),
    ("rss_state", probe_rss_state),
    ("importin", probe_importin),
    ("mcp_server", probe_mcp_server),
]

_PROBE_TIMEOUT_S = 10
_PRIMING_PATH = Path.home() / ".cache" / "inflammasome" / "priming.json"
_PYROPTOSIS_THRESHOLD = 3  # consecutive failed cycles before escalation


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


# ---------------------------------------------------------------------------
# Adaptive immune layer
# ---------------------------------------------------------------------------
# Known repair patterns.  Each entry: (probe_name, match_fn, repair_fn, label)
# match_fn(message: str) -> bool   — True when this pattern applies
# repair_fn() -> tuple[bool, str]  — (success, detail); must never raise
# label: str                       — short name for the repair_attempted field
# ---------------------------------------------------------------------------


def _repair_rss_stale() -> tuple[bool, str]:
    """Fire-and-forget `vivesca endocytosis fetch` to refresh RSS state."""
    try:
        import shutil

        binary = shutil.which("vivesca")
        if not binary:
            return False, "vivesca binary not found on PATH"
        subprocess.Popen(
            [binary, "endocytosis", "fetch"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        return True, "dispatched: vivesca endocytosis fetch (background)"
    except Exception as exc:
        return False, f"dispatch failed: {exc}"


def _repair_mcp_not_loaded() -> tuple[bool, str]:
    """Restart vivesca MCP server — launchctl on macOS, supervisorctl on Linux."""
    import platform

    try:
        if platform.system() == "Darwin":
            plist = str(Path.home() / "Library" / "LaunchAgents" / "com.vivesca.mcp.plist")
            result = subprocess.run(
                ["launchctl", "load", plist],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return (
                    False,
                    f"launchctl load exited {result.returncode}: {result.stderr.strip()[:200]}",
                )
            return True, f"launchctl load {plist} ok"
        else:
            # Linux: try supervisorctl, fall back to direct start
            result = subprocess.run(
                ["supervisorctl", "restart", "vivesca"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return True, "supervisorctl restart vivesca ok"
            return False, f"supervisorctl failed: {result.stderr.strip()[:200]}"
    except subprocess.TimeoutExpired:
        return False, "restart timed out (10s)"
    except Exception as exc:
        return False, f"exception: {exc}"


def _repair_chemotaxis_key() -> tuple[bool, str]:
    """Attempt to load PERPLEXITY_API_KEY from keychain via importin."""
    try:
        import importlib.machinery
        import importlib.util

        from metabolon.cytosol import VIVESCA_ROOT

        importin_path = str(VIVESCA_ROOT / "effectors" / "importin")
        loader = importlib.machinery.SourceFileLoader("keychain_env", importin_path)
        spec = importlib.util.spec_from_file_location("keychain_env", importin_path, loader=loader)
        if spec is None:
            return False, "could not build importlib spec for importin"
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        mod.load_keychain_env()
        # Verify the key is now present
        key = os.environ.get("PERPLEXITY_API_KEY")
        if not key:
            return False, "load_keychain_env() ran but PERPLEXITY_API_KEY still not set"
        return True, f"PERPLEXITY_API_KEY loaded from keychain ({len(key)} chars)"
    except FileNotFoundError:
        return False, "importin effector not found — keychain env unavailable"
    except Exception as exc:
        return False, f"exception: {exc}"


_REPAIR_PATTERNS: list[tuple[str, Any, Any, str]] = [
    # (probe_name, match_fn, repair_fn, label)
    (
        "rss_state",
        lambda msg: "stale" in msg,
        _repair_rss_stale,
        "rss_fetch_background",
    ),
    (
        "mcp_server",
        lambda msg: "not loaded" in msg,
        _repair_mcp_not_loaded,
        "launchctl_load_mcp",
    ),
    (
        "rheotaxis",
        lambda msg: "not set" in msg or "not set or empty" in msg,
        _repair_chemotaxis_key,
        "importin_load_keychain",
    ),
]

# Probes whose failures are structural config issues — log CRITICAL, no repair.
_CRITICAL_NO_REPAIR: dict[str, str] = {
    "endocytosis": "dangling symlink or not found — config issue, needs human",
}


def _load_priming() -> dict:
    """Load priming state: {probe_name: consecutive_failure_count}."""
    try:
        if _PRIMING_PATH.exists():
            return json.loads(_PRIMING_PATH.read_text())
    except Exception:
        pass
    return {}


def _save_priming(state: dict) -> None:
    """Persist priming state."""
    try:
        _PRIMING_PATH.parent.mkdir(parents=True, exist_ok=True)
        _PRIMING_PATH.write_text(json.dumps(state))
    except Exception:
        pass


def is_primed(probe_name: str, passed: bool, priming: dict) -> bool:
    """Two-signal model: only activate on second consecutive failure.

    Signal 1 (priming): first failure increments counter, returns False.
    Signal 2 (activation): second+ consecutive failure returns True.
    Pass resets the counter.
    """
    if passed:
        priming.pop(probe_name, None)
        return False
    count = priming.get(probe_name, 0) + 1
    priming[probe_name] = count
    return count >= 2


def check_pyroptosis(probe_name: str, priming: dict) -> bool:
    """Pyroptosis: escalate loudly when repair keeps failing.

    If a probe has failed >= _PYROPTOSIS_THRESHOLD consecutive cycles,
    it needs human attention — flag for Telegram/loud alert.
    """
    return priming.get(probe_name, 0) >= _PYROPTOSIS_THRESHOLD


def _pyroptosis_alert(probe_name: str, count: int, message: str) -> None:
    """Send Telegram alert on pyroptosis — the only loud escalation path.

    Throttling delegated to secretory_vesicle transport layer (24h cooldown per probe).
    """
    try:
        from metabolon.organelles.secretory_vesicle import secrete_text

        alert = (
            f"<b>🔴 PYROPTOSIS — {probe_name}</b>\n"
            f"{count} consecutive failures\n"
            f"<code>{message[:300]}</code>"
        )
        secrete_text(
            alert,
            html=True,
            label="inflammasome",
            cooldown_key=f"pyroptosis-{probe_name}",
            cooldown_seconds=24 * 3600,
        )
    except Exception:
        pass  # If Telegram itself is broken, don't crash the probe cycle


def adaptive_response(results: list[dict]) -> list[dict]:
    """Apply known repairs to probe failures; log unknowns for human review.

    Mutates each result dict in-place, adding ``repair_attempted`` (str | None):
      - None          — probe passed, no action taken
      - "<label>:ok"  — repair dispatched/applied successfully
      - "<label>:fail:<detail>" — repair attempted but failed
      - "critical"    — known-critical config issue, logged for human review
      - "unknown"     — no matching repair pattern, logged for human review

    Rules:
      - Only called for failed probes.
      - At most one repair attempt per probe per cycle.
      - All repair attempts and unknown failures are written to the infection log.
      - Never raises.
    """
    record_infection = None
    with contextlib.suppress(Exception):
        from metabolon.metabolism.infection import record_infection

    def _log(probe_name: str, error: str, healed: bool = False) -> None:
        if record_infection is not None:
            with contextlib.suppress(Exception):
                record_infection(
                    tool=f"self_test_failure:{probe_name}",
                    error=error,
                    healed=healed,
                )

    # Two-signal model: load priming state
    priming = _load_priming()

    for result in results:
        probe_name: str = result["name"]

        # Passed probes: reset priming counter, skip.
        if result.get("passed"):
            result["repair_attempted"] = None
            is_primed(probe_name, True, priming)
            continue

        message: str = result.get("message", "")

        # Signal 1 (priming): first failure → log but don't repair yet.
        if not is_primed(probe_name, False, priming):
            result["repair_attempted"] = "priming"
            continue

        # Pyroptosis: if this probe has failed too many times, escalate LOUDLY.
        if check_pyroptosis(probe_name, priming):
            fail_count = priming[probe_name]
            _log(
                probe_name,
                f"PYROPTOSIS — {fail_count} consecutive failures, human attention needed | {message}",
            )
            _pyroptosis_alert(probe_name, fail_count, message)
            result["repair_attempted"] = f"pyroptosis:{fail_count}"
            continue

        # Check for critical/structural failures first.
        if probe_name in _CRITICAL_NO_REPAIR:
            # Only log if this failure matches the structural pattern.
            critical_keywords = ("dangling symlink", "not found")
            if any(kw in message for kw in critical_keywords):
                detail = _CRITICAL_NO_REPAIR[probe_name]
                _log(probe_name, f"CRITICAL — {detail} | probe message: {message}")
                result["repair_attempted"] = "critical"
                continue

        # Walk the known repair patterns.
        repaired = False
        for pat_probe, match_fn, repair_fn, label in _REPAIR_PATTERNS:
            if pat_probe != probe_name:
                continue
            try:
                matched = match_fn(message)
            except Exception:
                matched = False
            if not matched:
                continue

            # Attempt the repair.
            try:
                success, detail = repair_fn()
            except Exception as exc:
                success, detail = False, f"repair raised: {exc}"

            if success:
                _log(probe_name, f"repair ok [{label}]: {detail}", healed=True)
                result["repair_attempted"] = f"{label}:ok"
            else:
                _log(probe_name, f"repair failed [{label}]: {detail}")
                result["repair_attempted"] = f"{label}:fail:{detail}"

            repaired = True
            break  # at most one repair per probe per cycle

        if not repaired:
            # Unknown failure — log for human review.
            _log(probe_name, f"unknown failure, human review needed | {message}")
            result["repair_attempted"] = "unknown"

    # Persist priming state for next cycle
    _save_priming(priming)

    # Post-repair verification: re-run probes that were repaired to confirm fix
    for result in results:
        ra = result.get("repair_attempted", "")
        if ra and ":ok" in str(ra):
            # Find the probe function and re-run
            for pname, pfn in _PROBES:
                if pname == result["name"]:
                    try:
                        passed, msg = _run_probe_with_timeout(pfn)
                        if passed:
                            result["verified"] = True
                            # Reset priming counter on verified fix
                            priming.pop(result["name"], None)
                        else:
                            result["verified"] = False
                            _log(
                                result["name"], f"repair claimed ok but verification failed: {msg}"
                            )
                    except Exception:
                        result["verified"] = False
                    break

    _save_priming(priming)
    return results


if __name__ == "__main__":
    print(probe_report())
