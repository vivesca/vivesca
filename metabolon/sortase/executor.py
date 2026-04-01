from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any
from datetime import datetime
from pathlib import Path

from metabolon.sortase.decompose import TaskSpec

DEFAULT_TIMEOUT_SEC = 600


def _cleanup_temp_specs(tasks: list[TaskSpec]) -> None:
    """Remove temp spec files created by _write_temp_specs."""
    for task in tasks:
        if task.temp_file:
            Path(task.temp_file).unlink(missing_ok=True)

_READ_PATTERN = re.compile(r"\bread\b", re.IGNORECASE)
_SOURCE_FILE_PATTERN = re.compile(r"\b[\w./-]+\.\w{1,4}\b")
_EXACTLY_ONE_PATTERN = re.compile(r"\bexactly\s+1\s+tool\s+call\b", re.IGNORECASE)


def _compute_adaptive_timeout(spec: str, base_timeout: int) -> int:
    """Adjust timeout based on spec characteristics.

    * If the spec is read-heavy (mentions "read" or references source files),
      double the timeout — those tasks need more processing time.
    * If the spec says "EXACTLY 1 tool call", halve the timeout — simple
      tasks finish fast.
    * Read-heavy takes priority over the exact-one heuristic.
    """
    if _READ_PATTERN.search(spec) or _SOURCE_FILE_PATTERN.search(spec):
        return base_timeout * 2
    if _EXACTLY_ONE_PATTERN.search(spec):
        return base_timeout // 2
    return base_timeout
STATUS_PATH = Path.home() / ".local" / "share" / "sortase" / "status.json"
COACHING_NOTES = Path.home() / "epigenome" / "marks" / "feedback_golem_coaching.md"


def _prepend_coaching(prompt: str, tool: str) -> str:
    """Prepend coaching notes for weaker models. Deterministic — no LLM needed.

    Tools routed through translocon (goose, droid) are excluded because
    translocon injects its own coaching via ``_inject_coaching``. Adding it
    here would double-inject, bloating the prompt and confusing the model.
    """
    if tool in ("goose", "droid"):
        return prompt
    if tool not in ("opencode", "golem", "crush", "codex") or not COACHING_NOTES.exists():
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
    "golem": lambda project, prompt: [
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

FLAT_RATE_TOOLS = {"goose", "droid", "golem"}
MODEL_BY_TOOL: dict[str, str | None] = {
    "gemini": "gemini-3-pro-preview",
    "codex": "gpt-5.3-codex",
    "goose": "glm-5.1",
    "opencode": None,
    "golem": "glm-5.1",
    "droid": "glm-5.1",
    "crush": "zhipu-coding/glm-5",
}

# Approximate per-token pricing (USD) for billable backends.
# Gemini 3 Pro Preview pricing is from ai.google.dev/gemini-api/docs/pricing.
# GPT-5.3-Codex pricing is from developers.openai.com/api/docs/models/gpt-5.3-codex.
TOKEN_PRICING: dict[str, dict[str, float]] = {
    "gemini-3-pro-preview": {"input_per_million": 2.00, "output_per_million": 12.00},
    "gpt-5.3-codex": {"input_per_million": 1.75, "output_per_million": 14.00},
}


def estimate_cost(tool: str, prompt: str, output: str) -> str:
    """Estimate API cost for a single execution attempt.

    For ZhiPu coding-plan backends (goose, droid, golem) the cost
    is covered by a flat-rate subscription so the estimate is "$0.00 (flat-rate)".

    For others, approximate input tokens as ``len(prompt) // 4`` and output
    tokens as ``len(output) // 4``, then apply per-million-token pricing.

    Returns a human-readable string like "$0.0023" or "$0.00 (flat-rate)".
    """
    if tool in FLAT_RATE_TOOLS:
        return "$0.00 (flat-rate)"

    model_name = MODEL_BY_TOOL.get(tool)
    pricing = TOKEN_PRICING.get(model_name or "")
    if pricing is None:
        return "$0.00 (unknown pricing)"

    approx_input_tokens = max(1, len(prompt)) // 4
    approx_output_tokens = max(1, len(output)) // 4

    input_cost = approx_input_tokens * pricing["input_per_million"] / 1_000_000
    output_cost = approx_output_tokens * pricing["output_per_million"] / 1_000_000
    total = input_cost + output_cost
    return f"${total:.4f}"


def summarize_cost_estimates(cost_estimates: list[str]) -> str:
    """Aggregate per-task cost strings into one run-level log entry value."""
    if not cost_estimates:
        return "N/A"

    total_cost = Decimal("0")
    saw_flat_rate = False
    saw_unknown_pricing = False

    for cost_estimate in cost_estimates:
        if "flat-rate" in cost_estimate:
            saw_flat_rate = True
            continue
        if "unknown pricing" in cost_estimate:
            saw_unknown_pricing = True
            continue

        matched_amount = re.match(r"^\$(\d+(?:\.\d+)?)$", cost_estimate.strip())
        if not matched_amount:
            saw_unknown_pricing = True
            continue
        try:
            total_cost += Decimal(matched_amount.group(1))
        except InvalidOperation:
            saw_unknown_pricing = True

    if total_cost == 0 and saw_flat_rate and not saw_unknown_pricing:
        return "$0.00 (flat-rate)"
    if total_cost == 0 and saw_unknown_pricing and not saw_flat_rate:
        return "N/A (unknown pricing)"

    summary = f"${total_cost:.4f}"
    notes: list[str] = []
    if saw_flat_rate:
        notes.append("flat-rate backends")
    if saw_unknown_pricing:
        notes.append("unknown-priced backends")
    if notes:
        return f"{summary} (+ {', '.join(notes)})"
    return summary


@dataclass(frozen=True)
class FallbackStep:
    """One step in a fallback chain — tried backend, outcome, and reason."""
    tool: str
    succeeded: bool
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        entry: dict[str, object] = {"tool": self.tool, "succeeded": self.succeeded}
        if self.failure_reason is not None:
            entry["failure_reason"] = self.failure_reason
        return entry


@dataclass(frozen=True)
class TaskExecutionResult:
    task_name: str
    tool: str
    prompt_file: str | None
    success: bool
    attempts: list[ExecutionAttempt] = field(default_factory=list)
    output: str = ""
    fallbacks: list[str] = field(default_factory=list)
    fallback_chain: list[FallbackStep] = field(default_factory=list)
    cost_estimate: str = ""


def _clean_env(tool: str) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    if tool in ("goose", "droid"):
        # translocon handles env vars internally
        pass
    if tool == "golem":
        # Headless CC with GLM via ZhiPu Coding Plan Anthropic-compat endpoint
        # Docs: https://docs.bigmodel.cn/cn/coding-plan/tool/claude
        env["ANTHROPIC_AUTH_TOKEN"] = env.get("ZHIPU_API_KEY", "")
        env["ANTHROPIC_BASE_URL"] = "https://open.bigmodel.cn/api/anthropic"
        env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = "GLM-5.1"
        env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = "GLM-5.1"
        env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = "GLM-4.5-air"
        env["API_TIMEOUT_MS"] = "3000000"
        env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
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


def _validate_backend(tool: str, project_dir: Path, prompt: str) -> None:
    """Check that the backend binary exists before dispatching.

    Extracts the executable name from the tool command and resolves it
    via ``shutil.which``.  Raises ``FileNotFoundError`` with a clear
    message so the caller gets an actionable error instead of a cryptic
    subprocess ``ENOENT``.
    """
    command = TOOL_COMMANDS[tool](project_dir, prompt)
    binary = command[0]
    if not shutil.which(binary):
        raise FileNotFoundError(
            f"Backend binary '{binary}' not found on PATH for tool '{tool}'. "
            f"Install it or check your PATH."
        )


def _status_path() -> Path:
    override = os.environ.get("OPIFEX_STATUS_PATH")
    return Path(override) if override else STATUS_PATH


def _legacy_tombstone(task_name: str) -> str:
    return f"__removed__:{task_name}"


def _read_status_entries() -> list[dict | str]:
    path = _status_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _write_status_entries(entries: list[dict | str]) -> None:
    path = _status_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def _locked_status_update(fn: "Callable[[list[dict | str]], list[dict | str]]") -> None:
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


def register_running(task_name: str, tool: str | None = None, project_dir: Path | None = None) -> None:
    def _add(entries: list[dict | str]) -> list[dict | str]:
        if tool is None or project_dir is None:
            tombstone = _legacy_tombstone(task_name)
            if tombstone in entries:
                entries.remove(tombstone)
                return entries
            entries.append(task_name)
            return entries

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


def unregister_running(task_name: str, project_dir: Path | None = None) -> None:
    def _remove(entries: list[dict | str]) -> list[dict | str]:
        if project_dir is None:
            remaining = [entry for entry in entries if entry != task_name]
            if len(remaining) == len(entries):
                remaining.append(_legacy_tombstone(task_name))
            return remaining

        return [
            entry
            for entry in entries
            if not (
                isinstance(entry, dict)
                and entry.get("task_name") == task_name
                and entry.get("project_dir") == str(project_dir)
            )
        ]
    _locked_status_update(_remove)


def list_running() -> list[dict[str, Any] | str]:
    entries = _read_status_entries()
    for entry in entries:
        if isinstance(entry, dict) and "pid" in entry:
            try:
                os.kill(entry["pid"], 0)  # signal 0 = check liveness
                entry["alive"] = True
            except (ProcessLookupError, PermissionError):
                entry["alive"] = False
    return entries


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
    # For codex: long specs get written to a file and referenced by path.
    # Must happen BEFORE coaching prepend — otherwise coaching drowns the spec.
    if tool == "codex" and len(prompt) > 2000:
        spec_file = Path(tempfile.gettempdir()) / f"sortase-codex-spec-{task_name or 'task'}.md"
        spec_file.write_text(prompt, encoding="utf-8")
        prompt = (
            f"You are working in {project_dir}. "
            f"Read the spec at {spec_file} and execute every step in it. "
            f"Only touch files listed in the spec's 'Files changed' section."
        )
    if coaching:
        prompt = _prepend_coaching(prompt, tool)
    if dry_run:
        prompt = (
            "DRY RUN MODE: Explain exactly what files you would edit and what changes you would make, "
            "but do NOT actually edit, create, or delete any files. "
            "Format as a numbered list of changes.\n\n" + prompt
        )
    _validate_backend(tool, project_dir, prompt)
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
        exit_code = process.returncode or 0
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
    fallback_chain: list[FallbackStep] = []
    effective_timeout = _compute_adaptive_timeout(task.spec, timeout_sec)

    try:
        for retry_index in range(max_retries + 1):
            if retry_index > 0:
                if verbose:
                    retry_label = f"[{task.name}] retry {retry_index}/{max_retries}: resetting git state"
                    sys.stderr.write(f"\033[33m{retry_label}\033[0m\n")
                    sys.stderr.flush()
                _reset_git_state(project_dir, task.name, verbose=verbose)
            attempts = []
            fallbacks = []
            fallback_chain = []
            for index, tool in enumerate(_tool_chain(initial_tool)):
                if index > 0:
                    fallbacks.append(tool)
                attempt = await _run_command(
                    tool, project_dir, task.spec, effective_timeout,
                    task_name=task.name, verbose=verbose, dry_run=dry_run,
                    coaching=coaching,
                )
                # Rate-limit backoff: if 429, wait and retry same backend once
                if attempt.failure_reason == "quota" and index == 0:
                    backoff_sec = 30
                    if verbose:
                        sys.stderr.write(
                            f"\033[33m[{task.name}] 429 rate limit on {tool}, "
                            f"backing off {backoff_sec}s before retry\033[0m\n"
                        )
                        sys.stderr.flush()
                    await asyncio.sleep(backoff_sec)
                    attempt = await _run_command(
                        tool, project_dir, task.spec, effective_timeout,
                        task_name=task.name, verbose=verbose, dry_run=dry_run,
                        coaching=coaching,
                    )
                attempts.append(attempt)
                succeeded = attempt.exit_code == 0 and not attempt.failure_reason
                fallback_chain.append(FallbackStep(
                    tool=tool,
                    succeeded=succeeded,
                    failure_reason=attempt.failure_reason,
                ))
                if succeeded:
                    result = TaskExecutionResult(
                        task_name=task.name,
                        tool=tool,
                        prompt_file=task.temp_file,
                        success=True,
                        attempts=list(attempts),
                        output=attempt.output,
                        fallbacks=list(fallbacks),
                        fallback_chain=list(fallback_chain),
                        cost_estimate=attempt.cost_estimate,
                    )
                    _emit_completion_signal(result)
                    _analyze_for_coaching(result)
                    return result
            # All backends failed — retry if retries remain
            if verbose and retry_index < max_retries:
                sys.stderr.write(
                    f"\033[33m[{task.name}] all backends failed on attempt "
                    f"{retry_index + 1}/{max_retries + 1}, retrying...\033[0m\n"
                )
                sys.stderr.flush()
        last = attempts[-1]
        result = TaskExecutionResult(
            task_name=task.name,
            tool=last.tool,
            prompt_file=task.temp_file,
            success=False,
            attempts=attempts,
            output=last.output,
            fallbacks=fallbacks,
            fallback_chain=fallback_chain,
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
    worktree_path = Path(tempfile.gettempdir()) / f"sortase-{task_name}-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(worktree_path)],
        cwd=project_dir,
        capture_output=True,
        check=True,
    timeout=300,
    )
    # Symlink untracked directories from the original project so backends
    # can find project rules, memory, and Python dependencies.
    for dirname in (".claude", ".venv"):
        source = project_dir / dirname
        target = worktree_path / dirname
        if source.is_dir() and not target.exists():
            target.symlink_to(source)
    return worktree_path


def _merge_worktree(project_dir: Path, worktree_path: Path) -> tuple[bool, str]:
    """Merge worktree branch back into current branch and clean up."""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    timeout=300,
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
    timeout=300,
    )
    if not diff.stdout.strip():
        _remove_worktree(project_dir, worktree_path, branch)
        return True, "no changes"

    # Detect files modified on BOTH branches — silent overwrite risk.
    worktree_changed = subprocess.run(
        ["git", "diff", "--name-only", f"HEAD...{branch}"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    timeout=300,
    )
    main_changed = subprocess.run(
        ["git", "diff", "--name-only", f"{branch}...HEAD"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    timeout=300,
    )
    # Exclude ephemeral files that worktrees recreate (e.g. .venv, .claude)
    _MERGE_EXCLUDES = {".venv", ".claude"}
    worktree_files = set(worktree_changed.stdout.splitlines()) - {""} - _MERGE_EXCLUDES
    main_files = set(main_changed.stdout.splitlines()) - {""} - _MERGE_EXCLUDES
    conflicted = sorted(worktree_files & main_files)

    if conflicted:
        sys.stderr.write(
            f"[sortase] CONFLICT: files modified in both branches, "
            f"aborting merge: {', '.join(conflicted)}\n"
            f"[sortase] Branch '{branch}' preserved for manual recovery.\n"
        )
        # Remove worktree directory but keep the branch so work isn't lost
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=project_dir,
            capture_output=True,
        timeout=300,
        )
        return False, f"conflict: files modified in both branches: {', '.join(conflicted)}. Branch '{branch}' preserved."

    merge = subprocess.run(
        ["git", "merge", "--no-ff", "-m", f"sortase: merge {branch}", branch],
        cwd=project_dir,
        capture_output=True,
        text=True,
    timeout=300,
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
    timeout=300,
    )
    subprocess.run(
        ["git", "branch", "-D", branch],
        cwd=project_dir,
        capture_output=True,
    timeout=300,
    )


def _force_remove_worktree(project_dir: Path, worktree_path: Path) -> None:
    """Remove a worktree by looking up its branch name automatically."""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    timeout=300,
    )
    branch = None
    found_path = False
    resolved_wt = str(worktree_path.resolve())
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            found_path = Path(line[len("worktree "):]).resolve() == Path(resolved_wt)
        if found_path and line.startswith("branch refs/heads/"):
            branch = line[len("branch refs/heads/"):]
            break
    if branch:
        _remove_worktree(project_dir, worktree_path, branch)
    else:
        # Fallback: just force-remove the directory
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=project_dir,
            capture_output=True,
        timeout=300,
        )


def _reset_git_state(project_dir: Path, task_name: str, verbose: bool = False) -> None:
    """Reset git working tree to clean state between retries.

    Discards all uncommitted changes and removes untracked files/directories
    so the next retry starts from a pristine checkout. Skipped on the first
    attempt (retry_index == 0).
    """
    if not _is_git_repo(project_dir):
        return

    # Log which files will be discarded before destroying them
    dirty = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    timeout=300,
    )
    untracked = subprocess.run(
        ["git", "clean", "-nd"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    timeout=300,
    )
    dirty_files = dirty.stdout.strip()
    untracked_files = untracked.stdout.strip()
    if dirty_files:
        sys.stderr.write(f"[{task_name}] Discarding modified files:\n{dirty_files}\n")
    if untracked_files:
        sys.stderr.write(f"[{task_name}] Removing untracked files:\n{untracked_files}\n")

    checkout = subprocess.run(
        ["git", "checkout", "--", "."],
        cwd=project_dir,
        capture_output=True,
        text=True,
    timeout=300,
    )
    if verbose and checkout.returncode != 0:
        sys.stderr.write(f"[{task_name}] git checkout -- . failed: {checkout.stderr}\n")
    clean = subprocess.run(
        ["git", "clean", "-fd"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    timeout=300,
    )
    if verbose and clean.returncode != 0:
        sys.stderr.write(f"[{task_name}] git clean -fd failed: {clean.stderr}\n")


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
    worktree: bool = False,
) -> list[TaskExecutionResult]:
    try:
        if serial:
            results: list[TaskExecutionResult] = []
            for task in tasks:
                if worktree and _is_git_repo(project_dir):
                    wt_path = _create_worktree(project_dir, task.name)
                    try:
                        result = await execute_task(task, wt_path, tool_by_task[task.name], timeout_sec=timeout_sec, verbose=verbose, dry_run=dry_run, max_retries=max_retries, coaching=coaching)
                    except Exception:
                        # On unexpected error, still clean up the worktree
                        _force_remove_worktree(project_dir, wt_path)
                        raise
                    if result.success:
                        _merge_worktree(project_dir, wt_path)
                    else:
                        _force_remove_worktree(project_dir, wt_path)
                    results.append(result)
                else:
                    results.append(await execute_task(task, project_dir, tool_by_task[task.name], timeout_sec=timeout_sec, verbose=verbose, dry_run=dry_run, max_retries=max_retries, coaching=coaching))
            return results

        use_worktrees = (worktree or (isolate and len(tasks) > 1)) and _is_git_repo(project_dir)

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
        raw_results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Convert exceptions into failed TaskExecutionResult so worktree cleanup runs
        results: list[TaskExecutionResult] = []
        for task, raw in zip(tasks, raw_results):
            if isinstance(raw, BaseException):
                results.append(TaskExecutionResult(
                    task_name=task.name,
                    tool=tool_by_task[task.name],
                    prompt_file=task.temp_file,
                    success=False,
                    attempts=[],
                    output=f"Unhandled exception: {raw}",
                    fallbacks=[],
                    fallback_chain=[],
                    cost_estimate="",
                ))
            else:
                results.append(raw)

        if use_worktrees:
            for task in tasks:
                wt = worktree_map.get(task.name)
                if not wt:
                    continue
                task_result = next((r for r in results if r.task_name == task.name), None)
                if task_result and task_result.success:
                    _merge_worktree(project_dir, wt)
                else:
                    _force_remove_worktree(project_dir, wt)

        return results
    finally:
        _cleanup_temp_specs(tasks)


def summarize_results(results: list[TaskExecutionResult]) -> dict[str, object]:
    changed_prompt_files = [result.prompt_file for result in results if result.prompt_file]
    return {
        "tasks": len(results),
        "successful": sum(1 for result in results if result.success),
        "failed": sum(1 for result in results if not result.success),
        "prompt_files": changed_prompt_files,
        "fallbacks": sum(len(result.fallbacks) for result in results),
    }
