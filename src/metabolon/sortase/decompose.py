
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ComplexityScore:
    level: str
    files_referenced: int
    code_blocks: int
    verification_commands: int
    estimated_lines: int


@dataclass(frozen=True)
class TaskSpec:
    name: str
    description: str
    spec: str
    files: list[str]
    signal: str = "default"
    prerequisite: str | None = None
    temp_file: str | None = None


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(?:yaml)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)


def _read_plan(plan_file: Path) -> str:
    return plan_file.read_text(encoding="utf-8")


def _parse_yaml_tasks(raw: str) -> list[TaskSpec]:
    payload = yaml.safe_load(raw)
    if isinstance(payload, dict):
        payload = payload.get("tasks", [])

    tasks: list[TaskSpec] = []
    for idx, item in enumerate(payload or [], start=1):
        if not isinstance(item, dict):
            raise ValueError("YAML task entries must be mappings")
        tasks.append(
            TaskSpec(
                name=item.get("name") or f"task-{idx}",
                description=item.get("description") or item.get("spec") or f"Task {idx}",
                files=list(item.get("files") or []),
                signal=item.get("signal") or "default",
                spec=item.get("spec") or item.get("description") or "",
                prerequisite=item.get("prerequisite"),
            )
        )
    return tasks


def _write_temp_specs(tasks: list[TaskSpec]) -> list[TaskSpec]:
    materialized: list[TaskSpec] = []
    for idx, task in enumerate(tasks, start=1):
        path = Path(tempfile.gettempdir()) / f"sortase-task-{idx}.txt"
        path.write_text(task.spec, encoding="utf-8")
        materialized.append(
            TaskSpec(
                name=task.name,
                description=task.description,
                files=task.files,
                signal=task.signal,
                spec=task.spec,
                prerequisite=task.prerequisite,
                temp_file=str(path),
            )
        )
    return materialized


def _gemini_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


def _run_gemini_decomposition(plan_text: str, timeout_sec: int) -> str:
    prompt = (
        "Read this plan and decompose it into independent tasks.\n"
        "For each task, output a YAML block:\n"
        "- name: short-kebab-name\n"
        "- description: one line\n"
        "- files: list of files that will be created/modified\n"
        "- signal: rust | algorithmic | multi-file | boilerplate | default\n"
        "- spec: the full self-contained prompt for this task\n\n"
        "Tasks are independent if they touch different files and don't depend on each other's output.\n"
        "If tasks share a dependency (e.g. a shared types file), mark the dependency as a prerequisite task that must run first.\n\n"
        "Plan:\n"
        f"{plan_text}"
    )
    command = ["gemini", "-m", "gemini-3.1-pro-preview", "-p", prompt, "--yolo"]
    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        env=_gemini_env(),
        text=True,
        timeout=timeout_sec,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            completed.stderr.strip() or completed.stdout.strip() or "Gemini decomposition failed"
        )
    return completed.stdout


def estimate_complexity(spec_text: str) -> ComplexityScore:
    """Estimate task complexity from spec text.

    Counts files referenced, fenced code blocks, verification commands,
    and estimated lines of code. Returns a ComplexityScore with a level
    of "simple", "medium", or "complex".
    """
    # Count fenced code blocks (``` ... ```)
    code_blocks = re.findall(r"^```[\w]*\s*$", spec_text, flags=re.MULTILINE)
    num_code_blocks = len(code_blocks) // 2  # opening + closing

    # Extract code block contents for line counting
    block_contents = re.findall(r"```[\w]*\s*\n(.*?)```", spec_text, flags=re.DOTALL)
    estimated_lines = sum(len(b.strip().splitlines()) for b in block_contents)

    # Count verification commands: code blocks under ## Verification or ### Verification
    verification_commands = 0
    ver_sections = re.split(
        r"^#{1,3}\s*Verification\b", spec_text, flags=re.MULTILINE | re.IGNORECASE
    )
    for section in ver_sections[1:]:
        ver_code_opens = re.findall(r"^```", section, flags=re.MULTILINE)
        verification_commands += len(ver_code_opens) // 2

    # Count files referenced: list items or inline file paths like README.md.
    file_pattern = re.compile(
        r"(?<![\w/.-])"  # avoid matching inside longer tokens
        r"([\w./~-]+\.\w{1,12})"  # path with extension
        r"(?::|\s|$)",  # followed by colon, space, or end
        flags=re.MULTILINE,
    )
    file_matches = file_pattern.findall(spec_text)
    # Deduplicate while preserving order
    seen_files: set[str] = set()
    unique_files: list[str] = []
    for f in file_matches:
        if f not in seen_files:
            seen_files.add(f)
            unique_files.append(f)
    files_referenced = len(unique_files)

    # Classify complexity
    score = files_referenced + num_code_blocks + verification_commands + (estimated_lines // 50)
    if score <= 2:
        level = "simple"
    elif score <= 6:
        level = "medium"
    else:
        level = "complex"

    return ComplexityScore(
        level=level,
        files_referenced=files_referenced,
        code_blocks=num_code_blocks,
        verification_commands=verification_commands,
        estimated_lines=estimated_lines,
    )


def score_spec_quality(spec_text: str) -> dict[str, int]:
    """Score a plan spec on five axes before dispatch.

    Each axis scores 0-10. Returns a dict with individual scores and total.

    Axes:
        clarity:      Does the spec name an explicit output path?
        scope:        Single deliverable vs. multiple?
        constraints:  Has "do not" / negative instructions?
        verification: Has a test/verification command?
        tool_budget:  Specifies max tool calls?
    """
    text = spec_text.strip()
    if not text:
        return {
            "clarity": 0,
            "scope": 0,
            "constraints": 0,
            "verification": 0,
            "tool_budget": 0,
            "total": 0,
        }

    # --- clarity: explicit output path? ---
    clarity = 0
    output_patterns = [
        r"(?i)output\s+path",
        r"(?i)write\s+(?:the\s+result\s+)?to\b",
        r"(?i)save\s+to\b",
        r"(?i)deliverable\b",
        r"(?i)output\b.*[:=]",
        r"(?:^|\n)\s*##\s*Output\b",
    ]
    if any(re.search(p, text) for p in output_patterns):
        clarity += 7
    # Check for actual file path (something.py, something.md, etc.)
    if re.search(r"(?:~/|/|\./)[\w/.-]+\.\w{1,12}", text):
        clarity += 3
    clarity = min(clarity, 10)

    # --- scope: single deliverable vs multiple ---
    scope = 0
    scope_lower = text.lower()
    if re.search(r"single\s+deliverable", scope_lower):
        scope = 10
    elif re.search(r"(?i)^#{1,3}\s*scope\b", text, flags=re.MULTILINE):
        scope = 8
    elif re.search(r"\bscope\b", scope_lower):
        scope = 5
    # Penalise multiple deliverables
    deliverable_mentions = len(re.findall(r"(?i)deliverable", text))
    if deliverable_mentions > 1:
        scope -= 3
    # Check for multiple output files listed
    file_list_pattern = re.findall(
        r"(?:^[\s*-]+)" r"([\w./~-]+\.\w{1,12})" r"(?::|\s|$)",
        text,
        flags=re.MULTILINE,
    )
    unique_output_files = len(set(file_list_pattern))
    if unique_output_files > 3:
        scope -= 3
    elif unique_output_files > 1:
        scope -= 1
    # Mention of "and" between file paths suggests multiple deliverables
    if re.search(r"\.py\b.*\band\b.*\.py\b", text):
        scope -= 2
    scope = max(min(scope, 10), 0)

    # --- constraints: has "do not" / negative instructions? ---
    constraints = 0
    do_not_count = len(re.findall(r"(?i)\bdo\s+not\b", text))
    never_count = len(re.findall(r"(?i)\bnever\b", text))
    must_not_count = len(re.findall(r"(?i)\bmust\s+not\b", text))
    total_constraints = do_not_count + never_count + must_not_count
    if total_constraints >= 3:
        constraints = 10
    elif total_constraints == 2:
        constraints = 8
    elif total_constraints == 1:
        constraints = 5
    # Bonus: explicit Constraints section
    if re.search(r"(?i)^#{1,3}\s*constraints?\b", text, flags=re.MULTILINE):
        constraints = min(constraints + 3, 10)

    # --- verification: has test command? ---
    verification = 0
    if re.search(r"(?i)^#{1,3}\s*verification\b", text, flags=re.MULTILINE):
        verification += 5
    if re.search(r"pytest\b", text):
        verification += 3
    elif re.search(r"(?:test|check|verify)\b", text, flags=re.IGNORECASE):
        verification += 2
    if re.search(r"```(?:bash|sh)?\s*\n.*(?:pytest|test|run)", text, flags=re.DOTALL):
        verification += 2
    verification = min(verification, 10)

    # --- tool_budget: specifies max tool calls? ---
    tool_budget = 0
    if re.search(r"(?i)tool\s+budget\b", text):
        tool_budget += 7
    if re.search(r"(?i)max\s+\d+\s+tool", text) or re.search(r"(?i)max\s+\d+\s+call", text):
        tool_budget += 3
    if re.search(r"(?i)budget\b", text):
        tool_budget += 2
    tool_budget = min(tool_budget, 10)

    total = clarity + scope + constraints + verification + tool_budget
    return {
        "clarity": clarity,
        "scope": scope,
        "constraints": constraints,
        "verification": verification,
        "tool_budget": tool_budget,
        "total": total,
    }


def lint_plan(plan_text: str) -> list[str]:
    """Check a plan file for common issues.

    Returns a list of warning strings. An empty list means no issues found.

    Checks:
        - Missing output path
        - Missing constraints section
        - No verification command
        - References to /tmp/ (should be ~/germline/loci/plans/)
        - Contains placeholder markers
    """
    warnings: list[str] = []
    text = plan_text.strip()

    if not text:
        return [
            "No output path specified",
            "No constraints section found",
            "No verification command found",
        ]

    # Missing output path
    output_indicators = [
        r"(?i)output\s+path",
        r"(?i)write\s+(?:the\s+result\s+)?to\b",
        r"(?i)save\s+to\b",
        r"(?i)deliverable\b",
        r"(?:^|\n)\s*##\s*Output\b",
    ]
    has_output = any(re.search(p, text) for p in output_indicators)
    if not has_output:
        warnings.append("No output path specified")

    # Missing constraints section
    has_constraints = bool(re.search(r"(?i)^#{1,3}\s*constraints?\b", text, flags=re.MULTILINE))
    if not has_constraints:
        warnings.append("No constraints section found")

    # No verification command
    has_verification = bool(re.search(r"(?i)^#{1,3}\s*verification\b", text, flags=re.MULTILINE))
    if not has_verification:
        warnings.append("No verification command found")

    # References to /tmp/
    tmp_matches = re.findall(r"/tmp/[\w/.-]+", text)
    for match in tmp_matches:
        warnings.append(f"References /tmp/ path: {match} — use ~/germline/loci/plans/ instead")

    # Placeholder markers
    for marker in ("TODO", "FIXME"):
        marker_matches = re.findall(rf"\b{marker}\b", text)
        for _ in marker_matches:
            warnings.append(f"Contains placeholder marker: {marker}")

    return warnings


def decompose_plan(
    plan_file: str | Path, smart: bool = False, timeout_sec: int = 180
) -> list[TaskSpec]:
    path = Path(plan_file)
    plan_text = _read_plan(path)

    if path.suffix.lower() in {".yaml", ".yml"} and not smart:
        return _write_temp_specs(_parse_yaml_tasks(plan_text))

    if not smart:
        return _write_temp_specs(
            [
                TaskSpec(
                    name=path.stem.replace(" ", "-"),
                    description=path.name,
                    files=[],
                    signal="default",
                    spec=plan_text,
                )
            ]
        )

    gemini_output = _strip_fences(_run_gemini_decomposition(plan_text, timeout_sec=timeout_sec))
    return _write_temp_specs(_parse_yaml_tasks(gemini_output))
