from __future__ import annotations

"""Symbiont — shared LLM dispatch. Single source of truth for multi-model queries.

The endosymbiont interface: deterministic routing to external LLM models.
No judgment here — just transport.

Config: ~/.config/llm-models.json
Usage:
    from metabolon.symbiont import transduce, parallel_query, list_models
    result = transduce("gemini", "What is 2+2?")
    results = parallel_query(["gemini", "claude"], "What is 2+2?")
"""


import concurrent.futures
import json
import os
import re
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".config" / "llm-models.json"
DEFAULT_TIMEOUT = 180
TimeoutSpec = int | dict[str, int] | None


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def restore_symbionts(config_path: str | None = None) -> dict:
    """Load model registry from JSON config."""
    path = config_path or CONFIG_PATH
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def available_symbionts(config_path: str | None = None) -> dict[str, str]:
    """Return {name: description} for all registered models."""
    models = restore_symbionts(config_path)
    return {name: cfg.get("description", name) for name, cfg in models.items()}


def _resolve_model_timeout(
    model_name: str, model_config: dict[str, Any], timeout: TimeoutSpec
) -> int:
    if isinstance(timeout, dict):
        if model_name in timeout:
            return timeout[model_name]
        if "default" in timeout:
            return timeout["default"]
        if "*" in timeout:
            return timeout["*"]
        if "timeout" in model_config:
            return int(model_config["timeout"])
        return DEFAULT_TIMEOUT
    if timeout is None:
        if "timeout" in model_config:
            return int(model_config["timeout"])
        return DEFAULT_TIMEOUT
    return timeout


def _load_model_config(
    model_name: str, config_path: str | None = None
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    models = restore_symbionts(config_path)
    if model_name not in models:
        raise ValueError(f"Unknown model: {model_name}. Available: {', '.join(models.keys())}")
    return models, models[model_name]


def _query_cmd(cmd: list[str], prompt: str, timeout: int) -> str:
    """Run a CLI command with prompt. Kills the entire process group on timeout."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    proc = subprocess.Popen(
        [*cmd, prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as err:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            proc.kill()
        proc.wait()
        raise subprocess.TimeoutExpired(cmd, timeout) from err
    return _strip_ansi(stdout.strip() or stderr.strip())


def _query_codex(cmd: list[str], prompt: str, timeout: int) -> str:
    """Run codex CLI with output file. Kills the entire process group on timeout."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        full_cmd = [*cmd, "-o", tmp_path, prompt]
        proc = subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            start_new_session=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as err:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                proc.kill()
            proc.wait()
            raise subprocess.TimeoutExpired(full_cmd, timeout) from err
        output = ""
        if tmp_path.exists():
            with open(tmp_path, encoding="utf-8") as f:
                output = f.read().strip()
        if not output:
            output = stdout.strip() or stderr.strip()
        return _strip_ansi(output)
    finally:
        tmp_path.unlink(missing_ok=True)


def transduce(
    model_name: str,
    prompt: str,
    timeout: TimeoutSpec = DEFAULT_TIMEOUT,
    config_path: str | None = None,
) -> str:
    """Query a single model. Returns response text. Raises on error."""
    _, cfg = _load_model_config(model_name, config_path)
    resolved_timeout = _resolve_model_timeout(model_name, cfg, timeout)
    backend = cfg["backend"]

    if backend == "cmd":
        return _query_cmd(cfg["cmd"], prompt, resolved_timeout)
    elif backend == "codex":
        return _query_codex(cfg["cmd"], prompt, resolved_timeout)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def transduce_safe(
    model_name: str,
    prompt: str,
    timeout: TimeoutSpec = DEFAULT_TIMEOUT,
    config_path: str | None = None,
) -> tuple[str, str]:
    """Query with error-as-string. Returns (model_name, result_or_error). Never raises."""
    outcome = _capture_transduction(model_name, prompt, timeout, config_path)
    return model_name, outcome["content"]


def _capture_transduction(
    model_name: str,
    prompt: str,
    timeout: TimeoutSpec = DEFAULT_TIMEOUT,
    config_path: str | None = None,
) -> dict[str, Any]:
    """Capture per-model outcome without letting one failure abort the quorum."""
    resolved_timeout = None
    try:
        _, model_config = _load_model_config(model_name, config_path)
        resolved_timeout = _resolve_model_timeout(model_name, model_config, timeout)
        result = transduce(model_name, prompt, resolved_timeout, config_path)
        return {
            "model": model_name,
            "ok": True,
            "content": result,
            "error": None,
            "error_type": None,
            "timeout": resolved_timeout,
        }
    except subprocess.TimeoutExpired:
        return {
            "model": model_name,
            "ok": False,
            "content": f"(timed out after {resolved_timeout}s)",
            "error": f"timed out after {resolved_timeout}s",
            "error_type": "timeout",
            "timeout": resolved_timeout,
        }
    except FileNotFoundError as error:
        return {
            "model": model_name,
            "ok": False,
            "content": f"(error: command not found — {error})",
            "error": str(error),
            "error_type": "command_not_found",
            "timeout": resolved_timeout,
        }
    except Exception as error:
        return {
            "model": model_name,
            "ok": False,
            "content": f"(error: {error})",
            "error": str(error),
            "error_type": type(error).__name__,
            "timeout": resolved_timeout,
        }


def parallel_query(
    model_names: list[str],
    prompt: str,
    timeout: TimeoutSpec = DEFAULT_TIMEOUT,
    config_path: str | None = None,
) -> list[dict[str, Any]]:
    """Query multiple models in parallel with per-model timeout/error capture."""
    if not model_names:
        return []

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(model_names)) as pool:
        futures = {
            pool.submit(_capture_transduction, name, prompt, timeout, config_path): name
            for name in model_names
        }
        for future in concurrent.futures.as_completed(futures):
            model_name = futures[future]
            try:
                results.append(future.result())
            except Exception as error:
                results.append(
                    {
                        "model": model_name,
                        "ok": False,
                        "content": f"(collector error: {error})",
                        "error": str(error),
                        "error_type": type(error).__name__,
                        "timeout": None,
                    }
                )
    return results


def parallel_transduce(
    model_names: list[str],
    prompt: str,
    timeout: TimeoutSpec = DEFAULT_TIMEOUT,
    config_path: str | None = None,
) -> list[tuple[str, str]]:
    """Query multiple models in parallel. Returns [(model_name, result_or_error)]."""
    return [
        (outcome["model"], outcome["content"])
        for outcome in parallel_query(model_names, prompt, timeout, config_path)
    ]


def parallel_transduce_multi(
    tasks: list[tuple[str, str]],
    timeout: TimeoutSpec = DEFAULT_TIMEOUT,
    config_path: str | None = None,
) -> list[tuple[str, str]]:
    """Query multiple models with per-model prompts in parallel.

    Args:
        tasks: list of (model_name, prompt) tuples
    Returns: [(model_name, result_or_error)]
    """
    if not tasks:
        return []

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        futures = {
            pool.submit(_capture_transduction, name, prompt, timeout, config_path): name
            for name, prompt in tasks
        }
        for future in concurrent.futures.as_completed(futures):
            model_name = futures[future]
            try:
                outcome = future.result()
            except Exception as error:
                outcome = {
                    "model": model_name,
                    "content": f"(collector error: {error})",
                }
            results.append((outcome["model"], outcome["content"]))
    return results
