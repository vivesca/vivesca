#!/usr/bin/env -S uv run --script --python 3.13
# /// script
# requires-python = ">=3.13"
# dependencies = ["anthropic"]
# ///
"""PostToolUse hook: auto-commit writes to tracked git repos.

Uses git rev-parse to detect repo membership — works for symlinks and any
path structure. Repo registry controls which repos auto-commit and whether
to push.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lib"))
import contextlib

from llm import load_models

# repo_root -> should_push
TRACKED_REPOS = {
    str(Path.home() / "reticulum"): True,  # auto-commit + push
    # notes (vault): too noisy for per-write commits. dirty-repos.js catches at session end.
}

# Paths requiring manual test-before-commit (relative to repo root, prefix match)
TEST_GATE_PREFIXES = ("claude/hooks/", "scripts/", "bin/")


def get_git_root(path: Path) -> str | None:
    """Return the git repo root for the given path, or None if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_staged_diff(repo_root: str) -> str:
    """Return truncated staged diff for commit message generation."""
    try:
        stat = subprocess.run(
            ["git", "-C", repo_root, "diff", "--cached", "--stat"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        diff = subprocess.run(
            ["git", "-C", repo_root, "diff", "--cached"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        combined = stat.stdout.strip() + "\n\n" + diff.stdout.strip()
        return combined[:3000]  # cap to avoid token overhead
    except Exception:
        return ""


def generate_commit_message(diff: str, fallback: str) -> str:
    """Call Haiku to produce a conventional commit message from the diff."""
    try:
        import anthropic

        haiku_model = load_models().get("haiku", {}).get("model", "claude-haiku-4-5-20251001")
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=haiku_model,
            max_tokens=60,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Write a conventional commit message for this diff.\n"
                        "Format: type(scope): description\n"
                        "Types: feat, fix, refactor, docs, chore, style, perf, test\n"
                        "Rules: imperative mood, lowercase, no period, max 72 chars total, "
                        "scope from file path (omit if multiple files), if unsure use chore.\n"
                        "Reply with ONLY the commit message, nothing else.\n\n"
                        f"Diff:\n{diff}"
                    ),
                }
            ],
        )
        raw = response.content[0].text.strip()
        # Sanity check: must look like a conventional commit
        if re.match(r"^[a-z]+(\([^)]+\))?!?: .+", raw):
            return raw[:72]
    except Exception:
        pass
    return fallback


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    # Only fire on write operations — Read also has file_path but must not trigger commits
    tool_name = data.get("tool_name", "")
    if tool_name.lower() not in ("edit", "multiedit", "write"):
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    try:
        real_path = Path(file_path).resolve()
    except Exception:
        sys.exit(0)

    repo_root = get_git_root(real_path)
    if repo_root is None or repo_root not in TRACKED_REPOS:
        sys.exit(0)

    # Debounce: don't call Haiku API more than once per 60s per repo
    import time

    debounce_file = (
        Path.home() / ".local/share/respirometry" / f"ligation-{Path(repo_root).name}.ts"
    )
    debounce_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        if debounce_file.exists():
            last = float(debounce_file.read_text().strip())
            if time.time() - last < 60:
                # Stage but skip commit — next call outside debounce will commit all
                subprocess.run(["git", "-C", repo_root, "add", "-A"], capture_output=True)
                sys.exit(0)
    except (ValueError, OSError):
        pass

    should_push = TRACKED_REPOS[repo_root]

    try:
        rel = real_path.relative_to(repo_root)
    except ValueError:
        rel = real_path.name

    subprocess.run(["git", "-C", repo_root, "add", "-A"], capture_output=True)

    status = subprocess.run(
        ["git", "-C", repo_root, "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if not status.stdout.strip():
        sys.exit(0)

    # Gate: hooks/scripts must be tested before committing
    rel_str = str(rel)
    if any(rel_str.startswith(p) for p in TEST_GATE_PREFIXES):
        print(
            f"⚠ TEST GATE: {rel} staged but not committed.\n"
            f"  Test it, then: git -C {repo_root} commit && git -C {repo_root} push",
            file=sys.stderr,
        )
        sys.exit(0)

    fallback = f"chore: update {rel}"
    diff = get_staged_diff(repo_root)
    message = generate_commit_message(diff, fallback) if diff else fallback

    subprocess.run(
        ["git", "-C", repo_root, "commit", "-m", message],
        capture_output=True,
    )

    with contextlib.suppress(OSError):
        debounce_file.write_text(str(time.time()))

    if should_push:
        subprocess.run(
            ["git", "-C", repo_root, "push"],
            capture_output=True,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
