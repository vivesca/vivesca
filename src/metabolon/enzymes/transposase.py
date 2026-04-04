"""transposase — MCP tool for systematic codebase renames.

Actions: scan|plan|execute|verify

Named after the enzyme that catalyzes cut-and-paste transposition of
genetic elements. Recognizes inverted terminal repeats (name variants)
and systematically transposes them to new sequences.

Usage via MCP:
    transposase(action="scan", old_name="golem")
    transposase(action="plan", old_name="golem", new_name="ribosome")
    transposase(action="execute", old_name="golem", new_name="ribosome", dry_run=False)
    transposase(action="verify", old_name="golem")
"""

import json
import subprocess
from pathlib import Path
from typing import Any

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations
from pydantic import Field

from metabolon.morphology import EffectorResult, Secretion

GERMLINE = Path.home() / "germline"
MARKS = Path.home() / "epigenome" / "marks"

# Directories to always exclude from rename
_EXCLUDE_DIRS = {".git", "__pycache__", ".worktrees", "node_modules", ".venv"}

# File patterns to skip (historical/generated)
_EXCLUDE_GLOBS = [
    "loci/plans/*",  # Historical plans — leave as-is
    "loci/pulse/*",  # Historical pulse logs
    "loci/copia/*",  # Historical copies
    "*.lock",  # Lock files (auto-generated)
    "*.bak*",  # Backup files
    "*.pre-dedup",  # Backup variants
]


class TransposaseResult(Secretion):
    """Structured output from transposase."""

    output: str
    data: dict[str, Any] = Field(default_factory=dict)
    files_affected: int = 0
    occurrences: int = 0


def _generate_variants(old: str, new: str) -> list[tuple[str, str]]:
    """Generate all case variants from a base name pair.

    Returns pairs sorted longest-first to avoid partial replacements.
    """
    variants = [
        (old.lower(), new.lower()),  # golem -> ribosome
        (old.capitalize(), new.capitalize()),  # Golem -> Ribosome
        (old.upper(), new.upper()),  # GOLEM -> RIBOSOME
    ]
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for pair in variants:
        if pair not in seen:
            seen.add(pair)
            unique.append(pair)
    return unique


def _build_exclude_args() -> list[str]:
    """Build ripgrep exclusion arguments."""
    args = []
    for dirname in _EXCLUDE_DIRS:
        args.extend(["--glob", f"!{dirname}"])
    for pattern in _EXCLUDE_GLOBS:
        args.extend(["--glob", f"!{pattern}"])
    return args


def _rg_search(pattern: str, path: Path, count: bool = False) -> str:
    """Run ripgrep and return output."""
    cmd = ["rg", "--no-heading"]
    if count:
        cmd.append("--count")
    else:
        cmd.extend(["-n", "--color", "never"])
    cmd.extend(["-i", pattern])
    cmd.extend(_build_exclude_args())
    cmd.append(str(path))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout.strip()


def _scan(old_name: str, scope: str) -> TransposaseResult:
    """Find all occurrences of old_name across the codebase."""
    search_paths = []
    if scope in ("all", "code"):
        search_paths.append(GERMLINE / "src")
        search_paths.append(GERMLINE / "effectors")
        search_paths.append(GERMLINE / "assays")
    if scope in ("all", "skills"):
        search_paths.append(GERMLINE / "membrane")
    if scope in ("all", "config"):
        for config_file in [
            "genome.md",
            "anatomy.md",
            "methylome.md",
            "AGENTS.md",
            "pyproject.toml",
        ]:
            config_path = GERMLINE / config_file
            if config_path.exists():
                search_paths.append(config_path)
    if scope in ("all", "marks"):
        search_paths.append(MARKS)

    results_by_file: dict[str, int] = {}
    total_occurrences = 0

    for search_path in search_paths:
        if not search_path.exists():
            continue
        count_output = _rg_search(old_name, search_path, count=True)
        for line in count_output.splitlines():
            if ":" in line:
                filepath, count_str = line.rsplit(":", 1)
                count_val = int(count_str.strip())
                results_by_file[filepath] = count_val
                total_occurrences += count_val

    # Also find files/dirs with the name in their path
    file_renames = []
    for search_path in [
        GERMLINE / "src",
        GERMLINE / "effectors",
        GERMLINE / "assays",
        GERMLINE / "loci",
    ]:
        if not search_path.exists():
            continue
        result = subprocess.run(
            [
                "find",
                str(search_path),
                "-name",
                f"*{old_name}*",
                "-not",
                "-path",
                "*/.git/*",
                "-not",
                "-path",
                "*/__pycache__/*",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        file_renames.extend(result.stdout.strip().splitlines())

    return TransposaseResult(
        output=f"Found {total_occurrences} occurrences in {len(results_by_file)} files, {len(file_renames)} files to rename",
        data={
            "by_file": dict(sorted(results_by_file.items(), key=lambda item: -item[1])),
            "file_renames": file_renames,
        },
        files_affected=len(results_by_file) + len(file_renames),
        occurrences=total_occurrences,
    )


def _plan(
    old_name: str, new_name: str, name_map: dict[str, str] | None = None
) -> TransposaseResult:
    """Generate a rename plan showing all replacements."""
    scan_result = _scan(old_name, "all")

    # Build replacement list: explicit map first, then auto-generated variants
    replacements: list[tuple[str, str]] = []
    if name_map:
        replacements.extend(sorted(name_map.items(), key=lambda pair: -len(pair[0])))
    replacements.extend(_generate_variants(old_name, new_name))

    return TransposaseResult(
        output=f"Plan: {scan_result.occurrences} replacements across {scan_result.files_affected} files",
        data={
            "replacements": [[old_val, new_val] for old_val, new_val in replacements],
            "scan": scan_result.data,
        },
        files_affected=scan_result.files_affected,
        occurrences=scan_result.occurrences,
    )


def _execute(
    old_name: str,
    new_name: str,
    name_map: dict[str, str] | None = None,
    dry_run: bool = True,
    scope: str = "all",
    exclude: list[str] | None = None,
) -> TransposaseResult:
    """Execute the rename. dry_run=True by default for safety."""
    if dry_run:
        plan = _plan(old_name, new_name, name_map)
        plan.output = f"[DRY RUN] {plan.output} — set dry_run=false to execute"
        return plan

    # Build replacement list
    replacements: list[tuple[str, str]] = []
    if name_map:
        replacements.extend(sorted(name_map.items(), key=lambda pair: -len(pair[0])))
    replacements.extend(_generate_variants(old_name, new_name))

    files_changed = 0
    total_replacements = 0
    errors: list[str] = []

    # Phase 1: File renames (git mv)
    scan = _scan(old_name, scope)
    for filepath in scan.data.get("file_renames", []):
        old_path = Path(filepath)
        new_path = Path(filepath.replace(old_name, new_name))
        if old_path.exists() and old_path != new_path:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                ["git", "mv", str(old_path), str(new_path)],
                capture_output=True,
                text=True,
                cwd=GERMLINE,
                timeout=10,
            )
            if result.returncode == 0:
                files_changed += 1
            else:
                # Fallback to filesystem rename for non-git files
                try:
                    old_path.rename(new_path)
                    files_changed += 1
                except OSError as exc:
                    errors.append(f"rename {old_path} -> {new_path}: {exc}")

    # Phase 2: Content replacements (longest match first)
    search_paths = []
    if scope in ("all", "code"):
        search_paths.extend([GERMLINE / "src", GERMLINE / "effectors", GERMLINE / "assays"])
    if scope in ("all", "skills"):
        search_paths.append(GERMLINE / "membrane")
    if scope in ("all", "config"):
        search_paths.extend(
            [
                GERMLINE / f
                for f in ["genome.md", "anatomy.md", "methylome.md"]
                if (GERMLINE / f).exists()
            ]
        )
    if scope in ("all", "marks"):
        search_paths.append(MARKS)

    exclude_set = set(exclude or [])

    for search_path in search_paths:
        if not search_path.exists():
            continue
        # Find files containing old_name
        rg_output = _rg_search(old_name, search_path, count=True)
        for line in rg_output.splitlines():
            if ":" not in line:
                continue
            filepath = line.rsplit(":", 1)[0]
            if any(Path(filepath).match(pat) for pat in exclude_set):
                continue

            try:
                content = Path(filepath).read_text()
                new_content = content
                for old_val, new_val in replacements:
                    new_content = new_content.replace(old_val, new_val)
                if new_content != content:
                    Path(filepath).write_text(new_content)
                    files_changed += 1
                    total_replacements += content.count(old_name.lower())
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(f"replace in {filepath}: {exc}")

    # Phase 3: Memory mark renames
    if scope in ("all", "marks") and MARKS.exists():
        for mark_file in MARKS.glob(f"*{old_name}*"):
            new_mark_name = mark_file.name.replace(old_name, new_name)
            new_mark_path = mark_file.parent / new_mark_name
            try:
                mark_file.rename(new_mark_path)
                # Update frontmatter
                content = new_mark_path.read_text()
                for old_val, new_val in replacements:
                    content = content.replace(old_val, new_val)
                new_mark_path.write_text(content)
                files_changed += 1
            except OSError as exc:
                errors.append(f"mark rename {mark_file} -> {new_mark_path}: {exc}")

    output = f"Renamed {files_changed} files with {total_replacements} replacements"
    if errors:
        output += f" ({len(errors)} errors)"

    return TransposaseResult(
        output=output,
        data={"errors": errors, "files_changed": files_changed},
        files_affected=files_changed,
        occurrences=total_replacements,
    )


def _verify(old_name: str) -> TransposaseResult:
    """Verify zero remaining references to old_name."""
    scan = _scan(old_name, "all")
    if scan.occurrences == 0:
        return TransposaseResult(
            output=f"Clean: zero references to '{old_name}' found",
            data={"clean": True},
            files_affected=0,
            occurrences=0,
        )
    return TransposaseResult(
        output=f"DIRTY: {scan.occurrences} references to '{old_name}' remain in {scan.files_affected} files",
        data={"clean": False, **scan.data},
        files_affected=scan.files_affected,
        occurrences=scan.occurrences,
    )


@tool(
    name="transposase",
    description="scan|plan|execute|verify — systematic codebase rename via cut-and-paste transposition",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
def transposase(
    action: str = "scan",
    old_name: str = "",
    new_name: str = "",
    scope: str = "all",
    dry_run: bool = True,
    name_map: str = "",
    exclude: str = "",
) -> TransposaseResult | EffectorResult:
    """Systematic codebase rename engine.

    Parameters
    ----------
    action : str
        scan: find all occurrences of old_name
        plan: generate rename map (old_name + new_name required)
        execute: apply rename (dry_run=true by default)
        verify: confirm zero remaining references
    old_name : str
        The name to find/replace (base form, e.g. "golem")
    new_name : str
        The replacement name (base form, e.g. "ribosome")
    scope : str
        all | code | skills | marks | config
    dry_run : bool
        If true, preview without changes (default: true)
    name_map : str
        JSON dict of explicit overrides, e.g. '{"GolemWorkflow": "TranslationWorkflow"}'
    exclude : str
        Comma-separated glob patterns to skip
    """
    action = action.lower().strip()

    if not old_name:
        return EffectorResult(success=False, message="old_name is required")

    parsed_map: dict[str, str] | None = None
    if name_map:
        try:
            parsed_map = json.loads(name_map)
        except json.JSONDecodeError:
            return EffectorResult(
                success=False, message=f"Invalid name_map JSON: {name_map[:100]}"
            )

    parsed_exclude = (
        [pat.strip() for pat in exclude.split(",") if pat.strip()] if exclude else None
    )

    if action == "scan":
        return _scan(old_name, scope)

    if action == "plan":
        if not new_name:
            return EffectorResult(success=False, message="new_name is required for plan action")
        return _plan(old_name, new_name, parsed_map)

    if action == "execute":
        if not new_name:
            return EffectorResult(success=False, message="new_name is required for execute action")
        return _execute(old_name, new_name, parsed_map, dry_run, scope, parsed_exclude)

    if action == "verify":
        return _verify(old_name)

    return EffectorResult(
        success=False, message="Unknown action. Valid: scan, plan, execute, verify"
    )
