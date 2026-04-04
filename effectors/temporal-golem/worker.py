#!/usr/bin/env python3
"""Temporal worker for golem task orchestration.

Polls the 'golem-tasks' task queue and executes golem commands as activities.
Each activity runs `bash effectors/golem --provider X task`, heartbeats every
30s, has a 30min timeout, and a retry policy (3 attempts, exponential backoff).

Usage:
    python worker.py                # Start worker
    python worker.py --help         # Show this help
"""

from __future__ import annotations

import asyncio
import contextlib
import fcntl as _fcntl
import os
import sys
from datetime import timedelta
from pathlib import Path

from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

TASK_QUEUE = "golem-tasks"
GOLEM_SCRIPT = Path(__file__).resolve().parent.parent / "golem"
REVIEW_LOG = Path.home() / "germline" / "loci" / "golem-reviews.jsonl"
OUTPUT_DIR = Path.home() / "germline" / "loci" / "golem-outputs"

# Per-provider concurrency limits (matching golem-daemon config)
PROVIDER_LIMITS = {
    "zhipu": 8,
    "infini": 8,
    "volcano": 16,
    "gemini": 4,
    "codex": 4,
}


# Serialize merges: only one golem merges at a time (file lock).
_MERGE_LOCK_PATH = Path(__file__).resolve().parent.parent.parent / ".worktrees" / ".merge.lock"

# Lockfiles: accept branch version on conflict (they get regenerated).
_LOCKFILE_NAMES = {"uv.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock"}

# How long we wait between heartbeats
_HEARTBEAT_INTERVAL = 30.0
# Maximum time a single golem invocation may run
_ACTIVITY_TIMEOUT = timedelta(minutes=30)


def _git_snapshot(cwd: str | None = None) -> dict:
    """Capture git diff stat + numstat for before/after comparison."""
    work_dir = cwd or str(Path.home() / "germline")
    try:
        stat = _subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=work_dir,
        )
        # numstat gives per-file +/- line counts for shrinkage detection
        numstat = _subprocess.run(
            ["git", "diff", "--numstat", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=work_dir,
        )
        return {
            "stat": stat.stdout[:2000],
            "numstat": numstat.stdout[:2000],
        }
    except Exception:
        return {"stat": "", "numstat": ""}


def _git_pull_ff_only(repo_root: str) -> None:
    """Pull latest changes before golem runs to pick up CC-written test files."""
    try:
        result = _subprocess.run(
            ["git", "pull", "--ff-only"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=repo_root,
        )
        if result.returncode != 0:
            print(f"WARNING: git pull --ff-only failed: {result.stderr.strip()}", file=sys.stderr)
    except _subprocess.TimeoutExpired:
        print("WARNING: git pull --ff-only timed out", file=sys.stderr)
    except Exception as exc:
        print(f"WARNING: git pull --ff-only error: {exc}", file=sys.stderr)


def _git_push(repo_root: str) -> None:
    """Push golem commits to origin so soma can pull without manual intervention."""
    try:
        result = _subprocess.run(
            ["git", "push"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=repo_root,
        )
        if result.returncode != 0:
            print(f"WARNING: git push failed: {result.stderr.strip()}", file=sys.stderr)
    except _subprocess.TimeoutExpired:
        print("WARNING: git push timed out", file=sys.stderr)
    except Exception as exc:
        print(f"WARNING: git push error: {exc}", file=sys.stderr)


def _create_worktree(repo_root: str, branch_name: str) -> str:
    """Create a git worktree for isolated golem execution. Returns worktree path."""
    worktree_base = os.path.join(repo_root, ".worktrees")
    os.makedirs(worktree_base, exist_ok=True)
    worktree_path = os.path.join(worktree_base, branch_name)

    # Clean up stale worktree if it exists
    if os.path.exists(worktree_path):
        _subprocess.run(
            ["git", "worktree", "remove", "--force", worktree_path],
            capture_output=True,
            timeout=10,
            cwd=repo_root,
        )

    result = _subprocess.run(
        ["git", "worktree", "add", "-b", branch_name, worktree_path, "HEAD"],
        capture_output=True,
        text=True,
        timeout=15,
        cwd=repo_root,
    )
    if result.returncode != 0:
        raise RuntimeError(f"worktree add failed: {result.stderr}")
    return worktree_path


def _merge_worktree(repo_root: str, branch_name: str, worktree_path: str) -> bool:
    """Merge worktree branch into main under exclusive lock.

    Strategy:
    - Serialize via file lock so concurrent golems queue instead of racing.
    - Fast-forward when main hasn't moved (common case).
    - Real 3-way merge (--no-ff) when another golem moved main.
    - Lockfile conflicts (uv.lock etc.): accept branch version automatically.
    - Code conflicts: abort cleanly, leave branch for inspection.
    - Worktree always removed; branch deleted only on success.
    """
    _MERGE_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(_MERGE_LOCK_PATH, "w")
    delete_branch = False
    try:
        _fcntl.flock(lock_fd, _fcntl.LOCK_EX)

        # Check if branch has commits beyond main
        check = _subprocess.run(
            ["git", "log", "--oneline", f"main..{branch_name}"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=repo_root,
        )
        if not check.stdout.strip():
            delete_branch = True
            return True

        # Try fast-forward first (zero overhead when no contention)
        merge = _subprocess.run(
            ["git", "merge", "--ff-only", branch_name],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=repo_root,
        )
        if merge.returncode == 0:
            delete_branch = True
            return True

        # FF failed — real 3-way merge
        merge = _subprocess.run(
            ["git", "merge", "--no-ff", "--no-edit", branch_name],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=repo_root,
        )
        if merge.returncode == 0:
            delete_branch = True
            return True

        # Conflicts — categorise them
        conflicted = _subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=repo_root,
        )
        conflicted_files = [f.strip() for f in conflicted.stdout.splitlines() if f.strip()]
        lockfiles = [f for f in conflicted_files if Path(f).name in _LOCKFILE_NAMES]
        code_files = [f for f in conflicted_files if Path(f).name not in _LOCKFILE_NAMES]

        # Resolve lockfile conflicts by accepting branch version
        for lockfile in lockfiles:
            _subprocess.run(
                ["git", "checkout", "--theirs", lockfile],
                capture_output=True,
                timeout=10,
                cwd=repo_root,
            )
            _subprocess.run(
                ["git", "add", lockfile],
                capture_output=True,
                timeout=10,
                cwd=repo_root,
            )

        if not code_files:
            # All conflicts were lockfiles — commit the resolution
            commit = _subprocess.run(
                ["git", "commit", "--no-edit"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=repo_root,
            )
            if commit.returncode == 0:
                delete_branch = True
                return True
            _subprocess.run(
                ["git", "merge", "--abort"], capture_output=True, timeout=10, cwd=repo_root
            )
            print(
                f"ERROR: merge commit failed for {branch_name}: {commit.stderr.strip()}",
                file=sys.stderr,
            )
            return False

        # Code conflicts — abort, leave branch for inspection
        _subprocess.run(
            ["git", "merge", "--abort"], capture_output=True, timeout=10, cwd=repo_root
        )
        conflict_list = ", ".join(code_files[:5])
        print(f"CONFLICT: {branch_name} has code conflicts: {conflict_list}", file=sys.stderr)
        return False

    except Exception as exc:
        print(f"ERROR: merge error for {branch_name}: {exc}", file=sys.stderr)
        with contextlib.suppress(Exception):
            _subprocess.run(
                ["git", "merge", "--abort"], capture_output=True, timeout=10, cwd=repo_root
            )
        return False
    finally:
        _fcntl.flock(lock_fd, _fcntl.LOCK_UN)
        lock_fd.close()
        # Always remove worktree
        with contextlib.suppress(Exception):
            _subprocess.run(
                ["git", "worktree", "remove", "--force", worktree_path],
                capture_output=True,
                timeout=10,
                cwd=repo_root,
            )
        # Delete branch only on successful merge
        if delete_branch:
            with contextlib.suppress(Exception):
                _subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    capture_output=True,
                    timeout=10,
                    cwd=repo_root,
                )


def _detect_prior_commits(
    repo_root: str, time_window_minutes: int = 40, author: str = "golem"
) -> list[str]:
    """Find commits from a prior killed golem attempt within the time window.

    Scans ``git log`` for oneline commits authored by *author* in the last
    *time_window_minutes* minutes.  Used so a retried activity can resume
    from partial work instead of starting from scratch.
    """
    try:
        result = _subprocess.run(
            [
                "git",
                "log",
                "--oneline",
                f"--since={time_window_minutes} minutes ago",
                f"--author={author}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=repo_root,
        )
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        return lines
    except Exception:
        return []


def _post_golem_checks(repo_root: str, task: str) -> tuple[int, str, dict]:
    """Run post-golem verification checks (ast, test, scope).

    Only call when the golem subprocess exited successfully (rc == 0).
    Returns (rc_override, stderr_append, post_checks).
    """
    import ast as _ast

    post_checks: dict = {"ast": True, "tests": True, "scope_warnings": []}
    rc_override = 0
    stderr_parts: list[str] = []

    # Get modified files from git — check committed changes (not just working tree)
    # Golem commits its work, so `git diff --name-only` shows nothing.
    # Use `git diff --name-only HEAD~5..HEAD` to catch recent golem commits,
    # falling back to working tree diff if that fails.
    try:
        diff_result = _subprocess.run(
            ["git", "diff", "--name-only", "HEAD~5..HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=repo_root,
        )
        modified_files = [f.strip() for f in diff_result.stdout.strip().splitlines() if f.strip()]
        if not modified_files:
            # Fallback: check working tree (uncommitted changes)
            diff_result = _subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=repo_root,
            )
            modified_files = [
                f.strip() for f in diff_result.stdout.strip().splitlines() if f.strip()
            ]
    except Exception:
        return (0, "", post_checks)

    # (1) ast_check: validate syntax of every modified .py file
    for mf in list(modified_files):
        if mf.endswith(".py"):
            fpath = os.path.join(repo_root, mf)
            if os.path.isfile(fpath):
                try:
                    _ast.parse(open(fpath).read())
                except SyntaxError:
                    rc_override = 1
                    stderr_parts.append(f"ast_check_failed: {mf}")
                    post_checks["ast"] = False

    # (2) test_check: run pytest suite (skip if ast failed)
    if post_checks["ast"]:
        try:
            test_result = _subprocess.run(
                ["uv", "run", "pytest", "assays/", "-q", "--tb=line", "-x", "--timeout=120"],
                capture_output=True,
                text=True,
                timeout=150,
                cwd=repo_root,
            )
            if test_result.returncode != 0:
                rc_override = 1
                last_lines = "\n".join(test_result.stdout.splitlines()[-10:])
                stderr_parts.append(f"test_regression: {last_lines}")
                post_checks["tests"] = False
        except _subprocess.TimeoutExpired:
            rc_override = 1
            stderr_parts.append("test_regression: timed out")
            post_checks["tests"] = False
        except Exception as exc:
            rc_override = 1
            stderr_parts.append(f"test_regression: {exc}")
            post_checks["tests"] = False
    else:
        post_checks["tests"] = False

    # (3) scope_check: warn if files modified outside target directory
    target_match = _re.search(r"~/germline/[\w/.-]+", task)
    if target_match:
        target_path = os.path.normpath(target_match.group(0).replace("~/", str(Path.home()) + "/"))
        # If target looks like a file, use its parent directory
        if os.path.splitext(target_path)[1]:
            target_path = os.path.dirname(target_path)
        for mf in modified_files:
            full_mf = os.path.normpath(os.path.join(repo_root, mf))
            in_target = full_mf.startswith(target_path + os.sep) or full_mf == target_path
            if not in_target and not mf.startswith("assays/"):
                post_checks["scope_warnings"].append(mf)
                stderr_parts.append(f"scope_drift: {mf}")

    return (rc_override, "\n".join(stderr_parts), post_checks)


@activity.defn
async def run_golem_task(task: str, provider: str, max_turns: int = 50) -> dict:
    """Execute a single golem task as a subprocess."""
    # #1: Idempotency — if output file from prior attempt exists, return cached
    task_id_match = _re.search(r"\[t-([0-9a-fA-F]+)\]", task)
    tid_str = task_id_match.group(1) if task_id_match else ""
    if tid_str:
        cached = OUTPUT_DIR / f"{_time.strftime('%Y%m%d')}-{tid_str}.txt"
        if cached.exists():
            content = cached.read_text()
            if "Exit: 0" in content[:200]:
                return {
                    "success": True,
                    "exit_code": 0,
                    "provider": provider,
                    "task": task[:200],
                    "stdout": "(cached from prior attempt)",
                    "stderr": "",
                    "pre_diff": {"stat": "", "numstat": ""},
                    "post_diff": {"stat": "", "numstat": ""},
                    "cost_info": "",
                    "output_path": str(cached),
                }
            print(f"cache: stale failure for {tid_str}, re-executing")

    # Syntax pre-check: validate golem script before dispatching
    try:
        syntax_check = await asyncio.to_thread(
            _subprocess.run,
            ["bash", "-n", str(GOLEM_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if syntax_check.returncode != 0:
            return {
                "exit_code": -1,
                "success": False,
                "stderr": f"golem script has syntax error: {syntax_check.stderr.strip()}",
            }
    except _subprocess.TimeoutExpired:
        pass  # proceed anyway if check times out

    # Run golem from repo root, not temporal-golem subdir
    repo_root = str(Path.home() / "germline")

    # Create isolated worktree for this task
    branch_name = f"golem-{tid_str or _time.strftime('%H%M%S')}"
    worktree_path = None
    try:
        worktree_path = await asyncio.to_thread(_create_worktree, repo_root, branch_name)
        work_dir = worktree_path
    except Exception as exc:
        print(
            f"WARNING: worktree creation failed ({exc}), falling back to repo root",
            file=sys.stderr,
        )
        work_dir = repo_root
        worktree_path = None

    # Detect partial progress from a prior killed attempt
    prior_commits = await asyncio.to_thread(
        _detect_prior_commits, work_dir, time_window_minutes=40, author="golem"
    )
    effective_task = task
    if prior_commits:
        commit_list = "\n".join(f"  - {c}" for c in prior_commits)
        prefix = (
            "NOTE: A prior attempt on this task made the following commits "
            "before being interrupted:\n"
            f"{commit_list}\n"
            "Review these commits — if they partially complete the task, "
            "continue from where they left off. "
            "Do NOT redo already-committed work.\n\n"
        )
        effective_task = prefix + task

    # Pull latest changes (e.g. CC-written test files) before running golem
    await asyncio.to_thread(_git_pull_ff_only, work_dir)

    # Snapshot before golem runs
    pre_diff = await asyncio.to_thread(_git_snapshot, work_dir)

    cmd = [
        "bash",
        str(GOLEM_SCRIPT),
        "--provider",
        provider,
        "--max-turns",
        str(max_turns),
        effective_task,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=work_dir,
        env={**os.environ, "GOLEM_PROVIDER": provider, "HOME": str(Path.home())},
    )

    # Heartbeat while subprocess runs
    async def _heartbeat():
        n = 0
        while True:
            await asyncio.sleep(_HEARTBEAT_INTERVAL)
            n += 1
            with contextlib.suppress(Exception):
                activity.heartbeat(f"{provider}:{task[:60]} tick:{n}")

    hb_task = asyncio.create_task(_heartbeat())
    try:
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=_ACTIVITY_TIMEOUT.total_seconds(),
            )
        except TimeoutError:
            proc.kill()
            await proc.communicate()
            return {
                "success": False,
                "exit_code": -1,
                "provider": provider,
                "task": task[:200],
                "stdout": "",
                "stderr": "timeout after 30m",
            }
    finally:
        hb_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await hb_task

    rc = proc.returncode or 0
    stdout = stdout_bytes.decode(errors="replace")
    stderr = stderr_bytes.decode(errors="replace")

    # Snapshot after golem runs (in worktree)
    post_diff = await asyncio.to_thread(_git_snapshot, work_dir)

    # Merge worktree back to main if golem made commits
    if worktree_path:
        merged = await asyncio.to_thread(_merge_worktree, repo_root, branch_name, worktree_path)
        if not merged:
            print(f"WARNING: worktree merge failed for {branch_name}", file=sys.stderr)

    # Push golem commits to origin so soma can pull without manual intervention
    if rc == 0 and merged and post_diff.get("stat", "").strip():
        await asyncio.to_thread(_git_push, repo_root)

    # #5: Extract token/cost info from golem output
    cost_info = ""
    for line in stdout.splitlines()[-10:]:
        if any(k in line.lower() for k in ["token", "cost", "usage", "input:", "output:"]):
            cost_info += line + "\n"

    # #8: Save full output to per-task file; #4: return path, not payload
    task_id_match = _re.search(r"\[t-([0-9a-fA-F]+)\]", task)
    tid_str = task_id_match.group(1) if task_id_match else _time.strftime("%H%M%S")
    out_path = ""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_file = OUTPUT_DIR / f"{_time.strftime('%Y%m%d')}-{tid_str}.txt"
        out_file.write_text(
            f"Task: {task}\nProvider: {provider}\nExit: {rc}\n\n--- stdout ---\n{stdout}\n\n--- stderr ---\n{stderr}\n\n--- diff ---\n{post_diff.get('stat', '')}\n"
        )
        out_path = str(out_file)
    except OSError:
        pass

    return {
        "success": rc == 0,
        "exit_code": rc,
        "provider": provider,
        "task": task[:200],
        "stdout": stdout[:1000],  # slim: just enough for review patterns
        "stderr": stderr[:500],
        "pre_diff": pre_diff,
        "post_diff": post_diff,
        "cost_info": cost_info[:500],
        "output_path": out_path,
    }


import json
import re as _re
import subprocess as _subprocess
import time as _time

# ── LangGraph golem activity ──


@activity.defn
async def run_golem_graph_task(task: str, provider: str, max_turns: int = 50) -> dict:
    """Execute a golem task via LangGraph agent graph (plan→execute→verify→review)."""
    # Run synchronously in a thread to avoid blocking the event loop
    import asyncio

    from golem_graph import run_golem_graph

    result = await asyncio.to_thread(run_golem_graph, task, provider)
    return result


# ── Red-flag patterns that indicate golem may have done damage ──

_DESTRUCTION_PATTERNS = _re.compile(
    r"rm -rf|rmdir|replaced entire|overwrote|deleted all|"
    r"file is now empty|wrote 0 bytes|No such file",
    _re.IGNORECASE,
)

_ERROR_PATTERNS = _re.compile(
    r"SyntaxError|ImportError|ModuleNotFoundError|PermissionError|"
    r"Traceback \(most recent|FAILED|panic:|fatal:",
    _re.IGNORECASE,
)


@activity.defn
async def review_golem_result(result: dict) -> dict:
    """Review a golem task result for quality signals.

    Checks for destruction patterns, errors, suspiciously short output,
    and writes a review entry to golem-reviews.jsonl.

    Returns {"approved": bool, "flags": [...], "verdict": str}.
    """
    task = result.get("task", "")
    provider = result.get("provider", "")
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code", -1)
    combined = f"{stdout}\n{stderr}"

    flags: list[str] = []

    # 1. Exit code
    if exit_code != 0:
        flags.append(f"exit_code={exit_code}")

    # 2. Destruction patterns in output
    destruction_hits = _DESTRUCTION_PATTERNS.findall(combined)
    if destruction_hits:
        flags.append(f"destruction: {', '.join(list(set(destruction_hits))[:3])}")

    # 3. Error patterns
    error_hits = _ERROR_PATTERNS.findall(combined)
    if error_hits:
        flags.append(f"errors: {', '.join(list(set(error_hits))[:3])}")

    # 4. Suspiciously short output for complex tasks
    task_words = len(task.split())
    output_words = len(stdout.split())
    if task_words > 20 and output_words < 10 and exit_code == 0:
        flags.append(f"thin_output: {output_words} words for {task_words}-word task")

    # 5. Empty stdout with success (golem should always produce output)
    if exit_code == 0 and len(stdout.strip()) < 5:
        flags.append("empty_stdout_on_success")

    # 5b. No git commit despite success — GLM ran to completion but built nothing
    post_stat_text = (
        result.get("post_diff", {}).get("stat", "")
        if isinstance(result.get("post_diff"), dict)
        else ""
    )
    if exit_code == 0 and not post_stat_text.strip():
        flags.append("no_commit_on_success")

    # 5c. Target file missing — prompt names a file that wasn't created/modified
    target_match = _re.search(r"(?:at|to)\s+([\w/]+\.py)", task)
    if target_match and exit_code == 0 and post_stat_text:
        target_file = target_match.group(1)
        if target_file not in post_stat_text:
            flags.append(f"target_file_missing: {target_file}")

    # 6. Git diff — per-file line count analysis from numstat
    pre_diff = result.get("pre_diff", {})
    post_diff = result.get("post_diff", {})
    pre_numstat = pre_diff.get("numstat", "") if isinstance(pre_diff, dict) else ""
    post_numstat = post_diff.get("numstat", "") if isinstance(post_diff, dict) else ""
    post_stat = post_diff.get("stat", "") if isinstance(post_diff, dict) else str(post_diff)

    if post_numstat and post_numstat != pre_numstat:
        for line in post_numstat.splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                added, removed, fname = parts
                try:
                    a, r = int(added), int(removed)
                    if r > a * 3 and r > 10:
                        flags.append(f"file_shrunk: {fname} +{a}/-{r}")
                    if a == 0 and r > 5:
                        flags.append(f"pure_deletion: {fname} -{r}")
                except ValueError:
                    pass

    # Verdict
    approved = exit_code == 0 and not any(
        f.startswith("destruction") or f == "no_commit_on_success" for f in flags
    )
    verdict = "approved" if approved else "rejected"
    if flags and approved:
        verdict = "approved_with_flags"

    review = {
        "ts": _time.strftime("%Y-%m-%dT%H:%M:%S"),
        "task": task[:200],
        "provider": provider,
        "exit_code": exit_code,
        "flags": flags,
        "verdict": verdict,
        "stdout_len": len(stdout),
        "stderr_len": len(stderr),
        "diff": post_stat[:500] if post_stat else "",
        "cost_info": result.get("cost_info", ""),
    }

    # Persist review
    try:
        REVIEW_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(REVIEW_LOG, "a") as f:
            f.write(json.dumps(review) + "\n")
    except OSError:
        pass

    # #9: Auto-requeue rejected thin_output with coaching prompt
    requeue_prompt = ""
    if verdict == "rejected" and any("thin_output" in f for f in flags):
        requeue_prompt = task[:200] + " — Be thorough. Read files before editing. Show your work."
    elif verdict == "rejected" and any("file_shrunk" in f for f in flags):
        requeue_prompt = (
            task[:200]
            + " — IMPORTANT: Read the entire file before modifying. Preserve ALL existing content."
        )

    return {
        "approved": approved,
        "flags": flags,
        "verdict": verdict,
        "requeue_prompt": requeue_prompt,
    }


async def main() -> None:
    """Start the Temporal worker."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    # Import workflow here to avoid circular import at module level
    from workflow import GolemDispatchWorkflow

    host = os.getenv("TEMPORAL_HOST", "ganglion:7233")
    client = await Client.connect(host)

    # Total concurrent activities across all providers
    max_concurrent = sum(PROVIDER_LIMITS.values())

    worker = Worker(
        client=client,
        task_queue=TASK_QUEUE,
        workflows=[GolemDispatchWorkflow],
        activities=[run_golem_task, run_golem_graph_task, review_golem_result],
        max_concurrent_activities=max_concurrent,
    )
    print(
        f"Temporal golem worker started on queue '{TASK_QUEUE}' (max_concurrent={max_concurrent})"
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
