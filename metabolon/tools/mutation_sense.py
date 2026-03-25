"""mutation_sense — monitor upstream changes in forked receptor suites.

Tools:
  proprioception_receptors — diff local receptor forks against CC plugin cache
"""

from __future__ import annotations

import filecmp
import os
import re
from pathlib import Path

import yaml
from fastmcp.tools import tool
from mcp.types import ToolAnnotations
from pydantic import Field

from metabolon.morphology import Secretion

REGISTRY_PATH = Path(os.path.expanduser("~/.local/share/vivesca/skill-forks.yaml"))

DEFAULT_REGISTRY = {
    "superpowers": {
        "local": os.path.expanduser("~/metabolon/receptors/superpowers"),
        "cache_pattern": os.path.expanduser(
            "~/.claude/plugins/cache/claude-plugins-official/superpowers"
        ),
    },
    "compound-engineering": {
        "local": os.path.expanduser("~/metabolon/receptors/compound-engineering"),
        "cache_pattern": os.path.expanduser(
            "~/.claude/plugins/cache/every-marketplace/compound-engineering"
        ),
    },
}


def restore_fork_registry(path: Path = REGISTRY_PATH) -> dict:
    """Load fork registry from YAML, or return defaults."""
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return DEFAULT_REGISTRY


def find_latest_cache_version(cache_dir: Path) -> Path | None:
    """Find the latest versioned directory in a cache path.

    Looks for directories matching semver (X.Y.Z) pattern.
    Returns the path to the skills/ subdirectory of the latest version.
    """
    if not cache_dir.exists():
        return None

    versions: list[tuple[tuple[int, ...], Path]] = []
    for entry in cache_dir.iterdir():
        if entry.is_dir() and re.match(r"^\d+\.\d+\.\d+$", entry.name):
            parts = tuple(int(x) for x in entry.name.split("."))
            skills_dir = entry / "skills"
            if skills_dir.exists():
                versions.append((parts, skills_dir))

    if not versions:
        return None
    versions.sort(key=lambda x: x[0])
    return versions[-1][1]


def diff_fork(local_dir: Path, cache_dir: Path) -> dict:
    """Compare local fork against upstream cache.

    Returns dict with: modified, added_upstream, removed_locally, total_changes.
    """
    modified: list[str] = []
    added_upstream: list[str] = []
    removed_locally: list[str] = []

    # Collect all relative paths from both sides
    local_files: set[str] = set()
    cache_files: set[str] = set()

    for f in local_dir.rglob("*"):
        if f.is_file() and not any(p.name == ".git" for p in f.parents):
            local_files.add(str(f.relative_to(local_dir)))

    for f in cache_dir.rglob("*"):
        if f.is_file() and not any(p.name == ".git" for p in f.parents):
            cache_files.add(str(f.relative_to(cache_dir)))

    # Modified: in both, but different
    for rel in sorted(local_files & cache_files):
        if not filecmp.cmp(local_dir / rel, cache_dir / rel, shallow=False):
            modified.append(rel)

    # Added upstream: in cache but not local
    added_upstream = sorted(cache_files - local_files)

    # Removed locally: in local but not cache (intentional omissions)
    removed_locally = sorted(local_files - cache_files)

    return {
        "modified": modified,
        "added_upstream": added_upstream,
        "removed_locally": removed_locally,
        "total_changes": len(modified) + len(added_upstream),
    }


class EnzymeSenseResult(Secretion):
    """Enzyme-level sensing — upstream receptor fork changes."""

    has_changes: bool
    summary: str
    suites: list[dict] = Field(default_factory=list)


@tool(
    name="proprioception_skills",
    description="Diff local receptor forks against CC plugin cache. Silent if no changes.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def proprioception_skills() -> EnzymeSenseResult:
    """Proprioceptive check for upstream enzyme (skill) changes."""
    registry = restore_fork_registry()
    suites: list[dict] = []
    parts: list[str] = []

    for suite_name, paths in registry.items():
        local_dir = Path(paths["local"])
        cache_base = Path(paths["cache_pattern"])

        if not local_dir.exists():
            continue

        cache_skills = find_latest_cache_version(cache_base)
        if cache_skills is None:
            continue

        diff = diff_fork(local_dir, cache_skills)
        if diff["total_changes"] == 0:
            continue

        suite_summary = {
            "suite": suite_name,
            "modified": diff["modified"],
            "added_upstream": diff["added_upstream"],
            "total": diff["total_changes"],
        }
        suites.append(suite_summary)

        lines = [f"**{suite_name}** — {diff['total_changes']} change(s):"]
        for f in diff["modified"]:
            lines.append(f"  modified: {f}")
        for f in diff["added_upstream"]:
            lines.append(f"  new upstream: {f}")
        parts.append("\n".join(lines))

    has_changes = len(suites) > 0
    summary = "\n\n".join(parts) if parts else ""

    return EnzymeSenseResult(
        has_changes=has_changes,
        summary=summary,
        suites=suites,
    )
