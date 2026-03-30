from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from metabolon.sortase.decompose import TaskSpec

DEFAULT_TIMEOUT_SEC = 600
STATUS_PATH = Path.home() / ".local" / "share" / "sortase" / "status.json"
COACHING_NOTES = Path.home() / "epigenome" / "marks" / "feedback_glm_coaching.md"


def _prepend_coaching(prompt: str, tool: str) -> str:
    """Prepend coaching notes for weaker models. Deterministic — no LLM needed."""
    if tool not in ("goose", "opencode", "cc-glm", "droid", "crush") or not COACHING_NOTES.exists():
        return prompt
    try:
        notes = COACHING_NOTES.read_text(encoding="utf-8")
        # Strip YAML frontmatter
        if notes.startswith("---"):
            _, _, notes = notes.split("---", 2)
        return f"{notes.strip()}\n\n---\n\n{prompt}"
    except Exception:
        return prompt


TOOL_COMMANDS: dict[str, Callable[[Path, str], list[str]]] = {
    "gemini": lambda project, prompt: [
        "gemini",
        "-m",
        "gemini-3.1-pro-preview",
        "-p",
        prompt,
        "--yolo",
    ],
    "codex": lambda project, prompt: [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--sandbox",
        "danger-full-access",
        "--full-auto",
        prompt,
    ],
    "goose": lambda project, prompt: [
        "translocon",
        "--backend", "goose",
        "--build",
        str(project),
        prompt,
    ],
    "opencode": lambda project, prompt: [
        "opencode",
        "run",
        "--print-logs",
        "--log-level", "INFO",
        "--dir", str(project),
        prompt,
    ],
    "cc-glm": lambda project, prompt: [
        "claude",
        "--print",
        "--bare",
        "--max-turns", "20",
        "-p", prompt,
    ],
    "droid": lambda project, prompt: [
        "translocon",
        "--backend", "droid",
        "--build",
        str(project),
        prompt,
    ],
    "crush": lambda project, prompt: [
        "crush",
        "run",
        "--quiet",
        "--model", "zhipu-coding/glm-5",
        "--cwd", str(project),
        prompt,
    ],
}

FALLBACK_ORDER = ["goose", "droid", "gemini", "codex"]


@dataclass(frozen=True)
class ExecutionAttempt:
    tool: str
    exit_code: int
    duration_s: float
    output: str
    failure_reason: str | None = None
    cost_estimate: str = ""


# ── cost estimation ──────────────────────────────────────────

FLAT_RATE_TOOLS = {"goose", "droid", "cc-glm", "crush"}

# Approximate per-token pricing (USD) for non-flat-rate backends.
# Sourced from public pricing pages as of 2025-06.
TOKEN_PRICING: dict[str, dict[str, float]] = {
    "gemini": {"input_per_million": 1.25, "output_per_million": 10.00},
    "codex": {"input_per_million": 0.00, "output_per_million": 0.00},  # free tier
    "opencode": {"input_per_million": 0.00, "output_per_million": 0.00},  # varies by model
}


def estimate_cost(tool: str, prompt: str, output: str) -> str:
    """Estimate API cost for a single execution attempt.

    For ZhiPu coding-plan backends (goose, droid, cc-glm, crush) the cost
    is covered by a flat-rate subscription so the estimate is "$0.00 (flat-rate)".

    For others, approximate input tokens as ``len(prompt) // 4`` and output
    tokens as ``len(output) // 4``, then apply per-million-token pricing.

    Returns a human-readable string like "$0.0023" or "$0.00 (flat-rate)".
    """
    if tool in FLAT_RATE_TOOLS:
        return "$0.00 (flat-rate)"

    pricing = TOKEN_PRICING.get(tool)
    if pricing is None:
        return "$0.00 (unknown pricing)"

    approx_input_tokens = max(1, len(prompt)) // 4
    approx_output_tokens = max(1, len(output)) // 4

    input_cost = approx_input_tokens * pricing["input_per_million"] / 1_000_000
    output_cost = approx_output_tokens * pricing["output_per_million"] / 1_000_000
    total = input_cost + output_cost
    return f"${total:.4f}"


@dataclass(frozen=True)
class TaskExecutionResult:
    task_name: str
    tool: str
    prompt_file: str | None
    success: bool
    attempts: list[ExecutionAttempt] = field(default_factory=list)
    output: str = ""
    fallbacks: list[str] = field(default_factory=list)
    cost_estimate: str = ""


def _clean_env(tool: str) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    if tool in ("goose", "droid"):
        # translocon handles env vars internally
        pass
    if tool == "cc-glm":
        # Headless CC with GLM-5.1 via ZhiPu Coding Plan Anthropic-compat endpoint
        env["ANTHROPIC_API_KEY"] = env.get("ZHIPU_API_KEY", "")
        env["ANTHROPIC_BASE_URL"] = "https://open.bigmodel.cn/api/anthropic"
        env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = "glm-5.1"
        env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = "glm-5.1"
    return env


def classify_failure(exit_code: int, output: str) -> str | None:
    if exit_code == 0:
        return None
    lowered = output.lower()
    if "429" in lowered or "quota" in lowered:
        return "quota"
    if "身份验证" in output:
        return "auth"
    if "operation not permitted" in lowered:
        return "sandbox"
    return "process-error"


def _tool_chain(initial_tool: str) -> list[str]:
    ordered = [initial_tool]
    ordered.extend(tool for tool in FALLBACK_ORDER if tool != initial_tool)
    return ordered


def _status_path() -> Path:
    override = os.environ.get("OPIFEX_STATUS_PATH")
    return Path(override) if override else STATUS_PATH


def _read_status_entries() -> list[dict]:
    path = _status_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _write_status_entries(entries: list[dict]) -> None:
    path = _status_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def _locked_status_update(fn: "Callable[[list[dict]], list[dict]]") -> None:
    """Atomically read-modify-write status.json with file locking."""
    import fcntl

    path = _status_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.parent / "status.lock"
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            entries = _read_status_entries()
            entries = fn(entries)
            _write_status_entries(entries)
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def register_running(task_name: str, tool: str, project_dir: Path) -> None:
    def _add(entries: list[dict]) -> list[dict]:
        entries.append(
            {
                "task_name": task_name,
                "tool": tool,
                "project_dir": str(project_dir),
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "pid": os.getpid(),
            }
        )
        return entries
    _locked_status_update(_add)


def unregister_running(task_name: str, project_dir: Path) -> None:
    def _remove(entries: list[dict]) -> list[dict]:
        return [
            entry
            for entry in entries
            if not (entry.get("task_name") == task_name and entry.get("project_dir") == str(project_dir))
        ]
    _locked_status_update(_remove)


def list_running() -> list[dict]:
    return _read_status_entries()


async def _run_command(
    tool: str,
    project_dir: Path,
    prompt: str,
    timeout_sec: int,
    task_name: str = "",
    verbose: bool = False,
    dry_run: bool = False,
    coaching: bool = True,
) -> ExecutionAttempt:
    if coaching:
        prompt = _prepend_coaching(prompt, tool)
    if dry_run:
        prompt = (
            "DRY RUN MODE: Explain exactly what files you would edit and what changes you would make, "
            "but do NOT actually edit, create, or delete any files. "
            "Format as a numbered list of changes.\n\n" + prompt
        )
    command = TOOL_COMMANDS[tool](project_dir, prompt)

    started = asyncio.get_running_loop().time()
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(project_dir),
        env=_clean_env(tool),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        chunks: list[bytes] = []
        assert process.stdout is not None
        while True:
            chunk = await asyncio.wait_for(
                process.stdout.read(4096),
                timeout=timeout_sec - (asyncio.get_running_loop().time() - started),
            )
            if not chunk:
                break
            chunks.append(chunk)
            if verbose and sys.stderr.isatty():
                line = chunk.decode("utf-8", errors="replace")
                prefix = f"[{task_name or tool}] " if task_name else f"[{tool}] "
                for text_line in line.splitlines(keepends=True):
                    sys.stderr.write(f"\033[2m{prefix}{text_line}\033[0m")
                    if not text_line.endswith("\n"):
                        sys.stderr.write("\n")
                sys.stderr.flush()
            elif verbose:
                # Non-TTY: write without ANSI escapes
                line = chunk.decode("utf-8", errors="replace")
                prefix = f"[{task_name or tool}] " if task_name else f"[{tool}] "
                for text_line in line.splitlines(keepends=True):
                    sys.stderr.write(f"{prefix}{text_line}")
                    if not text_line.endswith("\n"):
                        sys.stderr.write("\n")
                sys.stderr.flush()
        await process.wait()
        output = b"".join(chunks).decode("utf-8", errors="replace")
        exit_code = process.returncode
    except TimeoutError:
        process.kill()
        await process.communicate()
        output = f"{tool} timed out after {timeout_sec} seconds"
        exit_code = 124

    duration_s = asyncio.get_running_loop().time() - started
    return ExecutionAttempt(
        tool=tool,
        exit_code=exit_code,
        duration_s=round(duration_s, 3),
        output=output,
        failure_reason=classify_failure(exit_code, output),
        cost_estimate=estimate_cost(tool, prompt, output),
    )


def _emit_completion_signal(result: TaskExecutionResult) -> None:
    """Emit a demethylase signal when a task finishes."""
    try:
        sys.path.insert(0, str(Path.home() / "germline"))
        from metabolon.organelles.demethylase import emit_signal

        status = "success" if result.success else "failed"
        summary = result.output[-500:] if result.output else "no output"
        emit_signal(
            name=f"sortase-{result.task_name}",
            content=f"Task: {result.task_name}\nTool: {result.tool}\nStatus: {status}\n\n{summary}",
            source=result.tool,
        )
    except Exception:
        pass  # Signal emission is best-effort — never block execution


def _analyze_for_coaching(result: TaskExecutionResult) -> None:
    """Extract coaching patterns from failed or sketchy output. Best-effort."""
    if result.success and len(result.output) < 100:
        return  # Trivial success, nothing to learn

    try:
        import shutil

        channel_bin = shutil.which("channel")
        if not channel_bin:
            return

        # Truncate output to last 2000 chars to stay within token budget
        output_sample = result.output[-2000:] if result.output else ""
        if not output_sample.strip():
            return

        prompt = (
            "You are reviewing output from a GLM-5.1 coding agent. "
            "Identify any failure patterns that should be added to coaching notes. "
            "Known patterns: import hallucination, return type flattening, verbose descriptions, "
            "list output rendering (str(dict)), file indirection fails. "
            f"Task: {result.task_name}, Tool: {result.tool}, Success: {result.success}\n\n"
            f"Output:\n{output_sample}\n\n"
            "If you find a NEW pattern not listed above, output it in this format:\n"
            "### Pattern name\nGLM does X.\n**Fix:** \"Instruction to avoid X.\"\n\n"
            "If no new patterns found, output exactly: NO_NEW_PATTERNS"
        )

        proc = subprocess.run(
            [channel_bin, "--max-tokens", "500", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=60,
            env=_clean_env("gemini"),  # Use Gemini for analysis
        )

        if proc.returncode != 0 or "NO_NEW_PATTERNS" in proc.stdout:
            return

        # Append to coaching notes
        coaching_path = COACHING_NOTES
        if coaching_path.exists():
            existing = coaching_path.read_text(encoding="utf-8")
            if proc.stdout.strip() not in existing:  # Deduplicate
                from datetime import datetime as _dt
                timestamp = _dt.now().strftime("%Y-%m-%d %H:%M")
                with open(coaching_path, "a", encoding="utf-8") as f:
                    f.write(f"\n<!-- auto-detected {timestamp} -->\n{proc.stdout.strip()}\n")
    except Exception:
        pass  # Best-effort — never block execution


async def execute_task(
    task: TaskSpec,
    project_dir: Path,
    initial_tool: str,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
    verbose: bool = False,
    dry_run: bool = False,
    max_retries: int = 0,
    coaching: bool = True,
) -> TaskExecutionResult:
    register_running(task.name, initial_tool, project_dir)
    attempts: list[ExecutionAttempt] = []
    fallbacks: list[str] = []

    try:
        for _retry in range(max_retries + 1):
            attempts = []
            fallbacks = []
            for index, tool in enumerate(_tool_chain(initial_tool)):
                if index > 0:
                    fallbacks.append(tool)
                attempt = await _run_command(
                    tool, project_dir, task.spec, timeout_sec,
                    task_name=task.name, verbose=verbose, dry_run=dry_run,
                    coaching=coaching,
                )
                attempts.append(attempt)
                if attempt.exit_code == 0 and not attempt.failure_reason:
                    result = TaskExecutionResult(
                        task_name=task.name,
                        tool=tool,
                        prompt_file=task.temp_file,
                        success=True,
                        attempts=attempts,
                        output=attempt.output,
                        fallbacks=fallbacks,
                        cost_estimate=attempt.cost_estimate,
                    )
                    _emit_completion_signal(result)
                    _analyze_for_coaching(result)
                    return result
            # All backends failed — retry if retries remain
        last = attempts[-1]
        result = TaskExecutionResult(
            task_name=task.name,
            tool=last.tool,
            prompt_file=task.temp_file,
            success=False,
            attempts=attempts,
            output=last.output,
            fallbacks=fallbacks,
            cost_estimate=last.cost_estimate,
        )
        _emit_completion_signal(result)
        _analyze_for_coaching(result)
        return result
    finally:
        unregister_running(task.name, project_dir)


def _is_git_repo(project_dir: Path) -> bool:
    return (project_dir / ".git").exists()


def _create_worktree(project_dir: Path, task_name: str) -> Path:
    """Create a temporary git worktree for isolated parallel execution."""
    branch = f"sortase/{task_name}-{uuid.uuid4().hex[:8]}"
    worktree_path = Path(f"/tmp/sortase-{task_name}-{uuid.uuid4().hex[:8]}")
    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(worktree_path)],
        cwd=project_dir,
        capture_output=True,
        check=True,
    )
    return worktree_path


def _merge_worktree(project_dir: Path, worktree_path: Path) -> tuple[bool, str]:
    """Merge worktree branch back into current branch and clean up."""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    branch = None
    found_path = False
    resolved_wt = str(worktree_path.resolve())
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            wt_path = line[len("worktree "):]
            found_path = Path(wt_path).resolve() == Path(resolved_wt)
        if found_path and line.startswith("branch refs/heads/"):
            branch = line[len("branch refs/heads/"):]
            break

    if not branch:
        return False, f"Could not find branch for worktree {worktree_path}"

    diff = subprocess.run(
        ["git", "diff", "--stat", f"HEAD...{branch}"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if not diff.stdout.strip():
        _remove_worktree(project_dir, worktree_path, branch)
        return True, "no changes"

    merge = subprocess.run(
        ["git", "merge", "--no-ff", "-m", f"sortase: merge {branch}", branch],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    _remove_worktree(project_dir, worktree_path, branch)

    if merge.returncode != 0:
        return False, merge.stderr
    return True, diff.stdout.strip()


def _remove_worktree(project_dir: Path, worktree_path: Path, branch: str) -> None:
    """Remove worktree and its branch."""
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(worktree_path)],
        cwd=project_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "branch", "-D", branch],
        cwd=project_dir,
        capture_output=True,
    )


async def execute_tasks(
    tasks: list[TaskSpec],
    project_dir: Path,
    tool_by_task: dict[str, str],
    serial: bool = False,
    isolate: bool = True,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
    verbose: bool = False,
    dry_run: bool = False,
    max_retries: int = 0,
    coaching: bool = True,
) -> list[TaskExecutionResult]:
    if serial:
        results: list[TaskExecutionResult] = []
        for task in tasks:
            results.append(await execute_task(task, project_dir, tool_by_task[task.name], timeout_sec=timeout_sec, verbose=verbose, dry_run=dry_run, max_retries=max_retries, coaching=coaching))
        return results

    use_worktrees = isolate and _is_git_repo(project_dir) and len(tasks) > 1

    worktree_map: dict[str, Path] = {}
    if use_worktrees:
        for task in tasks:
            worktree_map[task.name] = _create_worktree(project_dir, task.name)

    coroutines = [
        execute_task(
            task,
            worktree_map.get(task.name, project_dir),
            tool_by_task[task.name],
            timeout_sec=timeout_sec,
            verbose=verbose,
            dry_run=dry_run,
            max_retries=max_retries,
            coaching=coaching,
        )
        for task in tasks
    ]
    results = list(await asyncio.gather(*coroutines))

    if use_worktrees:
        for task in tasks:
            wt = worktree_map.get(task.name)
            if not wt:
                continue
            task_result = next((r for r in results if r.task_name == task.name), None)
            if task_result and task_result.success:
                _merge_worktree(project_dir, wt)
            else:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(wt)],
                    cwd=project_dir,
                    capture_output=True,
                )

    return results


def summarize_results(results: list[TaskExecutionResult]) -> dict[str, object]:
    changed_prompt_files = [result.prompt_file for result in results if result.prompt_file]
    return {
        "tasks": len(results),
        "successful": sum(1 for result in results if result.success),
        "failed": sum(1 for result in results if not result.success),
        "prompt_files": changed_prompt_files,
        "fallbacks": sum(len(result.fallbacks) for result in results),
    }
