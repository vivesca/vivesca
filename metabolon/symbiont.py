"""Symbiont — shared LLM dispatch. Single source of truth for multi-model queries.

The endosymbiont interface: deterministic routing to external LLM models.
No judgment here — just transport.

Config: ~/.config/llm-models.json
Usage:
    from metabolon.symbiont import transduce, parallel_query, list_models
    result = transduce("deepseek", "What is 2+2?")
    results = parallel_query(["gemini", "deepseek"], "What is 2+2?")
"""

import concurrent.futures
import json
import os
import re
import signal
import subprocess
import tempfile
import urllib.error
import urllib.request

CONFIG_PATH = os.path.expanduser("~/.config/llm-models.json")


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def restore_symbionts(config_path: str | None = None) -> dict:
    """Load model registry from JSON config."""
    path = config_path or CONFIG_PATH
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def available_symbionts(config_path: str | None = None) -> dict[str, str]:
    """Return {name: description} for all registered models."""
    models = restore_symbionts(config_path)
    return {name: cfg.get("description", name) for name, cfg in models.items()}


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
        if os.path.exists(tmp_path):
            with open(tmp_path, encoding="utf-8") as f:
                output = f.read().strip()
        if not output:
            output = stdout.strip() or stderr.strip()
        return _strip_ansi(output)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _query_openrouter(model: str, prompt: str, timeout: int) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/terryli/llm-dispatch",
        "X-Title": "llm-dispatch",
    }
    data = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        res_json = json.loads(response.read().decode("utf-8"))
        return res_json["choices"][0]["message"]["content"].strip()


def transduce(
    model_name: str, prompt: str, timeout: int = 180, config_path: str | None = None
) -> str:
    """Query a single model. Returns response text. Raises on error."""
    models = restore_symbionts(config_path)
    if model_name not in models:
        if model_name.startswith("openrouter/"):
            return _query_openrouter(model_name.split("/", 1)[1], prompt, timeout)
        raise ValueError(f"Unknown model: {model_name}. Available: {', '.join(models.keys())}")

    cfg = models[model_name]
    backend = cfg["backend"]

    if backend == "cmd":
        return _query_cmd(cfg["cmd"], prompt, timeout)
    elif backend == "codex":
        return _query_codex(cfg["cmd"], prompt, timeout)
    elif backend == "openrouter":
        return _query_openrouter(cfg["model"], prompt, timeout)
    else:
        raise ValueError(f"Unknown backend: {backend}")


def transduce_safe(
    model_name: str, prompt: str, timeout: int = 180, config_path: str | None = None
) -> tuple[str, str]:
    """Query with error-as-string. Returns (model_name, result_or_error). Never raises."""
    try:
        result = transduce(model_name, prompt, timeout, config_path)
        return model_name, result
    except subprocess.TimeoutExpired:
        return model_name, f"(timed out after {timeout}s)"
    except FileNotFoundError as e:
        return model_name, f"(error: command not found — {e})"
    except Exception as e:
        return model_name, f"(error: {e})"


def parallel_transduce(
    model_names: list[str],
    prompt: str,
    timeout: int = 180,
    config_path: str | None = None,
) -> list[tuple[str, str]]:
    """Query multiple models in parallel. Returns [(model_name, result_or_error)]."""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(model_names)) as pool:
        futures = {
            pool.submit(transduce_safe, name, prompt, timeout, config_path): name
            for name in model_names
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    return results
