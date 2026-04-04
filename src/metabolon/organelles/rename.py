
"""rename — deterministic rename across the organism.

Scans and renames a concept (name, directory, file, reference) across the
germline and epigenome repos in one atomic pass.

Steps (in order):
    1. scan       — grep old_name in .py/.md/.json/.yaml/.toml/.plist files
    2. dirs       — rename directories named old_name
    3. files      — rename files with old_name in filename
    4. contents   — sed-replace old_name → new_name in all matched files
    5. locus      — update metabolon/locus.py if it references old_name
    6. symlinks   — fix symlinks whose targets contain old_name
    7. verify     — report summary of changes
    8. commit     — git add + commit in each affected repo (unless --dry-run)
"""


import subprocess
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CONTENT_EXTENSIONS = frozenset({".py", ".md", ".json", ".yaml", ".yml", ".toml", ".plist"})

_DEFAULT_SCOPE = [
    Path.home() / "germline",
    Path.home() / "epigenome",
]

_LOCUS_PATH = Path.home() / "germline" / "metabolon" / "locus.py"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class ScanResult(NamedTuple):
    """Files that contain old_name in their content."""

    files: list[Path]
    total_matches: int


class RenameReport(NamedTuple):
    renamed_dirs: list[tuple[Path, Path]]  # (old, new)
    renamed_files: list[tuple[Path, Path]]  # (old, new)
    updated_contents: list[Path]
    updated_locus: bool
    fixed_symlinks: list[tuple[Path, str, str]]  # (link, old_target, new_target)


# ---------------------------------------------------------------------------
# Step 1: scan
# ---------------------------------------------------------------------------


def scan(old_name: str, scope: list[Path]) -> ScanResult:
    """Return all files containing old_name, plus total match count."""
    matched: list[Path] = []
    total = 0
    for root in scope:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in _CONTENT_EXTENSIONS:
                continue
            try:
                text = path.read_text(errors="replace")
            except (OSError, PermissionError):
                continue
            count = text.count(old_name)
            if count:
                matched.append(path)
                total += count
    return ScanResult(files=matched, total_matches=total)


# ---------------------------------------------------------------------------
# Step 2: rename directories
# ---------------------------------------------------------------------------


def rename_dirs(
    old_name: str, new_name: str, scope: list[Path], *, dry_run: bool
) -> list[tuple[Path, Path]]:
    """Find directories named old_name and rename them to new_name.

    Returns list of (old_path, new_path) pairs.
    Processes deepest paths first to avoid parent-before-child conflicts.
    """
    candidates: list[Path] = []
    for root in scope:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_dir() and path.name == old_name:
                candidates.append(path)

    # Sort deepest-first so we don't rename a parent before its children
    candidates.sort(key=lambda p: len(p.parts), reverse=True)

    renamed: list[tuple[Path, Path]] = []
    for old_path in candidates:
        new_path = old_path.parent / new_name
        if dry_run:
            renamed.append((old_path, new_path))
        else:
            old_path.rename(new_path)
            renamed.append((old_path, new_path))
    return renamed


# ---------------------------------------------------------------------------
# Step 3: rename files
# ---------------------------------------------------------------------------


def rename_files(
    old_name: str, new_name: str, scope: list[Path], *, dry_run: bool
) -> list[tuple[Path, Path]]:
    """Find files with old_name in their filename and rename them.

    Returns list of (old_path, new_path) pairs.
    """
    candidates: list[Path] = []
    for root in scope:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and old_name in path.name:
                candidates.append(path)

    renamed: list[tuple[Path, Path]] = []
    for old_path in candidates:
        new_name_str = old_path.name.replace(old_name, new_name)
        new_path = old_path.parent / new_name_str
        if dry_run:
            renamed.append((old_path, new_path))
        else:
            old_path.rename(new_path)
            renamed.append((old_path, new_path))
    return renamed


# ---------------------------------------------------------------------------
# Step 4: update file contents
# ---------------------------------------------------------------------------


def update_contents(
    old_name: str, new_name: str, files: list[Path], *, dry_run: bool
) -> list[Path]:
    """Replace old_name with new_name in file contents.

    Skips files that no longer exist (may have been renamed in step 3).
    Returns list of files actually updated.
    """
    updated: list[Path] = []
    for path in files:
        if not path.exists():
            continue
        try:
            original = path.read_text(errors="replace")
        except (OSError, PermissionError):
            continue
        if old_name not in original:
            continue
        if not dry_run:
            path.write_text(original.replace(old_name, new_name))
        updated.append(path)
    return updated


# ---------------------------------------------------------------------------
# Step 5: update locus.py
# ---------------------------------------------------------------------------


def update_locus(old_name: str, new_name: str, *, dry_run: bool) -> bool:
    """Update locus.py if it references old_name. Returns True if a change was made."""
    if not _LOCUS_PATH.exists():
        return False
    try:
        original = _LOCUS_PATH.read_text()
    except (OSError, PermissionError):
        return False
    if old_name not in original:
        return False
    if not dry_run:
        _LOCUS_PATH.write_text(original.replace(old_name, new_name))
    return True


# ---------------------------------------------------------------------------
# Step 6: fix symlinks
# ---------------------------------------------------------------------------


def fix_symlinks(
    old_name: str, new_name: str, scope: list[Path], *, dry_run: bool
) -> list[tuple[Path, str, str]]:
    """Find symlinks whose targets contain old_name and update them.

    Returns list of (link_path, old_target, new_target) tuples.
    """
    fixed: list[tuple[Path, str, str]] = []
    for root in scope:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_symlink():
                continue
            try:
                target = str(path.readlink())
            except (OSError, AttributeError):
                # Fallback for Python < 3.9
                import os

                try:
                    target = os.readlink(str(path))
                except OSError:
                    continue
            if old_name not in target:
                continue
            new_target = target.replace(old_name, new_name)
            if not dry_run:
                path.unlink()
                path.symlink_to(new_target)
            fixed.append((path, target, new_target))
    return fixed


# ---------------------------------------------------------------------------
# Step 7: verify (summary)
# ---------------------------------------------------------------------------


def build_report(
    scan_result: ScanResult,
    renamed_dirs: list[tuple[Path, Path]],
    renamed_files: list[tuple[Path, Path]],
    updated_contents: list[Path],
    updated_locus: bool,
    fixed_symlinks: list[tuple[Path, str, str]],
) -> str:
    """Build a human-readable summary of what was (or would be) changed."""
    lines: list[str] = []
    lines.append(
        f"scan: {scan_result.total_matches} occurrences in {len(scan_result.files)} files"
    )

    if renamed_dirs:
        lines.append(f"\nrenamed dirs ({len(renamed_dirs)}):")
        for old, new in renamed_dirs:
            lines.append(f"  {old} -> {new.name}")

    if renamed_files:
        lines.append(f"\nrenamed files ({len(renamed_files)}):")
        for old, new in renamed_files:
            lines.append(f"  {old.name} -> {new.name}")

    if updated_contents:
        lines.append(f"\nupdated contents ({len(updated_contents)}):")
        for p in updated_contents:
            lines.append(f"  {p}")

    if updated_locus:
        lines.append(f"\nupdated locus.py: {_LOCUS_PATH}")

    if fixed_symlinks:
        lines.append(f"\nfixed symlinks ({len(fixed_symlinks)}):")
        for link, old_t, new_t in fixed_symlinks:
            lines.append(f"  {link}: {old_t} -> {new_t}")

    if not any([renamed_dirs, renamed_files, updated_contents, updated_locus, fixed_symlinks]):
        lines.append("\nnothing to change")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Step 8: git commit
# ---------------------------------------------------------------------------


def _find_git_repo(path: Path) -> Path | None:
    """Walk up from path to find the nearest .git directory."""
    current = path if path.is_dir() else path.parent
    for _ in range(20):
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def commit_changes(old_name: str, new_name: str, changed_paths: list[Path]) -> list[str]:
    """Run git add + commit in each affected repo. Returns list of commit messages."""
    if not changed_paths:
        return []

    # Group paths by their git repo
    repo_to_paths: dict[Path, list[Path]] = {}
    for p in changed_paths:
        repo = _find_git_repo(p)
        if repo:
            repo_to_paths.setdefault(repo, []).append(p)

    messages: list[str] = []
    for repo, paths in repo_to_paths.items():
        try:
            # Stage all changed paths
            for p in paths:
                subprocess.run(
                    ["git", "add", str(p)],
                    cwd=str(repo),
                    check=True,
                    capture_output=True,
                    timeout=300,
                )
            # Also stage any newly renamed items (git add -u covers deletions)
            subprocess.run(
                ["git", "add", "-u"],
                cwd=str(repo),
                check=True,
                capture_output=True,
                timeout=300,
            )
            msg = f"rename: {old_name} \u2192 {new_name}"
            result = subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=str(repo),
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                messages.append(f"{repo}: {msg}")
            else:
                # Nothing to commit or pre-commit hook message
                messages.append(f"{repo}: {result.stdout.strip() or result.stderr.strip()}")
        except subprocess.CalledProcessError as exc:
            messages.append(f"{repo}: git error — {exc}")
    return messages


# ---------------------------------------------------------------------------
# High-level runner (used by CLI and tests)
# ---------------------------------------------------------------------------


def _remap_paths(
    paths: list[Path],
    renamed_dirs: list[tuple[Path, Path]],
    renamed_files: list[tuple[Path, Path]],
) -> list[Path]:
    """Translate a list of pre-rename paths to their post-rename locations.

    After directories and files have been renamed on disk, any path that
    lived under a renamed directory needs its prefix updated, and any path
    that was itself renamed needs its full path updated.
    """
    # Build a lookup for directly renamed files: old -> new
    file_map = {old: new for old, new in renamed_files}

    remapped: list[Path] = []
    for p in paths:
        # Was the file itself renamed?
        if p in file_map:
            remapped.append(file_map[p])
            continue

        # Does the path live under a renamed directory?
        new_path = p
        for old_dir, new_dir in renamed_dirs:
            try:
                rel = p.relative_to(old_dir)
                new_path = new_dir / rel
                break
            except ValueError:
                continue
        remapped.append(new_path)
    return remapped


def run_rename(
    old_name: str,
    new_name: str,
    scope: list[Path],
    *,
    dry_run: bool,
) -> tuple[RenameReport, str]:
    """Execute the full rename pipeline. Returns (RenameReport, summary_text).

    In dry_run mode nothing is written to disk.
    """
    # Step 1: scan
    scan_result = scan(old_name, scope)

    # Step 2: rename directories
    renamed_dirs = rename_dirs(old_name, new_name, scope, dry_run=dry_run)

    # Step 3: rename files
    renamed_files = rename_files(old_name, new_name, scope, dry_run=dry_run)

    # Step 4: update file contents
    # Scanned paths may be stale after dirs/files were renamed; remap first.
    content_files: list[Path]
    if dry_run:
        # In dry-run nothing moved, paths are still valid
        content_files = list(scan_result.files)
    else:
        content_files = _remap_paths(scan_result.files, renamed_dirs, renamed_files)

    # Also include locus.py if it contains old_name
    if _LOCUS_PATH not in content_files and _LOCUS_PATH.exists():
        try:
            if old_name in _LOCUS_PATH.read_text(errors="replace"):
                content_files.append(_LOCUS_PATH)
        except (OSError, PermissionError):
            pass

    updated_contents = update_contents(old_name, new_name, content_files, dry_run=dry_run)

    # Step 5: update locus.py (idempotent if already covered above)
    updated_locus = update_locus(old_name, new_name, dry_run=dry_run)

    # Step 6: fix symlinks
    fixed_symlinks = fix_symlinks(old_name, new_name, scope, dry_run=dry_run)

    report = RenameReport(
        renamed_dirs=renamed_dirs,
        renamed_files=renamed_files,
        updated_contents=updated_contents,
        updated_locus=updated_locus,
        fixed_symlinks=fixed_symlinks,
    )

    summary = build_report(
        scan_result,
        renamed_dirs,
        renamed_files,
        updated_contents,
        updated_locus,
        fixed_symlinks,
    )

    return report, summary


# ---------------------------------------------------------------------------
# CLI entry point (called from pore.py)
# ---------------------------------------------------------------------------


def _cli(old_name: str, new_name: str, scope: list[str], dry_run: bool) -> None:
    """Execute rename and print report. Called by the vivesca CLI."""
    scope_paths = [Path(s).expanduser() for s in scope] if scope else _DEFAULT_SCOPE

    report, summary = run_rename(old_name, new_name, scope_paths, dry_run=dry_run)

    if dry_run:
        print("[dry-run] no files modified\n")

    print(summary)

    if not dry_run:
        # Collect all changed paths for git
        changed: list[Path] = []
        for old, new in report.renamed_dirs:
            changed.append(new)
        for old, new in report.renamed_files:
            changed.append(new)
        changed.extend(report.updated_contents)
        if report.updated_locus:
            changed.append(_LOCUS_PATH)
        for link, _, _ in report.fixed_symlinks:
            changed.append(link)

        commit_msgs = commit_changes(old_name, new_name, changed)
        if commit_msgs:
            print("\ngit commits:")
            for msg in commit_msgs:
                print(f"  {msg}")
