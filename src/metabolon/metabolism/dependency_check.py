
"""dependency_check — API key and external dependency integrity.

Runs monthly or on-demand. Checks:
- API keys are set and valid-looking
- Critical git repos are reachable and not corrupted
- Sortase/dispatch infrastructure is functional
"""


import os
from pathlib import Path
import subprocess
from dataclasses import dataclass

from metabolon.locus import epigenome, germline


@dataclass
class DependencyStatus:
    name: str
    healthy: bool
    message: str
    category: str = "unknown"  # api_key, git_repo, binary, service


def check_env_var(name: str, min_length: int = 10) -> DependencyStatus:
    """Check an environment variable is set and non-trivial."""
    val = os.environ.get(name, "")
    if not val:
        return DependencyStatus(name=name, healthy=False, message="Not set", category="api_key")
    if len(val) < min_length:
        return DependencyStatus(
            name=name, healthy=False, message=f"Too short ({len(val)} chars)", category="api_key"
        )
    return DependencyStatus(name=name, healthy=True, message="Set", category="api_key")


def check_binary(name: str) -> DependencyStatus:
    """Check a binary is on PATH and responds to --help."""
    import shutil

    path = shutil.which(name)
    if not path:
        return DependencyStatus(
            name=name, healthy=False, message="Not found on PATH", category="binary"
        )
    try:
        subprocess.run([path, "--help"], capture_output=True, timeout=5)
        return DependencyStatus(name=name, healthy=True, message=f"OK ({path})", category="binary")
    except (subprocess.TimeoutExpired, OSError) as e:
        return DependencyStatus(name=name, healthy=False, message=str(e), category="binary")


def check_git_repo(path: Path, name: str) -> DependencyStatus:
    """Check a git repo is accessible and has a valid HEAD."""
    if not path.exists():
        return DependencyStatus(
            name=name, healthy=False, message="Path missing", category="git_repo"
        )
    git_dir = path / ".git"
    if not git_dir.exists():
        return DependencyStatus(
            name=name, healthy=False, message="Not a git repo", category="git_repo"
        )
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(path),
        )
        if result.returncode != 0:
            return DependencyStatus(
                name=name, healthy=False, message="git rev-parse failed", category="git_repo"
            )
        return DependencyStatus(name=name, healthy=True, message="OK", category="git_repo")
    except Exception as e:
        return DependencyStatus(name=name, healthy=False, message=str(e), category="git_repo")


def run_dependency_check() -> list[DependencyStatus]:
    """Run all dependency checks."""
    results = []

    # API keys
    for key in ["ZHIPU_API_KEY", "ANTHROPIC_API_KEY"]:
        results.append(check_env_var(key))

    # Critical binaries
    for binary in ["goose", "sortase", "cytokinesis", "engram", "assay"]:
        results.append(check_binary(binary))

    # Git repos
    results.append(check_git_repo(germline, "germline"))
    results.append(check_git_repo(epigenome, "epigenome"))

    return results


def report() -> str:
    """Generate human-readable dependency report."""
    results = run_dependency_check()
    healthy = sum(1 for r in results if r.healthy)
    total = len(results)
    lines = [f"Dependency check: {healthy}/{total} healthy"]
    for r in results:
        status = "OK" if r.healthy else "FAIL"
        lines.append(f"  [{status}] {r.category}/{r.name}: {r.message}")
    return "\n".join(lines)
