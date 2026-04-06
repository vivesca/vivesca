#!/usr/bin/env python3
"""Translocase -- Temporal worker (eEF2) for the polysome translation system.

Polls the 'translation-queue' task queue and executes ribosome commands as activities.

Usage:
    python translocase.py
    python translocase.py --help
"""

import asyncio
import contextlib
import fcntl as _fcntl
import json
import os
import re as _re
import subprocess as _subprocess
import sys
import time as _time
from datetime import timedelta
from pathlib import Path

from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

TASK_QUEUE = "translation-queue"
RIBOSOME_SCRIPT = Path(__file__).resolve().parent.parent / "ribosome"
REVIEW_LOG = Path.home() / "germline" / "loci" / "ribosome-reviews.jsonl"
OUTPUT_DIR = Path.home() / "germline" / "loci" / "ribosome-outputs"

PROVIDER_LIMITS = {
    "zhipu": 8,
    "infini": 8,
    "volcano": 16,
    "gemini": 4,
    "codex": 4,
}

# Serialize merges so concurrent ribosomes queue instead of racing
_MERGE_LOCK_PATH = Path(__file__).resolve().parent.parent.parent / ".worktrees" / ".merge.lock"

# Accept branch version on conflict -- lockfiles get regenerated
_LOCKFILE_NAMES = {"uv.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock"}

_HEARTBEAT_INTERVAL = 30.0
_ACTIVITY_TIMEOUT = timedelta(minutes=30)


def _git_snapshot(cwd: str | None = None) -> dict:
    """Capture git diff stat + numstat + commit list + full patch for review."""
    work_dir = cwd or str(Path.home() / "germline")
    try:
        stat = _subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=work_dir,
        )
        numstat = _subprocess.run(
            ["git", "diff", "--numstat", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=work_dir,
        )
        commits_r = _subprocess.run(
            ["git", "log", "--oneline", "main..HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=work_dir,
        )
        commit_lines = [ln.strip() for ln in commits_r.stdout.strip().splitlines() if ln.strip()]
        patch_r = _subprocess.run(
            ["git", "diff", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=work_dir,
        )
        return {
            "stat": stat.stdout[:2000],
            "numstat": numstat.stdout[:2000],
            "commits": commit_lines,
            "commit_count": len(commit_lines),
            "patch": patch_r.stdout[:5000],
        }
    except Exception:
        return {"stat": "", "numstat": "", "commits": [], "commit_count": 0, "patch": ""}


def _git_pull_ff_only(repo_root: str) -> None:
    """Pull latest so CC-written test files are available before ribosome runs."""
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
    """Push ribosome commits so soma can pull without manual intervention."""
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
    """Create a git worktree for isolated ribosome execution. Returns worktree path."""
    worktree_base = os.path.join(repo_root, ".worktrees")
    os.makedirs(worktree_base, exist_ok=True)
    worktree_path = os.path.join(worktree_base, branch_name)

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
    """Merge worktree branch into main under exclusive file lock.

    FF when possible, 3-way merge otherwise. Lockfile conflicts auto-resolved
    (accept branch version). Code conflicts abort cleanly, leaving the branch.
    Worktree always removed; branch deleted only on success.
    """
    _MERGE_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(_MERGE_LOCK_PATH, "w")
    delete_branch = False
    try:
        _fcntl.flock(lock_fd, _fcntl.LOCK_EX)

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

        # Try FF first (zero overhead when no contention)
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

        # FF failed -- real 3-way merge
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

        # Categorise conflicts
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

        # Code conflicts -- abort, leave branch for inspection
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
        with contextlib.suppress(Exception):
            _subprocess.run(
                ["git", "worktree", "remove", "--force", worktree_path],
                capture_output=True,
                timeout=10,
                cwd=repo_root,
            )
        if delete_branch:
            with contextlib.suppress(Exception):
                _subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    capture_output=True,
                    timeout=10,
                    cwd=repo_root,
                )


def _detect_prior_commits(
    repo_root: str, time_window_minutes: int = 40, author: str = "ribosome"
) -> list[str]:
    """Find recent commits from a prior killed attempt so retries can resume."""
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
        return [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    except Exception:
        return []


@activity.defn
async def translate(task: str, provider: str, max_turns: int = 50) -> dict:
    """Execute a single ribosome task as a subprocess."""
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

    try:
        syntax_check = await asyncio.to_thread(
            _subprocess.run,
            ["bash", "-n", str(RIBOSOME_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if syntax_check.returncode != 0:
            return {
                "exit_code": -1,
                "success": False,
                "stderr": f"ribosome script has syntax error: {syntax_check.stderr.strip()}",
            }
    except _subprocess.TimeoutExpired:
        pass

    # Run from repo root, not polysome subdir
    repo_root = str(Path.home() / "germline")

    branch_name = f"ribosome-{tid_str or _time.strftime('%H%M%S')}"
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

    prior_commits = await asyncio.to_thread(
        _detect_prior_commits, work_dir, time_window_minutes=40, author="ribosome"
    )
    effective_task = task
    if prior_commits:
        commit_list = "\n".join(f"  - {c}" for c in prior_commits)
        prefix = (
            "NOTE: A prior attempt on this task made the following commits "
            "before being interrupted:\n"
            f"{commit_list}\n"
            "Review these commits -- if they partially complete the task, "
            "continue from where they left off. "
            "Do NOT redo already-committed work.\n\n"
        )
        effective_task = prefix + task

    await asyncio.to_thread(_git_pull_ff_only, work_dir)
    pre_diff = await asyncio.to_thread(_git_snapshot, work_dir)

    cmd = [
        "bash",
        str(RIBOSOME_SCRIPT),
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
        env={**os.environ, "RIBOSOME_PROVIDER": provider, "HOME": str(Path.home())},
    )

    async def _heartbeat_with_stall_detection():
        """Progress-based stall detection instead of dumb turn/time limits.

        Every 30s, hash the git diff in the worktree. If the hash is unchanged
        for 3 consecutive checks (frozen) or alternates between 2 values
        (edit/revert oscillation), the agent is stalled.

        Graduated response: first stall detection logs a warning; second kills.
        """
        import hashlib

        stall_frozen_threshold = 3  # consecutive identical hashes
        stall_oscillation_threshold = 6  # alternating between 2 hashes
        recent_hashes: list[str] = []
        warnings_sent = 0

        tick = 0
        while True:
            await asyncio.sleep(_HEARTBEAT_INTERVAL)
            tick += 1

            # Compute diff content hash
            diff_hash = "unknown"
            try:
                diff_result = await asyncio.to_thread(
                    lambda: _subprocess.run(
                        ["git", "diff", "HEAD"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=work_dir,
                    )
                )
                diff_hash = hashlib.sha256(diff_result.stdout.encode()).hexdigest()[:12]
            except Exception:
                pass

            recent_hashes.append(diff_hash)
            if len(recent_hashes) > stall_oscillation_threshold + 1:
                recent_hashes.pop(0)

            with contextlib.suppress(Exception):
                activity.heartbeat(f"{provider}:{task[:60]} tick:{tick} diff:{diff_hash}")

            # Skip stall checks for first 2 minutes (4 ticks) — let agent ramp up
            if tick < 4:
                continue

            # Detect frozen: last N hashes identical
            is_frozen = (
                len(recent_hashes) >= stall_frozen_threshold
                and len(set(recent_hashes[-stall_frozen_threshold:])) == 1
            )

            # Detect oscillation: alternating between exactly 2 hashes
            is_oscillating = False
            if len(recent_hashes) >= stall_oscillation_threshold:
                tail = recent_hashes[-stall_oscillation_threshold:]
                unique = set(tail)
                if len(unique) == 2:
                    # Check if it's truly alternating (ABAB pattern)
                    is_oscillating = all(
                        tail[idx] != tail[idx + 1] for idx in range(len(tail) - 1)
                    )

            if is_frozen or is_oscillating:
                stall_type = "frozen" if is_frozen else "oscillating"
                warnings_sent += 1
                print(
                    f"[stall-detect] {stall_type} at tick {tick} "
                    f"(warnings={warnings_sent}, hashes={recent_hashes[-4:]})",
                    file=sys.stderr,
                )
                if warnings_sent >= 2:
                    print(
                        f"[stall-detect] killing stalled process (pid={proc.pid})",
                        file=sys.stderr,
                    )
                    proc.kill()
                    return

    hb_task = asyncio.create_task(_heartbeat_with_stall_detection())
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

    post_diff = await asyncio.to_thread(_git_snapshot, work_dir)
    commit_count = post_diff.get("commit_count", 0)

    # Incomplete: non-zero exit but commits exist — preserve branch for re-dispatch
    is_incomplete = rc != 0 and commit_count > 0
    merged = False
    if worktree_path:
        if is_incomplete:
            # Just remove the worktree; leave branch alive for manual recovery
            with contextlib.suppress(Exception):
                _subprocess.run(
                    ["git", "worktree", "remove", "--force", worktree_path],
                    capture_output=True,
                    timeout=10,
                    cwd=repo_root,
                )
            print(
                f"INCOMPLETE: branch {branch_name} preserved ({commit_count} commits)",
                file=sys.stderr,
            )
        else:
            merged = await asyncio.to_thread(
                _merge_worktree, repo_root, branch_name, worktree_path
            )
            if not merged:
                print(f"WARNING: worktree merge failed for {branch_name}", file=sys.stderr)

    if rc == 0 and merged and post_diff.get("stat", "").strip():
        await asyncio.to_thread(_git_push, repo_root)

    cost_info = ""
    for line in stdout.splitlines()[-10:]:
        if any(k in line.lower() for k in ["token", "cost", "usage", "input:", "output:"]):
            cost_info += line + "\n"

    task_id_match = _re.search(r"\[t-([0-9a-fA-F]+)\]", task)
    tid_str = task_id_match.group(1) if task_id_match else _time.strftime("%H%M%S")
    out_path = ""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_file = OUTPUT_DIR / f"{_time.strftime('%Y%m%d')}-{tid_str}.txt"
        out_text = (
            f"Task: {task}\nProvider: {provider}\nExit: {rc}\n\n"
            f"--- stdout ---\n{stdout}\n\n--- stderr ---\n{stderr}\n\n"
            f"--- diff ---\n{post_diff.get('stat', '')}\n"
        )
        if is_incomplete:
            out_text += f"\nBranch preserved for re-dispatch: {branch_name}\n"
        # Preserve full patch when rejected or incomplete so work is recoverable
        if rc != 0 or not merged:
            out_text += f"\n\n--- full patch (recoverable) ---\n{post_diff.get('patch', '')}\n"
        out_file.write_text(out_text)
        out_path = str(out_file)
    except OSError:
        pass

    return {
        "success": rc == 0,
        "exit_code": rc,
        "provider": provider,
        "task": task[:200],
        "stdout": stdout[:1000],
        "stderr": stderr[:500],
        "pre_diff": pre_diff,
        "post_diff": post_diff,
        "cost_info": cost_info[:500],
        "output_path": out_path,
        "branch_name": branch_name if worktree_path else "",
        "merged": merged,
    }


@activity.defn
async def translate_graph(task: str, provider: str) -> dict:
    """Execute a ribosome task via LangGraph agent graph."""
    import asyncio

    from translation_graph import run_translation_graph

    result = await asyncio.to_thread(run_translation_graph, task, provider)
    return result


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
async def chaperone(result: dict) -> dict:
    """Review a ribosome task result for quality signals.

    Returns {"approved": bool, "flags": [...], "verdict": str}.
    """
    task = result.get("task", "")
    provider = result.get("provider", "")
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code", -1)
    combined = f"{stdout}\n{stderr}"

    flags: list[str] = []

    if exit_code != 0:
        flags.append(f"exit_code={exit_code}")

    destruction_hits = _DESTRUCTION_PATTERNS.findall(combined)
    if destruction_hits:
        flags.append(f"destruction: {', '.join(list(set(destruction_hits))[:3])}")

    error_hits = _ERROR_PATTERNS.findall(combined)
    if error_hits:
        flags.append(f"errors: {', '.join(list(set(error_hits))[:3])}")

    task_words = len(task.split())
    output_words = len(stdout.split())
    if task_words > 20 and output_words < 10 and exit_code == 0:
        flags.append(f"thin_output: {output_words} words for {task_words}-word task")

    if exit_code == 0 and len(stdout.strip()) < 5:
        flags.append("empty_stdout_on_success")

    # GLM ran to completion but committed nothing -- likely no-op
    post_stat_text = (
        result.get("post_diff", {}).get("stat", "")
        if isinstance(result.get("post_diff"), dict)
        else ""
    )
    commit_count = (
        result.get("post_diff", {}).get("commit_count", 0)
        if isinstance(result.get("post_diff"), dict)
        else 0
    )
    branch_name = result.get("branch_name", "")

    if exit_code == 0 and not post_stat_text.strip() and commit_count == 0:
        flags.append("no_commit_on_success")

    target_match = _re.search(r"(?:at|to)\s+([\w/]+\.py)", task)
    if target_match and exit_code == 0 and post_stat_text:
        target_file = target_match.group(1)
        if target_file not in post_stat_text:
            flags.append(f"target_file_missing: {target_file}")

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

    # Determine verdict: incomplete when work was done but process failed
    if exit_code != 0 and commit_count > 0:
        verdict = "incomplete"
        approved = False
    else:
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
    if verdict == "incomplete" and branch_name:
        review["branch_name"] = branch_name

    try:
        REVIEW_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(REVIEW_LOG, "a") as f:
            f.write(json.dumps(review) + "\n")
    except OSError:
        pass

    requeue_prompt = ""
    if verdict in ("rejected", "incomplete") and any("thin_output" in f for f in flags):
        requeue_prompt = task[:200] + " -- Be thorough. Read files before editing. Show your work."
    elif verdict in ("rejected", "incomplete") and any("file_shrunk" in f for f in flags):
        requeue_prompt = (
            task[:200]
            + " -- IMPORTANT: Read the entire file before modifying. Preserve ALL existing content."
        )

    return {
        "approved": approved,
        "flags": flags,
        "verdict": verdict,
        "requeue_prompt": requeue_prompt,
    }


async def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    # Deferred import to avoid circular dependency with workflow.py
    from workflow import TranslationWorkflow

    host = os.getenv("TEMPORAL_HOST", "ganglion:7233")
    client = await Client.connect(host)
    max_concurrent = sum(PROVIDER_LIMITS.values())

    worker = Worker(
        client=client,
        task_queue=TASK_QUEUE,
        workflows=[TranslationWorkflow],
        activities=[translate, translate_graph, chaperone],
        max_concurrent_activities=max_concurrent,
    )
    print(f"Translocase started on queue '{TASK_QUEUE}' (max_concurrent={max_concurrent})")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
