from __future__ import annotations

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
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Gemini decomposition failed")
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
    block_contents = re.findall(
        r"```[\w]*\s*\n(.*?)```", spec_text, flags=re.DOTALL
    )
    estimated_lines = sum(len(b.strip().splitlines()) for b in block_contents)

    # Count verification commands: code blocks under ## Verification or ### Verification
    verification_commands = 0
    ver_sections = re.split(r"^#{1,3}\s*Verification\b", spec_text, flags=re.MULTILINE | re.IGNORECASE)
    for section in ver_sections[1:]:
        ver_code_opens = re.findall(r"^```", section, flags=re.MULTILINE)
        verification_commands += len(ver_code_opens) // 2

    # Count files referenced: lines matching "- path/to/file.ext" or bare paths
    file_pattern = re.compile(
        r"(?:^[\s*-]+)"            # list item prefix
        r"([\w./~-]+\.\w{1,12})"   # path with extension
        r"(?::|\s|$)",             # followed by colon, space, or end
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
    score = files_referenced * 2 + num_code_blocks + verification_commands * 2 + (estimated_lines // 20)
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


def decompose_plan(plan_file: str | Path, smart: bool = False, timeout_sec: int = 180) -> list[TaskSpec]:
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
