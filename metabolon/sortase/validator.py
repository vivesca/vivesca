from __future__ import annotations

import re
import shlex
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


def check_dependency_pollution(pyproject_path: Path | None = None, cargo_path: Path | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if pyproject_path and pyproject_path.exists():
        payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        project = payload.get("project", {})
        main_dependencies = {_normalize_dep(dep) for dep in project.get("dependencies", [])}
        optional_groups = project.get("optional-dependencies", {})
        optional_dependencies = {
            _normalize_dep(dep)
            for deps in optional_groups.values()
            for dep in deps
        }
        duplicates = sorted(dep for dep in optional_dependencies if dep and dep in main_dependencies)
        if duplicates:
            issues.append(
                ValidationIssue(
                    check="dependency-pollution",
                    message=f"Optional dependencies promoted to main: {', '.join(duplicates)}",
                )
            )

    return issues


def check_scope(project_dir: Path, max_files: int = 20, changed_files: list[str] | None = None) -> list[ValidationIssue]:
    if changed_files is None:
        completed = subprocess.run(
            ["git", "diff", "--stat", "--name-only"],
            cwd=project_dir,
            capture_output=True,
            check=False,
            text=True,
        )
        changed_files = [line for line in completed.stdout.splitlines() if line.strip()]

    if len(changed_files) > max_files:
        return [
            ValidationIssue(
                check="scope-check",
                message=f"Change scope is large: {len(changed_files)} files changed (limit {max_files})",
                severity="warning",
            )
        ]
    return []


def run_test_command(project_dir: Path, test_command: str | None) -> tuple[bool, str]:
    if not test_command:
        return True, "No test command provided"

    completed = subprocess.run(
        shlex.split(test_command),
        cwd=project_dir,
        capture_output=True,
        check=False,
        text=True,
    )
    output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)
    return completed.returncode == 0, output


def _get_head_content(project_dir: Path, relative_path: str) -> str | None:
    """Return file content at HEAD, or None if the file didn't exist at HEAD."""
    completed = subprocess.run(
        ["git", "show", f"HEAD:{relative_path}"],
        cwd=project_dir,
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def scan_for_placeholders(project_dir: Path, new_files: list[str]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    pattern = re.compile(r"\b(TODO|FIXME|stub)\b", flags=re.IGNORECASE)
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "target"}
    for relative_path in new_files:
        parts = Path(relative_path).parts
        if any(part in skip_dirs for part in parts):
            continue
        path = project_dir / relative_path
        if not path.exists() or not path.is_file():
            continue
        contents = path.read_text(encoding="utf-8", errors="ignore")

        # For files that existed at HEAD, only flag NEW markers.
        head_content = _get_head_content(project_dir, relative_path)
        if head_content is not None:
            head_markers = list(pattern.finditer(head_content))
            head_texts = {m.group() for m in head_markers}
            head_positions = {m.start() for m in head_markers}
            # Only flag markers that are genuinely new: different text
            # or different position from any marker in the HEAD version.
            has_new = any(
                m.group() not in head_texts or m.start() not in head_positions
                for m in pattern.finditer(contents)
            )
            if not has_new:
                continue
        else:
            # Brand-new file: flag if any markers present.
            if not pattern.search(contents):
                continue

        issues.append(
            ValidationIssue(
                check="placeholder-scan",
                message=f"Placeholder marker found in {relative_path}",
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
