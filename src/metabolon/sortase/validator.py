import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ValidationIssue:
    check: str
    message: str
    severity: str = "error"


def _normalize_dep(dep: str) -> str:
    return re.split(r"[<>=!~ \[]", dep, maxsplit=1)[0].strip().lower()


def check_dependency_pollution(
    pyproject_path: Path | None = None, cargo_path: Path | None = None
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if pyproject_path and pyproject_path.exists():
        payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        project = payload.get("project", {})
        main_dependencies = {_normalize_dep(dep) for dep in project.get("dependencies", [])}
        optional_groups = project.get("optional-dependencies", {})
        optional_dependencies = {
            _normalize_dep(dep) for deps in optional_groups.values() for dep in deps
        }
        duplicates = sorted(
            dep for dep in optional_dependencies if dep and dep in main_dependencies
        )
        if duplicates:
            issues.append(
                ValidationIssue(
                    check="dependency-pollution",
                    message=f"Optional dependencies promoted to main: {', '.join(duplicates)}",
                )
            )

    return issues


def check_scope(
    project_dir: Path,
    max_files: int = 20,
    max_dirs: int = 3,
    changed_files: list[str] | None = None,
) -> list[ValidationIssue]:
    if changed_files is None:
        completed = subprocess.run(
            ["git", "diff", "HEAD", "--stat", "--name-only"],
            cwd=project_dir,
            capture_output=True,
            check=False,
            text=True,
            timeout=300,
        )
        changed_files = [line for line in completed.stdout.splitlines() if line.strip()]

    issues: list[ValidationIssue] = []

    if len(changed_files) > max_files:
        issues.append(
            ValidationIssue(
                check="scope-check",
                message=f"Change scope is large: {len(changed_files)} files changed (limit {max_files})",
                severity="warning",
            )
        )

    top_dirs = {Path(f).parts[0] for f in changed_files if Path(f).parts}
    if len(top_dirs) > max_dirs:
        sorted_dirs = sorted(top_dirs)
        issues.append(
            ValidationIssue(
                check="directory-spread",
                message=(
                    f"Changes span {len(top_dirs)} top-level directories (limit {max_dirs}): "
                    f"{', '.join(sorted_dirs)}"
                ),
                severity="warning",
            )
        )

    return issues


def run_test_command(project_dir: Path, test_command: str | None) -> tuple[bool, str]:
    if not test_command:
        return True, "No test command provided"

    completed = subprocess.run(
        test_command,
        shell=True,
        cwd=project_dir,
        capture_output=True,
        check=False,
        text=True,
        timeout=300,
    )
    output = "\n".join(
        part for part in [completed.stdout.strip(), completed.stderr.strip()] if part
    )
    return completed.returncode == 0, output


def _get_head_content(project_dir: Path, relative_path: str) -> str | None:
    """Return file content at HEAD, or None if the file didn't exist at HEAD."""
    completed = subprocess.run(
        ["git", "show", f"HEAD:{relative_path}"],
        cwd=project_dir,
        capture_output=True,
        check=False,
        text=True,
        timeout=300,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def _has_new_markers(
    pattern: re.Pattern[str],
    contents: str,
    head_content: str | None,
) -> bool:
    """Return True if the file contains genuinely new markers vs HEAD."""
    if head_content is not None:
        head_markers = list(pattern.finditer(head_content))
        head_texts = {m.group() for m in head_markers}
        head_positions = {m.start() for m in head_markers}
        return any(
            m.group() not in head_texts or m.start() not in head_positions
            for m in pattern.finditer(contents)
        )
    return bool(pattern.search(contents))


_HARD_FAIL_PATTERN = re.compile(r"\bstub\b", flags=re.IGNORECASE)
_SOFT_WARN_PATTERN = re.compile(r"\b(TODO|FIXME)\b", flags=re.IGNORECASE)
_SKIP_DIRS = frozenset({".git", "node_modules", "__pycache__", ".venv", "target"})


def scan_for_placeholders(project_dir: Path, new_files: list[str]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for relative_path in new_files:
        parts = Path(relative_path).parts
        if any(part in _SKIP_DIRS for part in parts):
            continue
        path = project_dir / relative_path
        if not path.exists() or not path.is_file():
            continue
        contents = path.read_text(encoding="utf-8", errors="ignore")
        head_content = _get_head_content(project_dir, relative_path)

        if _has_new_markers(_HARD_FAIL_PATTERN, contents, head_content):
            issues.append(
                ValidationIssue(
                    check="placeholder-scan",
                    message=f"Stub marker found in {relative_path}",
                    severity="error",
                )
            )

        if _has_new_markers(_SOFT_WARN_PATTERN, contents, head_content):
            issues.append(
                ValidationIssue(
                    check="placeholder-scan",
                    message=f"TODO/FIXME marker found in {relative_path}",
                    severity="warning",
                )
            )
    return issues


def validate_execution(
    project_dir: Path,
    new_files: list[str],
    test_command: str | None = None,
    pyproject_path: Path | None = None,
    cargo_path: Path | None = None,
) -> list[ValidationIssue]:
    issues = []
    issues.extend(check_dependency_pollution(pyproject_path=pyproject_path, cargo_path=cargo_path))
    issues.extend(check_scope(project_dir))
    issues.extend(scan_for_placeholders(project_dir, new_files))
    tests_ok, test_output = run_test_command(project_dir, test_command)
    if not tests_ok:
        issues.append(ValidationIssue(check="tests", message=test_output or "Test command failed"))
    return issues


def check_test_coverage(
    project_dir: Path,
    threshold: float = 0.8,
) -> list[ValidationIssue]:
    """Check that test coverage meets the minimum threshold.

    Uses complement.coverage_summary to cross-reference metabolon/ modules
    with assays/ test files.

    Args:
        project_dir: Root of the project (contains metabolon/ and assays/)
        threshold: Minimum required coverage ratio (0.0 to 1.0), default 0.8

    Returns:
        List of ValidationIssues if coverage is below threshold.
    """
    from metabolon.organelles.complement import coverage_summary

    summary = coverage_summary(project_root=project_dir)

    total = summary["total_modules"]
    covered = summary["covered_modules"]
    ratio = summary["coverage_ratio"]

    # Edge case: no modules found
    if total == 0:
        return [
            ValidationIssue(
                check="test-coverage",
                message="No modules found to check coverage",
                severity="warning",
            )
        ]

    if ratio < threshold:
        missing = [m["module"] for m in summary["modules"] if not m["has_test"]]
        # Truncate list if too long
        if len(missing) > 5:
            missing_display = ", ".join(missing[:5]) + f" (and {len(missing) - 5} more)"
        else:
            missing_display = ", ".join(missing)
        return [
            ValidationIssue(
                check="test-coverage",
                message=(
                    f"Test coverage {covered}/{total} ({ratio:.1%}) is below "
                    f"threshold {threshold:.0%}. Missing tests for: {missing_display}"
                ),
                severity="warning",
            )
        ]

    return []
