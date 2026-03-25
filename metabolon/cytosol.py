"""Shared helpers for invoking external CLI organelles and LLM calls from tools."""

import os
import shutil
import subprocess
from pathlib import Path

# Repo root: metabolon → src → vivesca
VIVESCA_ROOT = Path(__file__).resolve().parent.parent


def invoke_organelle(
    binary: str,
    args: list[str],
    timeout: int = 30,
    stdin_text: str | None = None,
) -> str:
    """Invoke an external CLI organelle, return stdout, raise ValueError on failure."""
    path = os.path.expanduser(binary)
    # Resolve via PATH if not an absolute/relative path
    if os.sep not in path:
        resolved = shutil.which(path)
        if resolved:
            path = resolved
    try:
        result = subprocess.run(
            [path, *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            input=stdin_text,
        )
        return result.stdout.strip() or "Done."
    except FileNotFoundError as exc:
        raise ValueError(f"Binary not found: {path}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"{os.path.basename(path)} timed out ({timeout}s)") from exc
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() or str(e)
        raise ValueError(f"{os.path.basename(path)} error: {error_msg}") from e


# -- LLM-as-tool: predictable transformations via LLM runtime ------------
# For tool-shaped work (extraction, classification, format conversion)
# where the transformation is predictable but an LLM is the cheapest
# runtime. NOT for judgment -- that belongs in skills.
#
# Backend and model are resolved by synthase from ~/.config/vivesca/config.yaml.
# Pass backend/model overrides here to forward them as CLI flags.


def synthesize(
    prompt: str,
    backend: str | None = None,
    model: str | None = None,
    timeout: int = 60,
) -> str:
    """Call an LLM for a predictable transformation. Returns text output.

    Shells out to synthase, which reads backend/model from vivesca config.
    Pass backend/model to override config for this call.

    This is for tool-shaped work: the same input should produce the same
    output every time. If the output depends on shifting context, use a
    skill instead.
    """
    synthase = shutil.which("synthase")
    if not synthase:
        raise ValueError("synthase not found on PATH")

    cmd = [synthase]
    if backend:
        cmd.extend(["--backend", backend])
    if model:
        cmd.extend(["--model", model])
    cmd.extend(["--timeout", str(timeout)])
    cmd.append(prompt)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    output = result.stdout.strip()
    if result.returncode != 0 or not output:
        err = result.stderr.strip() or "no output"
        raise ValueError(f"synthase error: {err}")
    return output


# Deprecated alias -- use synthesize() directly
invoke_symbiont = synthesize
