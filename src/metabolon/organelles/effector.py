"""effector — run CLI binaries from MCP tool handlers."""

import os
import subprocess


def run_cli(
    binary: str,
    args: list[str],
    timeout: int = 30,
    stdin_text: str | None = None,
) -> str:
    """Run a CLI binary, return stdout, raise ValueError on failure."""

    path = os.path.expanduser(binary)
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
        error_msg = (e.stderr or "").strip() or str(e)
        raise ValueError(f"{os.path.basename(path)} error: {error_msg}") from e
