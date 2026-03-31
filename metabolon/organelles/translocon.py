"""translocon — dispatch cheap LLM tasks via goose/droid on ZhiPu plan.

Organelle: pure functions returning structured dicts.
CLI effector and MCP enzyme both delegate here.

Modes:
  explore — cheap read-only queries (direct API, fallback goose)
  build   — implementation tasks (goose, GLM-5.1)
  mcp     — MCP tool building (droid, --auto high)
  safe    — read-only audit (droid)
  skill   — execute an organism skill (goose + recipe, or droid for --mcp)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COACHING_NOTES = Path.home() / "epigenome/marks/feedback_golem_coaching.md"
SORTASE_LOG = Path.home() / ".local/share/sortase/log.jsonl"
GOLEM_LOG = Path.home() / ".local/share/vivesca/golem.jsonl"
CACHE_DIR = Path.home() / ".cache/translocon"
CACHE_TTL = 3600  # 1 hour in seconds

# Provider concurrency limits for golem-daemon
PROVIDER_LIMITS = {
    "zhipu": 4,
    "infini": 6,
    "volcano": 8,
}


# ---------------------------------------------------------------------------
# Helpers (pure, testable)
# ---------------------------------------------------------------------------


def _cache_key(prompt: str, model: str) -> str:
    """Deterministic cache key from prompt + model."""
    raw = f"{model}:{prompt}".encode()
    return hashlib.sha256(raw).hexdigest()[:32]


def _cache_get(key: str) -> dict | None:
    """Return cached response if it exists and is < CACHE_TTL seconds old."""
    path = CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        entry = json.loads(path.read_text())
        age = time.time() - entry.get("timestamp", 0)
        if age < CACHE_TTL:
            return entry["response"]
        # Stale — remove
        path.unlink(missing_ok=True)
        return None
    except (json.JSONDecodeError, KeyError):
        return None


def _cache_put(key: str, response: dict) -> None:
    """Store response in cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.json"
    path.write_text(json.dumps({"timestamp": time.time(), "response": response}))


def _inject_coaching(prompt: str) -> str:
    """Prepend GLM coaching notes if the file exists."""
    if COACHING_NOTES.exists():
        notes = COACHING_NOTES.read_text().strip()
        # Strip YAML frontmatter
        if notes.startswith("---"):
            end = notes.find("---", 3)
            if end > 0:
                notes = notes[end + 3:].strip()
        return f"{notes}\n\n---\n\nTask:\n{prompt}"
    return prompt


_TOTAL_SIZE_CAP = 100_000  # 100 KB cumulative cap for _read_dir_context


def _read_dir_context(directory: str, glob_pattern: str = "*.py") -> str:
    """Read small source files from directory as context.

    Stops reading once cumulative content exceeds _TOTAL_SIZE_CAP and
    logs the number of files skipped.
    """
    parts: list[str] = []
    cumulative = 0
    skipped = 0
    for f in sorted(Path(directory).glob(glob_pattern)):
        if not f.is_file() or f.stat().st_size >= 50000:
            continue
        content = f.read_text()
        cumulative += len(content)
        if cumulative > _TOTAL_SIZE_CAP:
            skipped += 1
            continue
        parts.append(f"### {f.name}\n```\n{content}\n```")
    if skipped:
        logger.info(
            "_read_dir_context: skipped %d file(s) after reaching %d byte cap",
            skipped,
            _TOTAL_SIZE_CAP,
        )
    return "\n\n".join(parts)


def _direct_api(prompt: str, model: str = "glm-4.7") -> dict:
    """Call ZhiPu API directly (no goose/droid). Returns structured dict."""
    import urllib.error
    import urllib.request

    key = os.environ.get("ZHIPU_API_KEY", "")
    if not key:
        return {"success": False, "output": "ZHIPU_API_KEY not set", "returncode": 1}

    body = json.dumps({
        "model": model,
        "max_tokens": 8192,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/anthropic/v1/messages", body
    )
    req.add_header("x-api-key", key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            data = json.loads(urllib.request.urlopen(req, timeout=120).read())
            return {"success": True, "output": data["content"][0]["text"], "returncode": 0}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500) and attempt < max_retries:
                time.sleep(2)
                continue
            return {"success": False, "output": f"direct API failed: {exc}", "returncode": 1}
        except Exception as exc:
            return {"success": False, "output": f"direct API failed: {exc}", "returncode": 1}
    return {"success": False, "output": "direct API failed: max retries exceeded", "returncode": 1}


def _run_captured(cmd: list[str], **kwargs: Any) -> tuple[int, str]:
    """Run command, capture stdout. Returns (returncode, stdout)."""
    r = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    return r.returncode, (r.stdout or "")


def _build_goose_cmd(model: str, prompt: str, recipe: str | None = None) -> list[str]:
    """Build goose CLI command."""
    cmd = ["goose", "run", "-q", "--no-session",
           "--provider", "glm-coding", "--model", model]
    if recipe:
        cmd += ["--recipe", recipe]
    cmd += ["-t", prompt]
    return cmd


def _build_droid_cmd(
    model: str, directory: str, prompt: str, auto: str | None = None
) -> list[str]:
    """Build droid CLI command."""
    model_flag = model if model.startswith("custom:") else f"custom:{model}"
    cmd = ["droid", "exec", "-m", model_flag, "--cwd", directory, prompt]
    if auto:
        cmd.insert(2, "--auto")
        cmd.insert(3, auto)
    return cmd


def _resolve_mode(
    *,
    mode: str,
    model: str | None = None,
    backend: str | None = None,
) -> tuple[str, str, str | None]:
    """Resolve (backend, model, auto) from mode/overrides.

    Returns:
        (backend, model, auto_level)
    """
    auto: str | None = None

    if mode == "skill":
        # skill mode: backend decided by caller (goose by default, droid if mcp)
        backend_resolved = backend or "goose"
        model_resolved = model or "GLM-5.1"
    elif mode == "build":
        backend_resolved = backend or "goose"
        model_resolved = model or "GLM-5.1"
    elif mode == "mcp":
        backend_resolved = backend or "droid"
        model_resolved = model or "GLM-4.7"
        auto = "high"
    elif mode == "safe":
        backend_resolved = backend or "droid"
        model_resolved = model or "GLM-4.7"
    else:  # explore
        backend_resolved = backend or "goose"
        model_resolved = model or "GLM-4.7"

    # User overrides
    if backend:
        backend_resolved = backend
    if model:
        model_resolved = model

    return backend_resolved, model_resolved, auto


# ---------------------------------------------------------------------------
# Core dispatch
# ---------------------------------------------------------------------------


def _approx_tokens(text: str) -> int:
    """Rough token count: ~4 chars per token for English/mixed content."""
    return max(1, len(text) // 4)


def _explore_structured(
    output: str,
    prompt: str,
    model: str,
    duration_s: float,
    cached: bool = False,
) -> dict:
    """Wrap explore result in structured JSON envelope."""
    return {
        "query": prompt,
        "response": output,
        "model": model,
        "tokens_approx": _approx_tokens(output),
        "cached": cached,
        "duration_ms": round(duration_s * 1000),
    }


def dispatch(
    prompt: str,
    *,
    mode: str = "explore",
    skill: str | None = None,
    model: str | None = None,
    backend: str | None = None,
    directory: str = ".",
    json_output: bool = False,
) -> dict:
    """Dispatch a task to the appropriate backend.

    Returns:
        dict with keys: success (bool), output (str), backend (str), duration_s (float).
    """
    start = time.perf_counter()

    resolved_backend, resolved_model, auto = _resolve_mode(
        mode=mode, model=model, backend=backend,
    )

    # Skill mode: validate recipe exists
    recipe_path: str | None = None
    if mode == "skill" and not skill:
        elapsed = time.perf_counter() - start
        return {
            "success": False,
            "output": "skill mode requires a 'skill' name (pass skill='...')",
            "backend": resolved_backend,
            "duration_s": round(elapsed, 2),
        }
    if skill:
        rp = Path.home() / f"germline/membrane/receptors/{skill}/recipe.yaml"
        if not rp.exists():
            elapsed = time.perf_counter() - start
            return {
                "success": False,
                "output": f"skill '{skill}' not found (no recipe.yaml at {rp})",
                "backend": resolved_backend,
                "duration_s": round(elapsed, 2),
            }
        recipe_path = str(rp)
        if not prompt:
            prompt = f"Execute the {skill} skill."

    # Inject coaching notes
    prompt = _inject_coaching(prompt)

    # Safe mode: prepend read-only guard
    if mode == "safe":
        prompt = "READ ONLY. Do not create, modify, or delete any files. " + prompt

    # Explore mode: try direct API first (cheapest path)
    use_direct = mode == "explore" and not backend
    if use_direct:
        ctx = _read_dir_context(directory)
        full_prompt = (ctx + "\n\n" + prompt) if ctx else prompt
        cache_key = _cache_key(full_prompt, resolved_model.lower())

        # Check cache before API call
        cached = _cache_get(cache_key)
        if cached is not None:
            elapsed = time.perf_counter() - start
            if json_output:
                return {
                    "success": True,
                    "output": json.dumps(_explore_structured(
                        cached["output"], prompt, resolved_model, elapsed, cached=True,
                    )),
                    "backend": "direct (cached)",
                    "duration_s": round(elapsed, 2),
                }
            return {
                "success": True,
                "output": cached["output"],
                "backend": "direct (cached)",
                "duration_s": round(elapsed, 2),
            }

        api_result = _direct_api(full_prompt, resolved_model.lower())
        if api_result["success"]:
            _cache_put(cache_key, {"output": api_result["output"]})
            elapsed = time.perf_counter() - start
            if json_output:
                return {
                    "success": True,
                    "output": json.dumps(_explore_structured(
                        api_result["output"], prompt, resolved_model, elapsed,
                    )),
                    "backend": "direct",
                    "duration_s": round(elapsed, 2),
                }
            return {
                "success": True,
                "output": api_result["output"],
                "backend": "direct",
                "duration_s": round(elapsed, 2),
            }

    # Execute via goose or droid
    env = {**os.environ, "GOOGLE_API_KEY": "", "GEMINI_API_KEY": ""}

    if resolved_backend == "goose":
        cmd = _build_goose_cmd(resolved_model, prompt, recipe=recipe_path)
        try:
            rc, stdout_text = _run_captured(cmd, env=env, cwd=directory)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return {
                "success": False,
                "output": f"goose execution failed: {e}",
                "backend": "goose",
                "duration_s": round(elapsed, 2),
            }

        if rc == 0:
            elapsed = time.perf_counter() - start
            return {
                "success": True,
                "output": stdout_text,
                "backend": "goose",
                "duration_s": round(elapsed, 2),
            }

        # Fallback to droid on goose failure (unless user forced backend)
        if not backend:
            droid_cmd = _build_droid_cmd(resolved_model, directory, prompt, auto)
            rc2, stdout_text = _run_captured(droid_cmd)
            elapsed = time.perf_counter() - start
            return {
                "success": rc2 == 0,
                "output": stdout_text,
                "backend": "droid",
                "duration_s": round(elapsed, 2),
            }

        elapsed = time.perf_counter() - start
        return {
            "success": False,
            "output": stdout_text,
            "backend": "goose",
            "duration_s": round(elapsed, 2),
        }

    else:  # droid
        cmd = _build_droid_cmd(resolved_model, directory, prompt, auto)
        try:
            rc, stdout_text = _run_captured(cmd)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return {
                "success": False,
                "output": f"droid execution failed: {e}",
                "backend": "droid",
                "duration_s": round(elapsed, 2),
            }

        elapsed = time.perf_counter() - start
        return {
            "success": rc == 0,
            "output": stdout_text,
            "backend": "droid",
            "duration_s": round(elapsed, 2),
        }


# ---------------------------------------------------------------------------
# Eval — sortase trace analysis
# ---------------------------------------------------------------------------


def run_eval(count: int = 20, failures_only: bool = False) -> dict:
    """Analyze sortase traces. Returns structured summary.

    Returns:
        dict with keys: success (bool), output (str), duration_s (float).
    """
    start = time.perf_counter()

    if not SORTASE_LOG.exists():
        return {
            "success": False,
            "output": "no sortase log found",
            "duration_s": round(time.perf_counter() - start, 2),
        }

    traces: list[dict] = []
    with open(SORTASE_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    traces.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    traces = traces[-count:]
    total = len(traces)
    if total == 0:
        elapsed = time.perf_counter() - start
        return {
            "success": True,
            "output": "no traces found in log",
            "duration_s": round(elapsed, 2),
        }

    success = sum(1 for t in traces if t.get("success"))
    fail = total - success

    lines: list[str] = [
        f"Sortase traces: {total} | Success: {success} ({success/total*100:.0f}%) | Fail: {fail}",
        "",
    ]

    tools = Counter(t.get("tool", "?") for t in traces)
    for tool_name, n in tools.most_common():
        ts = sum(1 for t in traces if t.get("tool") == tool_name and t.get("success"))
        lines.append(f"  {tool_name}: {ts}/{n} ({ts/n*100:.0f}%)")
    lines.append("")

    reasons = Counter(
        t.get("failure_reason", "unknown") for t in traces if not t.get("success")
    )
    if reasons:
        lines.append("Failure reasons:")
        for reason, n in reasons.most_common():
            lines.append(f"  {reason}: {n}")
        lines.append("")

    if failures_only or fail > 0:
        failed = [t for t in traces if not t.get("success")]
        if failed:
            lines.append("Failed traces:")
            for t in failed:
                lines.append(
                    f"  [{t.get('tool', '?')}] {t.get('plan', '?')} — "
                    f"{t.get('failure_reason', '?')} ({t.get('duration_s', 0):.0f}s)"
                )

    elapsed = time.perf_counter() - start
    return {
        "success": True,
        "output": "\n".join(lines),
        "duration_s": round(elapsed, 2),
    }


# ---------------------------------------------------------------------------
# Dispatch stats — golem run analysis
# ---------------------------------------------------------------------------


def dispatch_stats(count: int = 50) -> dict:
    """Analyze golem runs from golem.jsonl. Returns structured summary.

    Returns:
        dict with keys: success (bool), output (str), duration_s (float).
    """
    start = time.perf_counter()

    if not GOLEM_LOG.exists():
        return {
            "success": False,
            "output": "no golem log found",
            "duration_s": round(time.perf_counter() - start, 2),
        }

    entries: list[dict] = []
    with open(GOLEM_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    entries = entries[-count:]
    total = len(entries)
    if total == 0:
        elapsed = time.perf_counter() - start
        return {
            "success": True,
            "output": "no entries found in log",
            "duration_s": round(elapsed, 2),
        }

    # Overall stats
    success_count = sum(1 for e in entries if e.get("exit") == 0)
    fail_count = total - success_count
    success_rate = (success_count / total * 100) if total > 0 else 0

    # Provider breakdown
    provider_counts: Counter = Counter(e.get("provider", "none") for e in entries)
    provider_success: dict[str, int] = {}
    for provider in provider_counts:
        provider_success[provider] = sum(
            1 for e in entries
            if e.get("provider") == provider and e.get("exit") == 0
        )

    # Duration stats
    durations = [e.get("duration", 0) for e in entries]
    avg_duration = sum(durations) / len(durations) if durations else 0
    total_duration = sum(durations)

    # Turn stats
    turns = [e.get("turns", 0) for e in entries]
    avg_turns = sum(turns) / len(turns) if turns else 0

    lines: list[str] = [
        f"Golem runs: {total} | Success: {success_count} ({success_rate:.0f}%) | Fail: {fail_count}",
        f"Duration: total={total_duration:.0f}s, avg={avg_duration:.0f}s | Turns: avg={avg_turns:.1f}",
        "",
        "By provider:",
    ]

    for provider, n in provider_counts.most_common():
        s = provider_success.get(provider, 0)
        rate = (s / n * 100) if n > 0 else 0
        limit = PROVIDER_LIMITS.get(provider, "?")
        lines.append(f"  {provider}: {s}/{n} ({rate:.0f}%) [limit={limit}]")

    # Recent failures
    recent_failures = [e for e in entries if e.get("exit") != 0]
    if recent_failures:
        lines.append("")
        lines.append("Recent failures:")
        for e in recent_failures[-5:]:  # Show last 5 failures
            prompt_preview = e.get("prompt", "?")[:50]
            lines.append(
                f"  [{e.get('provider', '?')}] ({e.get('duration', 0)}s) {prompt_preview}..."
            )

    elapsed = time.perf_counter() - start
    return {
        "success": True,
        "output": "\n".join(lines),
        "duration_s": round(elapsed, 2),
        "stats": {
            "total": total,
            "success": success_count,
            "fail": fail_count,
            "success_rate": success_rate,
            "providers": dict(provider_counts),
            "provider_success": provider_success,
            "avg_duration": avg_duration,
            "avg_turns": avg_turns,
        },
    }
